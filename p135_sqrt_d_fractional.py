#!/usr/bin/env python3
"""
sqrt(d) fractional analysis: log2(sqrt(d)) = log2(d)/2 vs mirror N-d.

Compare {log2(sqrt(d))}, {log2(sqrt(N-d))} to {log2(sqrt x/y)}, {H}, hinge gaps.
"""

from __future__ import annotations

import csv
import math
import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_keys_53125 import parse_53125

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
PN = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F - N
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590

getcontext().prec = 80
H = float(Decimal(PN).ln() / Decimal(2).ln())
LSY = float((Decimal(PY).ln() / Decimal(2).ln()) / 2)
LSX = float((Decimal(PX).ln() / Decimal(2).ln()) / 2)

REPORT = ROOT / "ARCHIVE" / "p135_sqrt_d_fractional.txt"


def frac(x: float) -> float:
    return x - math.floor(x)


def log2_sqrt_scalar(d: int) -> float:
    return math.log2(d) / 2


def isqrt(n: int) -> int:
    lo, hi = 1, max(1, n)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid * mid <= n:
            lo = mid
        else:
            hi = mid - 1
    return lo


def corr(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else 0.0


def main() -> int:
    keys = parse_53125()
    rows = list(csv.DictReader((ROOT / "ARCHIVE" / "hinge_distance_all_puzzles.csv").open()))
    frac_h = frac(H)
    frac_lsy = frac(LSY)
    frac_lsx = frac(LSX)

    solved = []
    for r in rows:
        if r["solved"] != "True" or float(r["min_delta"]) <= 0:
            continue
        n = int(r["puzzle"])
        if n not in keys or keys[n].d <= 0:
            continue
        d = keys[n].d
        dm = N - d
        lsd = log2_sqrt_scalar(d)
        lsdm = log2_sqrt_scalar(dm)
        flsd = frac(lsd)
        flsdm = frac(lsdm)
        bf = math.log2(d) - (n - 1)
        solved.append(
            {
                "n": n,
                "d": d,
                "bf": bf,
                "flsd": flsd,
                "flsdm": flsdm,
                "flsy": float(r["log2_sqrt_y"]) - math.floor(float(r["log2_sqrt_y"])),
                "flsx": float(r["log2_sqrt_x"]) - math.floor(float(r["log2_sqrt_x"])),
                "fdy": float(r["delta_y"]) - math.floor(float(r["delta_y"])),
                "isqrt_d": isqrt(d),
            }
        )

    lines = [
        "sqrt(d) fractional analysis  (log2(sqrt(d)) = log2(d)/2)",
        f"H={H:.6f}  frac(H)={frac_h:.6f}",
        f"P135 frac(log2 sqrt x)={frac_lsx:.6f}  frac(log2 sqrt y)={frac_lsy:.6f}",
        f"solved n={len(solved)}",
        "",
        "=== corr on solved puzzles ===",
        f"  frac(log2 sqrt d) vs frac(log2 sqrt y):  {corr([p['flsd'] for p in solved], [p['flsy'] for p in solved]):+.4f}",
        f"  frac(log2 sqrt d) vs frac(log2 sqrt x):  {corr([p['flsd'] for p in solved], [p['flsx'] for p in solved]):+.4f}",
        f"  frac(log2 sqrt d) vs band_frac:          {corr([p['flsd'] for p in solved], [p['bf'] for p in solved]):+.4f}",
        f"  frac(log2 sqrt d) vs frac(delta_y):      {corr([p['flsd'] for p in solved], [p['fdy'] for p in solved]):+.4f}",
        f"  frac(log2 sqrt N-d) vs frac(log2 sqrt y): {corr([p['flsdm'] for p in solved], [p['flsy'] for p in solved]):+.4f}",
        f"  frac(log2 sqrt d) vs frac(log2 sqrt N-d): {corr([p['flsd'] for p in solved], [p['flsdm'] for p in solved]):+.4f}",
        f"  frac(lsy)-frac(lsd) vs band_frac:        {corr([p['flsy']-p['flsd'] for p in solved], [p['bf'] for p in solved]):+.4f}",
        f"  frac(lsy)-frac(lsd) vs frac(dy):         {corr([p['flsy']-p['flsd'] for p in solved], [p['fdy'] for p in solved]):+.4f}",
        "",
        "=== fractional differences (y - sqrt d) ===",
        f"  mean frac(lsy)-frac(lsd):   {sum(p['flsy']-p['flsd'] for p in solved)/len(solved):+.6f}",
        f"  mean frac(lsy)-frac(lsdm):  {sum(p['flsy']-p['flsdm'] for p in solved)/len(solved):+.6f}",
        f"  mean frac(lsd)+frac(lsdm):  {sum(p['flsd']+p['flsdm'] for p in solved)/len(solved):+.6f}",
        f"  mean frac(H)-frac(lsd):     {sum(frac_h-p['flsd'] for p in solved)/len(solved):+.6f}",
        "",
        "=== anchor puzzles ===",
    ]

    for n in (130, 155, 160):
        p = next((x for x in solved if x["n"] == n), None)
        if p:
            lines.append(
                f"  P{n}: bf={p['bf']:.4f}  frac(lsd)={p['flsd']:.6f}  frac(lsdm)={p['flsdm']:.6f}  "
                f"flsy-flsd={p['flsy']-p['flsd']:.6f}  fdy={p['fdy']:.6f}"
            )

    lines.extend(["", "=== P135 anchors (+d and N-d sqrt) ==="])
    for name, bf in [("hinge_frac", 0.333450), ("upper_half", 0.584963), ("frac_H", 0.345702)]:
        d = int(round(2 ** (134 + bf)))
        dm = N - d
        lsd, lsdm = log2_sqrt_scalar(d), log2_sqrt_scalar(dm)
        lines.append(f"  {name} bf={bf:.6f}:")
        lines.append(
            f"    +d: log2(sqrt d)={lsd:.6f}  frac={frac(lsd):.6f}  "
            f"frac(lsy)-frac(lsd)={frac_lsy-frac(lsd):.6f}  "
            f"frac(lsx)-frac(lsd)={frac_lsx-frac(lsd):.6f}  "
            f"frac(H)-frac(lsd)={frac_h-frac(lsd):.6f}"
        )
        lines.append(
            f"    N-d: log2(sqrt N-d)={lsdm:.6f}  frac={frac(lsdm):.6f}  "
            f"frac(lsy)-frac(lsdm)={frac_lsy-frac(lsdm):.6f}  "
            f"frac(lsx)-frac(lsdm)={frac_lsx-frac(lsdm):.6f}"
        )
        lines.append(
            f"    frac(lsd)+frac(lsdm)={frac(lsd)+frac(lsdm):.6f}  "
            f"frac(lsd)-frac(lsdm)={frac(lsd)-frac(lsdm):.6f}"
        )

    lines.extend(["", "=== identity check: band_frac = 2*frac(lsd) mod 1? ==="])
    lines.append("  (since log2(d)=2*log2(sqrt d), frac(log2 d) = frac(2*frac(lsd)) when no carry)")
    for name, bf in [("hinge", 0.333450), ("upper", 0.584963)]:
        d = int(round(2 ** (134 + bf)))
        fl = frac(log2_sqrt_scalar(d))
        recon = frac(2 * fl) if 2 * fl < 1 else frac(2 * fl)
        # proper: frac(log2 d) = frac(2 * log2(sqrt d)) accounting for integer part
        l2d = math.log2(d)
        lines.append(
            f"  {name}: band_frac={bf:.6f}  frac(2*lsd) naive={frac(2*fl):.6f}  actual frac(log2d)={frac(l2d):.6f}"
        )

    lines.extend(["", "=== integer isqrt(d) fractional log (alternate sqrt) ==="])
    for name, bf in [("hinge", 0.333450), ("upper", 0.584963)]:
        d = int(round(2 ** (134 + bf)))
        dm = N - d
        si, sim = isqrt(d), isqrt(dm)
        fi, fim = frac(math.log2(si)), frac(math.log2(sim))
        lines.append(
            f"  {name}: isqrt(d) bits={si.bit_length()} frac(log2 isqrt d)={fi:.6f}  "
            f"isqrt(N-d) bits={sim.bit_length()} frac={fim:.6f}"
        )

    text = "\n".join(lines)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
