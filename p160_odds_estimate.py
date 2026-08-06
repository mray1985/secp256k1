#!/usr/bin/env python3
"""Rough hit odds for P160 complement KeyHunt windows vs band / 1.5x prior."""

from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "puzzle160_keyhunt_bsgs" / "complement_exports" / "complement_manifest.txt"


def parse_windows(n: int) -> list[dict]:
    rows: list[dict] = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.startswith("run_p160_comp_"):
            continue
        parts = line.split()
        lo_hex, hi_hex = parts[-1].split(":")
        w_lo, w_hi = int(lo_hex, 16), int(hi_hex, 16)
        center = (w_lo + w_hi) // 2
        span = w_hi - w_lo + 1
        rows.append(
            {
                "label": parts[1],
                "lo": w_lo,
                "hi": w_hi,
                "span": span,
                "center": center,
                "f": math.log2(center) - (n - 1),
            }
        )
    return rows


def zone(n: int, f_lo: float, f_hi: float) -> tuple[int, int, int]:
    d_lo = int(2 ** ((n - 1) + f_lo))
    d_hi = int(2 ** ((n - 1) + f_hi))
    return d_lo, d_hi, d_hi - d_lo


def overlap(a_lo: int, a_hi: int, b_lo: int, b_hi: int) -> int:
    return max(0, min(a_hi, b_hi) - max(a_lo, b_lo))


def main() -> None:
    n = 160
    lo, hi = 1 << (n - 1), 1 << n
    band = hi - lo
    target_f = math.log2(1.5)
    windows = parse_windows(n)

    priors = {
        "uniform full band": zone(n, 0.0, 1.0),
        "f in [0.58, 0.67]": zone(n, 0.58, 0.67),
        "f in [0.55, 0.62]": zone(n, 0.55, 0.62),
        "f in [0.50, 0.75]": zone(n, 0.50, 0.75),
    }

    def covered_in_zone(z_lo: int, z_hi: int) -> int:
        total = 0
        for w in windows:
            total += overlap(w["lo"], w["hi"], z_lo, z_hi)
        return min(total, z_hi - z_lo)

    print("P160 HIT ODDS (rough)")
    print("=" * 60)
    print(f"Band: 2^{n-1} keys")
    print(f"One window span: ~2^{windows[0]['span'].bit_length() - 1}")
    print(f"Windows: {len(windows)}")
    print()

    for name, (z_lo, z_hi, z_w) in priors.items():
        cov = covered_in_zone(z_lo, z_hi)
        p_zone = cov / z_w if z_w else 0
        p_uniform = cov / band
        print(name)
        print(f"  P(hit | d in this zone) ~ {100 * p_zone:.2f}%")
        print(f"  P(hit | d uniform in band) ~ {p_uniform:.2e}")
        print()

    ranked = sorted(windows, key=lambda w: abs(w["f"] - target_f))[:3]
    z_lo, z_hi, z_w = zone(n, 0.58, 0.67)
    print("Top 3 windows vs f[0.58,0.67] slice:")
    for w in ranked:
        ov = overlap(w["lo"], w["hi"], z_lo, z_hi)
        print(f"  {w['label']}: f={w['f']:.4f}, covers {100 * ov / z_w:.2f}% of prior slice")

    # solved-puzzle prior probability d is in f[0.58,0.67]
    p_prior_correct = 6 / 82  # from earlier batch
    cov_narrow = covered_in_zone(*zone(n, 0.58, 0.67)[:2])
    p_hit_if_prior = cov_narrow / zone(n, 0.58, 0.67)[2]
    p_total = p_prior_correct * p_hit_if_prior
    print()
    print("Combined (very rough):")
    print(f"  P(d in f[0.58,0.67]) from solved history ~ {100*p_prior_correct:.1f}%")
    print(f"  P(hit | d in slice, all 20 windows) ~ {100*p_hit_if_prior:.1f}%")
    print(f"  => P(hit) ~ {100*p_total:.2f}% if both heuristics hold")
    print(f"  Single best window alone: ~{100*p_hit_if_prior/len(windows):.2f}% of slice")


if __name__ == "__main__":
    main()
