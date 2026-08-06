#!/usr/bin/env python3
"""Ceiling-anchor hypothesis: does hinge beat gap at hi-anchor across many puzzles?

Tests public x+gap and x+hinge against puzzle-band hi = 2^n - 1.
d is band-limited; k is not used as an anchor variable.
"""

from __future__ import annotations

import json
from pathlib import Path

from hashkeys_rsz import N, PUZZLE_RSZ, p, y_roots_from_x
from puzzle_keys_53125 import parse_53125

GAP = p - N
HINGE = GAP + 1
OUT = Path(__file__).with_name("ceiling_anchor_hypothesis_probe_report.json")


def anchor_score(x: int, anchor: int, modulus: int) -> int:
    return min((x - anchor) % modulus, (anchor - x) % modulus)


def pubkey_xy(n: int, keys: dict) -> tuple[int, int]:
    if n in keys:
        return keys[n].px, keys[n].py
    pub = PUZZLE_RSZ[n].pub_compressed
    px = int(pub[2:], 16)
    yp, yn = y_roots_from_x(px)
    py = yp if pub.startswith("02") else yn
    return px, py


def main() -> None:
    keys = parse_53125()
    # All puzzles with RSZ pubkeys: solved 65-130 step 5, plus unsolved 135-160 step 5
    puzzles = sorted(n for n in PUZZLE_RSZ if n >= 65)

    rows = []
    hinge_wins_hi = 0
    hinge_wins_lo = 0
    hinge_wins_mid = 0

    for n in puzzles:
        if n not in PUZZLE_RSZ:
            continue
        px, _ = pubkey_xy(n, keys)
        lo = 1 << (n - 1)
        hi = (1 << n) - 1
        mid = (lo + hi) // 2
        x_gap = (px + GAP) % p
        x_hinge = (px + HINGE) % p

        gap_lo = anchor_score(x_gap, lo, GAP)
        hinge_lo = anchor_score(x_hinge, lo, HINGE)
        gap_hi = anchor_score(x_gap, hi, GAP)
        hinge_hi = anchor_score(x_hinge, hi, HINGE)
        gap_mid = anchor_score(x_gap, mid, GAP)
        hinge_mid = anchor_score(x_hinge, mid, HINGE)

        if hinge_hi < gap_hi:
            hinge_wins_hi += 1
        if hinge_lo < gap_lo:
            hinge_wins_lo += 1
        if hinge_mid < gap_mid:
            hinge_wins_mid += 1

        rows.append(
            {
                "puzzle": n,
                "solved": n in keys and keys[n].d > 0,
                "gap_to_hi": gap_hi,
                "hinge_to_hi": hinge_hi,
                "gap_to_lo": gap_lo,
                "hinge_to_lo": hinge_lo,
                "hinge_beats_hi": hinge_hi < gap_hi,
                "hinge_beats_lo": hinge_lo < gap_lo,
                "hi_improvement": gap_hi - hinge_hi if hinge_hi < gap_hi else 0,
            }
        )

    solved_rows = [r for r in rows if r["solved"]]
    unsolved_rows = [r for r in rows if not r["solved"]]

    report = {
        "question": "Does hinge consistently improve hi-anchor scores vs gap?",
        "facts": {
            "gap": GAP,
            "hinge": HINGE,
            "puzzle_count": len(rows),
            "solved_count": len(solved_rows),
            "unsolved_count": len(unsolved_rows),
        },
        "aggregate_hinge_wins": {
            "hi": hinge_wins_hi,
            "lo": hinge_wins_lo,
            "mid": hinge_wins_mid,
            "total_puzzles": len(rows),
        },
        "hi_win_rate": round(hinge_wins_hi / len(rows), 3) if rows else 0,
        "lo_win_rate": round(hinge_wins_lo / len(rows), 3) if rows else 0,
        "solved_hi_wins": sum(1 for r in solved_rows if r["hinge_beats_hi"]),
        "unsolved_hi_wins": sum(1 for r in unsolved_rows if r["hinge_beats_hi"]),
        "rows": rows,
        "notes": [
            "Ceiling hypothesis: hinge helps at hi = 2^n - 1 more than at lo.",
            "Public x transforms only; d band-limited, k not used.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Ceiling anchor hypothesis probe complete.")
    print(f"Hinge wins hi: {hinge_wins_hi}/{len(rows)} ({report['hi_win_rate']})")
    print(f"Hinge wins lo: {hinge_wins_lo}/{len(rows)} ({report['lo_win_rate']})")
    print(f"Solved hi: {report['solved_hi_wins']}/{len(solved_rows)} | Unsolved hi: {report['unsolved_hi_wins']}/{len(unsolved_rows)}")
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
