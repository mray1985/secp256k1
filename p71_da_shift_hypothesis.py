#!/usr/bin/env python3
"""
P71 hypothesis: same D/A chain as P70 but every puzzle index +1
  starts P68, falls 67, 64, 63, 60, 57 ... down to P2
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from puzzle_da_sequence import PUZZLE, parse_da, eval_tokens, format_da, Tok
from puzzle_keys_53125 import parse_53125

P70_CHAIN = (
    "D(67)A(67)D(67)A(67)D(66)A(66)D(63)A(63)D(62)A(59)D(56)A(56)"
    "D(50)A(50)D(48)A(48)D(45)A(45)D(44)A(39)D(34)A(30)D(28)A(27)"
    "D(23)A(23)D(22)A(21)D(17)A(17)D(13)A(11)D(10)A(8)D(4)A(1)"
)


def shift_chain(tokens: list[Tok], delta: int = 1) -> list[Tok]:
    return [Tok(t.op, t.k + delta) for t in tokens]


def ladder_indices(tokens: list[Tok]) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for t in tokens:
        if t.k not in seen:
            seen.add(t.k)
            out.append(t.k)
    return out


def net_weights(tokens: list[Tok]) -> dict[int, int]:
    c: Counter[int] = Counter()
    for t in tokens:
        c[t.k] += 2 if t.op == "D" else 1
    return dict(c)


def main() -> int:
    keys = parse_53125()
    p70_toks = parse_da(P70_CHAIN)
    p71_toks = shift_chain(p70_toks, 1)
    p71_chain = format_da(p71_toks)
    d71 = eval_tokens(p71_toks)

    lo, hi = 1 << 70, 1 << 71
    mid = 3 * (1 << 69)
    in_band = lo <= d71 < hi

    p70_ladder = ladder_indices(p70_toks)
    p71_ladder = ladder_indices(p71_toks)

    lines = [
        "P71 HYPOTHESIS — P70 chain with every index +1",
        f"  P70 ladder (first appearance): {p70_ladder}",
        f"  P71 ladder (first appearance): {p71_ladder}",
        "",
        f"P71 chain ({len(p71_toks)} steps):",
        f"  {p71_chain}",
        "",
        "Net weights (A=1x, D=2x):",
    ]
    for k in sorted(net_weights(p71_toks), reverse=True):
        w = net_weights(p71_toks)[k]
        lines.append(f"  {w}*P{k}  (d={keys[k].d if k in keys else PUZZLE.get(k, '?')})")

    lines += [
        "",
        f"d71_candidate = {d71}",
        f"d71_hex = {hex(d71)}",
        f"band [2^70, 2^71): {lo} .. {hi}",
        f"in_band: {in_band}",
        f"1.5 * 2^70 = {mid}",
        f"d71 / 2^70 = {d71 / lo:.6f}",
        f"d71 - 1.5*2^70 = {d71 - mid}",
        "",
        f"P70 = {keys[70].d}",
        f"P71_candidate - P70 = {d71 - keys[70].d}",
    ]

    if in_band:
        from ecdlp_full_pipeline import pubkey_from_scalar  # noqa: WPS433

        px, py = pubkey_from_scalar(d71)
        lines += ["", f"pubkey_x = {px}", f"pubkey_y = {py}"]

    text = "\n".join(lines) + "\n"
    out = ROOT / "ARCHIVE" / "p71_da_shift_hypothesis.txt"
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
