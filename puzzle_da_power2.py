#!/usr/bin/env python3
"""
Same D/A sequences as P1-P70 (corrected), but weights are 2^k only:
  A(k) = 1 * 2^k
  D(k) = 2 * 2^k = 2^(k+1)

Head anchor k = n-3 unchanged (indices in chain).
Compare sum to 2^n, (2^n - 1), and real d_n.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_da_sequence import (
    USER_DA,
    PUZZLE,
    Tok,
    parse_da,
    format_da,
    build_chain,
)

N_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def chains_p1_70() -> dict[int, str]:
    chains = {n: USER_DA[n] for n in range(1, 21)}
    prev = parse_da(chains[20])[-1].op
    for n in range(21, 71):
        toks = build_chain(n, prev)
        chains[n] = format_da(toks)
        prev = toks[-1].op
    return chains


def eval_power2(tokens: list[Tok]) -> int:
    return sum((2 ** (t.k + 1) if t.op == "D" else 2**t.k) for t in tokens)


def ladder(chain: str) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for t in parse_da(chain):
        if t.k not in seen:
            seen.add(t.k)
            out.append(t.k)
    return out


def gaps(lst: list[int]) -> list[int]:
    return [lst[i] - lst[i + 1] for i in range(len(lst) - 1)]


def main() -> None:
    chains = chains_p1_70()
    lines = [
        "D/A SAME SEQUENCE — weights 2^k only (double-and-add blocks)",
        "  A(k) = 2^k",
        "  D(k) = 2 * 2^k = 2^(k+1)",
        "  Chain tokens identical to corrected P1-P70; head k = n-3",
        "",
        "P    anchor  sum(2^k blocks)   2^n           2^n-sum      (2^n-1)-sum   d_n",
        "---  ------  ---------------   ---           -------      -----------   ---",
    ]

    rows = []
    for n in range(1, 71):
        ch = chains[n]
        toks = parse_da(ch)
        s = eval_power2(toks)
        hi = 2**n
        top = 2**n - 1
        anchor = n - 3 if n >= 4 else "-"
        d = PUZZLE[n]
        rows.append((n, s, hi, hi - s, top - s, d, anchor, ch))

        lines.append(
            f"P{n:02d}  {str(anchor):>6}  {s:<17} {hi:<13} {hi-s:<12} {top-s:<13} {d}"
        )

    lines += [
        "",
        "=== STRUCTURE CHECKS ===",
    ]
    exact_2n = sum(1 for r in rows if r[1] == r[2])
    exact_top = sum(1 for r in rows if r[1] == r[2] - 1)
    lines.append(f"  sum == 2^n exactly:     {exact_2n}/70")
    lines.append(f"  sum == 2^n - 1 exactly: {exact_top}/70")
    lines.append(f"  sum == d_n exactly:     {sum(1 for r in rows if r[1]==r[5])}/70")

    lines += ["", "=== sum / 2^n (by puzzle) ==="]
    for n in [4, 10, 20, 30, 40, 50, 60, 70]:
        r = rows[n - 1]
        lines.append(f"  P{n:02d}  sum/2^n = {r[1]/r[2]:.6f}  sum/2^(n-3) = {r[1]/2**(n-3):.2f}")

    lines += [
        "",
        "=== P70 full (same sequence, 2^k weights) ===",
        f"  chain: {rows[69][7]}",
        f"  ladder: {ladder(rows[69][7])}",
        f"  gaps: {gaps(ladder(rows[69][7]))}",
        f"  sum = {rows[69][1]}",
        f"  2^70 = {rows[69][2]}",
        f"  result (2^70 - sum) = {rows[69][3]}",
        f"  complement N - result = {N_ORDER - rows[69][3]}",
        "",
        "=== P71 preview (+1 index shift on P70 sequence) ===",
    ]

    p70_toks = parse_da(rows[69][7])
    p71_toks = [Tok(t.op, t.k + 1) for t in p70_toks]
    p71_ch = format_da(p71_toks)
    p71_sum = eval_power2(p71_toks)
    lines += [
        f"  chain: {p71_ch}",
        f"  ladder: {ladder(p71_ch)}",
        f"  gaps: {gaps(ladder(p71_ch))}",
        f"  sum = {p71_sum}",
        f"  2^71 = {2**71}",
        f"  2^71 - sum = {2**71 - p71_sum}",
    ]

    out = ROOT / "ARCHIVE" / "puzzle_da_power2_P1_P70.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
