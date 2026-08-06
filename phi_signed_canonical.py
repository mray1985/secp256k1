#!/usr/bin/env python3
"""
Lock signed vs canonical Phi for P and -P.

  Phi_+(P) = x/p + y/p^2
  Phi_-(P) = x/p - y/p^2
  Phi(-P)  = x/p + (p-y)/p^2 = Phi_-(P) + 1/p   (canonical)

  (Phi_+ + Phi_-)/2 = x/p
  (Phi_+ - Phi_-)/2 = y/p^2
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_SIGNED_CANONICAL.txt")
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
G = SECP256k1.generator


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Signed decomposition vs canonical radix-p encoding of P and -P")
    w("=" * 88)
    w()
    w("  Same x, branches y and p-y ARE P and -P.")
    w("  Distinction is only encoding: signed Phi_- vs canonical Phi(-P).")
    w()

    n_walk = 256
    ok_mid = ok_half = ok_canon = ok_points = 0

    for n in range(1, n_walk + 1):
        pt = n * G
        x, y = int(pt.x()), int(pt.y())
        yn = (P - y) % P  # = (-y) % P
        assert yn == (-y) % P

        Xp = Fraction(x, P)
        Fine = Fraction(y, P * P)
        Phi_p = Xp + Fine
        Phi_m = Xp - Fine
        Phi_neg = Fraction(x * P + yn, P * P)  # canonical Phi(-P)
        Phi_P = Fraction(x * P + y, P * P)     # canonical Phi(P) == Phi_+

        if Phi_P == Phi_p:
            ok_points += 1
        if (Phi_p + Phi_m) / 2 == Xp:
            ok_mid += 1
        if (Phi_p - Phi_m) / 2 == Fine:
            ok_half += 1
        if Phi_neg == Phi_m + Fraction(1, P):
            ok_canon += 1

    w(f"  walk 1..{n_walk}: canonical Phi(P) == Phi_+ :     {ok_points}/{n_walk}")
    w(f"  walk 1..{n_walk}: (Phi_++Phi_-)/2 == x/p :        {ok_mid}/{n_walk}")
    w(f"  walk 1..{n_walk}: (Phi_+-Phi_-)/2 == y/p^2 :      {ok_half}/{n_walk}")
    w(f"  walk 1..{n_walk}: Phi(-P) == Phi_- + 1/p :        {ok_canon}/{n_walk}")
    w()
    w("  Borrow picture: signed digit (-y) -> legal digit (p-y) costs +1/p")
    w("  (radix-p normalize), holding printed x/p fixed in the Phi_- + 1/p form.")
    w()
    w("  Two valid views:")
    w("    symmetric signed:   x/p ± y/p^2")
    w("    canonical nonnegative: (x*p + y)/p^2  and  (x*p + (p-y))/p^2")
    w()
    w("  Center = x-channel; displacement = signed y-channel.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
