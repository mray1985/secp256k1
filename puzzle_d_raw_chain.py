#!/usr/bin/env python3
"""Raw consecutive puzzle d relations P_n = P_{n-1} + delta, etc."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from puzzle_keys_53125 import parse_53125


def main() -> None:
    keys = parse_53125()
    ns = [n for n in sorted(keys) if n <= 70]

    print("=== EVERY SOLVED PUZZLE: P_n = P_{n-1} + delta ===\n")
    for i in range(1, len(ns)):
        n, p = ns[i], ns[i - 1]
        delta = keys[n].d - keys[p].d
        print(f"P{n:2d} = P{p:2d} + {delta}")

    print("\n=== EXACT TWO-PUZZLE SUMS: P_n = P_a + P_b (a,b < n) ===\n")
    for i, n in enumerate(ns):
        d = keys[n].d
        prev = ns[:i]
        hits: list[str] = []
        for j, a in enumerate(prev):
            for b in prev[j:]:
                if keys[a].d + keys[b].d == d:
                    hits.append(f"P{a}+P{b}")
        if hits:
            uniq = list(dict.fromkeys(hits))
            print(f"P{n:2d} = {' | '.join(uniq[:8])}")

    print("\n=== P70 BREAKDOWN ===")
    d68, d69, d70 = keys[68].d, keys[69].d, keys[70].d
    gap69 = d69 - d68
    gap70 = d70 - d69
    print(f"P70 = P69 + {gap70}")
    print(f"P69 = P68 + {gap69}")
    print(f"P70 - P69 = {gap70}")
    print(f"P69 - P68 = {gap69}")
    print(f"P70 = P69 + (P69 - P68)?  {d69 + gap69 == d70}  (need {d69 + gap69}, have {d70})")
    print(f"P70 = 2*P69 - P68?         {2 * d69 - d68 == d70}  (value {2 * d69 - d68})")
    print(f"P70 = P69 + P67?           {d69 + keys[67].d == d70}")
    print(f"P70 = P69 + P66?           {d69 + keys[66].d == d70}")

    for n in ns:
        if keys[n].d == gap70:
            print(f"  gap P69->P70 equals P{n}")
    for i in range(1, len(ns)):
        n, p = ns[i], ns[i - 1]
        g = keys[n].d - keys[p].d
        if g == gap70 and n != 70:
            print(f"  gap P69->P70 equals prior gap P{p}->P{n}")


if __name__ == "__main__":
    main()
