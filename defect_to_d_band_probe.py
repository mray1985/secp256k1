#!/usr/bin/env python3
"""Bring field/order defect (gap = p-N) into puzzle d-band range.

For puzzle n, d lives in [lo, hi] with lo=2^(n-1), hi=2^n-1, width=2^(n-1).

Reduction maps (defect folded to d-scale):
  mod_n       = gap mod 2^n
  mod_width   = gap mod 2^(n-1)
  band_lo     = lo + (gap mod 2^(n-1))          in [lo, hi]
  band_hi     = hi - (gap mod 2^(n-1))          in [lo, hi]
  top_bits    = gap >> (gap.bit_length() - n)    n-bit top slice
  mid_band    = (lo + hi) // 2 + (gap mod 2^(n-2)) - 2^(n-2)  centered fold

Tests each reduced value as public-x offset vs hi-anchor; on solved puzzles
also reports distance to true d.
"""

from __future__ import annotations

import json
from pathlib import Path

from hashkeys_rsz import N, PUZZLE_RSZ, p, y_roots_from_x
from puzzle_keys_53125 import parse_53125

GAP = p - N
H7 = GAP + 7
OUT = Path(__file__).with_name("defect_to_d_band_probe_report.json")


def anchor_score(x: int, anchor: int, modulus: int) -> int:
    m = abs(modulus)
    if m == 0:
        return 1
    return min((x - anchor) % m, (anchor - x) % m)


def hi_score(px: int, n: int, offset: int) -> int:
    hi = (1 << n) - 1
    return anchor_score((px + offset) % p, hi, offset)


def band(n: int) -> tuple[int, int, int]:
    lo = 1 << (n - 1)
    hi = (1 << n) - 1
    width = 1 << (n - 1)
    return lo, hi, width


def reduce_defect(n: int) -> dict[str, int]:
    lo, hi, width = band(n)
    mod_w = GAP % width
    bl = GAP.bit_length()
    shift = max(0, bl - n)
    top = GAP >> shift
    if top >= (1 << n):
        top %= 1 << n
    n2 = max(1, n - 2)
    half = 1 << (n - 2)
    mid = (lo + hi) // 2 + (GAP % half) - half

    return {
        "mod_n": GAP % (1 << n),
        "mod_width": mod_w,
        "band_lo": lo + mod_w,
        "band_hi": hi - mod_w,
        "top_bits": top,
        "mid_band": max(lo, min(hi, mid)),
        "gap_mod_N_band": (GAP % N) % width + lo if width else lo,
    }


def main() -> None:
    keys = parse_53125()
    puzzles = sorted(n for n in set(keys) | set(PUZZLE_RSZ) if n >= 65)

    map_names = ["mod_n", "mod_width", "band_lo", "band_hi", "top_bits", "mid_band", "gap_mod_N_band"]
    agg = {m: {"beats_gap": 0, "beats_h7": 0, "best_at_hi": 0, "in_band": 0} for m in map_names}
    agg["gap"] = {"beats_gap": 0, "beats_h7": 0, "best_at_hi": 0}
    agg["h7"] = {"beats_gap": 0, "beats_h7": 0, "best_at_hi": 0}
    d_dist = {m: [] for m in map_names}

    rows = []
    for n in puzzles:
        if n in keys and keys[n].px:
            px = keys[n].px
            solved = keys[n].d > 0
            d_true = keys[n].d if solved else None
        elif n in PUZZLE_RSZ:
            pub = PUZZLE_RSZ[n].pub_compressed
            px = int(pub[2:], 16)
            solved = False
            d_true = None
        else:
            continue

        lo, hi, width = band(n)
        reduced = reduce_defect(n)
        gap_s = hi_score(px, n, GAP)
        h7_s = hi_score(px, n, H7)

        variants = {}
        for name, rval in reduced.items():
            in_band = lo <= rval <= hi
            score = hi_score(px, n, rval)
            entry = {
                "value": rval,
                "in_band": in_band,
                "hi_score": score,
                "beats_gap": score < gap_s,
                "beats_h7": score < h7_s,
            }
            if solved and d_true is not None:
                entry["dist_to_d"] = abs(rval - d_true)
                entry["dist_to_d_mod_width"] = min((rval - d_true) % width, (d_true - rval) % width)
                d_dist[name].append(entry["dist_to_d_mod_width"])
            variants[name] = entry

            if in_band:
                agg[name]["in_band"] += 1
            if entry["beats_gap"]:
                agg[name]["beats_gap"] += 1
            if entry["beats_h7"]:
                agg[name]["beats_h7"] += 1

        all_scores = {"gap": gap_s, "h7": h7_s, **{m: variants[m]["hi_score"] for m in map_names}}
        best = min(all_scores, key=all_scores.get)
        for m in map_names:
            if best == m:
                agg[m]["best_at_hi"] += 1
        if best == "gap":
            agg["gap"]["best_at_hi"] += 1
        if best == "h7":
            agg["h7"]["best_at_hi"] += 1

        rows.append(
            {
                "puzzle": n,
                "lo": lo,
                "hi": hi,
                "width": width,
                "solved": solved,
                "d": d_true,
                "reduced": reduced,
                "variants": variants,
                "best_at_hi": best,
                "reference": {"gap": gap_s, "h7": h7_s},
            }
        )

    total = len(rows)
    solved_n = sum(1 for r in rows if r["solved"])

    summary = []
    for name in map_names:
        a = agg[name]
        summary.append(
            {
                "map": name,
                "in_band_rate": round(a["in_band"] / total, 3),
                "beats_gap": a["beats_gap"],
                "beats_h7": a["beats_h7"],
                "best_at_hi": a["best_at_hi"],
                "beats_gap_rate": round(a["beats_gap"] / total, 3),
                "beats_h7_rate": round(a["beats_h7"] / total, 3),
                "best_at_hi_rate": round(a["best_at_hi"] / total, 3),
                "mean_dist_to_d_mod_width": round(sum(d_dist[name]) / len(d_dist[name]), 2)
                if d_dist[name]
                else None,
            }
        )
    summary = sorted(summary, key=lambda x: x["best_at_hi"], reverse=True)

    report = {
        "question": "If gap is folded into puzzle d-band range, does hi-anchor scoring improve?",
        "facts": {"gap": GAP, "gap_bits": GAP.bit_length(), "puzzle_count": total, "solved_count": solved_n},
        "reduction_maps": {
            "mod_n": "gap mod 2^n",
            "mod_width": "gap mod 2^(n-1)",
            "band_lo": "lo + (gap mod 2^(n-1))",
            "band_hi": "hi - (gap mod 2^(n-1))",
            "top_bits": "gap >> (bitlen(gap)-n)",
            "mid_band": "mid + (gap mod 2^(n-2)) - 2^(n-2)",
            "gap_mod_N_band": "lo + ((gap mod N) mod 2^(n-1))",
        },
        "reference": {
            "gap_best_at_hi": agg["gap"]["best_at_hi"],
            "h7_best_at_hi": agg["h7"]["best_at_hi"],
        },
        "summary": summary,
        "rows": rows,
        "notes": [
            "Reduced values used directly as offsets on public x.",
            "in_band means value lies in [2^(n-1), 2^n-1].",
            "dist_to_d_mod_width on solved puzzles only.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("defect-to-d-band probe complete.")
    print(f"  puzzles: {total} (solved {solved_n})")
    print(f"  reference: gap best_hi={agg['gap']['best_at_hi']} h7 best_hi={agg['h7']['best_at_hi']}")
    print("  top maps by best_at_hi:")
    for s in summary[:5]:
        print(
            f"    {s['map']}: best_hi={s['best_at_hi']}/{total} "
            f"in_band={s['in_band_rate']} beats_h7={s['beats_h7']}/{total}"
        )
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
