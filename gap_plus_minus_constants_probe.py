#!/usr/bin/env python3
"""Probe gap +/- small constants as hi-anchor offsets.

Constants: 1, 3, 7, 8, 20, 21, 49, 76
Each tested as gap+c and gap-c separately on all pubkeys (n >= 65).
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from hashkeys_rsz import N, PUZZLE_RSZ, p, y_roots_from_x
from puzzle_keys_53125 import parse_53125

GAP = p - N
CONSTANTS = [1, 3, 7, 8, 20, 21, 49, 76]
FIXED = {
    "gap": GAP,
    "h1": GAP + 1,
    "h7": GAP + 7,
    "hm7": GAP - 7,
}
OUT = Path(__file__).with_name("gap_plus_minus_constants_probe_report.json")


def anchor_score(x: int, anchor: int, modulus: int) -> int:
    m = abs(modulus)
    if m == 0:
        return 0
    return min((x - anchor) % m, (anchor - x) % m)


def hi_score(px: int, n: int, offset: int) -> int:
    hi = (1 << n) - 1
    x_shift = (px + offset) % p
    return anchor_score(x_shift, hi, offset)


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


def main() -> None:
    keys = parse_53125()
    puzzles = sorted(n for n in set(keys) | set(PUZZLE_RSZ) if n >= 65 and pubkey_xy(n, keys))

    families: dict[str, dict] = {}
    agg_plus: dict[int, dict] = defaultdict(lambda: {"beats_gap": 0, "beats_h7": 0, "best_at_hi": 0})
    agg_minus: dict[int, dict] = defaultdict(lambda: {"beats_gap": 0, "beats_h7": 0, "best_at_hi": 0})

    per_puzzle = []

    for n in puzzles:
        px, _ = pubkey_xy(n, keys)  # type: ignore[misc]
        fixed_scores = {name: hi_score(px, n, off) for name, off in FIXED.items()}

        row = {"puzzle": n, "solved": n in keys and keys[n].d > 0, "fixed_scores": fixed_scores, "variants": {}}

        for c in CONSTANTS:
            for sign, label, offset in (
                ("+", f"gap+{c}", GAP + c),
                ("-", f"gap-{c}", GAP - c),
            ):
                score = hi_score(px, n, offset)
                all_scores = {**fixed_scores, label: score}
                best = min(all_scores, key=all_scores.get)
                beats_gap = score < fixed_scores["gap"]
                beats_h7 = score < fixed_scores["h7"]
                best_at_hi = best == label

                row["variants"][label] = {
                    "constant": c,
                    "sign": sign,
                    "offset": offset,
                    "hi_score": score,
                    "beats_gap": beats_gap,
                    "beats_h7": beats_h7,
                    "best_at_hi": best_at_hi,
                    "best_overall": best,
                }

                bucket = agg_plus if sign == "+" else agg_minus
                if beats_gap:
                    bucket[c]["beats_gap"] += 1
                if beats_h7:
                    bucket[c]["beats_h7"] += 1
                if best_at_hi:
                    bucket[c]["best_at_hi"] += 1

        per_puzzle.append(row)

    total = len(puzzles)

    def summarize(agg: dict, sign: str) -> list[dict]:
        rows = []
        for c in CONSTANTS:
            a = agg[c]
            rows.append(
                {
                    "label": f"gap{sign}{c}",
                    "constant": c,
                    "beats_gap": a["beats_gap"],
                    "beats_h7": a["beats_h7"],
                    "best_at_hi": a["best_at_hi"],
                    "beats_gap_rate": round(a["beats_gap"] / total, 3) if total else 0,
                    "beats_h7_rate": round(a["beats_h7"] / total, 3) if total else 0,
                    "best_at_hi_rate": round(a["best_at_hi"] / total, 3) if total else 0,
                }
            )
        return sorted(rows, key=lambda r: r["best_at_hi"], reverse=True)

    plus_summary = summarize(agg_plus, "+")
    minus_summary = summarize(agg_minus, "-")
    all_variants = plus_summary + minus_summary
    all_by_best = sorted(all_variants, key=lambda r: (r["best_at_hi"], r["beats_h7"]), reverse=True)

    report = {
        "question": "Which gap +/- small constants win hi-anchor vs gap and h7?",
        "facts": {
            "gap": GAP,
            "constants": CONSTANTS,
            "puzzle_count": total,
            "puzzles": puzzles,
        },
        "plus_summary": plus_summary,
        "minus_summary": minus_summary,
        "ranked_by_best_at_hi": all_by_best,
        "fixed_reference": {
            "h7_best_at_hi": sum(
                1
                for row in per_puzzle
                if min({**row["fixed_scores"], "h7": row["fixed_scores"]["h7"]}, key=lambda k: row["fixed_scores"].get(k, row["fixed_scores"]["h7"] if k == "h7" else 0))
                == "h7"
            ),
        },
        "per_puzzle": per_puzzle,
        "notes": [
            "Constants are fixed offsets from gap, not per-puzzle private keys.",
            "gap+7 equals h7; gap+1 equals h1.",
            "Public x only; d band-limited; k not used.",
        ],
    }

    # count how often h7 is best among fixed only
    h7_wins = 0
    for row in per_puzzle:
        if row["fixed_scores"]["h7"] == min(row["fixed_scores"].values()):
            h7_wins += 1
    report["fixed_reference"]["h7_best_among_fixed"] = h7_wins

    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("gap +/- constants probe complete.")
    print(f"  puzzles: {total}")
    print("  top by best_at_hi:")
    for r in all_by_best[:8]:
        print(f"    {r['label']}: best_hi={r['best_at_hi']}/{total} beats_h7={r['beats_h7']}/{total}")
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
