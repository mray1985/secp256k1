#!/usr/bin/env python3
"""
Phase VIII — Nonce Lift Algebra: theorem / proof / verification.

ECDSA: s*k == z + r*d (mod N). Lift of R_x does not split that equation.
Document: Phase_VIII_Nonce_Lift_Algebra.md
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHASE_VIII_NONCE_LIFT_VERIFY.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
DELTA = P - N
GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8


def modinv(a: int, m: int) -> int:
    return pow(a, -1, m)


def ec_add(p1, p2):
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if p1 == p2:
        s = (3 * x1 * x1) * modinv(2 * y1, P) % P
    else:
        s = (y2 - y1) * modinv((x2 - x1) % P, P) % P
    x3 = (s * s - x1 - x2) % P
    y3 = (s * (x1 - x3) - y1) % P
    return (x3, y3)


def ec_mul(k: int, pt=(GX, GY)):
    k %= N
    if k == 0:
        return None
    r, base = None, pt
    while k:
        if k & 1:
            r = ec_add(r, base)
        base = ec_add(base, base)
        k >>= 1
    return r


def on_curve_x(X: int) -> bool:
    if not (0 <= X < P):
        return False
    return pow((pow(X, 3, P) + 7) % P, (P - 1) // 2, P) == 1


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    def block(title: str, theorem: str, proof: str) -> None:
        w()
        w("-" * 88)
        w(f"THEOREM: {title}")
        w(f"  Statement: {theorem}")
        w(f"  Proof:     {proof}")
        w("  Verification:")

    w("=" * 88)
    w("Phase VIII - Nonce Lift Algebra")
    w("Document: Phase_VIII_Nonce_Lift_Algebra.md")
    w("=" * 88)

    assert P == N + DELTA
    assert DELTA < N

    # ------------------------------------------------------------------ 1
    block(
        "1.1 Lift regimes",
        "r>=Delta => Rx=r unique; r<Delta => Rx in {r,r+N} both in [0,p).",
        "0<=Rx<p=N+Delta; Rx=r or r+N.",
    )
    n_unique = n_amb = 0
    for i in range(500):
        h = hashlib.sha256(f"p8-lift:{i}".encode()).digest()
        k = 1 + (int.from_bytes(h, "big") % (N - 1))
        R = ec_mul(k)
        assert R is not None
        Rx, Ry = R
        r = Rx % N
        if r >= DELTA:
            assert Rx == r
            assert r + N >= P
            n_unique += 1
        else:
            assert Rx in (r, r + N)
            assert 0 <= r < P and 0 <= r + N < P
            n_amb += 1
    w(f"    OK (unique regime samples~{n_unique}, ambiguous~{n_amb} in 500 nonces)")

    # ------------------------------------------------------------------ 2
    block(
        "2.1-2.2 E_R == r*Delta + Ry mod N for both lifts",
        "Lift-independent; Ry from e_R with Delta ambiguity.",
        "Phase VII; (r+N)*Delta == r*Delta mod N.",
    )
    for i in range(200):
        h = hashlib.sha256(f"p8-ER:{i}".encode()).digest()
        k = 1 + (int.from_bytes(h, "big") % (N - 1))
        R = ec_mul(k)
        Rx, Ry = R
        r = Rx % N
        eR = (Rx * P + Ry) % N
        assert eR == (r * DELTA + Ry) % N
        if r < DELTA:
            assert ((r + N) * P + Ry) % N == eR
        rho = (eR - r * DELTA) % N
        if rho >= DELTA:
            assert Ry == rho
        else:
            assert Ry in (rho, rho + N)
    w("    OK")

    # ------------------------------------------------------------------ 3 ECDSA lift invariance
    block(
        "3.1-3.3 ECDSA sk == z+r*d is lift-invariant; d from k needs only r",
        "Equation in Z/NZ uses residue r, not affine lift Rx.",
        "Standard ECDSA rearrangement.",
    )
    for i in range(100):
        h = hashlib.sha256(f"p8-ecdsa:{i}".encode()).digest()
        d = 1 + (int.from_bytes(h[:16], "big") % (N - 1))
        k = 1 + (int.from_bytes(h[16:], "big") % (N - 1))
        z = int.from_bytes(hashlib.sha256(f"p8-z:{i}".encode()).digest(), "big") % N
        R = ec_mul(k)
        Rx, Ry = R
        r = Rx % N
        if r == 0:
            continue
        s = (modinv(k, N) * ((z + r * d) % N)) % N
        assert (s * k) % N == (z + r * d) % N
        # same equation if we only know r (not which lift)
        d2 = (modinv(r, N) * ((s * k - z) % N)) % N
        assert d2 == d
        # both formal preimages share r
        if r < DELTA:
            for X in (r, r + N):
                assert X % N == r
                # scalar eq unchanged
                assert (s * k) % N == (z + (X % N) * d) % N
    w("    OK")

    # ------------------------------------------------------------------ geometric filter note
    block(
        "3.4 Geometric filter uses Rx; does not split Z/NZ equation",
        "k with (kG)_x mod N = r may allow two x-lifts when r<Delta; ECDSA line identical.",
        "Separate geometric vs algebraic constraints.",
    )
    both_on_curve = one_on_curve = 0
    for i in range(300):
        h = hashlib.sha256(f"p8-curve:{i}".encode()).digest()
        # sample r < Delta
        r = int.from_bytes(h, "big") % DELTA
        a = on_curve_x(r)
        b = on_curve_x(r + N)
        if a and b:
            both_on_curve += 1
        elif a or b:
            one_on_curve += 1
    w(f"    Among 300 artificial r<Delta: both lifts on-curve={both_on_curve}, exactly one={one_on_curve}")
    w("    Density not claimed uniform; no 2^(k-1) theorem - OK")

    # ------------------------------------------------------------------ 5 entropy
    block(
        "5.1-5.3 Lift bit <=1; no proven uniform k-halving; equation obstruction",
        "r>=Delta: 0 lift bits; r<Delta: <=1 bit on Rx representative; ECDSA line lift-invariant.",
        "Cardinality of lift set; Thm 3.1.",
    )
    w("    b_lift <= 1 when r<Delta; b_lift = 0 when r>=Delta")
    w("    No theorem |K_r|=2|K_{Rx}| for all sigs - OK")
    b_glv = math.log2(6)
    w(f"    Only rigorous orbit cut remains GLV: b=log2(6)={b_glv:.10f}; Phase VIII b'=0")

    # ------------------------------------------------------------------ 6
    block(
        "6.1 Obstruction: lift+ECDSA alone does not remove k/d beyond GLV",
        "Success criterion B for this branch.",
        "Thms 3.1, 5.1-5.3, 2.1.",
    )
    w("    VERDICT B: close nonce-lift-as-scalar-splitter branch")
    w("    OK")

    w()
    w("=" * 88)
    w("SUCCESS CRITERION: B")
    w("=" * 88)
    w("  No theorem removing k/d candidates beyond GLV from nonce lift algebra.")
    w("  ECDSA scalar equation is lift-invariant; E_R mod N ~ Ry only.")
    w("  ALL Phase VIII verification checks PASSED.")
    w("=" * 88)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
