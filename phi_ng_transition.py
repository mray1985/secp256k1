#!/usr/bin/env python3
"""
Study Phi(nG) -> Phi((n+1)G) for n=1..100.

Phi(P) = (x*p + y)/p^2 = (x + y/p)/p

This is the actual repeated-addition sequence, not a fixed-C counter.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_NG_TRANSITION.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = SECP256k1.generator

# User-supplied spot checks (160 frac digits)
USER = {
    1: (
        55066263022277343669578718895168534326250603453777594175500187360389116729240,
        32670510020758816978083085130507043184471273380659243275938904335757337482424,
        "0.4755615291595515724707093458846219361009854858291324365504648581557686374849482070998285066314418988320192568208754286945733425390948749851222826364302583283178",
    ),
    2: (
        89565891926547004231252920425935692360644145829622209833684329913297188986597,
        12158399299693830322967808612713398636155367887041628176798871954788371653930,
        "0.7735061394650326247817956281830778319668277346998022724783426266591146909815788034255293324952337856366565521696270506134426907334005575102464176062875237611291",
    ),
    100: (
        107303582290733097924842193972465022053148211775194373671539518313500194639752,
        103795966108782717446806684023742168462365449272639790795591544606836007446638,
        "0.9266918232282182948283197762339936574596911858238559608298982825007786029331726034870150265160833177974942380354651120009181183730018418303204115902991553124406",
    ),
}


def phi_xy(x: int, y: int) -> Fraction:
    return Fraction(x * P + y, P * P)


def frac_dec(f: Fraction, places: int) -> str:
    whole = f.numerator // f.denominator
    rem = f.numerator % f.denominator
    d = f.denominator
    digits = []
    for _ in range(places):
        rem *= 10
        digits.append(str(rem // d))
        rem %= d
    if whole == 0:
        return "0." + "".join(digits)
    return f"{whole}." + "".join(digits)


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Phi(nG) transitions  n=1..100   Phi=(x*p+y)/p^2")
    w("=" * 88)
    w(f"  p bits={P.bit_length()}  N bits={N.bit_length()}")
    w("  Sequence: P_{n+1} = P_n + G  (actual EC); C_n = Phi(P_n) changes with the point.")
    w()

    # Build sequence
    pts: list[tuple[int, int, Fraction]] = []
    pt = G
    for n in range(1, 101):
        x, y = int(pt.x()), int(pt.y())
        C = phi_xy(x, y)
        pts.append((x, y, C))
        pt = pt + G

    # Verify user spot checks
    w("-" * 88)
    w("User table spot-check (x,y,Phi 160 digits)")
    w("-" * 88)
    for n, (ux, uy, uphi) in USER.items():
        x, y, C = pts[n - 1]
        got = frac_dec(C, 160)
        w(
            f"  {n}G  x_ok={x==ux} y_ok={y==uy} Phi_ok={got==uphi}"
        )
        if got != uphi:
            for i, (a, b) in enumerate(zip(got, uphi)):
                if a != b:
                    w(f"       first Phi diff at char {i}")
                    break
    w()

    # Transitions C_n -> C_{n+1}
    w("-" * 88)
    w("Transformation C_n -> C_{n+1}  (99 steps)")
    w("-" * 88)

    deltas = []
    signs = Counter()
    for n in range(1, 100):
        C0 = pts[n - 1][2]
        C1 = pts[n][2]
        d = C1 - C0
        deltas.append(d)
        signs["+" if d > 0 else ("0" if d == 0 else "-")] += 1

    uniq = len(set(deltas))
    w(f"  unique Delta_C = C_{'{n+1}'} - C_n : {uniq} / {len(deltas)}")
    w(f"  sign counts: {dict(signs)}")
    w(f"  constant step? {uniq == 1}")
    w(f"  equals 1/p ? {all(d == Fraction(1, P) for d in deltas)}")
    w()

    # Magnitude in float for readability only
    mags = [float(abs(d)) for d in deltas]
    w(f"  |Delta_C| min={min(mags):.6e}  max={max(mags):.6e}  mean={sum(mags)/len(mags):.6e}")
    w()

    # Digit agreement of Phi decimals between n and n+1 (not a predictor; diagnostic)
    agree = []
    for n in range(1, 100):
        s0 = frac_dec(pts[n - 1][2], 160)
        s1 = frac_dec(pts[n][2], 160)
        k = 0
        for a, b in zip(s0[2:], s1[2:]):  # skip '0.'
            if a != b:
                break
            k += 1
        agree.append(k)
    w(f"  leading digit agree C_n vs C_{'{n+1}'} (of 160):")
    w(f"    min={min(agree)} max={max(agree)} mean={sum(agree)/len(agree):.2f}")
    w()

    # Can Delta_C be written as rational with small denom related to p?
    # Delta = C1-C0 = ((x1-x0)p + (y1-y0))/p^2
    w("-" * 88)
    w("Exact Delta form: ((x'-x)p + (y'-y))/p^2")
    w("-" * 88)
    denoms = Counter()
    for n in range(1, 100):
        x0, y0, _ = pts[n - 1]
        x1, y1, _ = pts[n]
        num = (x1 - x0) * P + (y1 - y0)
        d = Fraction(num, P * P)
        assert d == deltas[n - 1]
        denoms[d.denominator] += 1
    w(f"  reduced denominator of Delta_C: {dict(denoms.most_common(5))} ...")
    w(f"  always denom | p^2 ? {all( (P*P) % d.denominator == 0 for d in deltas)}")
    w()

    # Falsify fixed-C counter on this sequence
    C_fixed = pts[0][2]
    taut_hits = sum(
        1
        for n in range(1, 101)
        if pts[n - 1][2] == (Fraction(n) + C_fixed) / P
    )
    w("-" * 88)
    w("Falsify fixed-fingerprint counter on this walk")
    w("-" * 88)
    w(f"  hits of Phi(nG) == (n + Phi(G))/p : {taut_hits}/100")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  User x,y,Phi table matches EC nG (spot-checked).")
    w("  Phi changes with every addition; Delta_C is not constant and not 1/p.")
    w("  A decimal-side predictor must map C_n -> C_{n+1} without recomputing (n+1)G.")
    w("  No such reusable Delta found in n=1..100.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    w()
    w(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
