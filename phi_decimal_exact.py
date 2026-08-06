#!/usr/bin/env python3
"""
Exact decimal Phi pipeline (no binary float).

  Phi(P) = (x*p + y) / p^2 = x/p + y/p^2

Use decimal.Decimal for paper-style forward arithmetic / digit chains.
Use fractions.Fraction (or ints) as algebraic ground truth.

Decimal still rounds at getcontext().prec (p is not a power of 10), so:
  - Build Phi from ints each time when transforming
  - Compare by fractional digit prefix (~156), not bare ==
  - Never seed from float / Decimal(float(...))
"""
from __future__ import annotations

from decimal import Decimal, getcontext, ROUND_DOWN
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_DECIMAL_EXACT.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE

# ~78 digits for p, ~156 for 1/p^2; headroom so 156-digit prefixes are stable
PREC = 220
FRAC_DIGITS = 156
getcontext().prec = PREC
getcontext().rounding = ROUND_DOWN

G = SECP256k1.generator

Dp = Decimal(P)
Dp2 = Dp * Dp


def phi_fraction(x: int, y: int) -> Fraction:
    return Fraction(x * P + y, P * P)


def phi_decimal(x: int, y: int) -> Decimal:
    """Paper decimal from ints only: (x*p + y) / p^2."""
    return (Decimal(x) * Dp + Decimal(y)) / Dp2


def fraction_to_decimal(f: Fraction) -> Decimal:
    return Decimal(f.numerator) / Decimal(f.denominator)


def decimal_frac_digits(d: Decimal, places: int) -> str:
    q = Decimal(1).scaleb(-places)
    t = d.quantize(q, rounding=ROUND_DOWN)
    s = format(t, "f")
    if "." not in s:
        return "0" * places
    return s.split(".", 1)[1][:places]


def digit_prefix_match(a: Decimal, b: Decimal, places: int = FRAC_DIGITS) -> bool:
    return decimal_frac_digits(a, places) == decimal_frac_digits(b, places)


def split_layers(x: int, y: int) -> tuple[Decimal, Decimal]:
    """X=x/p, Fine=y/p^2 from known ints (do not decode from truncated C)."""
    return Decimal(x) / Dp, Decimal(y) / Dp2


def T_neg_from_ints(x: int, y: int) -> Decimal:
    return phi_decimal(x, (-y) % P)


def T_neg_residual(c: Decimal, y: int) -> Decimal:
    """C + (p-2y)/p^2 with residual from int y."""
    return c + Decimal(P - 2 * y) / Dp2


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Exact decimal Phi (decimal.Decimal) — no binary float in the chain")
    w("=" * 88)
    w(f"  getcontext().prec = {PREC}   compare first {FRAC_DIGITS} frac digits")
    w(f"  p digits ~ {len(str(P))}   p^2 digits ~ {len(str(P * P))}")
    w("  Build Phi from Decimal(int) / digit strings — never from float.")
    w()

    w("-" * 88)
    w("0) Why not float / Decimal(float)")
    w("-" * 88)
    bad = Decimal(0.1) + Decimal(0.2)
    good = Decimal("0.1") + Decimal("0.2")
    w(f"  Decimal(0.1)+Decimal(0.2) = {bad}")
    w(f"  Decimal('0.1')+Decimal('0.2') = {good}")
    w()

    w("-" * 88)
    w("1) Phi(nG): Decimal vs Fraction vs float")
    w("-" * 88)
    n_test = 64
    match_digits = 0
    match_neg_ints = 0
    match_neg_resid = 0
    float_sees_neg = 0

    for n in range(1, n_test + 1):
        pt = n * G
        x, y = int(pt.x()), int(pt.y())
        cf = phi_fraction(x, y)
        cd = phi_decimal(x, y)
        if digit_prefix_match(cd, fraction_to_decimal(cf)):
            match_digits += 1

        cd_neg = T_neg_from_ints(x, y)
        cf_neg = phi_fraction(x, (-y) % P)
        if digit_prefix_match(cd_neg, fraction_to_decimal(cf_neg)):
            match_neg_ints += 1
        if digit_prefix_match(T_neg_residual(cd, y), cd_neg):
            match_neg_resid += 1
        if float(cf) != float(cf_neg):
            float_sees_neg += 1

    w(f"  n=1..{n_test}: Decimal Phi digit-match Fraction:     {match_digits}/{n_test}")
    w(f"  n=1..{n_test}: T_neg from ints digit-match Fraction: {match_neg_ints}/{n_test}")
    w(f"  n=1..{n_test}: C+(p-2y)/p^2 digit-match T_neg:       {match_neg_resid}/{n_test}")
    w(f"  n=1..{n_test}: float(Phi)!=float(Phi(-P)):           {float_sees_neg}/{n_test}")
    w("  float collapses negation (0/64). Decimal keeps the Fine-layer gap.")
    w()

    w("-" * 88)
    w(f"2) Sample forward decimals ({FRAC_DIGITS} frac digits, truncated)")
    w("-" * 88)
    for n in (1, 2, 5, 17):
        pt = n * G
        x, y = int(pt.x()), int(pt.y())
        cd = phi_decimal(x, y)
        X, Fine = split_layers(x, y)
        cd_neg = T_neg_from_ints(x, y)
        cd_lam = phi_decimal((BETA * x) % P, y)
        _, Fine_lam = split_layers((BETA * x) % P, y)
        w(f"  n={n}")
        w(f"    C     = 0.{decimal_frac_digits(cd, FRAC_DIGITS)}")
        w(f"    X     = 0.{decimal_frac_digits(X, 78)}")
        w(f"    Fine  = 0.{decimal_frac_digits(Fine, FRAC_DIGITS)}")
        w(f"    C_neg = 0.{decimal_frac_digits(cd_neg, FRAC_DIGITS)}")
        w(f"    C_lam = 0.{decimal_frac_digits(cd_lam, FRAC_DIGITS)}")
        w(f"    Fine_lam digit-match Fine: {digit_prefix_match(Fine_lam, Fine)}")
        w()

    w("-" * 88)
    w("3) Forward orbit chain (ints -> Decimal encode each step)")
    w("-" * 88)
    pt = 1 * G
    x, y = int(pt.x()), int(pt.y())
    c = phi_decimal(x, y)
    c_neg = T_neg_from_ints(x, y)
    x_lam = (BETA * x) % P
    c_lam = phi_decimal(x_lam, y)
    c_neg_lam = T_neg_from_ints(x_lam, y)
    ok = (
        digit_prefix_match(c_neg, fraction_to_decimal(phi_fraction(x, (-y) % P)))
        and digit_prefix_match(c_lam, fraction_to_decimal(phi_fraction(x_lam, y)))
        and digit_prefix_match(
            c_neg_lam, fraction_to_decimal(phi_fraction(x_lam, (-y) % P))
        )
        and digit_prefix_match(T_neg_residual(c, y), c_neg)
        and digit_prefix_match(T_neg_residual(c_lam, y), c_neg_lam)
    )
    w(f"  orbit + residual digit-match Fraction: {ok}")
    w("  Pattern: mutate (x,y) in Z/pZ, then phi_decimal(x,y) — never float.")
    w()

    w("-" * 88)
    w("4) Policy")
    w("-" * 88)
    w("  • EC / F / psi: integer mod p (exact)")
    w("  • Algebraic Phi identities: Fraction (exact, unlimited)")
    w("  • Paper decimal print / forward digits: Decimal from ints, prec>=220")
    w("  • Init: Decimal(int) or Decimal('0.digits') — never Decimal(float)")
    w("  • Compare Phi values by digit prefix, not float==")
    w("  • Round-trip decode: keep (x,y) or Fraction; truncated Decimal is display")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Decimal is correct for human-exact Phi digit chains.")
    w("  Rebuild from ints on each orbit step; residual (p-2y)/p^2 matches at 156 digits.")
    w("  float is unfit (hides negation). F stays integer EC.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
