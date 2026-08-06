#!/usr/bin/env python3
"""
Harvester Makeup Builder

Purpose:
  Rebuild and analyze a Harvester-style dump that may be either:
    1) binary-byte text such as: 01010000 01001011 ...
    2) raw/corrupted ZIP/IPA bytes containing PK signatures
    3) clean secp256k1 double-and-add logs like publicTOnegated.txt

Outputs:
  - decoded/rebuilt binary candidates
  - extracted ZIP/IPA folders when possible
  - parsed Apple plist metadata when possible
  - parsed point/multiplier/double-add CSV/JSON when present

Usage:
  python harvester_builder.py harvestermakeup.txt --out out_harvester
  python harvester_builder.py publicTOnegated.txt --out out_points
"""
from __future__ import annotations

import argparse
import csv
import json
import plistlib
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional


BINARY_TOKEN_RE = re.compile(rb"(?<![01])([01]{8})(?![01])")
POINT_RE = re.compile(r"point\s*=\s*x:(\d+),\s*y:(\d+)", re.I)
MULT_BIN_RE = re.compile(r"multiplier\s*=\s*([01]{32,})\s*\(in binary\)", re.I)
DAD_RE = re.compile(
    r"(?:(\d+)\.\s*)?(double(?:\s+and\s+add)?|add|double)\s*=\s*x:(\d+),\s*y:(\d+)",
    re.I,
)
BLOCK_TITLE_RE = re.compile(r"^(N[^\n\r]*|point\s+1)\s*$", re.I | re.M)


@dataclass
class Step:
    index: Optional[int]
    operation: str
    x: int
    y: int


@dataclass
class ECCBlock:
    title: str
    point_x: Optional[int]
    point_y: Optional[int]
    multiplier_bin: Optional[str]
    multiplier_dec: Optional[int]
    steps: list[Step]


def read_input(path: Path) -> bytes:
    return path.read_bytes()


def decode_binary_token_stream(raw: bytes) -> Optional[bytes]:
    """Decode text containing 8-bit binary tokens into bytes."""
    tokens = BINARY_TOKEN_RE.findall(raw)
    if len(tokens) < 16:
        return None
    try:
        return bytes(int(tok, 2) for tok in tokens)
    except ValueError:
        return None


def printable_ratio(data: bytes) -> float:
    if not data:
        return 0.0
    printable = sum(1 for b in data if b in b"\r\n\t" or 32 <= b <= 126)
    return printable / len(data)


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def find_pk_offsets(data: bytes) -> list[int]:
    offsets = []
    start = 0
    while True:
        idx = data.find(b"PK\x03\x04", start)
        if idx == -1:
            break
        offsets.append(idx)
        start = idx + 1
    return offsets


def try_extract_zip(data: bytes, out_dir: Path, stem: str) -> list[Path]:
    extracted = []
    offsets = find_pk_offsets(data)
    # Try the full buffer first, then each PK offset.
    candidates = [(0, data)] + [(off, data[off:]) for off in offsets[:25]]
    seen = set()
    for off, blob in candidates:
        if blob in seen:
            continue
        seen.add(blob)
        zip_path = out_dir / f"{stem}_from_offset_{off}.zip"
        write_bytes(zip_path, blob)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                bad = zf.testzip()
                if bad is not None:
                    continue
                target = out_dir / f"extracted_offset_{off}"
                zf.extractall(target)
                extracted.append(target)
        except zipfile.BadZipFile:
            continue
        except Exception as exc:
            print(f"[warn] ZIP candidate at offset {off} could not extract cleanly: {exc}", file=sys.stderr)
    return extracted


def parse_plists(root: Path) -> dict[str, object]:
    found: dict[str, object] = {}
    for p in root.rglob("*.plist"):
        try:
            with p.open("rb") as f:
                found[str(p.relative_to(root))] = plistlib.load(f)
        except Exception:
            try:
                found[str(p.relative_to(root))] = p.read_text(errors="replace")[:20000]
            except Exception:
                pass
    return found


def parse_ecc_blocks(text: str) -> list[ECCBlock]:
    # Split loosely by long separator lines or repeated point headers.
    parts = re.split(r"={20,}|\n(?=N[-+]|point\s+1\s*\n)", text)
    blocks: list[ECCBlock] = []
    for i, part in enumerate(parts):
        if "double" not in part.lower() and "point" not in part.lower():
            continue
        title_match = BLOCK_TITLE_RE.search(part)
        title = title_match.group(1).strip() if title_match else f"block_{i}"
        point = POINT_RE.search(part)
        point_x = int(point.group(1)) if point else None
        point_y = int(point.group(2)) if point else None
        mult_match = MULT_BIN_RE.search(part)
        multiplier_bin = mult_match.group(1) if mult_match else None
        multiplier_dec = int(multiplier_bin, 2) if multiplier_bin else None
        steps: list[Step] = []
        for m in DAD_RE.finditer(part):
            idx = int(m.group(1)) if m.group(1) else None
            operation = " ".join(m.group(2).lower().split())
            steps.append(Step(idx, operation, int(m.group(3)), int(m.group(4))))
        if point_x or steps or multiplier_bin:
            blocks.append(ECCBlock(title, point_x, point_y, multiplier_bin, multiplier_dec, steps))
    return blocks


def write_ecc_outputs(blocks: list[ECCBlock], out_dir: Path) -> None:
    if not blocks:
        return
    json_path = out_dir / "ecc_blocks.json"
    json_path.write_text(json.dumps([asdict(b) for b in blocks], indent=2), encoding="utf-8")

    csv_path = out_dir / "ecc_steps.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["block", "title", "point_x", "point_y", "multiplier_dec", "step_index", "operation", "x", "y"])
        for bi, block in enumerate(blocks):
            for step in block.steps:
                w.writerow([
                    bi,
                    block.title,
                    block.point_x,
                    block.point_y,
                    block.multiplier_dec,
                    step.index,
                    step.operation,
                    step.x,
                    step.y,
                ])


def main() -> int:
    ap = argparse.ArgumentParser(description="Rebuild/analyze Harvester makeup binary dumps and ECC traces.")
    ap.add_argument("input", type=Path)
    ap.add_argument("--out", type=Path, default=Path("harvester_out"))
    args = ap.parse_args()

    raw = read_input(args.input)
    args.out.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "input": str(args.input),
        "raw_size": len(raw),
        "raw_printable_ratio": printable_ratio(raw),
    }

    decoded = decode_binary_token_stream(raw)
    buffers: list[tuple[str, bytes]] = [("raw", raw)]
    if decoded is not None:
        decoded_path = args.out / "decoded_from_binary_tokens.bin"
        write_bytes(decoded_path, decoded)
        buffers.append(("decoded", decoded))
        report["decoded_size"] = len(decoded)
        report["decoded_printable_ratio"] = printable_ratio(decoded)
        report["decoded_path"] = str(decoded_path)

    all_extracted: list[str] = []
    for name, data in buffers:
        offsets = find_pk_offsets(data)
        report[f"{name}_pk_offsets_first_25"] = offsets[:25]
        extracted = try_extract_zip(data, args.out, name)
        all_extracted.extend(str(p) for p in extracted)
        for root in extracted:
            plists = parse_plists(root)
            if plists:
                plist_json = args.out / f"plists_{root.name}.json"
                plist_json.write_text(json.dumps(plists, indent=2, default=str), encoding="utf-8")

    report["extracted_dirs"] = all_extracted

    # ECC trace parse from raw text and decoded text, when readable.
    texts = []
    for name, data in buffers:
        try:
            texts.append((name, data.decode("utf-8", errors="replace")))
        except Exception:
            pass
    all_blocks: list[ECCBlock] = []
    for name, text in texts:
        blocks = parse_ecc_blocks(text)
        if blocks:
            all_blocks.extend(blocks)
            report[f"{name}_ecc_blocks"] = len(blocks)
            report[f"{name}_ecc_steps"] = sum(len(b.steps) for b in blocks)
    write_ecc_outputs(all_blocks, args.out)

    report_path = args.out / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
