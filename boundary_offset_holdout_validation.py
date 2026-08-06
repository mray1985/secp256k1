#!/usr/bin/env python3
"""Holdout validation: does p-N+7 remain best hi-anchor offset out-of-sample?

Calibration: P65-P125 (fixed before holdout).
Holdout: P130-P160 (no tuning after seeing holdout).
"""

from __future__ import annotations

import json
from pathlib import Path

from hashkeys_rsz import N, PUZZLE_RSZ, p, y_roots_from_x
from puzzle_keys_53125 import parse_53125

GAP = p - N
OFFSETS = {
    "gap": GAP,
    "h1": GAP + 1,
    "h7": GAP + 7,
    "hm7": GAP - 7,
}
CALIBRATION = range(65, 126)
HOLDOUT = range(130, 161)
OUT = Path(__file__).with_name("boundary_offset_holdout_validation_report.json")


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


def score_puzzle(n: int, px: int) -> dict:
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
    winners = {}
    for anchor in ("lo", "hi", "mid"):
        best = min(OFFSETS, key=lambda name: scores[name][anchor])
        winners[anchor] = best
    return {"puzzle": n, "scores": scores, "winners": winners}


def winner_counts(rows: list[dict], anchor: str) -> dict[str, int]:
    counts = {name: 0 for name in OFFSETS}
    for row in rows:
        w = row["winners"][anchor]
        counts[w] += 1
    return counts


def main() -> None:
    keys = parse_53125()
    cal_puzzles = sorted(n for n in CALIBRATION if pubkey_xy(n, keys))
    hold_puzzles = sorted(n for n in HOLDOUT if pubkey_xy(n, keys))

    cal_rows = []
    for n in cal_puzzles:
        px, _ = pubkey_xy(n, keys)  # type: ignore[misc]
        cal_rows.append(score_puzzle(n, px))

    hold_rows = []
    for n in hold_puzzles:
        px, _ = pubkey_xy(n, keys)  # type: ignore[misc]
        hold_rows.append(score_puzzle(n, px))

    cal_hi = winner_counts(cal_rows, "hi")
    hold_hi = winner_counts(hold_rows, "hi")
    cal_lo = winner_counts(cal_rows, "lo")
    hold_lo = winner_counts(hold_rows, "lo")
    cal_mid = winner_counts(cal_rows, "mid")
    hold_mid = winner_counts(hold_rows, "mid")

    h7_survives = hold_hi["h7"] == max(hold_hi.values()) and hold_hi["h7"] > 0
    h7_unique_best_holdout = hold_hi["h7"] == max(hold_hi.values()) and sum(
        1 for v in hold_hi.values() if v == hold_hi["h7"]
    ) == 1

    report = {
        "question": "Does h7 (p-N+7) remain the best hi-anchor offset on holdout puzzles?",
        "protocol": {
            "calibration": f"P{CALIBRATION.start}-P{CALIBRATION.stop - 1}",
            "holdout": f"P{HOLDOUT.start}-P{HOLDOUT.stop - 1}",
            "no_tuning_after_holdout": True,
            "offsets": {k: v for k, v in OFFSETS.items()},
        },
        "calibration": {
            "puzzle_count": len(cal_rows),
            "puzzles": cal_puzzles,
            "hi_winner_counts": cal_hi,
            "lo_winner_counts": cal_lo,
            "mid_winner_counts": cal_mid,
            "per_puzzle": cal_rows,
        },
        "holdout": {
            "puzzle_count": len(hold_rows),
            "puzzles": hold_puzzles,
            "hi_winner_counts": hold_hi,
            "lo_winner_counts": hold_lo,
            "mid_winner_counts": hold_mid,
            "per_puzzle": hold_rows,
        },
        "verdict": {
            "h7_best_hi_calibration": cal_hi["h7"] == max(cal_hi.values()),
            "h7_best_hi_holdout": h7_survives,
            "h7_unique_best_holdout": h7_unique_best_holdout,
            "h7_advantage_survives_oos": h7_survives,
            "calibration_h7_rate": round(cal_hi["h7"] / len(cal_rows), 3) if cal_rows else 0,
            "holdout_h7_rate": round(hold_hi["h7"] / len(hold_rows), 3) if hold_rows else 0,
        },
        "notes": [
            "Public x transforms only; d band-limited, k not used.",
            "Winner = smallest circular distance to anchor for that offset modulus.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Holdout validation complete.")
    print(f"  calibration hi winners: {cal_hi}")
    print(f"  holdout hi winners:     {hold_hi}")
    print(f"  h7 survives OOS: {report['verdict']['h7_advantage_survives_oos']}")
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
