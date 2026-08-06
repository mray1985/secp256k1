#!/usr/bin/env python3
"""
Scan EC neighborhood around sqrt(Px) multiple candidates for P135.

For each center d from the multiples file, walk [d-radius, d+radius] by +G steps.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from bucket_slice_search import band_midpoint  # noqa: E402
from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle135_bucket_bsgs.p135_common import G, point_add, scalar_mult  # noqa: E402

CANDIDATES = Path(r"C:\Users\mitch\Downloads\P135_sqrtPx_multiples_227_to_453(1).txt")
REPORT = ROOT / "ARCHIVE" / "p135_sqrtpx_neighbor_scan.txt"


def parse_candidates(path: Path) -> list[tuple[int, int]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*(\d+):\s*(\d+)\s*$", line)
        if m:
            rows.append((int(m.group(1)), int(m.group(2))))
    return rows


def scan_window(
    center: int,
    radius: int,
    lo: int,
    hi: int,
    px: int,
    py: int,
    *,
    emit_every: int = 0,
    label: str = "",
) -> int | None:
    d_start = max(lo, center - radius)
    d_end = min(hi - 1, center + radius)
    if d_start > d_end:
        return None

    pt = scalar_mult(d_start)
    if pt is None:
        return None

    want_y = py
    checked = 0
    for d in range(d_start, d_end + 1):
        x, y = pt
        if x == px and y == want_y:
            return d
        if d < d_end:
            pt = point_add(pt, G)
            if pt is None:
                break
        checked += 1
        if emit_every and checked % emit_every == 0:
            print(f"    {label} checked {checked:,} at d_tail...{str(d)[-8:]}", flush=True)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Neighbor scan around sqrt(Px) multiples")
    ap.add_argument("--radius", type=int, default=1 << 18, help="scan +/- radius (default 2^18)")
    ap.add_argument("--upper-only", action="store_true", default=True)
    ap.add_argument("--all", dest="upper_only", action="store_false")
    ap.add_argument("--m-min", type=int, default=0)
    ap.add_argument("--m-max", type=int, default=9999)
    ap.add_argument("--candidates", type=Path, default=CANDIDATES)
    args = ap.parse_args()

    lo, hi, _ = puzzle_band(135)
    mid = band_midpoint(lo, hi)
    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn

    rows = [
        (m, d)
        for m, d in parse_candidates(args.candidates)
        if args.m_min <= m <= args.m_max and (not args.upper_only or d >= mid)
    ]

    width = 2 * args.radius + 1
    est = len(rows) * width
    lines = [
        "P135 sqrt(Px) neighbor scan",
        f"candidates: {len(rows)}  radius=+/-{args.radius:,}  (~{width:,}/each)",
        f"est keys: {est:,} (~2^{est.bit_length()})",
        f"upper_only: {args.upper_only}",
        "",
    ]
    print("\n".join(lines), flush=True)

    t0 = time.perf_counter()
    total_checked = 0
    hit = None
    for i, (m, center) in enumerate(rows):
        frac = (center - lo) / lo
        label = f"m={m} frac={frac:.4f}"
        print(f"[{i+1}/{len(rows)}] {label} center_tail...{str(center)[-8:]}", flush=True)
        found = scan_window(center, args.radius, lo, hi, px, py, label=label)
        total_checked += min(width, max(0, min(center + args.radius, hi - 1) - max(lo, center - args.radius) + 1))
        if found is not None:
            hit = (m, found)
            lines.append(f"HIT m={m} center={center} d={found} hex={hex(found)}")
            print(f"*** HIT d={found} hex={hex(found)} near m={m} ***", flush=True)
            break

    elapsed = time.perf_counter() - t0
    rate = total_checked / max(elapsed, 1e-9)
    lines.extend(
        [
            "",
            f"elapsed: {elapsed:.1f}s  rate: {rate:,.0f} keys/s",
            f"hits: {1 if hit else 0}",
        ]
    )
    if not hit:
        lines.append("no hit in scanned windows")

    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0 if hit else 1


if __name__ == "__main__":
    raise SystemExit(main())
