#!/usr/bin/env python3
"""For each solved puzzle: which earlier puzzles (D/A chain) build d_n."""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_da_sequence import PUZZLE, parse_da, eval_tokens, USER_DA, build_chain, format_da
from puzzle_keys_53125 import parse_53125


@dataclass
class Term:
    sign: int  # +1 for A, -2 for D
    k: int

    @property
    def label(self) -> str:
        if self.sign == 1:
            return f"+P{self.k}"
        return f"-2*P{self.k}"


def chain_for(n: int) -> str:
    if n in USER_DA:
        return USER_DA[n]
    chains: dict[int, str] = {i: USER_DA[i] for i in range(1, 21)}
    prev_end = parse_da(chains[20])[-1].op
    for i in range(21, n + 1):
        toks = build_chain(i, prev_end)
        if toks is None:
            raise RuntimeError(f"no chain for P{i}")
        chains[i] = format_da(toks)
        prev_end = toks[-1].op
    return chains[n]


def terms_from_chain(s: str) -> list[Term]:
    out: list[Term] = []
    for tok in parse_da(s):
        out.append(Term(1 if tok.op == "A" else -2, tok.k))
    return out


def expand_chain(n: int, terms: list[Term]) -> str:
    parts = [f"P{t.k}" if t.sign == 1 else f"2*P{t.k}" for t in terms]
    signs = ["+" if t.sign == 1 else "-" for t in terms]
    expr = parts[0]
    for sign, part in zip(signs[1:], parts[1:], strict=False):
        op = sign
        expr += f" {op} {part}"
    return expr


def net_coefficients(terms: list[Term]) -> dict[int, int]:
    """A(k) contributes +1*P_k, D(k) contributes +2*P_k in the depletion sum."""
    c: Counter[int] = Counter()
    for t in terms:
        c[t.k] += 2 if t.sign == -2 else 1
    return dict(c)


def main() -> None:
    keys = parse_53125()
    out_lines: list[str] = []
    out_lines.append("PUZZLE INGREDIENTS TO REACH EACH d (D/A depletion model)")
    out_lines.append("  A(k) = +1*P_k   D(k) = +2*P_k   (weighted sum = d_n)")
    out_lines.append("")

    for n in range(1, 71):
        d = keys[n].d if n in keys else PUZZLE[n]
        chain = chain_for(n)
        terms = terms_from_chain(chain)
        val = eval_tokens(parse_da(chain))
        ok = val == d
        prev = n - 1 if n > 1 else None
        gap = d - keys[prev].d if prev else None

        puzzles_used = sorted({t.k for t in terms})
        coeffs = net_coefficients(terms)
        net_parts = []
        for k in sorted(coeffs, reverse=True):
            c = coeffs[k]
            net_parts.append(f"{c}*P{k}")

        out_lines.append(f"P{n:02d} = {d}")
        if prev:
            out_lines.append(f"  consecutive: P{n} = P{prev} + {gap}")
        out_lines.append(f"  puzzles used ({len(puzzles_used)}): {', '.join(f'P{k}' for k in puzzles_used)}")
        out_lines.append(f"  net: {' '.join(net_parts)}  [{'OK' if ok else f'SUM={val}'}]")
        out_lines.append(f"  chain ({len(terms)} steps): {chain}")
        out_lines.append("")

    path = ROOT / "ARCHIVE" / "puzzle_d_ingredients_P1_P70.txt"
    path.parent.mkdir(exist_ok=True)
    text = "\n".join(out_lines)
    path.write_text(text, encoding="utf-8")
    print(text[:4000])
    if len(text) > 4000:
        print(f"\n... [{len(out_lines)} lines total, wrote {path}]")
    else:
        print(f"\nwrote {path}")

    print("\n=== P70 DETAIL ===")
    n = 70
    chain = chain_for(n)
    terms = terms_from_chain(chain)
    print(f"P70 = P69 + {keys[70].d - keys[69].d}")
    print(f"puzzles in chain: {sorted({t.k for t in terms})}")
    print(f"chain: {chain}")


if __name__ == "__main__":
    main()
