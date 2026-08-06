#!/usr/bin/env python3
"""
'Taxation' probe = truncation / skim at the x/p | Fine boundary.

Tax_k(C)  := truncate fractional digits of C to k places (ROUND_DOWN)
Residual  := C - Tax_k(C)   # skimmed Fine-ish tail

Ask:
  - For which k does Tax_k(Phi) == Tax_k(x/p)?  (clean x-channel)
  - Does residual encode y / parity?
  - Tax on Phi+ vs Phi- / Phi(-P)
"""
from __future__ import annotations

from decimal import Decimal, getcontext, ROUND_DOWN
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_TAXATION_TRUNC.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
getcontext().prec = 400
getcontext().rounding = ROUND_DOWN
G = SECP256k1.generator


def to_dec(f: Fraction) -> Decimal:
    return Decimal(f.numerator) / Decimal(f.denominator)


def tax(d: Decimal, k: int) -> Decimal:
    """Truncate (tax away) digits after place k."""
    return d.quantize(Decimal(1).scaleb(-k), rounding=ROUND_DOWN)


def frac_str(d: Decimal, k: int) -> str:
    t = tax(d, k)
    s = format(t, "f")
    return s.split(".", 1)[1][:k] if "." in s else "0" * k


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Taxation = truncation at x-channel / Fine boundary")
    w("=" * 88)
    w("  Tax_k(C) = first k fractional digits of C (truncate)")
    w("  Skim     = C - Tax_k(C)  (deep tail)")
    w()

    ks = list(range(70, 82))
    n_walk = 256

    w("-" * 88)
    w(f"1) When does Tax_k(Phi) == Tax_k(x/p)?  (walk 1..{n_walk})")
    w("-" * 88)
    for k in ks:
        hit = 0
        for n in range(1, n_walk + 1):
            pt = n * G
            x, y = int(pt.x()), int(pt.y())
            Xp = Fraction(x, P)
            Phi = Xp + Fraction(y, P * P)
            if frac_str(to_dec(Phi), k) == frac_str(to_dec(Xp), k):
                hit += 1
        w(f"  k={k:2d}:  Tax_k(Phi)==Tax_k(x/p)  {hit}/{n_walk}  ({100*hit/n_walk:.1f}%)")
    w()

    w("-" * 88)
    w("2) Tax on Phi+ vs Phi- vs Phi(-P) — shared taxed body?")
    w("-" * 88)
    for k in (74, 75, 76, 77, 78):
        same_pm = same_true = 0
        for n in range(1, n_walk + 1):
            pt = n * G
            x, y = int(pt.x()), int(pt.y())
            yn = (-y) % P
            Xp = Fraction(x, P)
            Fine = Fraction(y, P * P)
            Pp = Xp + Fine
            Pm = Xp - Fine
            Pn = Fraction(x * P + yn, P * P)
            if frac_str(to_dec(Pp), k) == frac_str(to_dec(Pm), k):
                same_pm += 1
            if frac_str(to_dec(Pp), k) == frac_str(to_dec(Pn), k):
                same_true += 1
        w(
            f"  k={k}: Tax(Phi+)==Tax(Phi-) {same_pm}/{n_walk}  "
            f"Tax(Phi)==Tax(Phi(-P)) {same_true}/{n_walk}"
        )
    w()

    w("-" * 88)
    w("3) Can the skimmed residual recover parity / y?")
    w("-" * 88)
    w("  After Tax_77: residual R = Phi - Tax_77(Phi)")
    w("  Test: sign(R) or magnitude vs y parity — weak probes only")
    parity_from_sign = 0
    # Better: recover x from Tax_k(x/p) then recover y from curve+parity of Fine
    recover_via_tax_body = {k: 0 for k in (75, 76, 77, 78)}
    for n in range(1, n_walk + 1):
        pt = n * G
        x, y = int(pt.x()), int(pt.y())
        Phi = Fraction(x * P + y, P * P)
        Xp = Fraction(x, P)
        R = to_dec(Phi) - tax(to_dec(Phi), 77)
        # Fine is always > 0 for y>0, so R after truncate is not a clean Fine
        # parity probe: nonsense on R sign (always >=0 for truncate residual of positive)
        if R >= 0 and (y % 2 == 0 or y % 2 == 1):
            parity_from_sign += 1  # always true — shows sign useless

        for k in recover_via_tax_body:
            body = frac_str(to_dec(Xp), k)  # tax pure x channel
            # reconstruct x candidate from body
            b = Decimal("0." + body)
            x0 = int(b * Decimal(P))
            ok = False
            for cand in (x0 - 1, x0, x0 + 1, x0 + 2):
                if 0 <= cand < P:
                    d = (Decimal(cand) / Decimal(P)).quantize(
                        Decimal(1).scaleb(-k), rounding=ROUND_DOWN
                    )
                    if format(d, "f").split(".", 1)[1][:k] == body and cand == x:
                        ok = True
                        break
            if ok:
                # with known x + true parity, y recovers; tax body alone has no parity
                recover_via_tax_body[k] += 1

    w(f"  residual sign encodes parity? useless (always R>=0): {parity_from_sign}/{n_walk}")
    for k, v in recover_via_tax_body.items():
        w(f"  Tax_k(x/p) digits recover integer x (near candidates): k={k} -> {v}/{n_walk}")
    w("  Skim alone does not give y; need 02/03 (or Fine) as separate tax stamp.")
    w()

    w("-" * 88)
    w("4) Practical 'tax schedule'")
    w("-" * 88)
    w("  Tax body  (keep):  first ~75 digits of Phi  ~  shared x-channel")
    w("                      safer: Tax(x/p) directly, not Tax(Phi)")
    w("  Tax stamp (keep):  02/03 parity  OR  full Fine = y/p^2")
    w("  Tax discard:       trying to read y from Phi digit 78 alone under float")
    w("  Best levy:         pack = Tax_78(x/p) + '.' + parity   (already tested)")
    w()

    # show one sample
    pt = 1 * G
    x, y = int(pt.x()), int(pt.y())
    Phi = to_dec(Fraction(x * P + y, P * P))
    Xp = to_dec(Fraction(x, P))
    w("-" * 88)
    w("5) Sample n=1")
    w("-" * 88)
    for k in (74, 75, 76, 77, 78):
        w(f"  Tax_{k}(Phi)= 0.{frac_str(Phi, k)}")
        w(f"  Tax_{k}(x/p)= 0.{frac_str(Xp, k)}  match={frac_str(Phi,k)==frac_str(Xp,k)}")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Yes: a useful 'tax' is truncation of the x-channel.")
    w("  Tax_k(Phi)~Tax_k(x/p) is reliable for k<=75 (~99%), weakens by k=77-78.")
    w("  Do not tax Phi for the body — tax x/p (or compressed x) to avoid Fine carry.")
    w("  Second levy: parity stamp 02/03 (or keep Fine). That is the y-branch tax.")
    w("  If you meant transformation (not truncation): T_neg / T_lambda already exist.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
