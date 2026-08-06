#!/usr/bin/env python3
"""Transform-family twist map for every puzzle in PUZZLE_RSZ."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from hashkeys_rsz import N, PUZZLE_RSZ, p, y_roots_from_x
from puzzle_keys_53125 import parse_53125

GAP = p - N
HINGE = GAP + 1
PLUS7 = GAP + 7
MINUS7 = GAP - 7
OUT = Path(__file__).with_name("all_puzzles_transform_family_map_report.json")

BASE_FAMILIES = ("gap", "hinge", "gap+7", "gap-7", "rsz", "py", "moduli", "literal")


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


def pubkey_xy(n: int, keys: dict) -> tuple[int, int]:
    if n in keys and keys[n].px:
        return keys[n].px, keys[n].py
    pub = PUZZLE_RSZ[n].pub_compressed
    px = int(pub[2:], 16)
    yp, yn = y_roots_from_x(px)
    py = yp if pub.startswith("02") else yn
    return px, py


def family_defs(n: int) -> dict[str, tuple[str, ...]]:
    lo = 1 << (n - 1)
    hi = 1 << n
    return {
        "gap": ("x+gap", "x-gap"),
        "hinge": ("x+hinge", "x-hinge"),
        "gap+7": ("x+gap+7", "x-gap-7"),
        "gap-7": ("x+gap-7", "x-gap+7"),
        "2^(n-1)": (f"x+2^{n - 1}", f"x-2^{n - 1}", "x+gap+2^(n-1)", "x+hinge+2^(n-1)"),
        "2^n": (f"x+2^{n}", f"x-2^{n}", "x+gap+2^n", "x+hinge+2^n"),
        "rsz": ("x+R", "x-R", "x+S", "x-S", "x+Z", "x-Z"),
        "py": ("x+Py", "x-Py"),
        "moduli": ("x+N", "x-N", "x+p", "x-p"),
        "index": (f"x+{n}", f"x-{n}"),
        "literal": ("x",),
    }


def build_transforms(n: int, px: int, py: int, rsz) -> dict[str, int]:
    lo = 1 << (n - 1)
    hi = 1 << n
    t = {
        "x": px,
        "x+gap": px + GAP,
        "x-gap": px - GAP,
        "x+hinge": px + HINGE,
        "x-hinge": px - HINGE,
        "x+gap+7": px + PLUS7,
        "x-gap-7": px - PLUS7,
        "x+gap-7": px + MINUS7,
        "x-gap+7": px - MINUS7,
        "x+N": px + N,
        "x-N": px - N,
        "x+p": px + p,
        "x-p": px - p,
        f"x+{n}": px + n,
        f"x-{n}": px - n,
        f"x+2^{n - 1}": px + lo,
        f"x-2^{n - 1}": px - lo,
        f"x+2^{n}": px + hi,
        f"x-2^{n}": px - hi,
        "x+gap+2^(n-1)": px + GAP + lo,
        "x+hinge+2^(n-1)": px + HINGE + lo,
        "x+gap+2^n": px + GAP + hi,
        "x+hinge+2^n": px + HINGE + hi,
        "x+Py": px + py,
        "x-Py": px - py,
        "x+R": px + rsz.r,
        "x-R": px - rsz.r,
        "x+S": px + rsz.s,
        "x-S": px - rsz.s,
        "x+Z": px + rsz.z,
        "x-Z": px - rsz.z,
    }
    return t


def summarize_family(names: tuple[str, ...], rows: dict[str, str]) -> dict:
    sides = [rows[n] for n in names if n in rows]
    main = sides.count("main")
    twist = sides.count("twist")
    return {
        "transforms": list(names),
        "main": main,
        "twist": twist,
        "twist_rate": round(twist / len(sides), 3) if sides else 0,
        "dominant": "twist" if twist > main else ("main" if main > twist else "mixed"),
        "details": {n: rows[n] for n in names if n in rows},
    }


def main() -> None:
    keys = parse_53125()
    puzzles = sorted(PUZZLE_RSZ)
    per_puzzle = {}
    agg: dict[str, dict[str, int]] = defaultdict(lambda: {"main": 0, "twist": 0, "singular": 0, "count": 0})

    for n in puzzles:
        rsz = PUZZLE_RSZ[n]
        px, py = pubkey_xy(n, keys)
        transforms = build_transforms(n, px, py, rsz)
        rows = {name: classify_x(val) for name, val in transforms.items()}
        families = family_defs(n)
        family_summary = {fam: summarize_family(names, rows) for fam, names in families.items()}
        ranked = sorted(family_summary.items(), key=lambda kv: kv[1]["twist_rate"], reverse=True)
        per_puzzle[str(n)] = {
            "puzzle": n,
            "solved": n in keys and keys[n].d > 0,
            "literal_side": rows["x"],
            "family_summary": dict(ranked),
            "top_twist_family": ranked[0][0] if ranked else None,
            "top_twist_rate": ranked[0][1]["twist_rate"] if ranked else 0,
        }
        for fam, summary in family_summary.items():
            for side in summary["details"].values():
                agg[fam][side] = agg[fam].get(side, 0) + 1
                agg[fam]["count"] += 1

    aggregate = {}
    for fam, counts in agg.items():
        main = counts.get("main", 0)
        twist = counts.get("twist", 0)
        total = counts["count"]
        aggregate[fam] = {
            "main": main,
            "twist": twist,
            "singular": counts.get("singular", 0),
            "transform_instances": total,
            "twist_rate": round(twist / total, 3) if total else 0,
            "dominant": "twist" if twist > main else ("main" if main > twist else "mixed"),
        }

    ranked_agg = sorted(aggregate.items(), key=lambda kv: kv[1]["twist_rate"], reverse=True)

    report = {
        "question": "Which public transform families flip to twist most reliably across all RSZ puzzles?",
        "facts": {
            "puzzle_count": len(puzzles),
            "puzzles": puzzles,
            "gap": GAP,
            "hinge": HINGE,
            "gap_plus_7": PLUS7,
            "gap_minus_7": MINUS7,
        },
        "aggregate_family_summary": dict(ranked_agg),
        "ranked_by_twist_rate": [{"family": f, **s} for f, s in ranked_agg],
        "per_puzzle": per_puzzle,
        "notes": [
            "Per puzzle: 2^(n-1) and 2^n families use puzzle-specific band powers.",
            "gap+7 / gap-7 are p-N+7 and p-N-7 boundary offsets.",
            "d band-limited; k not used.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("All-puzzles transform family map complete.")
    print(f"  puzzles: {len(puzzles)}")
    for fam, s in ranked_agg[:6]:
        print(f"  {fam}: twist_rate={s['twist_rate']} ({s['twist']}/{s['transform_instances']})")
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
