#!/usr/bin/env python3
"""Probe main-curve/twist-boundary structure on puzzle public data.

Questions:
1. Do published puzzle pubkey x-coordinates land on the main curve side?
2. Do simple public transforms of x cross onto the twist side?
3. Do solved d/k/r/Px residues show obvious bias modulo the twist-cofactor factors?
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from hashkeys_rsz import N, PUZZLE_RSZ, p
from puzzle_keys_53125 import parse_53125

TWIST_FACTORS = (3, 9, 13, 169, 3319, 22639)
OUT = Path(__file__).with_name("twist_boundary_probe_report.json")


@dataclass(frozen=True)
class SymbolRow:
    puzzle: int
    expr: str
    value_mod_p: int
    legendre: int
    side: str


def legendre_symbol(a: int) -> int:
    a %= p
    if a == 0:
        return 0
    v = pow(a, (p - 1) // 2, p)
    if v == p - 1:
        return -1
    return v


def classify_x(x: int) -> tuple[int, int, str]:
    y_sq = (pow(x, 3, p) + 7) % p
    chi = legendre_symbol(y_sq)
    side = {1: "main", -1: "twist", 0: "singular"}[chi]
    return y_sq, chi, side


def solve_k(d: int, n: int) -> int | None:
    rsz = PUZZLE_RSZ.get(n)
    if rsz is None:
        return None
    return rsz.k or rsz.recover_k_from_d(d)


def residue_table(values: dict[int, int], modulus: int) -> dict[str, object]:
    residues = {n: v % modulus for n, v in values.items()}
    counts = Counter(residues.values())
    top = counts.most_common(min(10, len(counts)))
    return {
        "modulus": modulus,
        "distinct_residues": len(counts),
        "top_counts": top,
        "all_same": len(counts) == 1,
        "zero_count": counts.get(0, 0),
    }


def main() -> None:
    keys = parse_53125()
    solved = {n: pk for n, pk in sorted(keys.items()) if 65 <= n <= 130 and pk.d > 0 and n in PUZZLE_RSZ}

    symbol_rows: list[SymbolRow] = []
    summary_counts = Counter()
    transform_defs = [
        ("x", lambda x, n: x),
        ("x+gap", lambda x, n: x + (p - N)),
        ("x+hinge", lambda x, n: x + (p - N + 1)),
        ("x-gap", lambda x, n: x - (p - N)),
        ("x-hinge", lambda x, n: x - (p - N + 1)),
        ("x+n", lambda x, n: x + n),
        ("x-n", lambda x, n: x - n),
    ]
    for puzzle_num, pk in solved.items():
        for label, fn in transform_defs:
            x = fn(pk.px, puzzle_num) % p
            y_sq, chi, side = classify_x(x)
            summary_counts[f"{label}:{side}"] += 1
            symbol_rows.append(SymbolRow(puzzle_num, label, y_sq, chi, side))

    d_vals = {n: pk.d for n, pk in solved.items()}
    px_vals = {n: pk.px for n, pk in solved.items()}
    py_vals = {n: pk.py for n, pk in solved.items()}
    r_vals = {n: PUZZLE_RSZ[n].r for n in solved}
    s_vals = {n: PUZZLE_RSZ[n].s for n in solved}
    z_vals = {n: PUZZLE_RSZ[n].z for n in solved}
    k_vals = {n: solve_k(pk.d, n) for n, pk in solved.items()}
    k_vals = {n: v for n, v in k_vals.items() if v is not None}

    residue_report: dict[str, list[dict[str, object]]] = {}
    value_sets = {
        "d": d_vals,
        "k": k_vals,
        "r": r_vals,
        "s": s_vals,
        "z": z_vals,
        "px": px_vals,
        "py": py_vals,
    }
    for name, values in value_sets.items():
        residue_report[name] = [residue_table(values, mod) for mod in TWIST_FACTORS]

    report = {
        "question": "Do puzzles reveal recurring secp256k1 twist-boundary structure?",
        "facts": {
            "curve": "y^2 = x^3 + 7 mod p",
            "p": p,
            "N": N,
            "gap": p - N,
            "hinge": p - N + 1,
            "twist_factors": TWIST_FACTORS,
            "solved_puzzles_tested": list(solved),
        },
        "legendre_summary": dict(summary_counts),
        "legendre_rows": [asdict(r) for r in symbol_rows],
        "residue_report": residue_report,
        "notes": [
            "Published pubkeys should land on the main curve side for the literal x expression.",
            "Transforms using gap and hinge are public-only probes for boundary crossing.",
            "Residue tables are descriptive only; they are not blind key-recovery claims.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Twist boundary probe complete.")
    print(f"Solved puzzles tested: {len(solved)}")
    print(f"Literal x main-side count: {summary_counts['x:main']}")
    print(f"Literal x twist-side count: {summary_counts['x:twist']}")
    print(f"Hinge-shift twist-side count: {summary_counts['x+hinge:twist']}")
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
