#!/usr/bin/env python3
"""
Complement ladder test:
  HI = 2^n - 1
  C  = HI - d
  bit positions of C (MSB index n-1 .. 0)
  gaps vs D/A ladder gaps
  n -> n+1 shift by +1 hypothesis
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_da_sequence import PUZZLE, USER_DA, parse_da, build_chain, format_da
from puzzle_keys_53125 import parse_53125

P70_CHAIN = (
    "D(67)A(67)D(67)A(67)D(66)A(66)D(63)A(63)D(62)A(59)D(56)A(56)"
    "D(50)A(50)D(48)A(48)D(45)A(45)D(44)A(39)D(34)A(30)D(28)A(27)"
    "D(23)A(23)D(22)A(21)D(17)A(17)D(13)A(11)D(10)A(8)D(4)A(1)"
)
P71_SHIFT = (
    "D(68)A(68)D(68)A(68)D(67)A(67)D(64)A(64)D(63)A(60)D(57)A(57)"
    "D(51)A(51)D(49)A(49)D(46)A(46)D(45)A(40)D(35)A(31)D(29)A(28)"
    "D(24)A(24)D(23)A(22)D(18)A(18)D(14)A(12)D(11)A(9)D(5)A(2)"
)


def chains_p1_70() -> dict[int, str]:
    chains = {n: USER_DA[n] for n in range(1, 21)}
    prev = parse_da(chains[20])[-1].op
    for n in range(21, 71):
        chains[n] = format_da(build_chain(n, prev))
        prev = parse_da(chains[n])[-1].op
    return chains


def d_for(n: int, keys: dict) -> int | None:
    if n in PUZZLE:
        return PUZZLE[n]
    if n in keys:
        return keys[n].d
    return None


def da_ladder(chain: str) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for t in parse_da(chain):
        if t.k not in seen:
            seen.add(t.k)
            out.append(t.k)
    return out


def complement_bit_positions_msb(c: int, n: int) -> list[int]:
    """Set bit indices 0..n-1, MSB at n-1, descending list."""
    return [n - 1 - i for i in range(n) if (c >> (n - 1 - i)) & 1]


def gap_list(lst: list[int]) -> list[int]:
    return [lst[i] - lst[i + 1] for i in range(len(lst) - 1)]


def shift_match(a: list[int], b: list[int], delta: int = 1) -> bool:
    return len(a) == len(b) and b == [x + delta for x in a]


def gap_match(a: list[int], b: list[int]) -> bool:
    return a == b


def main() -> None:
    keys = parse_53125()
    chains = chains_p1_70()
    solved = sorted(n for n in range(1, 131) if d_for(n, keys))

    lines = [
        "COMPLEMENT LADDER TEST",
        "  HI = 2^n - 1",
        "  C  = HI - d",
        "  d XOR C = HI  (bit partition of n-bit height)",
        "",
        "=== P70: D/A ladder vs complement bit positions ===",
    ]

    n = 70
    d = PUZZLE[n]
    hi = 2**n - 1
    c = hi - d
    lad = da_ladder(chains[n])
    bpos = complement_bit_positions_msb(c, n)
    lg = gap_list(lad)
    bg = gap_list(bpos)

    lines += [
        f"  d bits={d.bit_length()}  C bits={c.bit_length()}  popcount(C)={c.bit_count()}",
        f"  D/A ladder ({len(lad)}): {lad}",
        f"  C bit pos  ({len(bpos)}): {bpos}",
        f"  D/A gaps:   {lg}",
        f"  C gaps:     {bg}",
        f"  identical lists? {lad == bpos}",
        f"  identical gaps?  {lg == bg}",
        "",
        "  Note: same HI partition, different order/count — D/A is depletion indices,",
        "  C bits are literal 0-bits of d in the n-bit window.",
        "",
        "=== P70 -> P71 +1 SHIFT (D/A hypothesis) ===",
    ]

    p71_lad = da_ladder(P71_SHIFT)
    lines += [
        f"  P70 ladder: {lad}",
        f"  P71 +1:     {p71_lad}",
        f"  ladder +1 match: {shift_match(lad, p71_lad)}",
        f"  P70 gaps:   {lg}",
        f"  P71 gaps:   {gap_list(p71_lad)}",
        f"  gaps match: {gap_match(lg, gap_list(p71_lad))}",
        "",
        "=== P70 -> P71 +1 SHIFT (complement bit positions) ===",
    ]

    # hypothetical P71 d from +1 shift eval - use shift hypothesis d if we can
    from puzzle_da_sequence import eval_tokens, Tok

    p71_toks = [Tok(t.op, t.k + 1) for t in parse_da(P70_CHAIN)]
    d71_hyp = eval_tokens(p71_toks)
    c71_hyp = (2**71 - 1) - d71_hyp
    b71 = complement_bit_positions_msb(c71_hyp, 71)
    lines += [
        f"  P70 C positions ({len(bpos)}): {bpos[:12]}...",
        f"  P71 C from +1-shift d ({len(b71)}): {b71[:12]}...",
        f"  C pos +1 match: {shift_match(bpos, b71)}",
        f"  P70 C gaps: {bg[:12]}...",
        f"  P71 C gaps: {gap_list(b71)[:12]}...",
        f"  C gap match: {gap_match(bg, gap_list(b71))}",
        "",
        "=== CONSECUTIVE SOLVED: D/A ladder n+1 == ladder(n)+1 ? ===",
    ]

    da_shift_hits = 0
    da_gap_hits = 0
    c_shift_hits = 0
    c_gap_hits = 0
    pairs = 0

    prev_n = None
    prev_lad = prev_bpos = prev_lg = prev_bg = None

    for n in solved:
        if n > 70:
            break
        dd = d_for(n, keys)
        if dd is None:
            continue
        hi = 2**n - 1
        c = hi - dd
        lad = da_ladder(chains[n]) if n <= 70 else []
        bpos = complement_bit_positions_msb(c, n)

        if prev_n is not None and n == prev_n + 1:
            pairs += 1
            if shift_match(prev_lad, lad):
                da_shift_hits += 1
            if gap_match(prev_lg, gap_list(lad)):
                da_gap_hits += 1
            if shift_match(prev_bpos, bpos):
                c_shift_hits += 1
            if gap_match(prev_bg, gap_list(bpos)):
                c_gap_hits += 1

        prev_n, prev_lad, prev_bpos = n, lad, bpos
        prev_lg, prev_bg = gap_list(lad), gap_list(bpos)

    lines += [
        f"  consecutive pairs P1-P70: {pairs}",
        f"  D/A ladder(n+1) == ladder(n)+1: {da_shift_hits}/{pairs}",
        f"  D/A gaps match:                {da_gap_hits}/{pairs}",
        f"  C bit pos(n+1) == pos(n)+1:    {c_shift_hits}/{pairs}",
        f"  C gaps match:                  {c_gap_hits}/{pairs}",
        "",
        "=== SAMPLE: complement bit ladders (every 5th + P69-P70) ===",
    ]

    for n in list(range(10, 21, 5)) + [65, 66, 67, 68, 69, 70]:
        dd = d_for(n, keys)
        if not dd:
            continue
        c = (2**n - 1) - dd
        bpos = complement_bit_positions_msb(c, n)
        lines.append(
            f"  P{n:02d} popcount(C)={c.bit_count():3d}  "
            f"positions[:8]={bpos[:8]}  gaps[:6]={gap_list(bpos)[:6]}"
        )

    lines += [
        "",
        "=== VERDICT ===",
        "  Exact always: d + C = HI, d & C = 0, d XOR C = HI",
        "  D/A ladder == C bit positions: NO (different objects)",
        "  P70->P71 +1 on D/A ladder: YES (by construction of shift hypothesis)",
        "  P70->P71 +1 on C bit positions from +1-shift d: test above",
        "  Consecutive puzzle +1 shift rarely exact for either ladder",
    ]

    text = "\n".join(lines) + "\n"
    out = ROOT / "ARCHIVE" / "complement_ladder_test.txt"
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
