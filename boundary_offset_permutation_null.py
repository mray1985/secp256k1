#!/usr/bin/env python3
"""Permutation/null test: is h7 (p-N+7) special vs random offsets near p-N?

For each puzzle, compare h7 hi-anchor distance against 1000 random offsets
offset = p-N + delta, delta in [-1000, 1000].
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from hashkeys_rsz import N, PUZZLE_RSZ, p, y_roots_from_x
from puzzle_keys_53125 import parse_53125

GAP = p - N
H7 = GAP + 7
DELTA_MIN = -1000
DELTA_MAX = 1000
N_PERM = 1000
SEED = 20260701
OUT = Path(__file__).with_name("boundary_offset_permutation_null_report.json")


def anchor_score(x: int, anchor: int, modulus: int) -> int:
    return min((x - anchor) % modulus, (anchor - x) % modulus)


def pubkey_xy(n: int, keys: dict) -> tuple[int, int] | None:
    if n in keys and keys[n].px:
        return keys[n].px, keys[n].py
    if n in PUZZLE_RSZ:
        pub = PUZZLE_RSZ[n].pub_compressed
        px = int(pub[2:], 16)
        yp, yn = y_roots_from_x(px)
        py = yp if pub.startswith("02") else yn
        return px, py
    return None


def hi_distance(px: int, n: int, offset: int) -> int:
    hi = (1 << n) - 1
    x_shift = (px + offset) % p
    return anchor_score(x_shift, hi, offset)


def percentile_rank(h7_dist: int, null_dists: list[int]) -> float:
    """Fraction of null distances strictly worse (larger) than h7."""
    worse = sum(1 for d in null_dists if d > h7_dist)
    return worse / len(null_dists)


def main() -> None:
    rng = random.Random(SEED)
    keys = parse_53125()
    puzzles = sorted(n for n in keys if n >= 65 and pubkey_xy(n, keys))

    rows = []
    top5_count = 0
    top1_count = 0

    for n in puzzles:
        px, _ = pubkey_xy(n, keys)  # type: ignore[misc]
        h7_dist = hi_distance(px, n, H7)

        null_dists = []
        for _ in range(N_PERM):
            delta = rng.randint(DELTA_MIN, DELTA_MAX)
            offset = GAP + delta
            null_dists.append(hi_distance(px, n, offset))

        pct = percentile_rank(h7_dist, null_dists)
        rank = 1 + sum(1 for d in null_dists if d < h7_dist)
        in_top5 = pct >= 0.95
        in_top1 = pct >= 0.99
        if in_top5:
            top5_count += 1
        if in_top1:
            top1_count += 1

        rows.append(
            {
                "puzzle": n,
                "h7_hi_distance": h7_dist,
                "null_mean": round(sum(null_dists) / len(null_dists), 2),
                "null_min": min(null_dists),
                "null_median": sorted(null_dists)[len(null_dists) // 2],
                "percentile_rank": round(pct, 4),
                "rank_among_null": rank,
                "in_top_5pct": in_top5,
                "in_top_1pct": in_top1,
                "h7_delta": 7,
            }
        )

    total = len(rows)
    avg_pct = round(sum(r["percentile_rank"] for r in rows) / total, 4) if total else 0
    median_pct = round(sorted(r["percentile_rank"] for r in rows)[total // 2], 4) if total else 0

    if top1_count >= total * 0.5:
        label = "PROMISING"
    elif top5_count >= total * 0.5:
        label = "PROMISING"
    elif avg_pct >= 0.75:
        label = "PROMISING"
    elif avg_pct <= 0.55:
        label = "COINCIDENCE"
    else:
        label = "INCONCLUSIVE"

    report = {
        "question": "Is h7 (p-N+7) special vs random offsets near p-N for hi-anchor distance?",
        "protocol": {
            "h7": H7,
            "gap": GAP,
            "delta_range": [DELTA_MIN, DELTA_MAX],
            "permutations_per_puzzle": N_PERM,
            "seed": SEED,
            "puzzle_count": total,
        },
        "aggregate": {
            "mean_percentile_rank": avg_pct,
            "median_percentile_rank": median_pct,
            "top_5pct_count": top5_count,
            "top_1pct_count": top1_count,
            "top_5pct_rate": round(top5_count / total, 3) if total else 0,
            "top_1pct_rate": round(top1_count / total, 3) if total else 0,
        },
        "verdict": {
            "label": label,
            "criteria": {
                "PROMISING": "h7 in top 5% for majority of puzzles, or mean percentile >= 0.75",
                "COINCIDENCE": "mean percentile near 0.5 (<= 0.55)",
            },
        },
        "per_puzzle": rows,
        "notes": [
            "Lower hi-anchor distance is better.",
            "Percentile rank = fraction of null offsets with strictly larger hi distance.",
            "h7 delta=7 is fixed; null draws delta uniformly from [-1000,1000].",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Permutation null test complete.")
    print(f"  puzzles: {total}")
    print(f"  mean percentile: {avg_pct}")
    print(f"  top 5%: {top5_count}/{total} | top 1%: {top1_count}/{total}")
    print(f"  verdict: {label}")
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
