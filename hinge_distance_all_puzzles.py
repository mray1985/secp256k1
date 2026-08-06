#!/usr/bin/env python3
"""
Hinge-distance metric for all puzzles with pubkey coordinates.

H = log2(p - N)
Δ_x = H - log2(sqrt(x)) = H - log2(x)/2
Δ_y = H - log2(sqrt(y)) = H - log2(y)/2

Classify: which coordinate is closer to the p-N defect hinge.
"""

from __future__ import annotations

import csv
import math
import sys
from collections import Counter
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
P_MINUS_N = P - N

CSV_OUT = ROOT / "ARCHIVE" / "hinge_distance_all_puzzles.csv"
REPORT = ROOT / "ARCHIVE" / "hinge_distance_all_puzzles.txt"


def log2_decimal(n: int) -> Decimal:
    getcontext().prec = 80
    return Decimal(n).ln() / Decimal(2).ln()


def log2_sqrt_coord(v: int) -> Decimal:
    return log2_decimal(v) / 2


def load_all_coords() -> list[dict]:
    rows = []
    keys = parse_53125()
    seen = set()

    for n, pk in sorted(keys.items()):
        if pk.px <= 0 or pk.py <= 0:
            continue
        rows.append(
            {
                "n": n,
                "solved": pk.d > 0,
                "d": pk.d,
                "px": pk.px,
                "py": pk.py,
            }
        )
        seen.add(n)

    for n, rsz in sorted(PUZZLE_RSZ.items()):
        if n in seen or not rsz.pub_compressed:
            continue
        px = int(rsz.pub_compressed[2:], 16)
        yp, yn = y_roots(px)
        py = yp if yp % 2 == 0 else yn
        rows.append({"n": n, "solved": False, "d": 0, "px": px, "py": py})
        seen.add(n)

    return sorted(rows, key=lambda r: r["n"])


def main() -> int:
    getcontext().prec = 80
    h = log2_decimal(P_MINUS_N)
    rows_in = load_all_coords()
    out_rows = []

    for r in rows_in:
        n = r["n"]
        px, py = r["px"], r["py"]
        lx = log2_sqrt_coord(px)
        ly = log2_sqrt_coord(py)
        dx = h - lx
        dy = h - ly
        closer = "y" if dy < dx else "x" if dx < dy else "tie"
        min_delta = min(dx, dy)
        out_rows.append(
            {
                "puzzle": n,
                "solved": r["solved"],
                "log2_sqrt_x": float(lx),
                "log2_sqrt_y": float(ly),
                "delta_x": float(dx),
                "delta_y": float(dy),
                "min_delta": float(min_delta),
                "ratio_pmn_over_coord": float(Decimal(2) ** min_delta),
                "closer_side": closer,
                "gap_x_bits": float(dx),
                "gap_y_bits": float(dy),
            }
        )

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    solved = [r for r in out_rows if r["solved"]]
    unsolved = [r for r in out_rows if not r["solved"]]

    y_closer = sum(1 for r in out_rows if r["closer_side"] == "y")
    x_closer = sum(1 for r in out_rows if r["closer_side"] == "x")

    # bucket min_delta to 0.05
    buckets = Counter(round(r["min_delta"], 1) for r in out_rows)

    lines = [
        "HINGE-DISTANCE: log2(p-N) - log2(sqrt(coord))",
        f"H = log2(p-N) = {float(h)}",
        f"p-N = {P_MINUS_N} ({P_MINUS_N.bit_length()} bits)",
        f"puzzles with coords: {len(out_rows)}  (solved {len(solved)}, unsolved pub {len(unsolved)})",
        "",
        f"closer to hinge: y-side {y_closer}, x-side {x_closer}",
        "",
        "=== all puzzles ===",
        "puz  solved  log2(sqrt(x))  log2(sqrt(y))  d_x      d_y      min_d   closer  2^min_d",
    ]

    for r in out_rows:
        lines.append(
            f"{r['puzzle']:3d}  {'Y' if r['solved'] else 'N':5s}  "
            f"{r['log2_sqrt_x']:17.12f}  {r['log2_sqrt_y']:17.12f}  "
            f"{r['delta_x']:8.6f}  {r['delta_y']:8.6f}  "
            f"{r['min_delta']:7.4f}  {r['closer_side']:6s}  {r['ratio_pmn_over_coord']:.4f}"
        )

    lines.extend(["", "=== min_delta histogram (rounded 0.1) ==="])
    for b in sorted(buckets):
        lines.append(f"  {b:.1f}: {buckets[b]}")

    lines.extend(["", "=== user anchor puzzles ==="])
    for n in (130, 135, 155, 160):
        hit = next((r for r in out_rows if r["puzzle"] == n), None)
        if hit:
            lines.append(
                f"P{n}: d_x={hit['delta_x']:.6f} d_y={hit['delta_y']:.6f} closer={hit['closer_side']}"
            )
        else:
            lines.append(f"P{n}: not in dataset")

    if len(solved) >= 3:
        ns = [r["puzzle"] for r in solved]
        dys = [r["delta_y"] for r in solved]
        mx = sum(ns) / len(ns)
        my = sum(dys) / len(dys)
        num = sum((ns[i] - mx) * (dys[i] - my) for i in range(len(ns)))
        den = math.sqrt(sum((x - mx) ** 2 for x in ns) * sum((y - my) ** 2 for y in dys))
        corr = num / den if den else 0
        lines.extend(["", f"corr(puzzle_n, delta_y) on solved only: {corr:+.4f}"])

    text = "\n".join(lines)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {CSV_OUT}")
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
