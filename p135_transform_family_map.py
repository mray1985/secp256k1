#!/usr/bin/env python3
"""P135 transform-family classification for twist sensitivity."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from hashkeys_rsz import N, PUZZLE_RSZ, p, y_roots_from_x

GAP = p - N
HINGE = GAP + 1
OUT = Path(__file__).with_name("p135_transform_family_map_report.json")

FAMILIES = {
    "gap": ("x+gap", "x-gap"),
    "hinge": ("x+hinge", "x-hinge"),
    "2^134": ("x+2^134", "x-(2^134)", "x+gap+2^134", "x+hinge+2^134"),
    "2^135": ("x+2^135", "x-(2^135)", "x+gap+2^135", "x+hinge+2^135"),
    "rsz": ("x+R", "x-R", "x+S", "x-S", "x+Z", "x-Z"),
    "py": ("x+Py", "x-Py"),
    "moduli": ("x+N", "x-N", "x+p", "x-p"),
    "index": ("x+135", "x-135"),
    "literal": ("x",),
}


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


def main() -> None:
    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots_from_x(px)
    py = yp if rsz.pub_compressed.startswith("02") else yn

    transforms = {
        "x": px,
        "x+gap": px + GAP,
        "x-gap": px - GAP,
        "x+hinge": px + HINGE,
        "x-hinge": px - HINGE,
        "x+N": px + N,
        "x-N": px - N,
        "x+p": px + p,
        "x-p": px - p,
        "x+135": px + 135,
        "x-135": px - 135,
        "x+2^134": px + (1 << 134),
        "x-(2^134)": px - (1 << 134),
        "x+2^135": px + (1 << 135),
        "x-(2^135)": px - (1 << 135),
        "x+gap+2^134": px + GAP + (1 << 134),
        "x+hinge+2^134": px + HINGE + (1 << 134),
        "x+gap+2^135": px + GAP + (1 << 135),
        "x+hinge+2^135": px + HINGE + (1 << 135),
        "x+Py": px + py,
        "x-Py": px - py,
        "x+R": px + rsz.r,
        "x-R": px - rsz.r,
        "x+S": px + rsz.s,
        "x-S": px - rsz.s,
        "x+Z": px + rsz.z,
        "x-Z": px - rsz.z,
    }

    rows = {name: {"side": classify_x(val), "x_mod_p": val % p} for name, val in transforms.items()}

    family_summary = {}
    for fam, names in FAMILIES.items():
        sides = [rows[n]["side"] for n in names if n in rows]
        main = sides.count("main")
        twist = sides.count("twist")
        family_summary[fam] = {
            "transforms": list(names),
            "main": main,
            "twist": twist,
            "twist_rate": round(twist / len(sides), 3) if sides else 0,
            "dominant": "twist" if twist > main else ("main" if main > twist else "mixed"),
            "details": {n: rows[n]["side"] for n in names if n in rows},
        }

    ranked = sorted(family_summary.items(), key=lambda kv: kv[1]["twist_rate"], reverse=True)

    report = {
        "question": "Which P135 public transform families flip to twist most reliably?",
        "facts": {"puzzle": 135, "px": px, "gap": GAP, "hinge": HINGE},
        "family_summary": dict(ranked),
        "ranked_by_twist_rate": [{"family": f, **s} for f, s in ranked],
        "notes": [
            "Families with highest twist_rate are the most boundary-sensitive.",
            "gap/hinge/2^n families are structural; RSZ/Py are signature/pubkey-linked.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("P135 transform family map complete.")
    for f, s in ranked[:5]:
        print(f"  {f}: twist_rate={s['twist_rate']} ({s['twist']}/{s['main']+s['twist']})")
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
