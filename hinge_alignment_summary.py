#!/usr/bin/env python3
"""What lines up across hinge experiments."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PN = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F - (
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
)


def frac(x: float) -> float:
    return x - math.floor(x)


def main() -> None:
    getcontext().prec = 80
    h = float(Decimal(PN).ln() / Decimal(2).ln())
    fh, fh2 = frac(h), frac(h / 2)

    psd = list(csv.DictReader((ROOT / "ARCHIVE" / "hinge_normalization_per_slot_d.csv").open()))
    hn = list(csv.DictReader((ROOT / "ARCHIVE" / "hinge_normalization_errors.csv").open()))
    hx = list(csv.DictReader((ROOT / "ARCHIVE" / "hinge_normalization_3x_dxy.csv").open()))

    true_psd = [r for r in psd if r["is_true_xy"] == "True"]

    lines = ["WHAT LINES UP — hinge experiment synthesis", ""]

    lines.append("=== 1. EXACT IDENTITIES (algebra, always true) ===")
    lines.append(f"  {{H}} = {fh:.6f}   {{H/2}} = {fh2:.6f}")
    lines.append(f"  {{H}} - {{log2 sqrt y}} = {{Delta_y}}  (P135: 0.345702 - 0.339576 = 0.006126)")
    lines.append(f"  band_frac(d) = {{2 * log2 sqrt d}}  (doubling identity)")
    lines.append("")

    lines.append("=== 2. TIGHTEST |E_x - E_d| on true branch (per-slot d) ===")
    for r in sorted(true_psd, key=lambda x: abs(float(x["E_x_minus_E_d"])))[:10]:
        lines.append(
            f"  P{r['puzzle']:>3} {r['d_model']:12} "
            f"|Ex-Ed|={abs(float(r['E_x_minus_E_d'])):.6f} "
            f"Ex={float(r['E_x']):+.4f} Ed={float(r['E_d']):+.4f}"
        )
    lines.append("")

    lines.append("=== 3. TIGHTEST |E_x| / |E_y| single pubkey ===")
    for r in sorted(hn, key=lambda x: abs(float(x["E_x"])))[:5]:
        lines.append(f"  P{r['puzzle']:>3} Ex={float(r['E_x']):+.6f} Ey={float(r['E_y']):+.6f}")
    for r in sorted(hn, key=lambda x: abs(float(x["E_y"])))[:5]:
        lines.append(f"  P{r['puzzle']:>3} Ey={float(r['E_y']):+.6f} Ex={float(r['E_x']):+.6f}")
    lines.append("")

    by = defaultdict(dict)
    for r in hx:
        if int(r["slot"]) == int(r["true_slot"]):
            by[r["puzzle"]][r["y_branch"]] = float(r["E_y"])

    lines.append("=== 4. SAME x: -y often beats +y on |E_y| (true slot) ===")
    wins = tot = 0
    for p in sorted(by, key=lambda x: int(x)):
        v = by[p]
        if "y" not in v or "-y" not in v:
            continue
        tot += 1
        y, yn = v["y"], v["-y"]
        if abs(yn) < abs(y):
            wins += 1
        if abs(yn) < 0.02 or abs(y) < 0.02:
            lines.append(f"  P{p:>3} Ey_plus={y:+.4f} Ey_minus={yn:+.4f}")
    lines.append(f"  -y tighter than +y: {wins}/{tot} puzzles")
    lines.append("")

    lines.append("=== 5. lambda_band |Ex-Ed| < 0.05 ===")
    lb = [r for r in true_psd if r["d_model"] == "lambda_band"]
    tight = [r for r in lb if abs(float(r["E_x_minus_E_d"])) < 0.05]
    for r in sorted(tight, key=lambda x: abs(float(x["E_x_minus_E_d"]))):
        lines.append(f"  P{r['puzzle']:>3} {float(r['E_x_minus_E_d']):+.6f}")
    lines.append(f"  count {len(tight)}/{len(lb)}")
    lines.append("")

    lines.append("=== 6. WHAT DOES NOT LINE UP ===")
    ex = [abs(float(r["E_x"])) for r in hn]
    ey = [abs(float(r["E_y"])) for r in hn]
    lines.append(f"  mean |Ex|={sum(ex)/len(ex):.3f}  mean |Ey|={sum(ey)/len(ey):.3f}  (not clustered at 0)")
    lines.append(f"  oracle 3x2 min |Ey| mean ~0.246 still wide")
    lines.append(f"  log2(d) vs hinge gap: corr ~0 (independent)")
    lines.append(f"  upper-half bf~0.585 vs frac hinge 0.006: incompatible same d")
    lines.append("")

    lines.append("=== 7. P135 SUMMARY (outlier) ===")
    lines.append("  Ex = +0.001  (best in dataset)")
    lines.append("  Ey(+y) = +0.285  but Ey(-y) = -0.006 at SAME x  (hinge-perfect on -y leg)")
    lines.append("  true x slot required; wrong cube-root slot adds ~0.25 to Ex")
    lines.append("  d not tested (unsolved); x-side hinge alignment without d")

    text = "\n".join(lines)
    out = ROOT / "ARCHIVE" / "hinge_what_lines_up.txt"
    out.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
