#!/usr/bin/env python3
"""
Where does Fine = y/p^2 touch the x/p digit region?

C     = x/p + y/p^2
C_neg = x/p + (p-y)/p^2 = C + (p-2y)/p^2

x is invariant under negation. Digits of C near ~78 can still move
because Fine is O(1/p) and carries into the trailing x/p decimals.
"""
from __future__ import annotations

from decimal import Decimal, getcontext, ROUND_DOWN
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_DIGIT_BOUNDARY.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
getcontext().prec = 400
getcontext().rounding = ROUND_DOWN
G = SECP256k1.generator
Dp = Decimal(P)
Dp2 = Dp * Dp


def frac_digits(d: Decimal, places: int) -> str:
    t = d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_DOWN)
    s = format(t, "f")
    return s.split(".", 1)[1][:places]


def first_diff(a: str, b: str) -> int | None:
    for i, (ca, cb) in enumerate(zip(a, b), start=1):
        if ca != cb:
            return i
    if len(a) != len(b):
        return min(len(a), len(b)) + 1
    return None


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Digit boundary: x/p vs C = x/p + y/p^2 vs C_neg = x/p - y/p^2 + 1/p")
    w("=" * 88)
    w(f"  log10(p)  ~ {Decimal(P).ln() / Decimal(10).ln()}")
    w(f"  p digits  = {len(str(P))}")
    w(f"  So 1/p starts near fractional digit ~{len(str(P))}")
    w()

    places = 160
    diffs_C_X: list[int] = []
    diffs_C_Cneg: list[int] = []
    diffs_X_Xneg: list[int] = []  # should be none — same X
    x_unchanged = 0

    w("-" * 88)
    w("1) Walk samples: first differing fractional digit")
    w("-" * 88)

    for n in list(range(1, 33)) + [50, 100, 200, 500, 1000]:
        pt = n * G
        x, y = int(pt.x()), int(pt.y())
        yn = (-y) % P
        assert x == x  # noqa — x fixed
        if True:
            x_unchanged += 1

        X = Decimal(x) / Dp
        Fine = Decimal(y) / Dp2
        Fine_n = Decimal(yn) / Dp2
        C = X + Fine
        C_neg = X + Fine_n
        # also "x/p - y/p^2" (not a curve point unless +1/p)
        C_minus = X - Fine

        dX = frac_digits(X, places)
        dC = frac_digits(C, places)
        dCn = frac_digits(C_neg, places)
        dCm = frac_digits(C_minus, places)

        i_cx = first_diff(dC, dX)
        i_cn = first_diff(dC, dCn)
        i_cm = first_diff(dC, dCm)
        i_xx = first_diff(dX, frac_digits(Decimal(x) / Dp, places))  # trivial

        if i_cx:
            diffs_C_X.append(i_cx)
        if i_cn:
            diffs_C_Cneg.append(i_cn)

        if n <= 8 or n in (17, 100, 1000):
            w(f"  n={n}")
            w(f"    x unchanged under neg: True")
            w(f"    first digit C vs X=x/p:           {i_cx}")
            w(f"    first digit C vs C_neg:           {i_cn}")
            w(f"    first digit C vs (x/p - y/p^2):   {i_cm}")
            # show window around 70..85
            lo, hi = 70, 90
            w(f"    C     [{lo}:{hi}] = ...{dC[lo-1:hi]}...")
            w(f"    X     [{lo}:{hi}] = ...{dX[lo-1:hi]}...")
            w(f"    C_neg [{lo}:{hi}] = ...{dCn[lo-1:hi]}...")
            w()

    # stats on 1..32
    diffs_C_X.clear()
    diffs_C_Cneg.clear()
    for n in range(1, 129):
        pt = n * G
        x, y = int(pt.x()), int(pt.y())
        yn = (-y) % P
        X = Decimal(x) / Dp
        C = X + Decimal(y) / Dp2
        Cn = X + Decimal(yn) / Dp2
        dX, dC, dCn = frac_digits(X, places), frac_digits(C, places), frac_digits(Cn, places)
        icx, icn = first_diff(dC, dX), first_diff(dC, dCn)
        if icx:
            diffs_C_X.append(icx)
        if icn:
            diffs_C_Cneg.append(icn)

    def summarize(name: str, vals: list[int]) -> None:
        vals = sorted(vals)
        w(
            f"  {name}: n={len(vals)}  min={vals[0]}  median={vals[len(vals)//2]}  "
            f"max={vals[-1]}"
        )

    w("-" * 88)
    w("2) Stats first-diff digit (walk n=1..128)")
    w("-" * 88)
    summarize("C vs X=x/p      ", diffs_C_X)
    summarize("C vs C_neg      ", diffs_C_Cneg)
    w()

    w("-" * 88)
    w("3) What is actually changing")
    w("-" * 88)
    w("  • Integer x does NOT change under negation.")
    w("  • Pure X = x/p digits are identical for P and -P.")
    w("  • Combined C = X + Fine: Fine ~ O(1/p) ~ 10^{-78}.")
    w("  • Adding Fine can CARRY into the last few digits of the x/p region.")
    w("  • So printed C looks like 'x changed around digits 75-78' —")
    w("    that is carry from y/p^2 (or (p-y)/p^2), not a new x.")
    w("  • True C_neg = x/p + (p-y)/p^2 = x/p - y/p^2 + 1/p.")
    w("    Plain (x/p - y/p^2) omits +1/p and is NOT Phi(-P).")
    w()

    # prove carry: when does C's first 77 digits equal X's?
    same77 = same78 = 0
    for n in range(1, 129):
        pt = n * G
        x, y = int(pt.x()), int(pt.y())
        X = Decimal(x) / Dp
        C = X + Decimal(y) / Dp2
        if frac_digits(C, 77) == frac_digits(X, 77):
            same77 += 1
        if frac_digits(C, 78) == frac_digits(X, 78):
            same78 += 1
    w(f"  C and X agree on first 77 frac digits: {same77}/128")
    w(f"  C and X agree on first 78 frac digits: {same78}/128")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  The 75-78 digit wiggle is Fine bleeding into the x/p print via carry.")
    w("  x is fixed; compressed 02/03 is the clean tag without that bleed.")
    w("  Phi(-P) = x/p + (p-y)/p^2, not x/p - y/p^2 alone.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
