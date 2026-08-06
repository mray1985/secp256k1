#!/usr/bin/env python3
"""
Compressed-x + 02/03 tail vs Phi layers.

secp256k1 compressed pubkey:
  02 || x   if y even
  03 || x   if y odd

Hypothesis: use only x (decimal body) + parity tail; compare to Phi Fine layer.
"""
from __future__ import annotations

from decimal import Decimal, getcontext, ROUND_DOWN
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_COMPRESSED_TAIL.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE

getcontext().prec = 220
getcontext().rounding = ROUND_DOWN
G = SECP256k1.generator
Dp = Decimal(P)


def parity_prefix(y: int) -> str:
    return "02" if (y % 2 == 0) else "03"


def compressed(x: int, y: int) -> str:
    return parity_prefix(y) + f"{x:064x}"


def x_over_p_digits(x: int, places: int = 78) -> str:
    d = (Decimal(x) / Dp).quantize(Decimal(1).scaleb(-places), rounding=ROUND_DOWN)
    s = format(d, "f")
    return s.split(".", 1)[1][:places]


def recover_y(x: int, prefix: str) -> int:
    """y^2 = x^3 + 7; pick root with requested parity."""
    y2 = (pow(x, 3, P) + 7) % P
    y = pow(y2, (P + 1) // 4, P)  # secp256k1 p%4==3
    if y % 2 == 0 and prefix == "03":
        y = (-y) % P
    elif y % 2 == 1 and prefix == "02":
        y = (-y) % P
    return y


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Compressed x + 02/03 tail  vs  Phi (x/p + y/p^2)")
    w("=" * 88)
    w()
    w("  Compressed = prefix(y parity) || x")
    w("  User idea: decimal body from x; differing tail = 02 or 03")
    w()

    # --- 1) Negation ---
    w("-" * 88)
    w("1) Negation: same x, flip 02 <-> 03")
    w("-" * 88)
    same_x = flip = recover_ok = 0
    for n in range(1, 65):
        pt = n * G
        x, y = int(pt.x()), int(pt.y())
        yn = (-y) % P
        c0, c1 = compressed(x, y), compressed(x, yn)
        if x == x:
            same_x += 1
        if c0[:2] != c1[:2] and c0[2:] == c1[2:]:
            flip += 1
        y_back = recover_y(x, c1[:2])
        if y_back == yn:
            recover_ok += 1
    w(f"  walk 1..64: x unchanged under neg:     {same_x}/64")
    w(f"  walk 1..64: prefix flips, x hex same:  {flip}/64")
    w(f"  walk 1..64: recover_y from (x,tail)= -P: {recover_ok}/64")
    w("  Matches Phi: X=x/p invariant; only Fine/parity changes.")
    w()

    # --- 2) GLV ---
    w("-" * 88)
    w("2) GLV psi: new x = beta*x, SAME parity (y unchanged)")
    w("-" * 88)
    same_pref = x_changes = 0
    for n in range(1, 65):
        pt = n * G
        x, y = int(pt.x()), int(pt.y())
        x2 = (BETA * x) % P
        if parity_prefix(y) == parity_prefix(y):  # y same
            if compressed(x, y)[:2] == compressed(x2, y)[:2]:
                same_pref += 1
        if x2 != x:
            x_changes += 1
    w(f"  walk 1..64: prefix unchanged under psi: {same_pref}/64")
    w(f"  walk 1..64: x changes under psi:        {x_changes}/64")
    w("  Matches Phi: Fine invariant under GLV; coarse X moves.")
    w()

    # --- 3) What you keep / lose ---
    w("-" * 88)
    w("3) Information: compressed vs full Phi")
    w("-" * 88)
    w("  KEEP:  x (32 bytes) + 1-bit parity  => unique affine point via curve")
    w("  DROP:  full y magnitude in Phi Fine = y/p^2")
    w("  Tail 02/03 is NOT a decimal fraction of y — only parity.")
    w("  So 'differing tail' works for +/- orbit; it does not encode Fine digits.")
    w()

    # --- 4) Proposed decimal print forms ---
    w("-" * 88)
    w("4) Candidate print forms (samples)")
    w("-" * 88)
    for n in (1, 2, 5, 17):
        pt = n * G
        x, y = int(pt.x()), int(pt.y())
        pref = parity_prefix(y)
        pref_n = parity_prefix((-y) % P)
        body = x_over_p_digits(x, 78)
        w(f"  n={n}")
        w(f"    compressed hex = {compressed(x, y)}")
        w(f"    form A (prefix|x/p):  {pref}.{body}")
        w(f"    form B (x/p|tail):    0.{body}.{pref}")
        w(f"    negation tail only:   0.{body}.{pref_n}")
        w(f"    Phi still needs y:    Fine~y/p^2 not in compressed")
        w()

    # --- 5) Addition ---
    w("-" * 88)
    w("5) Does compressed-x + tail make F cheaper?")
    w("-" * 88)
    w("  No. To add you still decompress (recover y) or stay in EC.")
    w("  Tail flip = negation only. x-body + tail has no schoolbook add rule.")
    w("  Same junction as Phi: orbit symmetries cheap; F is still EC.")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Yes: compressed x + 02/03 tail is the clean 'coarse + tag' form.")
    w("  Negation = identical x digits, flip tail. GLV = new x, same tail.")
    w("  That matches Phi layer symmetries without storing y/p^2.")
    w("  Cost: lose Fine decimal; recover y from curve when needed.")
    w("  Does not replace F; only clarifies the +/- half of the orbit.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
