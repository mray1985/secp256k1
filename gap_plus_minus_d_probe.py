#!/usr/bin/env python3
"""Probe gap+d and gap-d separately for solved puzzle private keys.

gap   = p - N
plus  = gap + d   (per puzzle, d = private key in band)
minus = gap - d

Tests public-x hi-anchor scoring vs fixed offsets (gap, h1, h7, hm7).
Calibration only — uses known d. Not a blind solver.
"""

from __future__ import annotations

import json
from pathlib import Path

from hashkeys_rsz import N, PUZZLE_RSZ, p, y_roots_from_x
from puzzle_keys_53125 import parse_53125

GAP = p - N
FIXED = {
    "gap": GAP,
    "h1": GAP + 1,
    "h7": GAP + 7,
    "hm7": GAP - 7,
}
OUT = Path(__file__).with_name("gap_plus_minus_d_probe_report.json")


def anchor_score(x: int, anchor: int, modulus: int) -> int:
    m = abs(modulus)
    if m == 0:
        return 0
    return min((x - anchor) % m, (anchor - x) % m)


def legendre_symbol(a: int) -> int:
    a %= p
    if a == 0:
        return 0
    v = pow(a, (p - 1) // 2, p)
    return -1 if v == p - 1 else v


def classify_x(x: int) -> str:
    y_sq = (pow(x, 3, p) + 7) % p
    chi = legendre_symbol(y_sq)
    return {1: "main", -1: "twist", 0: "singular"}[chi]


def hi_score(px: int, n: int, offset: int) -> int:
    hi = (1 << n) - 1
    x_shift = (px + offset) % p
    return anchor_score(x_shift, hi, offset)


def main() -> None:
    keys = parse_53125()
    puzzles = sorted(n for n in keys if n >= 65 and keys[n].d > 0 and keys[n].px)

    plus_rows = []
    minus_rows = []
    plus_beats_gap = 0
    minus_beats_gap = 0
    plus_beats_h7 = 0
    minus_beats_h7 = 0
    plus_best_hi = 0
    minus_best_hi = 0

    for n in puzzles:
        pk = keys[n]
        d = pk.d
        px = pk.px
        lo = 1 << (n - 1)
        hi = (1 << n) - 1

        offset_plus = GAP + d
        offset_minus = GAP - d

        fixed_scores = {name: hi_score(px, n, off) for name, off in FIXED.items()}
        score_plus = hi_score(px, n, offset_plus)
        score_minus = hi_score(px, n, offset_minus)

        all_scores = {**fixed_scores, "gap+d": score_plus, "gap-d": score_minus}
        best_hi = min(all_scores, key=all_scores.get)

        x_plus = (px + offset_plus) % p
        x_minus = (px + offset_minus) % p

        plus_row = {
            "puzzle": n,
            "d": d,
            "offset": offset_plus,
            "hi_score": score_plus,
            "fixed_scores": fixed_scores,
            "beats_gap": score_plus < fixed_scores["gap"],
            "beats_h7": score_plus < fixed_scores["h7"],
            "best_at_hi": best_hi == "gap+d",
            "twist_side": classify_x(x_plus),
            "scalar_mod_gap": offset_plus % GAP,
            "scalar_mod_N": offset_plus % N,
            "scalar_mod_p": offset_plus % p,
            "equals_px_mod_p": (offset_plus % p) == (px % p),
            "equals_hi": offset_plus == hi,
            "d_fraction_of_gap": round(d / GAP, 12),
        }
        minus_row = {
            "puzzle": n,
            "d": d,
            "offset": offset_minus,
            "hi_score": score_minus,
            "fixed_scores": fixed_scores,
            "beats_gap": score_minus < fixed_scores["gap"],
            "beats_h7": score_minus < fixed_scores["h7"],
            "best_at_hi": best_hi == "gap-d",
            "twist_side": classify_x(x_minus),
            "scalar_mod_gap": offset_minus % GAP,
            "scalar_mod_N": offset_minus % N,
            "scalar_mod_p": offset_minus % p,
            "equals_px_mod_p": (offset_minus % p) == (px % p),
            "equals_lo": offset_minus == lo,
            "d_fraction_of_gap": round(d / GAP, 12),
        }

        if plus_row["beats_gap"]:
            plus_beats_gap += 1
        if minus_row["beats_gap"]:
            minus_beats_gap += 1
        if plus_row["beats_h7"]:
            plus_beats_h7 += 1
        if minus_row["beats_h7"]:
            minus_beats_h7 += 1
        if plus_row["best_at_hi"]:
            plus_best_hi += 1
        if minus_row["best_at_hi"]:
            minus_best_hi += 1

        plus_rows.append(plus_row)
        minus_rows.append(minus_row)

    total = len(puzzles)

    report = {
        "question": "Do gap+d and gap-d (separately) improve hi-anchor vs fixed offsets?",
        "facts": {
            "gap": GAP,
            "puzzle_count": total,
            "puzzles": puzzles,
            "d_is_private_key_in_band": True,
        },
        "gap_plus_d": {
            "formula": "offset = (p - N) + d",
            "beats_gap_at_hi": plus_beats_gap,
            "beats_h7_at_hi": plus_beats_h7,
            "best_at_hi": plus_best_hi,
            "beats_gap_rate": round(plus_beats_gap / total, 3) if total else 0,
            "beats_h7_rate": round(plus_beats_h7 / total, 3) if total else 0,
            "best_at_hi_rate": round(plus_best_hi / total, 3) if total else 0,
            "twist_count": sum(1 for r in plus_rows if r["twist_side"] == "twist"),
            "rows": plus_rows,
        },
        "gap_minus_d": {
            "formula": "offset = (p - N) - d",
            "beats_gap_at_hi": minus_beats_gap,
            "beats_h7_at_hi": minus_beats_h7,
            "best_at_hi": minus_best_hi,
            "beats_gap_rate": round(minus_beats_gap / total, 3) if total else 0,
            "beats_h7_rate": round(minus_beats_h7 / total, 3) if total else 0,
            "best_at_hi_rate": round(minus_best_hi / total, 3) if total else 0,
            "twist_count": sum(1 for r in minus_rows if r["twist_side"] == "twist"),
            "rows": minus_rows,
        },
        "head_to_head": {
            "plus_beats_minus_at_hi": sum(
                1 for a, b in zip(plus_rows, minus_rows) if a["hi_score"] < b["hi_score"]
            ),
            "minus_beats_plus_at_hi": sum(
                1 for a, b in zip(plus_rows, minus_rows) if b["hi_score"] < a["hi_score"]
            ),
            "ties": sum(1 for a, b in zip(plus_rows, minus_rows) if a["hi_score"] == b["hi_score"]),
        },
        "notes": [
            "Two families tested separately: gap+d and gap-d.",
            "Uses known private keys — calibration/structure only.",
            "Public x transform: (px + offset) mod p; score vs hi = 2^n - 1.",
            "d band-limited; k not used.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("gap +/- d probe complete.")
    print(f"  puzzles: {total}")
    print(f"  gap+d: beats_gap={plus_beats_gap}/{total} beats_h7={plus_beats_h7}/{total} best_hi={plus_best_hi}/{total}")
    print(f"  gap-d: beats_gap={minus_beats_gap}/{total} beats_h7={minus_beats_h7}/{total} best_hi={minus_best_hi}/{total}")
    print(f"  head_to_head: plus wins {report['head_to_head']['plus_beats_minus_at_hi']} | minus wins {report['head_to_head']['minus_beats_plus_at_hi']}")
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
