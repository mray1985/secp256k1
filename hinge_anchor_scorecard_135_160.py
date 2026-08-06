#!/usr/bin/env python3
"""Gap-vs-hinge anchor scorecard across puzzles 135-160.

Public-only scorecard using puzzle pubkeys and puzzle-band anchors.
`d` is treated as band-limited; `k` is intentionally not used as an anchor variable.
"""

from __future__ import annotations

import json
from pathlib import Path

from hashkeys_rsz import PUZZLE_RSZ, p, N, y_roots_from_x

GAP = p - N
HINGE = GAP + 1
OUT = Path(__file__).with_name("hinge_anchor_scorecard_135_160_report.json")


def anchor_score(x: int, anchor: int, modulus: int) -> int:
    return min((x - anchor) % modulus, (anchor - x) % modulus)


def pubkey_xy(n: int) -> tuple[int, int]:
    pub = PUZZLE_RSZ[n].pub_compressed
    px = int(pub[2:], 16)
    yp, yn = y_roots_from_x(px)
    py = yp if pub.startswith("02") else yn
    return px, py


def main() -> None:
    rows = []
    hinge_wins = {"lo": 0, "hi": 0, "mid": 0, "width": 0}
    puzzles = [n for n in range(135, 161) if n in PUZZLE_RSZ]

    for n in puzzles:
        px, py = pubkey_xy(n)
        lo = 1 << (n - 1)
        hi = (1 << n) - 1
        mid = (lo + hi) // 2
        width = hi - lo
        x_gap = (px + GAP) % p
        x_hinge = (px + HINGE) % p

        gap_lo = anchor_score(x_gap, lo, GAP)
        hinge_lo = anchor_score(x_hinge, lo, HINGE)
        gap_hi = anchor_score(x_gap, hi, GAP)
        hinge_hi = anchor_score(x_hinge, hi, HINGE)
        gap_mid = anchor_score(x_gap, mid, GAP)
        hinge_mid = anchor_score(x_hinge, mid, HINGE)
        gap_width = abs(x_gap - width)
        hinge_width = abs(x_hinge - width)

        if hinge_lo < gap_lo:
            hinge_wins["lo"] += 1
        if hinge_hi < gap_hi:
            hinge_wins["hi"] += 1
        if hinge_mid < gap_mid:
            hinge_wins["mid"] += 1
        if hinge_width < gap_width:
            hinge_wins["width"] += 1

        rows.append(
            {
                "puzzle": n,
                "lo": lo,
                "hi": hi,
                "mid": mid,
                "gap_to_lo": gap_lo,
                "hinge_to_lo": hinge_lo,
                "gap_to_hi": gap_hi,
                "hinge_to_hi": hinge_hi,
                "gap_to_mid": gap_mid,
                "hinge_to_mid": hinge_mid,
                "gap_to_width": gap_width,
                "hinge_to_width": hinge_width,
                "hinge_beats_gap_lo": hinge_lo < gap_lo,
                "hinge_beats_gap_hi": hinge_hi < gap_hi,
                "hinge_beats_gap_mid": hinge_mid < gap_mid,
                "hinge_beats_gap_width": hinge_width < gap_width,
            }
        )

    report = {
        "question": "Does hinge beat gap on anchor scores across puzzles 135-160?",
        "facts": {
            "gap": GAP,
            "hinge": HINGE,
            "puzzles": puzzles,
            "d_is_band_limited": True,
            "k_not_used_as_anchor_variable": True,
        },
        "hinge_wins": hinge_wins,
        "rows": rows,
        "notes": [
            "Scores use public x only and compare shifted x against puzzle-band anchors.",
            "A hinge win means smaller anchor distance under this metric, not key recovery.",
            "This scorecard is meant to reveal whether hinge helps consistently in the unsolved range.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Hinge anchor scorecard 135-160 complete.")
    print(f"Hinge wins: {hinge_wins}")
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
