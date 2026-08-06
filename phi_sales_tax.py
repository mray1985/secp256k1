#!/usr/bin/env python3
"""
Sales-tax style levy on Phi layers.

  Like: for every dollar of food, pay 10% tax
    taxed = amount * (1 + rate)
    tax   = amount * rate

Apply to X=x/p, Fine=y/p^2, C=X+Fine and ask if any rate
links to negation / GLV / +G in a reusable way.
"""
from __future__ import annotations

from decimal import Decimal, getcontext, ROUND_DOWN
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_SALES_TAX.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE

getcontext().prec = 220
getcontext().rounding = ROUND_DOWN
G = SECP256k1.generator


def phi(x: int, y: int) -> Fraction:
    return Fraction(x * P + y, P * P)


def layers(x: int, y: int) -> tuple[Fraction, Fraction, Fraction]:
    X = Fraction(x, P)
    Fine = Fraction(y, P * P)
    return X, Fine, X + Fine


def digit_match(a: Fraction, b: Fraction, places: int = 120) -> bool:
    """Compare deep enough to see Fine (~digit 78); default 120."""
    da = Decimal(a.numerator) / Decimal(a.denominator)
    db = Decimal(b.numerator) / Decimal(b.denominator)
    q = Decimal(1).scaleb(-places)
    return da.quantize(q, rounding=ROUND_DOWN) == db.quantize(q, rounding=ROUND_DOWN)


def exact(a: Fraction, b: Fraction) -> bool:
    return a == b


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    rates = [
        Fraction(1, 10),   # 10%
        Fraction(1, 100),
        Fraction(1, P),    # microscopic field-scale
        Fraction(2, 1),    # 200% nonsense scale
    ]
    rate_names = ["10%", "1%", "1/p", "200%"]

    w("=" * 88)
    w("Sales-tax levy: taxed = amount * (1+r),  tax = amount * r")
    w("=" * 88)
    w("  Targets: does any r map C or layers toward Phi(-P), Phi(lambda P), Phi((n+1)G)?")
    w()

    n_walk = 64

    # Precompute points
    pts = {}
    for n in range(1, n_walk + 1):
        pt = n * G
        pts[n] = (int(pt.x()), int(pt.y()))

    w("-" * 88)
    w("1) Tax whole C: C*(1+r)  vs known transforms  [exact Fraction ==]")
    w("-" * 88)
    for r, name in zip(rates, rate_names):
        hit_neg = hit_lam = hit_next = hit_pm = 0
        for n in range(1, n_walk + 1):
            x, y = pts[n]
            _, _, C = layers(x, y)
            taxed = C * (1 + r)
            C_neg = phi(x, (-y) % P)
            C_lam = phi((BETA * x) % P, y)
            C_next = phi(*pts[n + 1]) if n < n_walk else None
            Phi_m = Fraction(x, P) - Fraction(y, P * P)
            if exact(taxed, C_neg):
                hit_neg += 1
            if exact(taxed, C_lam):
                hit_lam += 1
            if C_next is not None and exact(taxed, C_next):
                hit_next += 1
            if exact(taxed, Phi_m):
                hit_pm += 1
        w(
            f"  r={name:4s}: vs Phi(-P) {hit_neg}/{n_walk}  "
            f"vs Phi(lam) {hit_lam}/{n_walk}  "
            f"vs Phi((n+1)G) {hit_next}/{n_walk - 1}  "
            f"vs Phi- {hit_pm}/{n_walk}"
        )
    w()

    w("-" * 88)
    w("2) Tax Fine only: X + Fine*(1+r)   [exact]")
    w("-" * 88)
    for r, name in zip(rates, rate_names):
        hit_neg = 0
        for n in range(1, n_walk + 1):
            x, y = pts[n]
            X, Fine, _ = layers(x, y)
            taxed = X + Fine * (1 + r)
            C_neg = phi(x, (-y) % P)
            if exact(taxed, C_neg):
                hit_neg += 1
        w(f"  r={name:4s}: X+Fine*(1+r) == Phi(-P)? {hit_neg}/{n_walk}")
    w("  Exact Fine tax for negation would need r* = p/y - 2  (depends on y, not fixed %)")
    for n in range(1, min(9, n_walk + 1)):
        x, y = pts[n]
        r_star = Fraction(P, y) - 2
        # verify: X + Fine*(1+r*) == Phi(-P)
        X, Fine, _ = layers(x, y)
        ok = exact(X + Fine * (1 + r_star), phi(x, (-y) % P))
        w(f"    n={n}: r*=p/y-2={float(r_star):.6e}  exact-neg={ok}")
    w()

    w("-" * 88)
    w("3) Tax X only: X*(1+r) + Fine  [exact]")
    w("-" * 88)
    for r, name in zip(rates, rate_names):
        hit_lam = hit_neg = 0
        for n in range(1, n_walk + 1):
            x, y = pts[n]
            X, Fine, _ = layers(x, y)
            taxed = X * (1 + r) + Fine
            C_lam = phi((BETA * x) % P, y)
            C_neg = phi(x, (-y) % P)
            if exact(taxed, C_lam):
                hit_lam += 1
            if exact(taxed, C_neg):
                hit_neg += 1
        w(f"  r={name:4s}: vs Phi(lam) {hit_lam}/{n_walk}  vs Phi(-P) {hit_neg}/{n_walk}")
    w("  GLV needs x |-> beta*x mod p, not multiply X by (1+r) in Q.")
    w()

    w("-" * 88)
    w("4) '10% of every dollar of X paid into Fine'  X*1.10  [exact]")
    w("-" * 88)
    hit = 0
    for n in range(1, n_walk + 1):
        x, y = pts[n]
        X, Fine, C = layers(x, y)
        food_plus_tax = X * Fraction(11, 10)
        if exact(food_plus_tax, C):
            hit += 1
    w(f"  X*1.10 == Phi(P)? {hit}/{n_walk}")
    w()

    # Deep digit check: 10% on C vs Phi(-P) — agree on first 75, disagree by 120
    w("-" * 88)
    w("5) 10% tax looks 'close' only because x-channel dominates shallow digits")
    w("-" * 88)
    shallow = deep = 0
    for n in range(1, n_walk + 1):
        x, y = pts[n]
        _, _, C = layers(x, y)
        taxed = C * Fraction(11, 10)
        C_neg = phi(x, (-y) % P)
        if digit_match(taxed, C_neg, 40):
            shallow += 1
        if digit_match(taxed, C_neg, 120):
            deep += 1
    w(f"  C*1.10 vs Phi(-P): match first 40 digits {shallow}/{n_walk}  first 120 {deep}/{n_walk}")
    w()

    w("-" * 88)
    w("6) Metaphor that fits")
    w("-" * 88)
    w("  Negation on Fine is REFLECT, not VAT: Fine -> 1/p - Fine")
    w("  Fixed % tax would need r = p/y - 2 (a different rate every point).")
    w("  GLV is modular *beta on x, not *(1+r) on the decimal X.")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Flat 10% sales tax on C / X / Fine does NOT give negation, GLV, or +G.")
    w("  Shallow digits can look similar (shared x/p); exact compare kills it.")
    w("  Closest 'rate' for neg is r*=p/y-2 — not a store-wide 10%.")
    w()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
