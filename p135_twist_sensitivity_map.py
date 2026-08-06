#!/usr/bin/env python3
"""P135-only public transform map for main-curve/twist sensitivity."""

from __future__ import annotations

import json
from pathlib import Path

from hashkeys_rsz import N, PUZZLE_RSZ, p, y_roots_from_x

GAP = p - N
HINGE = GAP + 1
OUT = Path(__file__).with_name("p135_twist_sensitivity_map_report.json")


def legendre_symbol(a: int) -> int:
    a %= p
    if a == 0:
        return 0
    v = pow(a, (p - 1) // 2, p)
    return -1 if v == p - 1 else v


def classify_x(x: int) -> dict[str, object]:
    y_sq = (pow(x, 3, p) + 7) % p
    chi = legendre_symbol(y_sq)
    side = {1: "main", -1: "twist", 0: "singular"}[chi]
    return {"x_mod_p": x % p, "y_sq": y_sq, "legendre": chi, "side": side}


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

    rows = {name: classify_x(val) for name, val in transforms.items()}
    side_counts = {"main": 0, "twist": 0, "singular": 0}
    for row in rows.values():
        side_counts[row["side"]] += 1

    report = {
        "question": "How twist-sensitive is P135 under public x-transforms?",
        "facts": {
            "puzzle": 135,
            "pub_compressed": rsz.pub_compressed,
            "px": px,
            "py": py,
            "gap": GAP,
            "hinge": HINGE,
        },
        "side_counts": side_counts,
        "transforms": rows,
        "notes": [
            "Literal P135 x is main-curve as expected.",
            "The goal is to map which public transforms flip P135 onto the twist side.",
            "This is a structure map only, not a key-recovery method.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("P135 twist sensitivity map complete.")
    print(f"Main/twist counts: {side_counts}")
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
