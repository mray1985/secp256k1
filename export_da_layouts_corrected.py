#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from puzzle_da_sequence import USER_DA, parse_da, build_chain, format_da, PUZZLE, verify_row

chains = {n: USER_DA[n] for n in range(1, 21)}
prev = parse_da(chains[20])[-1].op
for n in range(21, 71):
    toks = build_chain(n, prev)
    chains[n] = format_da(toks)
    prev = toks[-1].op

lines = [
    "PUZZLE D/A LAYOUTS P1-P70 (CORRECTED)",
    "  P1-P20: hand-trusted USER_DA",
    "  P21-P70: regenerated — P20 ends A(1) -> P21 starts D(18) (fixes prior A/A glitch)",
    "  A(k) = +1 x d_k ,  D(k) = +2 x d_k ,  chain sums to d_n",
    "",
]
for n in range(1, 71):
    ch = chains[n]
    ok, delta = verify_row(n, ch)
    first, last = parse_da(ch)[0], parse_da(ch)[-1]
    tag = "OK" if ok else f"BAD delta={delta}"
    lines.append(f"P{n:02d}  d={PUZZLE[n]}  start={first.op}({first.k}) end={last.op}({last.k})  [{tag}]")
    lines.append(f"     {ch}")
    lines.append("")

out = ROOT / "ARCHIVE" / "puzzle_da_layouts_P1_P70_corrected.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out}")
print(f"P20 ends: {parse_da(chains[20])[-1]}")
print(f"P21 starts: {parse_da(chains[21])[0]}")
