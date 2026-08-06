#!/usr/bin/env python3
"""
Complement ladder: C = (2^n - 1) - d
  used bits  = positions where d has 1 (MSB index n-1 .. 0)
  comp bits  = positions where C has 1
  gaps       = steps between consecutive comp bits (descending)

Anchor n-3 checked against complement ladder membership.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_da_sequence import PUZZLE, USER_DA, parse_da, build_chain, format_da


def chains_p1_70() -> dict[int, str]:
    chains = {n: USER_DA[n] for n in range(1, 21)}
    prev = parse_da(chains[20])[-1].op
    for n in range(21, 71):
        chains[n] = format_da(build_chain(n, prev))
        prev = parse_da(chains[n])[-1].op
    return chains


def bits_set_msb(x: int, n: int) -> list[int]:
    """Descending bit indices 0..n-1 where x has bit set (MSB = n-1)."""
    return [n - 1 - i for i in range(n) if (x >> (n - 1 - i)) & 1]


def gaps(lst: list[int]) -> list[int]:
    return [lst[i] - lst[i + 1] for i in range(len(lst) - 1)]


def da_ladder(chain: str) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for t in parse_da(chain):
        if t.k not in seen:
            seen.add(t.k)
            out.append(t.k)
    return out


def shift_match(a: list[int], b: list[int], d: int = 1) -> bool:
    return len(a) == len(b) and b == [x + d for x in a]


def main() -> None:
    chains = chains_p1_70()
    lines = [
        "COMPLEMENT LADDER - C = (2^n - 1) - d",
        "  used bits = 1-positions in d",
        "  comp bits = 1-positions in C  (unused mask bits)",
        "  anchor    = n - 3",
        "",
    ]

    comp_by_n: dict[int, list[int]] = {}
    gap_by_n: dict[int, list[int]] = {}

    for n in range(1, 71):
        d = PUZZLE[n]
        top = 2**n - 1
        c = top - d
        used = bits_set_msb(d, n)
        comp = bits_set_msb(c, n)
        g = gaps(comp)
        comp_by_n[n] = comp
        gap_by_n[n] = g
        anchor = n - 3
        in_lad = anchor in comp if n >= 4 else False

        lines += [
            f"P{n:02d}",
            f"  d          = {d}",
            f"  full mask  = 2^{n} - 1",
            f"  complement = {c}",
            f"  anchor     = n-3 = {anchor}",
            f"  used bits  = {used}",
            f"  comp bits  = {comp}",
            f"  comp gaps  = {g}",
            f"  partition ok = {sorted(used + comp) == list(range(n)) and not set(used)&set(comp)}",
            f"  anchor in comp ladder? {in_lad}",
            "",
        ]

    lines += ["=== ANCHOR n-3 IN COMPLEMENT LADDER ==="]
    hits = sum(1 for n in range(4, 71) if (n - 3) in comp_by_n[n])
    lines.append(f"  {hits}/67 puzzles: anchor appears in comp bits")

    lines += ["", "=== COMP GAPS vs D/A LADDER GAPS (P70) ==="]
    n = 70
    dl = da_ladder(chains[n])
    lines.append(f"  D/A ladder:  {dl}")
    lines.append(f"  D/A gaps:    {gaps(dl)}")
    lines.append(f"  comp bits:   {comp_by_n[n]}")
    lines.append(f"  comp gaps:   {gap_by_n[n]}")
    lines.append(f"  same gaps?   {gaps(dl) == gap_by_n[n]}")

    lines += ["", "=== CONSECUTIVE n->n+1: comp bits +1 shift? ==="]
    bit_shift = gap_match_cnt = 0
    pairs = 0
    for n in range(1, 70):
        pairs += 1
        if shift_match(comp_by_n[n], comp_by_n[n + 1]):
            bit_shift += 1
        if gap_by_n[n] == gap_by_n[n + 1]:
            gap_match_cnt += 1
    lines.append(f"  comp bits(n+1) == comp bits(n)+1: {bit_shift}/{pairs}")
    lines.append(f"  comp gaps match:                  {gap_match_cnt}/{pairs}")

    lines += ["", "=== P69 / P70 / P71(+1 comp hypothesis) ==="]
    for label, nn in [("P69", 69), ("P70", 70)]:
        lines.append(f"  {label} comp[:12] = {comp_by_n[nn][:12]}")
        lines.append(f"  {label} gaps[:12] = {gap_by_n[nn][:12]}")
    p71_comp = [b + 1 for b in comp_by_n[70]]
    p71_g = gaps(p71_comp)
    lines.append(f"  P71 hyp (+1) comp[:12] = {p71_comp[:12]}")
    lines.append(f"  P71 hyp gaps[:12]      = {p71_g[:12]}")
    lines.append(f"  P70 gaps == P71 hyp gaps? {gap_by_n[70] == p71_g}")

    lines += ["", "=== D/A LADDER +1 vs COMP +1 (P70) ==="]
    p71_da = [k + 1 for k in da_ladder(chains[70])]
    lines.append(f"  D/A +1 ladder: {p71_da}")
    lines.append(f"  comp +1 bits:  {p71_comp}")
    lines.append(f"  identical? {p71_da == p71_comp}")

    out = ROOT / "ARCHIVE" / "complement_bit_ladder_P1_P70.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    text = "\n".join(lines[-40:])
    sys.stdout.buffer.write((text + f"\n\nwrote {out}\n").encode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
