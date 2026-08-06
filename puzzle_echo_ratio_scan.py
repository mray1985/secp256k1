#!/usr/bin/env python3
"""Scan page/priv/x/y/echo-prime ratios vs 2^k across puzzles (120-135)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_keys_53125 import parse_53125

getcontext().prec = 120

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# Puzzle 135 ECDLP row-3 (unsolved target slice)
P135_PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
P135_PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
P135_MYSTERY = 80184233617433755134183875136831551618578922487806929476230322368028862899169

# User "page" values from 61425.txt
PAGE = {
    120: 15322391680683005559008517510312739,
    125: 627509161962375741762900164621920358,
    130: 18397899749225123993799089185733430493,
}


@dataclass
class Row:
    n: int
    d: int
    x: int
    y: int
    echo: int  # x^3 + 7 mod p
    page: int | None


def ratio(v: int, k: int) -> Decimal:
    return Decimal(v) / Decimal(2**k)


def pct_diff(a: int, b: int) -> Decimal:
    return (Decimal(a) / Decimal(b) - 1) * 100


def main() -> None:
    keys = parse_53125()
    lines = [
        "PUZZLE ECHO / PAGE RATIO SCAN",
        "  echo_prime := (x^3 + 7) mod p  [on-curve y^2]",
        "  page from 61425.txt where listed",
        "",
    ]

    puzzles = [120, 125, 130]
    for n in puzzles:
        k = keys[n]
        echo = (pow(k.px, 3, p) + 7) % p
        pg = PAGE.get(n)
        lines += [f"=== Puzzle {n} ===", f"  d    = {k.d}", f"  x    = {k.px}", f"  y    = {k.py}", f"  echo = {echo}"]
        if pg:
            lines.append(f"  page = {pg}")

        # User divisors from notes
        divs = {
            "page": n - 7,
            "priv": n - 1,
            "x": {120: 255, 125: 253, 130: 254}[n],
            "y": {120: 253, 125: 253, 130: 255}[n],
            "echo": 255,
        }
        if pg:
            lines.append(f"  page/2^{divs['page']} = {ratio(pg, divs['page'])}")
        lines.append(f"  priv/2^{divs['priv']} = {ratio(k.d, divs['priv'])}")
        lines.append(f"  x/2^{divs['x']}     = {ratio(k.px, divs['x'])}")
        lines.append(f"  y/2^{divs['y']}     = {ratio(k.py, divs['y'])}")
        lines.append(f"  echo/2^{divs['echo']} = {ratio(echo, divs['echo'])}")
        lines.append(f"  x/echo            = {Decimal(k.px) / Decimal(echo)}")
        lines.append(f"  x-echo            = {k.px - echo}")
        lines.append(f"  pct x vs echo     = {pct_diff(k.px, echo):.6f}%")
        lines.append(f"  2^134 * x mod p   = {(pow(2, 134, p) * k.px) % p}")
        lines.append("")

    # Puzzle 135
    echo135 = (pow(P135_PX, 3, p) + 7) % p
    lines += [
        "=== Puzzle 135 (row 3 Px/Py — UNSOLVED) ===",
        f"  Px3  = {P135_PX}",
        f"  Py3  = {P135_PY}",
        f"  echo = (Px3^3+7) mod p = {echo135}",
        f"  mystery 80184... = {P135_MYSTERY}",
        f"  mystery == echo? {P135_MYSTERY == echo135}",
        f"  mystery == Py3^2 mod p? {P135_MYSTERY == pow(P135_PY, 2, p)}",
        f"  Px3/2^252 = {ratio(P135_PX, 252)}",
        f"  Py3/2^254 = {ratio(P135_PY, 254)}",
        f"  mystery/2^255 = {ratio(P135_MYSTERY, 255)}",
        f"  2^134 * Px3 mod p = {(pow(2, 134, p) * P135_PX) % p}",
        "",
        "=== CROSS-PUZZLE: echo/2^255 and x/echo pct ===",
    ]

    for n in puzzles:
        k = keys[n]
        echo = (pow(k.px, 3, p) + 7) % p
        lines.append(
            f"  P{n:3d}  echo/2^255={ratio(echo, 255):.6f}  x/echo-1={pct_diff(k.px, echo):.4f}%  priv/2^(n-1)={ratio(k.d, n-1):.4f}"
        )
    lines.append(
        f"  P135   mystery/2^255={ratio(P135_MYSTERY, 255):.6f}  (if mystery=echo: Px/echo TBD)"
    )

    # Predict P135 echo from P120 pattern?
    lines += ["", "=== P135 echo estimate from P120 x/echo ratio ==="]
    r120 = Decimal(keys[120].px) / Decimal((pow(keys[120].px, 3, p) + 7) % p)
    est_echo135 = int(Decimal(P135_PX) / r120)
    lines.append(f"  P120 x/echo = {r120}")
    lines.append(f"  est echo135 = Px3 / (x/echo)_120 = {est_echo135}")
    lines.append(f"  est vs mystery diff = {est_echo135 - P135_MYSTERY}")

    # Page formula hunt: page vs d, x, echo
    lines += ["", "=== PAGE vs priv (ratio page/priv) ==="]
    for n in puzzles:
        pg, d = PAGE[n], keys[n].d
        lines.append(f"  P{n} page/priv = {Decimal(pg) / Decimal(d)}")

    out = ROOT / "ARCHIVE" / "puzzle_echo_ratio_scan.txt"
    text = "\n".join(lines) + "\n"
    out.write_text(text, encoding="utf-8")
    sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
    print(f"\nwrote {out}", flush=True)


if __name__ == "__main__":
    main()
