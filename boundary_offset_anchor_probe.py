#!/usr/bin/env python3
"""Boundary-offset anchor probe: gap, hinge, p-N+7, p-N-7 across all pubkeys.

Compares x+offset distances to puzzle-band lo/hi/mid anchors.
Uses all solved keys from 53125 plus RSZ pubkeys for unsolved entries.
"""

from __future__ import annotations

import json
from pathlib import Path

from hashkeys_rsz import N, PUZZLE_RSZ, p, y_roots_from_x
from puzzle_keys_53125 import parse_53125

GAP = p - N
OFFSETS = {
    "gap": GAP,
    "hinge": GAP + 1,
    "gap+7": GAP + 7,
    "gap-7": GAP - 7,
}
OUT = Path(__file__).with_name("boundary_offset_anchor_probe_report.json")


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


def main() -> None:
    keys = parse_53125()
    # All solved puzzles with pubkey coords from 53125 (n >= 65 for band relevance)
    puzzles = sorted(n for n in keys if n >= 65 and keys[n].px)

    rows = []
    wins = {name: {"lo": 0, "hi": 0, "mid": 0} for name in OFFSETS}
    best_at_hi: dict[int, str] = {}

    for n in puzzles:
        xy = pubkey_xy(n, keys)
        if not xy:
            continue
        px, _ = xy
        lo = 1 << (n - 1)
        hi = (1 << n) - 1
        mid = (lo + hi) // 2

        scores = {}
        for name, offset in OFFSETS.items():
            x_shift = (px + offset) % p
            scores[name] = {
                "lo": anchor_score(x_shift, lo, offset),
                "hi": anchor_score(x_shift, hi, offset),
                "mid": anchor_score(x_shift, mid, offset),
            }

        hi_rank = sorted(OFFSETS, key=lambda name: scores[name]["hi"])
        best_hi = hi_rank[0]
        best_at_hi[n] = best_hi

        for name in OFFSETS:
            for anchor in ("lo", "hi", "mid"):
                if scores[name][anchor] == min(scores[o][anchor] for o in OFFSETS):
                    wins[name][anchor] += 1

        row = {
            "puzzle": n,
            "solved": n in keys and keys[n].d > 0,
            "has_rsz": n in PUZZLE_RSZ,
            "best_at_hi": best_hi,
            "scores": scores,
            "hinge_beats_gap_hi": scores["hinge"]["hi"] < scores["gap"]["hi"],
            "plus7_beats_gap_hi": scores["gap+7"]["hi"] < scores["gap"]["hi"],
            "minus7_beats_gap_hi": scores["gap-7"]["hi"] < scores["gap"]["hi"],
            "plus7_beats_hinge_hi": scores["gap+7"]["hi"] < scores["hinge"]["hi"],
            "minus7_beats_hinge_hi": scores["gap-7"]["hi"] < scores["hinge"]["hi"],
        }
        rows.append(row)

    solved_rows = [r for r in rows if r["solved"]]
    unsolved_rows = [r for r in rows if not r["solved"]]
    total = len(rows)

    def rate(flag: str) -> float:
        return round(sum(1 for r in rows if r[flag]) / total, 3) if total else 0

    def best_hi_count(name: str) -> int:
        return sum(1 for r in rows if r["best_at_hi"] == name)

    report = {
        "question": "Which boundary offset (gap, hinge, p-N+7, p-N-7) wins hi-anchor?",
        "facts": {
            "offsets": {k: v for k, v in OFFSETS.items()},
            "puzzle_count": total,
            "solved_count": len(solved_rows),
            "unsolved_count": len(unsolved_rows),
            "rsz_count": sum(1 for r in rows if r["has_rsz"]),
        },
        "best_at_hi": {name: best_hi_count(name) for name in OFFSETS},
        "best_at_hi_rate": {name: round(best_hi_count(name) / total, 3) if total else 0 for name in OFFSETS},
        "strict_wins_vs_all_others": wins,
        "beats_gap_at_hi": {
            "hinge": sum(1 for r in rows if r["hinge_beats_gap_hi"]),
            "gap+7": sum(1 for r in rows if r["plus7_beats_gap_hi"]),
            "gap-7": sum(1 for r in rows if r["minus7_beats_gap_hi"]),
        },
        "beats_gap_at_hi_rate": {
            "hinge": rate("hinge_beats_gap_hi"),
            "gap+7": rate("plus7_beats_gap_hi"),
            "gap-7": rate("minus7_beats_gap_hi"),
        },
        "beats_hinge_at_hi": {
            "gap+7": sum(1 for r in rows if r["plus7_beats_hinge_hi"]),
            "gap-7": sum(1 for r in rows if r["minus7_beats_hinge_hi"]),
        },
        "rows": rows,
        "notes": [
            "best_at_hi = offset with smallest circular distance to hi = 2^n - 1.",
            "strict_wins counts puzzles where offset ties for best among the four.",
            "Public x transforms only; d band-limited, k not used.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Boundary offset anchor probe complete.")
    print(f"  puzzles: {total} (solved {len(solved_rows)}, unsolved {len(unsolved_rows)})")
    print("  best_at_hi:", report["best_at_hi"])
    print("  beats_gap_at_hi:", report["beats_gap_at_hi"])
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
