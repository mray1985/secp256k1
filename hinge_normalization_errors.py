#!/usr/bin/env python3
"""
Hinge normalization errors across solved puzzles:

  E_x = {log2(sqrt(x))} - {log2(p-N) / 2}
  E_y = {log2(sqrt(y))} - {log2(p-N)}

If these cluster or progress with puzzle number, hinge frac is a universal invariant.
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

from puzzle_keys_53125 import parse_53125

CSV_IN = ROOT / "ARCHIVE" / "hinge_distance_all_puzzles.csv"
REPORT = ROOT / "ARCHIVE" / "hinge_normalization_errors.txt"
CSV_OUT = ROOT / "ARCHIVE" / "hinge_normalization_errors.csv"

PN = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F - (
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
)


def frac(x: float) -> float:
    return x - math.floor(x)


def wrap_frac(x: float) -> float:
    """Map to (-0.5, 0.5] for circular distance."""
    f = frac(x)
    return f - 1.0 if f > 0.5 else f


def corr(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else 0.0


def main() -> int:
    getcontext().prec = 80
    h = float(Decimal(PN).ln() / Decimal(2).ln())
    frac_h = frac(h)
    frac_h_half = frac(h / 2)

    rows = list(csv.DictReader(CSV_IN.open(encoding="utf-8")))
    keys = parse_53125()

    out = []
    for r in rows:
        if r["solved"] != "True" or float(r["min_delta"]) <= 0:
            continue
        n = int(r["puzzle"])
        if n not in keys or keys[n].d <= 0:
            continue
        lsx = float(r["log2_sqrt_x"])
        lsy = float(r["log2_sqrt_y"])
        flsx, flsy = frac(lsx), frac(lsy)
        ex = flsx - frac_h_half
        ey = flsy - frac_h
        dx = float(r["delta_x"])
        dy = float(r["delta_y"])
        out.append(
            {
                "puzzle": n,
                "log2_sqrt_x": lsx,
                "log2_sqrt_y": lsy,
                "E_x": ex,
                "E_y": ey,
                "E_x_wrapped": wrap_frac(ex),
                "E_y_wrapped": wrap_frac(ey),
                "delta_x": dx,
                "delta_y": dy,
                "neg_frac_delta_y": -(dy - math.floor(dy)) if dy >= 0 else None,
            }
        )

    out.sort(key=lambda r: r["puzzle"])
    n = len(out)
    exs = [r["E_x"] for r in out]
    eys = [r["E_y"] for r in out]
    ns = [r["puzzle"] for r in out]

    def stats(vals: list[float]) -> dict:
        m = sum(vals) / len(vals)
        var = sum((v - m) ** 2 for v in vals) / len(vals)
        return {
            "mean": m,
            "std": math.sqrt(var),
            "min": min(vals),
            "max": max(vals),
            "range": max(vals) - min(vals),
        }

    sx, sy = stats(exs), stats(eys)

    # histogram buckets 0.05
    bx = Counter(round(v, 2) for v in exs)
    by = Counter(round(v, 2) for v in eys)

    lines = [
        "HINGE NORMALIZATION ERRORS (solved puzzles)",
        f"H = log2(p-N) = {h:.12f}",
        f"{{H}} = {frac_h:.6f}   {{H/2}} = {frac_h_half:.6f}",
        f"n = {n}",
        "",
        "Definitions:",
        "  E_x = {log2(sqrt(x))} - {log2(p-N) / 2}",
        "  E_y = {log2(sqrt(y))} - {log2(p-N)}",
        "",
        "=== E_x summary ===",
        f"  mean={sx['mean']:+.6f}  std={sx['std']:.6f}  range=[{sx['min']:+.6f}, {sx['max']:+.6f}]  width={sx['range']:.6f}",
        f"  corr(puzzle_n, E_x) = {corr(ns, exs):+.4f}",
        "",
        "=== E_y summary ===",
        f"  mean={sy['mean']:+.6f}  std={sy['std']:.6f}  range=[{sy['min']:+.6f}, {sy['max']:+.6f}]  width={sy['range']:.6f}",
        f"  corr(puzzle_n, E_y) = {corr(ns, eys):+.4f}",
        "",
        "=== cross-check: E_y vs -{delta_y} ===",
        f"  corr(E_y, -frac(delta_y)) = {corr(eys, [-(r['delta_y']-math.floor(r['delta_y'])) for r in out]):+.4f}",
        f"  mean(E_y + frac(delta_y)) = {sum(r['E_y'] + (r['delta_y']-math.floor(r['delta_y'])) for r in out)/n:+.6f}",
        "",
        "=== E_x histogram (round 0.05) top bins ===",
    ]
    for b in sorted(bx, key=lambda k: -bx[k])[:12]:
        lines.append(f"  {b:+.2f}: {bx[b]}")

    lines.append("")
    lines.append("=== E_y histogram (round 0.05) top bins ===")
    for b in sorted(by, key=lambda k: -by[k])[:12]:
        lines.append(f"  {b:+.2f}: {by[b]}")

    lines.extend(
        [
            "",
            "=== all puzzles ===",
            "puz   E_x        E_y        delta_y    closer?",
        ]
    )
    for r in out:
        closer = "x" if abs(r["E_x"]) < abs(r["E_y"]) else "y"
        lines.append(
            f"{r['puzzle']:3d}  {r['E_x']:+.6f}  {r['E_y']:+.6f}  "
            f"{r['delta_y']:8.4f}  {closer}"
        )

    # P135 unsolved
    r135 = next((r for r in rows if r["puzzle"] == "135"), None)
    if r135:
        flsx = frac(float(r135["log2_sqrt_x"]))
        flsy = frac(float(r135["log2_sqrt_y"]))
        ex135 = flsx - frac_h_half
        ey135 = flsy - frac_h
        lines.extend(
            [
                "",
                "=== P135 (unsolved pubkey) ===",
                f"  E_x = {ex135:+.6f}",
                f"  E_y = {ey135:+.6f}",
                f"  rank |E_y| among solved: {1 + sum(1 for r in out if abs(r['E_y']) < abs(ey135))} / {n}",
                f"  rank |E_x| among solved: {1 + sum(1 for r in out if abs(r['E_x']) < abs(ex135))} / {n}",
            ]
        )

    lines.extend(
        [
            "",
            "=== tightest |E_y| (closest to hinge frac on y) ===",
        ]
    )
    for r in sorted(out, key=lambda x: abs(x["E_y"]))[:10]:
        lines.append(f"  P{r['puzzle']:3d}  E_y={r['E_y']:+.6f}  E_x={r['E_x']:+.6f}")

    lines.extend(["", "=== tightest |E_x| ==="])
    for r in sorted(out, key=lambda x: abs(x["E_x"]))[:10]:
        lines.append(f"  P{r['puzzle']:3d}  E_x={r['E_x']:+.6f}  E_y={r['E_y']:+.6f}")

    # verdict
    lines.extend(
        [
            "",
            "=== verdict ===",
        ]
    )
    if sy["std"] < 0.15 and sx["std"] < 0.15:
        verdict = "TIGHT cluster — hinge fractional normalization may be structural"
    elif sy["std"] < 0.25 and sx["std"] < 0.25:
        verdict = "MODERATE cluster — weak invariant, inspect histogram"
    else:
        verdict = "WIDE spread — hinge frac alignment likely not universal"
    lines.append(f"  {verdict}")
    lines.append(f"  E_y std={sy['std']:.4f}  E_x std={sx['std']:.4f}")
    if abs(corr(ns, eys)) > 0.3 or abs(corr(ns, exs)) > 0.3:
        lines.append(f"  puzzle-number trend detected (corr Ey={corr(ns,eys):+.3f} Ex={corr(ns,exs):+.3f})")
    else:
        lines.append(f"  no puzzle-number trend (corr Ey={corr(ns,eys):+.3f} Ex={corr(ns,exs):+.3f})")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    import csv as csvmod

    with CSV_OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csvmod.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    print("\n".join(lines))
    print(f"\nwrote {REPORT}")
    print(f"wrote {CSV_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
