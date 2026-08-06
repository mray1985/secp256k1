#!/usr/bin/env python3
"""
Hinge-distance on N+1 double-and-add pubkey chains (structured run from Px).

H = log2(p-N)
log2(sqrt(x)) = log2(x)/2
d_x = H - log2(sqrt(x)),  d_y = H - log2(sqrt(y))
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
P_MINUS_N = P - N
H = Decimal(P_MINUS_N).ln() / Decimal(2).ln()

P135_PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
P135_PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800

DA_RE = re.compile(
    r"(?:double and add|point)\s*=\s*x:(-?\d+),\s*y:(-?\d+)",
    re.I,
)
POINT_RE = re.compile(
    r"point\s*=\s*x:(-?\d+),\s*y:(-?\d+)",
    re.I,
)

DEFAULT_FILES = [
    ROOT / "00_Projects" / "patent" / "puzzle135da.txt",
    ROOT / "00_Projects" / "patent" / "2^135-1da.txt",
    ROOT / "puzzle160_all_barcodes_Nplus1_point_da.txt",
]

REPORT = ROOT / "ARCHIVE" / "hinge_distance_da_chains.txt"
CSV_OUT = ROOT / "ARCHIVE" / "hinge_distance_da_chains.csv"


def log2_half(v: int) -> Decimal:
    getcontext().prec = 80
    if v <= 0:
        return Decimal("-999")
    return Decimal(v).ln() / Decimal(2).ln() / 2


def hinge_row(idx: int, x: int, y: int, source: str, tag: str) -> dict:
    lx = log2_half(x)
    ly = log2_half(y)
    dx = H - lx
    dy = H - ly
    closer = "y" if dy < dx else "x" if dx < dy else "tie"
    min_d = min(dx, dy)
    return {
        "source": source,
        "tag": tag,
        "step": idx,
        "x": str(x),
        "y": str(y),
        "log2_sqrt_x": float(lx),
        "log2_sqrt_y": float(ly),
        "delta_x": float(dx),
        "delta_y": float(dy),
        "min_delta": float(min_d),
        "closer": closer,
        "ratio_pmn_over_sqrt": float(Decimal(2) ** min_d),
        "is_p135_pubkey": x == P135_PX and y == P135_PY,
        "x_eq_p135_px": x == P135_PX,
    }


def parse_da_file(path: Path) -> list[tuple[int, int, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rows: list[tuple[int, int, str]] = []
    current_tag = path.stem
    for line in text.splitlines():
        if line.startswith("BARCODE ") or line.startswith("==="):
            m = re.search(r"BARCODE\s+(\S+)", line)
            if m:
                current_tag = m.group(1)
        m = DA_RE.search(line)
        if m:
            rows.append((int(m.group(1)), int(m.group(2)), current_tag))
    return rows


def discover_da_files(root: Path) -> list[Path]:
    out = []
    for pat in ("*da.txt", "*_da.txt", "*Nplus1*da*.txt"):
        out.extend(root.rglob(pat))
    # dedupe
    seen = set()
    unique = []
    for p in sorted(out, key=lambda x: str(x)):
        rp = p.resolve()
        if rp not in seen and p.stat().st_size > 100:
            seen.add(rp)
            unique.append(p)
    return unique


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", nargs="*", type=Path, default=None)
    ap.add_argument("--discover", action="store_true", help="scan repo for *da.txt")
    ap.add_argument("--p135-only", action="store_true")
    args = ap.parse_args()

    if args.files:
        paths = [p for p in args.files if p.exists()]
    elif args.discover:
        paths = discover_da_files(ROOT)
    else:
        paths = [p for p in DEFAULT_FILES if p.exists()]

    if args.p135_only:
        paths = [p for p in paths if "135" in p.name.lower()]

    all_rows: list[dict] = []
    by_source: dict[str, list[dict]] = defaultdict(list)

    for path in paths:
        pts = parse_da_file(path)
        src = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        for i, (x, y, tag) in enumerate(pts):
            row = hinge_row(i, x, y, src, tag)
            all_rows.append(row)
            by_source[src].append(row)

    if not all_rows:
        print("no double-and-add points found")
        return 1

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)

    lines = [
        "HINGE-DISTANCE: N+1 double-and-add chains",
        f"H = log2(p-N) = {float(H)}",
        f"total points: {len(all_rows)}",
        f"source files: {len(paths)}",
        "",
    ]

    for src, rows in sorted(by_source.items(), key=lambda kv: -len(kv[1])):
        mins = [r["min_delta"] for r in rows]
        y_closer = sum(1 for r in rows if r["closer"] == "y")
        x_closer = sum(1 for r in rows if r["closer"] == "x")
        best = min(rows, key=lambda r: r["min_delta"])
        lines.append(f"=== {src} ({len(rows)} points) ===")
        lines.append(f"  closer: y={y_closer} x={x_closer}")
        lines.append(f"  min_delta range: [{min(mins):.4f}, {max(mins):.4f}]")
        lines.append(
            f"  best: step={best['step']} tag={best['tag']} "
            f"d_x={best['delta_x']:.4f} d_y={best['delta_y']:.4f} closer={best['closer']}"
        )
        if any(r["is_p135_pubkey"] for r in rows):
            lines.append("  contains P135 pubkey point")
        lines.append("")

    # P135 puzzle135da detail
    p135_rows = [r for r in all_rows if "puzzle135da" in r["source"]]
    if p135_rows:
        lines.append("=== P135 puzzle135da step detail (first/last/best) ===")
        for label, r in [
            ("first", p135_rows[0]),
            ("last", p135_rows[-1]),
            ("best", min(p135_rows, key=lambda x: x["min_delta"])),
        ]:
            lines.append(
                f"  {label} step={r['step']}: log2(sqrt x)={r['log2_sqrt_x']:.6f} "
                f"log2(sqrt y)={r['log2_sqrt_y']:.6f} "
                f"d_x={r['delta_x']:.6f} d_y={r['delta_y']:.6f} closer={r['closer']}"
            )

    # histogram all min_delta
    buckets = Counter(round(r["min_delta"], 1) for r in all_rows)
    lines.extend(["", "=== min_delta histogram (all DA points, round 0.1) ==="])
    for b in sorted(buckets):
        lines.append(f"  {b:.1f}: {buckets[b]}")

    # closest 10 overall
    lines.extend(["", "=== closest 10 to p-N hinge (all chains) ==="])
    for r in sorted(all_rows, key=lambda x: x["min_delta"])[:10]:
        lines.append(
            f"  min_d={r['min_delta']:.4f} closer={r['closer']} "
            f"step={r['step']} src={r['source']} tag={r['tag']}"
        )

    text = "\n".join(lines)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {CSV_OUT}")
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
