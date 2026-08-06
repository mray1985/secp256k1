#!/usr/bin/env python3
"""Probe whether p-N+1 behaves differently from p-N on solved puzzles.

This is a calibration/structure script, not a blind solver. It compares
descriptive residue, distance, and ranking behavior under:
  gap   = p - N
  hinge = p - N + 1
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from hashkeys_rsz import N, PUZZLE_RSZ, p
from puzzle_keys_53125 import parse_53125

GAP = p - N
HINGE = GAP + 1
OUT = Path(__file__).with_name("p_minus_N_plus_1_hinge_probe_report.json")


@dataclass(frozen=True)
class HingeRow:
    puzzle: int
    d_mod_gap: int
    d_mod_hinge: int
    k_mod_gap: int
    k_mod_hinge: int
    px_mod_gap: int
    px_mod_hinge: int
    r_mod_gap: int
    r_mod_hinge: int
    d_dist_gap: int
    d_dist_hinge: int
    px_dist_gap: int
    px_dist_hinge: int


def solve_k(d: int, n: int) -> int:
    rsz = PUZZLE_RSZ[n]
    return rsz.k or rsz.recover_k_from_d(d)


def nearest_multiple_distance(x: int, modulus: int) -> int:
    r = x % modulus
    return min(r, modulus - r)


def anchor_score(x: int, anchor: int, modulus: int) -> int:
    return min((x - anchor) % modulus, (anchor - x) % modulus)


def main() -> None:
    keys = parse_53125()
    solved = {n: pk for n, pk in sorted(keys.items()) if 65 <= n <= 130 and pk.d > 0 and n in PUZZLE_RSZ}

    rows: list[HingeRow] = []
    hinge_better = {
        "d_distance": 0,
        "px_distance": 0,
        "k_distance": 0,
        "r_distance": 0,
    }
    anchor_rows = []

    for n, pk in solved.items():
        rsz = PUZZLE_RSZ[n]
        k = solve_k(pk.d, n)

        d_gap = pk.d % GAP
        d_hinge = pk.d % HINGE
        k_gap = k % GAP
        k_hinge = k % HINGE
        px_gap = pk.px % GAP
        px_hinge = pk.px % HINGE
        r_gap = rsz.r % GAP
        r_hinge = rsz.r % HINGE

        d_dist_gap = nearest_multiple_distance(pk.d, GAP)
        d_dist_hinge = nearest_multiple_distance(pk.d, HINGE)
        px_dist_gap = nearest_multiple_distance(pk.px, GAP)
        px_dist_hinge = nearest_multiple_distance(pk.px, HINGE)
        k_dist_gap = nearest_multiple_distance(k, GAP)
        k_dist_hinge = nearest_multiple_distance(k, HINGE)
        r_dist_gap = nearest_multiple_distance(rsz.r, GAP)
        r_dist_hinge = nearest_multiple_distance(rsz.r, HINGE)

        if d_dist_hinge < d_dist_gap:
            hinge_better["d_distance"] += 1
        if px_dist_hinge < px_dist_gap:
            hinge_better["px_distance"] += 1
        if k_dist_hinge < k_dist_gap:
            hinge_better["k_distance"] += 1
        if r_dist_hinge < r_dist_gap:
            hinge_better["r_distance"] += 1

        lo = 1 << (n - 1)
        hi = (1 << n) - 1
        anchor_rows.append(
            {
                "puzzle": n,
                "gap_anchor_lo": anchor_score(pk.d, lo, GAP),
                "hinge_anchor_lo": anchor_score(pk.d, lo, HINGE),
                "gap_anchor_hi": anchor_score(pk.d, hi, GAP),
                "hinge_anchor_hi": anchor_score(pk.d, hi, HINGE),
                "gap_anchor_px": anchor_score(pk.px, lo, GAP),
                "hinge_anchor_px": anchor_score(pk.px, lo, HINGE),
            }
        )

        rows.append(
            HingeRow(
                puzzle=n,
                d_mod_gap=d_gap,
                d_mod_hinge=d_hinge,
                k_mod_gap=k_gap,
                k_mod_hinge=k_hinge,
                px_mod_gap=px_gap,
                px_mod_hinge=px_hinge,
                r_mod_gap=r_gap,
                r_mod_hinge=r_hinge,
                d_dist_gap=d_dist_gap,
                d_dist_hinge=d_dist_hinge,
                px_dist_gap=px_dist_gap,
                px_dist_hinge=px_dist_hinge,
            )
        )

    report = {
        "question": "Does p-N+1 act as a better field-scalar boundary hinge than p-N?",
        "facts": {
            "p": p,
            "N": N,
            "gap": GAP,
            "hinge": HINGE,
            "gap_plus_one_identity_term": True,
            "solved_puzzles_tested": list(solved),
        },
        "hinge_better_counts": hinge_better,
        "rows": [asdict(r) for r in rows],
        "anchor_rows": anchor_rows,
        "notes": [
            "This script compares descriptive residue and distance behavior only.",
            "A hinge win here means 'closer under this score', not blind key recovery.",
            "The intended follow-up is whether hinge rankings improve lane or anchor hypotheses.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("p-N+1 hinge probe complete.")
    print(f"Solved puzzles tested: {len(solved)}")
    print(f"Hinge better counts: {hinge_better}")
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
