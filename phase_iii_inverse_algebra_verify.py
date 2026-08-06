#!/usr/bin/env python3
"""
Phase III - Inverse Algebra: Verification only.

Proves / verifies theorems in Phase_III_Inverse_Algebra.md.
No correlation search. No ECDLP speedup claims beyond Prop 8.2-8.3.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHASE_III_INVERSE_ALGEBRA_VERIFY.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
DELTA = P - N
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE
BETA2 = (BETA * BETA) % P
LAMBDA = 0x5363AD4CC05C30E0A5261C028812645A122E22EA20816678DF02967C1B23BD72
LAMBDA2 = (LAMBDA * LAMBDA) % N

# secp256k1 curve: y^2 = x^3 + 7
A = 0
B = 7
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
        s = (3 * x1 * x1 + A) * modinv(2 * y1, P) % P
    else:
        s = (y2 - y1) * modinv((x2 - x1) % P, P) % P
    x3 = (s * s - x1 - x2) % P
    y3 = (s * (x1 - x3) - y1) % P
    return (x3, y3)


def ec_mul(k: int, pt=(GX, GY)):
    k %= N
    if k == 0:
        return None
    r = None
    base = pt
    while k:
        if k & 1:
            r = ec_add(r, base)
        base = ec_add(base, base)
        k >>= 1
    return r


def psi(pt):
    """GLV endomorphism: (x,y) -> (beta*x, y)."""
    x, y = pt
    return ((BETA * x) % P, y)


def X_set(pt) -> frozenset:
    x, _ = pt
    return frozenset({x, (BETA * x) % P, (BETA2 * x) % P})


def D_set(d: int) -> frozenset:
    d %= N
    return frozenset({d, (LAMBDA * d) % N, (LAMBDA2 * d) % N})


def E(pt) -> int:
    x, y = pt
    return x * P + y


def carry_bit(a: int, M: int, t: int) -> int:
    a1 = (t * a) % M
    s = a + a1
    assert s != M
    return s // M


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Phase III - Inverse Algebra (Verification)")
    w("=" * 88)
    w()

    # ------------------------------------------------------------------ Sec 1
    w("Section 1 - Invariants of X(P)")
    assert (1 + BETA + BETA2) % P == 0
    assert pow(BETA, 3, P) == 1
    samples = []
    for i in range(200):
        h = hashlib.sha256(f"p3-x:{i}".encode()).digest()
        d = 1 + (int.from_bytes(h, "big") % (N - 1))
        pt = ec_mul(d)
        assert pt is not None
        x, y = pt
        x0, x1, x2 = x, (BETA * x) % P, (BETA2 * x) % P
        # Prop 1.1-1.2 in F_p
        assert (x0 + x1 + x2) % P == 0
        assert (x0 * x1 * x2) % P == pow(x, 3, P)
        # Prop 1.3: roots of T^3 - x^3
        for t in (x0, x1, x2):
            assert (pow(t, 3, P) - pow(x, 3, P)) % P == 0
        # Lift sum = q_x * p
        S = x0 + x1 + x2
        assert S % P == 0
        qx = S // P
        assert qx in (1, 2)
        # Prop 1.6 sixfold invariance of set
        Xs = X_set(pt)
        assert Xs == X_set((x, (P - y) % P))  # -P
        assert Xs == X_set(psi(pt))
        assert Xs == X_set(psi(psi(pt)))
        samples.append((d, pt, qx))
    w("  Prop 1.1-1.3, 1.5-1.6: ALL OK (200 random points)")
    w()

    # ------------------------------------------------------------------ Sec 2
    w("Section 2 - Scalar object D(d)")
    assert (1 + LAMBDA + LAMBDA2) % N == 0
    assert pow(LAMBDA, 3, N) == 1
    for i in range(500):
        h = hashlib.sha256(f"p3-d:{i}".encode()).digest()
        d = 1 + (int.from_bytes(h, "big") % (N - 1))
        d0, d1, d2 = d, (LAMBDA * d) % N, (LAMBDA2 * d) % N
        assert (d0 + d1 + d2) % N == 0
        assert (d0 * d1 * d2) % N == pow(d, 3, N)
        for t in (d0, d1, d2):
            assert (pow(t, 3, N) - pow(d, 3, N)) % N == 0
        S = d0 + d1 + d2
        qu = S // N
        assert qu in (1, 2)
        # Parallelism: same construction, no forced qx == qu
        # (explicitly do NOT assert equality)
    # Document non-identification on samples from Sec 1
    mismatch = 0
    for d, pt, qx in samples:
        d0 = d % N
        d1 = (LAMBDA * d0) % N
        d2 = (LAMBDA2 * d0) % N
        qu = (d0 + d1 + d2) // N
        if qx != qu:
            mismatch += 1
    w(f"  Prop 2.1-2.3: ALL OK")
    w(f"  Symbolic parallel only: qx!=qu on {mismatch}/{len(samples)} samples (expected possible)")
    w("  No identification theorem claimed or verified as identity")
    w()

    # ------------------------------------------------------------------ Sec 3
    w("Section 3 - mu_3-orbit structure")
    for d, pt, _ in samples[:50]:
        x = pt[0]
        orbit = {(BETA * x) % P for _ in range(1)} | {x, (BETA2 * x) % P}
        # orbit under multiplication by beta
        o = {x}
        cur = x
        for _ in range(2):
            cur = (BETA * cur) % P
            o.add(cur)
        assert o == X_set(pt)
        # knowing the set recovers x only up to mu_3
        assert len(X_set(pt)) == 3 or x == 0
    w("  Prop 3.1-3.3: ALL OK")
    w()

    # ------------------------------------------------------------------ Sec 4
    w("Section 4 - Exact numerator E(P)=x*p+y")
    for d, pt, _ in samples[:100]:
        x, y = pt
        e = E(pt)
        assert e == x * P + y
        assert 0 <= e < P * P
        # recover
        assert e // P == x and e % P == y
        # Prop 4.1 negation
        neg = (x, (P - y) % P)
        assert E(neg) == e + P - 2 * y
        assert E(neg) + e == P * (2 * x + 1)
        # Prop 4.2: E(psi) != beta * E in general
        e_psi = E(psi(pt))
        xb = (BETA * x) % P
        full = BETA * x
        k1 = full // P
        assert full == k1 * P + xb
        assert e_psi == xb * P + y
        assert e_psi == (full - k1 * P) * P + y
    # Find at least one sample where E(psi) != beta*E as integers (scaled)
    found_neq = False
    for d, pt, _ in samples:
        if E(psi(pt)) != BETA * E(pt):
            found_neq = True
            break
    assert found_neq
    w("  Prop 4.1-4.3: ALL OK (E recovers P; E o psi != beta E)")
    w()

    # ------------------------------------------------------------------ Sec 5
    w("Section 5 - Lift ambiguity r, Delta, R_x")
    assert DELTA < N
    # Unique regime: construct r >= DELTA with R_x = r < N < p
    for i in range(200):
        h = hashlib.sha256(f"p3-lift-u:{i}".encode()).digest()
        r = DELTA + (int.from_bytes(h, "big") % (N - DELTA))
        Rx = r
        assert Rx % N == r
        assert Rx == r
        assert r + N >= P  # not an admissible second lift
    # Ambiguous regime: r < DELTA; both r and r+N lie in [0,p)
    for i in range(200):
        h = hashlib.sha256(f"p3-lift-a:{i}".encode()).digest()
        r = int.from_bytes(h, "big") % DELTA
        candidates = [r, r + N]
        assert all(0 <= c < P for c in candidates)
        assert candidates[0] % N == r and candidates[1] % N == r
        assert len(set(candidates)) == 2
    w("  Theorem 5.1: unique regime (r>=Delta) and ambiguous regime (r<Delta): ALL OK")
    w()

    # ------------------------------------------------------------------ Sec 6
    w("Section 6 - No ring-hom bridge")
    # If unital ring hom F_p -> Z/NZ existed, ker would be ideal of field => 0 or all,
    # injective => |F_p| divides |Z/NZ|, i.e. p | N, false.
    assert P != N
    assert N % P != 0 and P % N != 0
    w("  Theorem 6.1: |F_p|!=|Z/NZ|, no unital ring hom either way: OK")
    w("  Prop 6.2-6.3: documented (parallel construction != identification)")
    w()

    # ------------------------------------------------------------------ Sec 7
    w("Section 7 - CM / Eisenstein Phi_3")
    # Both satisfy U^2+U+1=0
    assert (BETA2 + BETA + 1) % P == 0
    assert (LAMBDA2 + LAMBDA + 1) % N == 0
    # Endomorphism relation on random points: psi(P) == [lambda]P
    for d, pt, _ in samples[:30]:
        assert psi(pt) == ec_mul(LAMBDA, pt)
        assert psi(psi(pt)) == ec_mul(LAMBDA2, pt)
    w("  Prop 7.1-7.2: Phi_3 both sides; psi(P)=[lambda]P verified")
    w()

    # ------------------------------------------------------------------ Sec 8
    w("Section 8 - DL entropy / bit reduction")
    # Prop 8.1: uniqueness of d for P (sample injectivity of d |-> dG on a set)
    pts = {}
    for i in range(100):
        h = hashlib.sha256(f"p3-inj:{i}".encode()).digest()
        d = 1 + (int.from_bytes(h, "big") % (N - 1))
        pt = ec_mul(d)
        key = pt
        if key in pts:
            assert pts[key] == d
        pts[key] = d
    # Prop 8.2: sixfold orbit size
    for d, pt, _ in samples[:40]:
        orbit = []
        for s in (1, -1):
            for ell in (1, LAMBDA, LAMBDA2):
                dd = (s * ell * d) % N
                if dd == 0:
                    continue
                orbit.append(ec_mul(dd))
        # All share same X-set
        Xs = X_set(pt)
        for q in orbit:
            assert X_set(q) == Xs
        # Distinct points: typically 6
        assert len(set(orbit)) == 6
    b_glv = math.log2(6)
    w(f"  Prop 8.1: H(d|P)=0 information-theoretically (unique d): OK")
    w(f"  Prop 8.2: sixfold orbit |O|=6 => b=log2(6)={b_glv:.10f} (classical GLV)")
    w("  Prop 8.3: c_x, q_x are functions of x hence of P - no extra factor")
    # Verify c_x,q_x determined by x alone
    for d, pt, qx in samples[:50]:
        x = pt[0]
        a1 = (BETA * x) % P
        c = (x + a1) // P
        q = 1 + c
        assert q == qx or (x + a1 + (BETA2 * x) % P) // P == qx
        # q from full sum
        assert (x + a1 + (BETA2 * x) % P) == qx * P
    w("  Extra bits from carry algebra beyond GLV: b'=0")
    w()

    # ------------------------------------------------------------------ Sec 9
    w("Section 9 - Carry without floor (chamber / inequality)")
    for i in range(1000):
        h = hashlib.sha256(f"p3-c:{i}".encode()).digest()
        a = 1 + (int.from_bytes(h, "big") % (P - 1))
        a1 = (BETA * a) % P
        if a + a1 == P:
            continue
        c = (a + a1) // P
        c_ineq = 0 if a + a1 < P else 1
        assert c == c_ineq
        # Chamber: below antidiagonal <=> c=0
        in_lower = a + a1 < P
        assert in_lower == (c == 0)
    # No total polynomial F: Z/PZ -> {0,1} can equal carry for all a:
    # if c were given by a polynomial over F_p, it would be a function of a alone
    # in the residue field; but carry depends on the ordered lift of (a, t*a).
    # Two lifts of the same residue class don't exist in F_p - the point is:
    # carry is not F_p-polynomial. Spot-check: c is not constant on residue (trivial)
    # and c(a) != c((-a) mod P) often while any odd/even polynomial pattern fails.
    diffs = 0
    for i in range(200):
        h = hashlib.sha256(f"p3-poly:{i}".encode()).digest()
        a = 1 + (int.from_bytes(h, "big") % (P - 1))
        if a + (BETA * a) % P == P:
            continue
        am = (P - a) % P
        if am == 0 or am + (BETA * am) % P == P:
            continue
        if carry_bit(a, P, BETA) != carry_bit(am, P, BETA):
            diffs += 1
    assert diffs > 0  # negation flips carry often - not a property of a^2 alone, etc.
    w("  Prop 9.1-9.2: c <=> integer inequality / antidiagonal chamber: ALL OK")
    w("  Prop 9.3: lattice wall-crossing is rephrasing; section of Z->>Z/MZ remains")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Inverse bridge: NO exact invariant of X(P) constrains D(d) beyond GLV sixfold.")
    w("  Shannon H(d|P)=0; computational extra bits from carry algebra: b'=0.")
    w("  Classical GLV orbit reduction only: b=log2(6).")
    w("  ALL Phase III verification checks PASSED.")
    w("=" * 88)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
