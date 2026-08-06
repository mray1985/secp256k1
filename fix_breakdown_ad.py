#!/usr/bin/env python3
"""Compare cheat-sheet AD vs formula-derived AD with continuity."""
from __future__ import annotations

import re
from pathlib import Path

from generate_ad_sequences_1_70 import D, V2N, fmt, parse_expansion_line, tokens_to_ops, val

BREAKDOWN = Path(r"F:\New folder\secp256k1\DOUBLE_AND_ADD+BREAKDOWN.txt")
OP_RE = re.compile(r"([AD])\((\d+)\)")
ARITH = re.compile(r"^(\d+)\s*=\s*(.+)$")


def load_cheat() -> tuple[dict[int, str], dict[int, str]]:
    lines = [ln.strip() for ln in BREAKDOWN.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    formulas: dict[int, str] = {}
    ads: dict[int, str] = {}
    i = 0
    while i < len(lines):
        m = ARITH.match(lines[i])
        if not m:
            i += 1
            continue
        target = int(m.group(1))
        formula = m.group(2)
        n = V2N.get(target)
        if n and n <= 34:
            formulas[n] = formula
            if i + 1 < len(lines) and OP_RE.search(lines[i + 1]):
                ads[n] = lines[i + 1]
                i += 2
                continue
        i += 1
    return formulas, ads


def derive_chain(formulas: dict[int, str]) -> dict[int, list[tuple[str, int]]]:
    out: dict[int, list[tuple[str, int]]] = {}
    prev_end: str | None = None
    for n in range(1, 35):
        if n not in formulas:
            continue
        toks = parse_expansion_line(f"= {formulas[n]}")
        need = "A" if n == 1 else ("D" if prev_end == "A" else "A")
        ops = tokens_to_ops(toks, need)
        if not ops or sum(val(o, m) for o, m in ops) != D[n]:
            alt = "D" if need == "A" else "A"
            ops = tokens_to_ops(toks, alt)
        if ops and sum(val(o, m) for o, m in ops) == D[n]:
            out[n] = ops
            prev_end = ops[-1][0]
    return out


def main() -> None:
    formulas, ads = load_cheat()
    derived = derive_chain(formulas)
    prev_end: str | None = None
    print("=== Cheat sheet vs derived (P1-34) ===")
    for n in range(1, 35):
        if n not in ads:
            continue
        cheat_ops = [(g, int(i)) for g, i in OP_RE.findall(ads[n])]
        issues = []
        for j in range(1, len(cheat_ops)):
            if cheat_ops[j][0] == cheat_ops[j - 1][0]:
                issues.append(f"internal AA/DD @{j}")
        if prev_end and cheat_ops[0][0] == prev_end:
            issues.append(f"cross AA/DD (starts {cheat_ops[0][0]} after {prev_end})")
        cs = sum(val(o, m) for o, m in cheat_ops)
        if cs != D[n]:
            issues.append(f"sum delta {D[n] - cs}")
        der = derived.get(n)
        der_s = fmt(der) if der else "MISSING"
        match = fmt(cheat_ops) == der_s
        print(f"P{n:2d} cheat={'OK' if not issues else 'BAD'} match_derived={match}")
        for iss in issues:
            print(f"     {iss}")
        if not match and der:
            print(f"     cheat: {ads[n][:100]}")
            print(f"     fixed: {der_s[:100]}")
        prev_end = cheat_ops[-1][0] if cheat_ops else prev_end


if __name__ == "__main__":
    main()
