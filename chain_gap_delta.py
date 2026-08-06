#!/usr/bin/env python3
"""
Compare 2^k-weighted chain sum to actual key d_n.

  chain_sum         = eval_power2(D/A chain)     # A(k)=2^k, D(k)=2^(k+1)
  chain_gap         = 2^n - chain_sum
  actual_complement = (2^n - 1) - d_n            # bitmask complement of d
  delta_to_key      = actual_complement - chain_gap
                    = chain_sum - d_n - 1        # algebraically

P71 +1 shift: sum doubles, gap doubles (one octave).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_da_power2 import chains_p1_70, eval_power2, ladder, gaps
from puzzle_da_sequence import PUZZLE, parse_da, Tok, format_da


def row(n: int, chain: str) -> dict:
    s = eval_power2(parse_da(chain))
    d = PUZZLE[n]
    hi = 2**n
    top = hi - 1
    chain_gap = hi - s
    actual_comp = top - d
    delta = actual_comp - chain_gap
    return {
        "n": n,
        "chain_sum": s,
        "two_n": hi,
        "chain_gap": chain_gap,
        "actual_complement": actual_comp,
        "delta": delta,
        "d": d,
        "ratio_sum_2n": s / hi,
        "ratio_gap_comp": chain_gap / actual_comp if actual_comp else 0,
        "delta_over_d": delta / d if d else 0,
        "delta_over_2n": delta / hi,
    }


def main() -> None:
    chains = chains_p1_70()
    rows = [row(n, chains[n]) for n in range(1, 71)]

    lines = [
        "CHAIN GAP vs KEY COMPLEMENT — delta_to_key = (2^n-1-d) - (2^n-sum) = sum-d-1",
        "",
        "P    chain_sum              chain_gap            actual_comp          delta                sum/2^n",
        "---  ---------------------  -------------------  -------------------  -------------------  --------",
    ]
    for r in rows:
        n = r["n"]
        lines.append(
            f"P{n:02d}  {r['chain_sum']:<21} {r['chain_gap']:<20} "
            f"{r['actual_complement']:<20} {r['delta']:<20} {r['ratio_sum_2n']:.6f}"
        )

    # P70 / P71 octave
    p70 = rows[69]
    p70_toks = parse_da(chains[70])
    p71_toks = [Tok(t.op, t.k + 1) for t in p70_toks]
    p71_sum = eval_power2(p71_toks)
    p71_gap = 2**71 - p71_sum

    lines += [
        "",
        "=== P70 scaffold ===",
        f"  chain_sum     = {p70['chain_sum']}",
        f"  2^70          = {p70['two_n']}",
        f"  chain_gap     = {p70['chain_gap']}",
        f"  sum/2^70      = {p70['ratio_sum_2n']:.6f}",
        f"  d_70          = {p70['d']}",
        f"  actual_comp   = {p70['actual_complement']}",
        f"  delta_to_key  = {p70['delta']}",
        "",
        "=== P71 +1 shift (same tokens, k+1) ===",
        f"  P71 sum       = {p71_sum}",
        f"  2 * P70 sum   = {2 * p70['chain_sum']}",
        f"  sum doubled?  {p71_sum == 2 * p70['chain_sum']}",
        f"  P71 gap       = {p71_gap}",
        f"  2 * P70 gap   = {2 * p70['chain_gap']}",
        f"  gap doubled?  {p71_gap == 2 * p70['chain_gap']}",
        f"  P71 sum/2^71  = {p71_sum / 2**71:.6f}",
        "",
        "=== DELTA PATTERNS ===",
    ]

    # consecutive delta ratios
    deltas = [r["delta"] for r in rows]
    lines.append(f"  delta == 0:           {sum(1 for d in deltas if d == 0)}/70")
    lines.append(f"  delta == chain_gap:   {sum(1 for r in rows if r['delta'] == r['chain_gap'])}/70")
    lines.append(f"  delta == actual_comp: {sum(1 for r in rows if r['delta'] == r['actual_complement'])}/70")
    lines.append(f"  delta == d:           {sum(1 for r in rows if r['delta'] == r['d'])}/70")
    lines.append(f"  delta == sum:         {sum(1 for r in rows if r['delta'] == r['chain_sum'])}/70")

    # delta / chain_gap stability
    ratios_dg = [r["delta"] / r["chain_gap"] if r["chain_gap"] else 0 for r in rows[3:]]
    lines.append(f"  delta/chain_gap mean (P4+): {sum(ratios_dg)/len(ratios_dg):.4f}")
    lines.append(f"  delta/chain_gap min/max:    {min(ratios_dg):.4f} / {max(ratios_dg):.4f}")

    # consecutive n -> n+1
    delta_shift = delta_ratio = 0
    for i in range(3, 69):
        if deltas[i + 1] == 2 * deltas[i]:
            delta_shift += 1
        if deltas[i] and deltas[i + 1] / deltas[i] == 2.0:
            delta_ratio += 1
    lines.append(f"  delta(n+1) == 2*delta(n):   {delta_shift}/66 (P4-P69)")
    lines.append(f"  delta ratio exactly 2:      {delta_ratio}/66")

    # delta vs 2^(n-3) head anchor
    lines += ["", "=== delta / 2^(n-3) (head block) ==="]
    for n in [4, 10, 20, 30, 40, 50, 60, 70]:
        r = rows[n - 1]
        head = 2 ** (n - 3)
        lines.append(
            f"  P{n:02d}  delta/2^(n-3) = {r['delta']/head:.4f}  "
            f"delta/d = {r['delta_over_d']:.4f}  chain_gap/actual_comp = {r['ratio_gap_comp']:.4f}"
        )

    # low-bit of delta
    lines += ["", "=== delta low bits (mod small powers) ==="]
    for mod in [2, 4, 8, 16]:
        residues = [r["delta"] % mod for r in rows[3:]]
        from collections import Counter
        c = Counter(residues)
        lines.append(f"  delta mod {mod}: {dict(sorted(c.items()))}")

    # check if delta equals complement of something fixed
    lines += ["", "=== delta vs bitmask structure ==="]
    for n in [4, 20, 40, 70]:
        r = rows[n - 1]
        nn = r["n"]
        d = r["d"]
        s = r["chain_sum"]
        # bits where delta has 1
        delta = r["delta"]
        bits = [nn - 1 - i for i in range(nn) if (delta >> (nn - 1 - i)) & 1]
        lines.append(f"  P{n:02d} delta bit count = {len(bits)}  MSB positions[:8] = {bits[:8]}")

    # P71 predicted delta if d_71 unknown: delta_71 = 2*sum_70 - d_71 - 1
    lines += [
        "",
        "=== P71 delta from +1 shift (unknown d_71) ===",
        f"  P71 chain_sum (shifted) = {p71_sum}",
        f"  delta_71 = sum_71 - d_71 - 1",
        f"  If delta_71 = 2*delta_70:  d_71 = {p71_sum - 2 * p70['delta'] - 1}",
        f"  If delta_71 = delta_70:   d_71 = {p71_sum - p70['delta'] - 1}",
    ]

    out = ROOT / "ARCHIVE" / "chain_gap_delta_P1_P70.txt"
    text = "\n".join(lines) + "\n"
    out.write_text(text, encoding="utf-8")
    sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
    print(f"\nwrote {out}", flush=True)


if __name__ == "__main__":
    main()
