#!/usr/bin/env python3
"""Folded defect + ceiling offset at puzzle scale.

Combines band folding with +7:
  fold_mod_n      = gap mod 2^n
  fold_mod_n+7    = (gap mod 2^n) + 7
  fold_band_hi    = hi - (gap mod 2^(n-1))     in [lo, hi]
  fold_band_hi+7  = band_hi + 7

Compared against gap, h7 (gap+7), gap+21 on hi-anchor (24 puzzles).
"""

from __future__ import annotations

import json
from pathlib import Path

from hashkeys_rsz import N, PUZZLE_RSZ, p, y_roots_from_x
from puzzle_keys_53125 import parse_53125

GAP = p - N
OUT = Path(__file__).with_name("defect_fold_plus7_probe_report.json")


def anchor_score(x: int, anchor: int, modulus: int) -> int:
    m = abs(modulus)
    if m == 0:
        return 1
    return min((x - anchor) % m, (anchor - x) % m)


def hi_score(px: int, n: int, offset: int) -> int:
    hi = (1 << n) - 1
    return anchor_score((px + offset) % p, hi, offset)


def fold_values(n: int) -> dict[str, int]:
    lo = 1 << (n - 1)
    hi = (1 << n) - 1
    width = 1 << (n - 1)
    mod_w = GAP % width
    mod_n = GAP % (1 << n)
    band_hi = hi - mod_w
    band_lo = lo + mod_w
    return {
        "fold_mod_n": mod_n,
        "fold_mod_n+7": mod_n + 7,
        "fold_mod_n+21": mod_n + 21,
        "fold_band_hi": band_hi,
        "fold_band_hi+7": band_hi + 7,
        "fold_band_lo": band_lo,
        "fold_band_lo+7": band_lo + 7,
    }


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

    baseline = {
        "gap": GAP,
        "h7": GAP + 7,
        "gap+21": GAP + 21,
    }
    fold_names = [
        "fold_mod_n",
        "fold_mod_n+7",
        "fold_mod_n+21",
        "fold_band_hi",
        "fold_band_hi+7",
        "fold_band_lo",
        "fold_band_lo+7",
    ]

    agg = {name: {"beats_gap": 0, "beats_h7": 0, "best_at_hi": 0, "in_band": 0} for name in fold_names}
    for b in baseline:
        agg[b] = {"beats_gap": 0, "beats_h7": 0, "best_at_hi": 0}

    rows = []

    for n in puzzles:
        px, _ = pubkey_xy(n, keys)  # type: ignore[misc]
        lo = 1 << (n - 1)
        hi = (1 << n) - 1
        folded = fold_values(n)

        scores = {name: hi_score(px, n, off) for name, off in baseline.items()}
        for name in fold_names:
            scores[name] = hi_score(px, n, folded[name])

        best = min(scores, key=scores.get)

        variant_meta = {}
        for name in fold_names:
            val = folded[name]
            in_band = lo <= val <= hi
            variant_meta[name] = {
                "offset": val,
                "hi_score": scores[name],
                "in_band": in_band,
                "beats_gap": scores[name] < scores["gap"],
                "beats_h7": scores[name] < scores["h7"],
                "best_at_hi": best == name,
            }
            if in_band:
                agg[name]["in_band"] += 1
            if scores[name] < scores["gap"]:
                agg[name]["beats_gap"] += 1
            if scores[name] < scores["h7"]:
                agg[name]["beats_h7"] += 1
            if best == name:
                agg[name]["best_at_hi"] += 1

        for name in baseline:
            if best == name:
                agg[name]["best_at_hi"] += 1
            if scores[name] < scores["gap"]:
                agg[name]["beats_gap"] += 1
            if name != "h7" and scores[name] < scores["h7"]:
                agg[name]["beats_h7"] += 1

        rows.append(
            {
                "puzzle": n,
                "solved": n in keys and keys[n].d > 0,
                "lo": lo,
                "hi": hi,
                "folded": folded,
                "scores": scores,
                "best_at_hi": best,
                "variants": variant_meta,
            }
        )

    total = len(rows)

    def summarize(names: list[str]) -> list[dict]:
        out = []
        for name in names:
            a = agg[name]
            out.append(
                {
                    "offset": name,
                    "best_at_hi": a["best_at_hi"],
                    "beats_h7": a["beats_h7"],
                    "beats_gap": a["beats_gap"],
                    "in_band_rate": round(a.get("in_band", 0) / total, 3) if "in_band" in a else None,
                    "best_at_hi_rate": round(a["best_at_hi"] / total, 3),
                    "beats_h7_rate": round(a["beats_h7"] / total, 3),
                }
            )
        return sorted(out, key=lambda r: r["best_at_hi"], reverse=True)

    all_names = list(baseline) + fold_names
    ranked = summarize(all_names)

    report = {
        "question": "Does folded defect +7 beat full gap+7 at puzzle-scale hi-anchor?",
        "facts": {
            "gap": GAP,
            "puzzle_count": total,
            "formulas": {
                "fold_mod_n": "gap mod 2^n",
                "fold_mod_n+7": "(gap mod 2^n) + 7",
                "fold_band_hi": "hi - (gap mod 2^(n-1))",
                "fold_band_hi+7": "band_hi + 7",
            },
        },
        "ranked_by_best_at_hi": ranked,
        "reference": {
            "h7_best": agg["h7"]["best_at_hi"],
            "fold_mod_n+7_best": agg["fold_mod_n+7"]["best_at_hi"],
            "fold_band_hi+7_best": agg["fold_band_hi+7"]["best_at_hi"],
        },
        "rows": rows,
        "notes": [
            "Folded offsets used directly as public-x shift and score modulus.",
            "in_band: offset value in [2^(n-1), 2^n-1].",
            "h7 = full gap+7; fold_mod_n+7 = puzzle-scaled defect + curve constant.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("defect fold +7 probe complete.")
    print(f"  puzzles: {total}")
    print("  ranked best_at_hi:")
    for r in ranked[:8]:
        ib = f" in_band={r['in_band_rate']}" if r["in_band_rate"] is not None else ""
        print(f"    {r['offset']}: {r['best_at_hi']}/{total}{ib} beats_h7={r['beats_h7']}/{total}")
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
