#!/usr/bin/env python3
"""EC-verify every unique d in tax_math packet against its puzzle pubkey."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import puzzle_band, pubkey_from_scalar, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402

PACKET = ROOT / "ARCHIVE" / "tax_math_trials_P135_P160_full_hex.txt"
PUZZLES = (135, 140, 145, 150, 155, 160)
OUT = ROOT / "ARCHIVE" / "packet_candidate_verify.txt"


def target_xy(n: int) -> tuple[int, int]:
    rsz = PUZZLE_RSZ[n]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    comp = bytes.fromhex(rsz.pub_compressed)
    py = yp if comp[0] == 2 else yn
    return px, py


def main() -> int:
    text = PACKET.read_text(encoding="utf-8")
    lines = ["PACKET CANDIDATE EC VERIFY — d*G == target pubkey", ""]
    hits: list[str] = []
    checked = 0

    for n in PUZZLES:
        m = re.search(rf"=== P{n} .*?===(.*?)(?=\n=== P|\Z)", text, re.S)
        if not m:
            lines.append(f"P{n}: block not found")
            continue
        tpx, tpy = target_xy(n)
        band_lo, band_hi, _ = puzzle_band(n)
        seen: set[int] = set()
        in_band = 0
        x_only = 0
        exact = 0

        for stage, hx in re.findall(r"\[([^\]]+)\]\s*\n\s*d = (0x[0-9a-f]+)", m.group(1)):
            d = int(hx, 16)
            if d in seen:
                continue
            seen.add(d)
            checked += 1
            if band_lo <= d < band_hi:
                in_band += 1
            gx, gy = pubkey_from_scalar(d)
            if gx == tpx and gy == tpy:
                exact += 1
                hits.append(f"P{n} HIT  [{stage}]  d={hx}")
            elif gx == tpx:
                x_only += 1

        lines.append(
            f"P{n}: unique={len(seen)}  in_band={in_band}  "
            f"exact_pubkey_hits={exact}  x_only_wrong_y={x_only}"
        )

    lines.extend(["", f"TOTAL unique checked: {checked}", ""])
    if hits:
        lines.append("EXACT HITS:")
        lines.extend(hits)
    else:
        lines.append("EXACT HITS: none")

    # cross-puzzle: does any P135 candidate solve P140 etc?
    lines.extend(["", "=== CROSS-PUZZLE CHECK (any d -> any higher pubkey) ==="])
    cross_hits: list[str] = []
    all_ds: list[tuple[int, str, int]] = []
    for n in PUZZLES:
        m = re.search(rf"=== P{n} .*?===(.*?)(?=\n=== P|\Z)", text, re.S)
        if not m:
            continue
        seen: set[int] = set()
        for stage, hx in re.findall(r"\[([^\]]+)\]\s*\n\s*d = (0x[0-9a-f]+)", m.group(1)):
            d = int(hx, 16)
            if d not in seen:
                seen.add(d)
                all_ds.append((n, stage, d))

    for target_n in PUZZLES:
        tpx, tpy = target_xy(target_n)
        band_lo, band_hi, _ = puzzle_band(target_n)
        for src_n, stage, d in all_ds:
            if not (band_lo <= d < band_hi):
                continue
            gx, gy = pubkey_from_scalar(d)
            if gx == tpx and gy == tpy:
                cross_hits.append(
                    f"P{target_n} solved by d from P{src_n} [{stage}]  d={hex(d)}"
                )

    if cross_hits:
        lines.extend(cross_hits)
    else:
        lines.append("cross-puzzle hits: none")

    report = "\n".join(lines) + "\n"
    OUT.write_text(report, encoding="utf-8")
    print(report)
    return 0 if not hits and not cross_hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
