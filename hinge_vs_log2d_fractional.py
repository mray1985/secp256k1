#!/usr/bin/env python3
"""
Fractional-part correlation: hinge gaps vs {log2(d)} for solved puzzles.

frac(x) = x - floor(x)   (right side of decimal in log2 space)

Also band fraction: log2(d) - (n-1)  in [0,1) for puzzle n.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_keys_53125 import parse_53125

CSV_IN = ROOT / "ARCHIVE" / "hinge_distance_all_puzzles.csv"
REPORT = ROOT / "ARCHIVE" / "hinge_vs_log2d_fractional.txt"
H = 128.34570214660884


def frac(x: float) -> float:
    return x - math.floor(x)


def corr(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else 0.0


def main() -> int:
    rows = list(csv.DictReader(CSV_IN.open(encoding="utf-8")))
    keys = parse_53125()

    pairs = []
    for r in rows:
        if r["solved"] != "True":
            continue
        n = int(r["puzzle"])
        if n not in keys or keys[n].d <= 0:
            continue
        d = keys[n].d
        log2d = math.log2(d)
        if float(r["min_delta"]) <= 0:
            continue
        pairs.append(
            {
                "n": n,
                "d": d,
                "log2d": log2d,
                "frac_log2d": frac(log2d),
                "band_frac": log2d - (n - 1),  # position in [2^(n-1), 2^n)
                "dx": float(r["delta_x"]),
                "dy": float(r["delta_y"]),
                "min_d": float(r["min_delta"]),
                "lsx": float(r["log2_sqrt_x"]),
                "lsy": float(r["log2_sqrt_y"]),
                "frac_lsx": frac(float(r["log2_sqrt_x"])),
                "frac_lsy": frac(float(r["log2_sqrt_y"])),
                "frac_dx": frac(float(r["delta_x"])),
                "frac_dy": frac(float(r["delta_y"])),
                "closer": r["closer_side"],
            }
        )

    lines = [
        f"solved puzzles: {len(pairs)}",
        "",
        "frac(x) = x - floor(x)  (log2 fractional part / right of decimal)",
        "",
        "=== corr(frac_log2(d), hinge metric) ===",
        f"  frac_log2(d) vs delta_y:     {corr([p['frac_log2d'] for p in pairs], [p['dy'] for p in pairs]):+.4f}",
        f"  frac_log2(d) vs delta_x:     {corr([p['frac_log2d'] for p in pairs], [p['dx'] for p in pairs]):+.4f}",
        f"  frac_log2(d) vs min_delta:   {corr([p['frac_log2d'] for p in pairs], [p['min_d'] for p in pairs]):+.4f}",
        f"  frac_log2(d) vs log2(sqrt y):{corr([p['frac_log2d'] for p in pairs], [p['lsy'] for p in pairs]):+.4f}",
        f"  frac_log2(d) vs log2(sqrt x):{corr([p['frac_log2d'] for p in pairs], [p['lsx'] for p in pairs]):+.4f}",
        "",
        "=== corr(band_frac = log2(d)-(n-1), hinge metric) ===",
        f"  band_frac vs delta_y:        {corr([p['band_frac'] for p in pairs], [p['dy'] for p in pairs]):+.4f}",
        f"  band_frac vs delta_x:        {corr([p['band_frac'] for p in pairs], [p['dx'] for p in pairs]):+.4f}",
        f"  band_frac vs min_delta:      {corr([p['band_frac'] for p in pairs], [p['min_d'] for p in pairs]):+.4f}",
        f"  band_frac vs frac(delta_y):  {corr([p['band_frac'] for p in pairs], [p['frac_dy'] for p in pairs]):+.4f}",
        f"  band_frac vs frac(log2 sqrt y): {corr([p['band_frac'] for p in pairs], [p['frac_lsy'] for p in pairs]):+.4f}",
        "",
        "=== fractional-to-fractional (the key test) ===",
        f"  frac_log2(d) vs frac(delta_y):     {corr([p['frac_log2d'] for p in pairs], [p['frac_dy'] for p in pairs]):+.4f}",
        f"  frac_log2(d) vs frac(delta_x):     {corr([p['frac_log2d'] for p in pairs], [p['frac_dx'] for p in pairs]):+.4f}",
        f"  frac_log2(d) vs frac(log2 sqrt y): {corr([p['frac_log2d'] for p in pairs], [p['frac_lsy'] for p in pairs]):+.4f}",
        f"  frac_log2(d) vs frac(log2 sqrt x): {corr([p['frac_log2d'] for p in pairs], [p['frac_lsx'] for p in pairs]):+.4f}",
        f"  band_frac vs frac(delta_y):        {corr([p['band_frac'] for p in pairs], [p['frac_dy'] for p in pairs]):+.4f}",
        f"  band_frac vs frac(log2 sqrt y):    {corr([p['band_frac'] for p in pairs], [p['frac_lsy'] for p in pairs]):+.4f}",
        f"  frac(delta_y) vs frac(log2 sqrt y): {corr([p['frac_dy'] for p in pairs], [p['frac_lsy'] for p in pairs]):+.4f}",
        f"  frac(delta_x) vs frac(log2 sqrt x): {corr([p['frac_dx'] for p in pairs], [p['frac_lsx'] for p in pairs]):+.4f}",
        "",
        "=== H fractional anchor ===",
        f"  H = {H}",
        f"  frac(H) = {frac(H):.6f}",
        f"  band_frac mean = {sum(p['band_frac'] for p in pairs)/len(pairs):.4f}",
        f"  frac(delta_y) mean = {sum(p['frac_dy'] for p in pairs)/len(pairs):.4f}",
        f"  frac(log2 sqrt y) mean = {sum(p['frac_lsy'] for p in pairs)/len(pairs):.4f}",
    ]

    # distance to frac(H) as target
    dist_h = [abs(p["frac_dy"] - frac(H)) for p in pairs]
    lines.append(f"  mean |frac(dy) - frac(H)| = {sum(dist_h)/len(dist_h):.4f}")

    lines.extend(["", "=== anchor puzzles ==="])
    for n in (130, 155, 160):
        hit = next((p for p in pairs if p["n"] == n), None)
        if hit:
            lines.append(
                f"  P{n}: band_frac={hit['band_frac']:.6f} frac_log2d={hit['frac_log2d']:.6f} "
                f"dy={hit['dy']:.4f} frac(dy)={hit['frac_dy']:.6f} "
                f"frac(lsy)={hit['frac_lsy']:.6f} closer={hit['closer']}"
            )

    # P135 unsolved pubkey from csv
    r135 = next((r for r in rows if r["puzzle"] == "135"), None)
    if r135:
        dy = float(r135["delta_y"])
        lsy = float(r135["log2_sqrt_y"])
        lines.append(
            f"  P135 (unsolved): dy={dy:.4f} frac(dy)={frac(dy):.6f} "
            f"frac(lsy)={frac(lsy):.6f}  (no d yet)"
        )
        # if d were at upper half midpoint
        mid = 2**134 + 2**133
        bf_mid = math.log2(mid) - 134
        lines.append(
            f"  P135 upper-half mid: band_frac={bf_mid:.6f}  "
            f"|frac(dy)-band_frac|={abs(frac(dy)-bf_mid):.6f}  "
            f"|frac(lsy)-band_frac|={abs(frac(lsy)-bf_mid):.6f}"
        )

    lines.extend(["", "=== closest frac(dy) to frac(H) (solved) ==="])
    for p in sorted(pairs, key=lambda x: abs(x["frac_dy"] - frac(H)))[:8]:
        lines.append(
            f"  P{p['n']:3d} frac(dy)={p['frac_dy']:.6f} band_frac={p['band_frac']:.6f} dy={p['dy']:.4f}"
        )

    lines.extend(["", "=== scatter: band_frac vs frac(dy) extremes ==="])
    by_bf = sorted(pairs, key=lambda x: x["band_frac"])
    lines.append("  lowest band_frac: " + ", ".join(f"P{p['n']}({p['band_frac']:.3f},{p['frac_dy']:.3f})" for p in by_bf[:4]))
    lines.append("  highest band_frac: " + ", ".join(f"P{p['n']}({p['band_frac']:.3f},{p['frac_dy']:.3f})" for p in by_bf[-4:]))

    text = "\n".join(lines)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
