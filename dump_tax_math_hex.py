#!/usr/bin/env python3
"""Dump all tax_math_falsify trial k and d as full hex."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    P115_R_TRUE_X,
    P115_R_TRUE_Y,
    P135_R_TRUE_X,
    P135_R_TRUE_Y,
    puzzle_band,
)
from hashkeys_rsz import PUZZLE_RSZ, resolve_r_true_from_rsz  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402
from tax_math_falsify import H2_FRAC, H_FRAC, PIVOT_I99, hunt_puzzle, k_from_d  # noqa: E402

# hunt_puzzle stores pivot-arrested scalar in Trial.k and d_from_k() in Trial.d.
# Tax Math convention: arrested scalar is d (n-bit band); k = k_from_d(r,s,z,d).
# Raw pivot is ~lk bits (often n+8); fold into puzzle band before output.


def fold_d_to_band(val: int, n: int) -> int:
    """Right-shift geometric arrest into [2^(n-1), 2^n)."""
    lo, hi, top = puzzle_band(n)
    if lo <= val < hi:
        return val
    while val.bit_length() > n:
        val >>= 1
    if val < lo:
        val = lo + (val % lo)
    if val >= hi:
        val = top
    return val

OUT = ROOT / "ARCHIVE" / "tax_math_trials_full_hex.txt"


def r_true(n: int) -> tuple[int, int] | None:
    if n == 115:
        return P115_R_TRUE_X, P115_R_TRUE_Y
    if n == 135:
        return P135_R_TRUE_X, P135_R_TRUE_Y
    pt = resolve_r_true_from_rsz(n)
    return (pt[0], pt[1]) if pt else None


def main() -> None:
    keys = parse_53125()
    lines = [
        "TAX MATH TRIALS — FULL HEX (no EC gate)",
        f"I99 pivot = {PIVOT_I99}",
        f"{{H}} = {H_FRAC:.6f}  {{H/2}} = {H2_FRAC:.6f}",
        "",
    ]
    total_trials = 0

    for n in sorted(PUZZLE_RSZ):
        d_known = keys[n].d if n in keys and keys[n].d > 0 else None
        rt = r_true(n)
        if rt is None:
            lines.append(f"=== P{n} SKIP (no R_true) ===")
            lines.append("")
            continue
        rx, ry = rt
        trials, _ = hunt_puzzle(n, d_known, rx, ry)
        total_trials += len(trials)
        lines.append(f"=== P{n}  known_d={d_known is not None}  trials={len(trials)} ===")
        rsz = PUZZLE_RSZ[n]
        if d_known:
            kt = k_from_d(rsz.r, rsz.s, rsz.z, d_known)
            lines.append(f"  d_known = {hex(d_known)}")
            lines.append(f"  k_true  = {hex(kt)}")
        for t in trials:
            d_arrested = fold_d_to_band(t.k, n)
            k_nonce = k_from_d(rsz.r, rsz.s, rsz.z, d_arrested)
            lines.append(f"  [{t.stage}]")
            lines.append(f"    d = {hex(d_arrested)}")
            lines.append(f"    k = {hex(k_nonce)}")
        lines.append("")

    lines.append(f"TOTAL TRIALS: {total_trials}")
    text = "\n".join(lines) + "\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(text[:15000])
    if len(text) > 15000:
        print(f"\n... truncated screen output ({len(text)} chars total)")
    print(f"\nFULL FILE: {OUT}")
    print(f"TOTAL TRIALS: {total_trials}")


if __name__ == "__main__":
    main()
