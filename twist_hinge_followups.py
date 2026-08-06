#!/usr/bin/env python3
"""Follow-up tests for twist boundary and p-N+1 hinge ideas.

Runs three public-structure tests:
1. Extend twist/hinge Legendre checks to unsolved P135/P160.
2. Compare hinge-shifted x against puzzle-range / lane-style anchors.
3. Compare corner deltas under gap vs hinge boundary terms.

Important framing:
- d lives in the puzzle band [2^(n-1), 2^n - 1]
- k is a large scalar modulo N and should not be treated like a puzzle-band value
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from hashkeys_rsz import N, PUZZLE_RSZ, p, y_roots_from_x
from puzzle_keys_53125 import parse_53125

GAP = p - N
HINGE = GAP + 1
OUT = Path(__file__).with_name("twist_hinge_followups_report.json")


@dataclass(frozen=True)
class PublicPoint:
    puzzle: int
    px: int
    py: int
    pub: str
    solved: bool


def legendre_symbol(a: int) -> int:
    a %= p
    if a == 0:
        return 0
    v = pow(a, (p - 1) // 2, p)
    return -1 if v == p - 1 else v


def point_for_puzzle(n: int, keys: dict[int, object]) -> PublicPoint:
    if n in keys:
        pk = keys[n]
        return PublicPoint(n, pk.px, pk.py, PUZZLE_RSZ[n].pub_compressed, pk.d > 0)
    pub = PUZZLE_RSZ[n].pub_compressed
    px = int(pub[2:], 16)
    yp, yn = y_roots_from_x(px)
    py = yp if pub.startswith("02") else yn
    return PublicPoint(n, px, py, pub, False)


def classify_x(x: int) -> dict[str, object]:
    y_sq = (pow(x, 3, p) + 7) % p
    chi = legendre_symbol(y_sq)
    side = {1: "main", -1: "twist", 0: "singular"}[chi]
    return {"y_sq": y_sq, "legendre": chi, "side": side}


def anchor_score(x: int, anchor: int, modulus: int) -> int:
    return min((x - anchor) % modulus, (anchor - x) % modulus)


def lane_scores(px: int, n: int) -> dict[str, int]:
    lo = 1 << (n - 1)
    hi = (1 << n) - 1
    x_gap = (px + GAP) % p
    x_hinge = (px + HINGE) % p
    return {
        "gap_to_lo_mod_gap": anchor_score(x_gap, lo, GAP),
        "hinge_to_lo_mod_hinge": anchor_score(x_hinge, lo, HINGE),
        "gap_to_hi_mod_gap": anchor_score(x_gap, hi, GAP),
        "hinge_to_hi_mod_hinge": anchor_score(x_hinge, hi, HINGE),
        "gap_raw_to_band_width": abs(x_gap - (hi - lo)),
        "hinge_raw_to_band_width": abs(x_hinge - (hi - lo)),
    }


def corner_deltas(n: int) -> dict[str, int]:
    lo = 1 << (n - 1)
    top = (1 << n) - 1
    # Existing gap-space formula from GAP_NEW_N_RESULTS uses delta = gap.
    gap_corner = {
        "delta_A": GAP - lo,
        "delta_B": GAP + (1 << n),
        "delta_C": GAP + lo,
        "delta_D": GAP + (1 << n) + 1,
    }
    hinge_corner = {
        "delta_A": HINGE - lo,
        "delta_B": HINGE + (1 << n),
        "delta_C": HINGE + lo,
        "delta_D": HINGE + (1 << n) + 1,
    }
    return {
        "n": n,
        "lo": lo,
        "top": top,
        "gap_corner": gap_corner,
        "hinge_corner": hinge_corner,
        "corner_diffs_hinge_minus_gap": {k: hinge_corner[k] - gap_corner[k] for k in gap_corner},
    }


def main() -> None:
    keys = parse_53125()
    target_puzzles = [65, 80, 100, 130, 135, 160]
    points = [point_for_puzzle(n, keys) for n in target_puzzles]

    unsolved_legendre = {}
    for pt in points:
        x = pt.px
        x_gap = (x + GAP) % p
        x_hinge = (x + HINGE) % p
        x_mgap = (x - GAP) % p
        x_mhinge = (x - HINGE) % p
        unsolved_legendre[pt.puzzle] = {
            "solved": pt.solved,
            "x": classify_x(x),
            "x+gap": classify_x(x_gap),
            "x+hinge": classify_x(x_hinge),
            "x-gap": classify_x(x_mgap),
            "x-hinge": classify_x(x_mhinge),
        }

    lane_report = {pt.puzzle: lane_scores(pt.px, pt.puzzle) for pt in points}
    corner_report = {n: corner_deltas(n) for n in (135, 160)}

    report = {
        "question": "Run all follow-up tests for twist boundary and p-N+1 hinge.",
        "facts": {
            "p": p,
            "N": N,
            "gap": GAP,
            "hinge": HINGE,
            "d_is_puzzle_range": True,
            "k_is_large_scalar_mod_N": True,
            "target_puzzles": target_puzzles,
        },
        "unsolved_and_reference_legendre": unsolved_legendre,
        "lane_report": lane_report,
        "corner_report": corner_report,
        "notes": [
            "Literal x stays main-curve for all sampled pubkeys.",
            "Shifted x values are public transforms used only to probe boundary crossing.",
            "Lane scores treat d as band-limited and avoid pretending k belongs to the puzzle band.",
            "Hinge corner deltas are exactly +1 relative to gap corner deltas at every corner.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    p135 = unsolved_legendre[135]
    p160 = unsolved_legendre[160]
    print("Twist/hinge follow-ups complete.")
    print(f"P135 literal side: {p135['x']['side']}, x+hinge side: {p135['x+hinge']['side']}")
    print(f"P160 literal side: {p160['x']['side']}, x+hinge side: {p160['x+hinge']['side']}")
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
