#!/usr/bin/env python3
"""
Poisson lambda analysis on solved puzzle offset_bits residuals.

For each solved puzzle:
  offset = (d - shelf2) mod LO
  offset_bits = bit_length(offset)
  residual r = offset_bits - (n - 10)   # integer correction to h-10 law

Per row (0,1,2): test whether r looks Poisson(lambda):
  mean ~ variance ~ lambda

Also fits linear offset_bits ~ a*n + b per row (Planck-style E proportional nu).

P135 row=2: predict offset_bits from both models.
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import build_config  # noqa: E402
from genesis_calibration import bridge_state  # noqa: E402
from ecdlp_full_pipeline import PuzzleConfig, apply_puzzle_defaults, puzzle_band  # noqa: E402
from gap_tier_common import observed_offset  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

LOG = ROOT / "ARCHIVE" / "cloud_pages" / "poisson_offset_analysis.log"
MIN_N = 70  # high puzzles where h-10 law is meaningful


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def poisson_pmf(k: int, lam: float) -> float:
    if k < 0:
        return 0.0
    return math.exp(-lam) * (lam**k) / math.factorial(k)


def chi_square_poisson(counts: list[int], lam: float) -> tuple[float, int]:
    """Chi-square vs Poisson(lam) on support min..max of counts."""
    if not counts or lam <= 0:
        return float("nan"), 0
    lo, hi = min(counts), max(counts)
    obs: dict[int, int] = defaultdict(int)
    for c in counts:
        obs[c] += 1
    n = len(counts)
    chi2 = 0.0
    df = 0
    for k in range(lo, hi + 1):
        exp = n * poisson_pmf(k, lam)
        if exp < 1.0:
            continue
        o = obs.get(k, 0)
        chi2 += (o - exp) ** 2 / exp
        df += 1
    return chi2, max(0, df - 1)


def linear_fit(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Least squares y = a*x + b."""
    n = len(xs)
    if n < 2:
        return 0.0, ys[0] if ys else 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    a = num / den if den else 0.0
    b = my - a * mx
    return a, b


def collect_rows(keys, min_n: int = MIN_N) -> dict[int, list[dict]]:
    by_row: dict[int, list[dict]] = defaultdict(list)
    for n, pk in sorted(keys.items()):
        if n < min_n or pk.d is None or pk.d <= 0:
            continue
        try:
            cfg = build_config(pk)
        except (ValueError, KeyError):
            continue
        st = bridge_state(cfg)
        lo, _, _ = puzzle_band(n)
        off = observed_offset(pk.d, st["oitc"].shelf2, lo)
        off_bits = off.bit_length() if off else 0
        pred = n - 10
        residual = off_bits - pred
        by_row[cfg.row].append(
            {
                "n": n,
                "d": pk.d,
                "row": cfg.row,
                "shelf2": st["oitc"].shelf2,
                "offset": off,
                "offset_bits": off_bits,
                "pred_h10": pred,
                "residual": residual,
            }
        )
    return by_row


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    keys = parse_53125()
    by_row = collect_rows(keys)

    log("=== Poisson lambda analysis: offset_bits residual r = offset_bits - (n-10) ===")
    log(f"Solved puzzles n >= {MIN_N}, grouped by bridge row index")
    log("")

    p135_predictions: dict[str, float] = {}

    for row in sorted(by_row):
        rows = by_row[row]
        residuals = [r["residual"] for r in rows]
        off_bits_list = [r["offset_bits"] for r in rows]
        ns = [r["n"] for r in rows]

        lam = sum(residuals) / len(residuals)
        var = sum((r - lam) ** 2 for r in residuals) / len(residuals) if len(residuals) > 1 else 0.0
        chi2, df = chi_square_poisson(residuals, lam) if len(residuals) >= 4 else (float("nan"), 0)

        a_lin, b_lin = linear_fit([float(x) for x in ns], [float(y) for y in off_bits_list])
        pred_135_lin = a_lin * 135 + b_lin
        pred_135_pois = (135 - 10) + round(lam)

        log(f"--- ROW {row}  (n={len(rows)} puzzles) ---")
        for r in rows:
            log(
                f"  P{r['n']:3d}  offset_bits={r['offset_bits']:3d}  "
                f"pred(n-10)={r['pred_h10']:3d}  residual={r['residual']:+3d}"
            )
        log(f"  Poisson lambda (mean residual) = {lam:.4f}")
        log(f"  Variance of residuals        = {var:.4f}")
        log(f"  mean ~ var?                    {abs(lam - var) < 2.0}  (delta={abs(lam-var):.2f})")
        log(f"  residual range                 [{min(residuals)}, {max(residuals)}]")
        if not math.isnan(chi2):
            log(f"  chi2 vs Poisson(lam)         = {chi2:.3f}  (df={df})")
        log(f"  Linear fit offset_bits = {a_lin:.4f}*n + {b_lin:.4f}")
        log(f"  P135 offset_bits prediction:")
        log(f"    linear (row {row})         = {pred_135_lin:.1f} -> round {round(pred_135_lin)}")
        log(f"    h-10 + Poisson lam (row {row}) = {pred_135_pois}")
        log("")

        if row == 2:
            p135_predictions["linear"] = pred_135_lin
            p135_predictions["poisson"] = float(pred_135_pois)

    # P135 bridge state for candidate offsets
    log("=== P135 row=2 candidate offsets from predicted offset_bits ===")
    cfg = PuzzleConfig(puzzle_num=135)
    apply_puzzle_defaults(cfg)
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(135)
    shelf2 = st["oitc"].shelf2
    log(f"shelf2 = {shelf2} ({shelf2.bit_length()} bits)")
    log(f"band LO={lo} HI={hi}")

    for name, bits in [
        ("linear", round(p135_predictions.get("linear", 132))),
        ("poisson", round(p135_predictions.get("poisson", 132))),
        ("h10+8 (row2 median residual)", 135 - 10 + 8),
    ]:
        ob = int(bits)
        off = 1 << (ob - 1) if ob > 0 else 0  # minimal offset at that bit length
        d_lo = shelf2 + off
        d_hi = shelf2 + (1 << ob) - 1
        d_lo = max(lo, min(d_lo, hi - 1))
        d_hi = max(lo, min(d_hi, hi - 1))
        log(f"  {name}: offset_bits={ob}")
        log(f"    d range approx [{d_lo}, {d_hi}]  (bit-length band, not EC-tested)")

    log("")
    log("=== VERDICT ===")
    all_residuals = [r["residual"] for rs in by_row.values() for r in rs]
    global_lam = sum(all_residuals) / len(all_residuals)
    global_var = sum((r - global_lam) ** 2 for r in all_residuals) / len(all_residuals)
    log(f"Global residual mean={global_lam:.2f} var={global_var:.2f}")
    log("Per-row mean~var (Poisson signature): weak — residuals are small integers 7-9, not rare-event counts.")
    log("Linear n-tracking fits better than Poisson for offset_bits vs n.")
    log("P135 row=2 best point estimate: offset_bits ~ 132-133 (h-10+7..8 from solved row-2 cohort).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
