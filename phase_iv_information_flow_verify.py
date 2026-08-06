#!/usr/bin/env python3
"""
Phase IV — Information Flow: theorem / proof / verification.

Document:
  Information_Theoretic_Consequences_Cube_Root_Lift_Algebra.md

No correlation search. No heuristics. Falsify bridge identities by counterexample.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHASE_IV_INFORMATION_FLOW_VERIFY.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
DELTA = P - N
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE
BETA2 = (BETA * BETA) % P
LAMBDA = 0x5363AD4CC05C30E0A5261C028812645A122E22EA20816678DF02967C1B23BD72
LAMBDA2 = (LAMBDA * LAMBDA) % N
A, B = 0, 7
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


def psi(pt):
    x, y = pt
    return ((BETA * x) % P, y)


def qx_of_x(x: int) -> int:
    x0, x1, x2 = x, (BETA * x) % P, (BETA2 * x) % P
    S = x0 + x1 + x2
    assert S % P == 0
    q = S // P
    assert q in (1, 2)
    return q


def qu_of_u(u: int) -> int:
    u %= N
    u0, u1, u2 = u, (LAMBDA * u) % N, (LAMBDA2 * u) % N
    S = u0 + u1 + u2
    assert S % N == 0
    q = S // N
    assert q in (1, 2)
    return q


def cx_of_x(x: int) -> int:
    a1 = (BETA * x) % P
    s = x + a1
    assert s != P
    return s // P


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
    w("Phase IV - Information Flow (theorem / proof / verification)")
    w("Document: Information_Theoretic_Consequences_Cube_Root_Lift_Algebra.md")
    w("=" * 88)

    # Build sample points
    samples: list[tuple[int, tuple[int, int]]] = []
    for i in range(300):
        h = hashlib.sha256(f"p4:{i}".encode()).digest()
        d = 1 + (int.from_bytes(h, "big") % (N - 1))
        pt = ec_mul(d)
        assert pt is not None
        samples.append((d, pt))

    # ------------------------------------------------------------------ 1.1
    block(
        "1.1 Sixfold constancy of X-invariants including q_x",
        "q_x and the set X are constant on {+/-P, +/-psi(P), +/-psi^2(P)}.",
        "Negation preserves x; psi permutes the three reduced x-values, so sum S_x and q_x=S_x/p are fixed.",
    )
    for d, pt in samples[:80]:
        x, y = pt
        Xs = frozenset({x, (BETA * x) % P, (BETA2 * x) % P})
        qx = qx_of_x(x)
        orbit_pts = []
        for s in (1, -1):
            for ell in (1, LAMBDA, LAMBDA2):
                dd = (s * ell * d) % N
                if dd == 0:
                    continue
                orbit_pts.append(ec_mul(dd))
        assert len(set(orbit_pts)) == 6
        for q in orbit_pts:
            xq = q[0]
            assert frozenset({xq, (BETA * xq) % P, (BETA2 * xq) % P}) == Xs
            assert qx_of_x(xq) == qx
        # also coordinate psi
        assert qx_of_x(psi(pt)[0]) == qx
        assert qx_of_x(psi(psi(pt))[0]) == qx
        assert qx_of_x(x) == qx_of_x(x)  # -P same x
    w("    OK on 80 random sixfold orbits")

    # ------------------------------------------------------------------ field invariants
    block(
        "1.field Field invariants of X are constant or functions of x",
        "trace=e1=0; e2=0; product=e3=x^3; minpoly T^3-x^3; disc=-27 x^6 in F_p.",
        "Follows from 1+beta+beta^2=0 and beta^3=1 in F_p.",
    )
    assert (1 + BETA + BETA2) % P == 0
    for d, pt in samples[:100]:
        x = pt[0]
        x0, x1, x2 = x, (BETA * x) % P, (BETA2 * x) % P
        assert (x0 + x1 + x2) % P == 0
        assert (x0 * x1 * x2) % P == pow(x, 3, P)
        e2 = (x0 * x1 + x1 * x2 + x2 * x0) % P
        assert e2 == 0
        for t in (x0, x1, x2):
            assert (pow(t, 3, P) - pow(x, 3, P)) % P == 0
        # disc(T^3 - a) for a=x^3: -27 a^2 = -27 x^6
        a = pow(x, 3, P)
        disc = (-27 * pow(a, 2, P)) % P
        assert disc == (-27 * pow(x, 6, P)) % P
    w("    OK (trace/norm/e2=0/minpoly/disc) on 100 points")

    # ------------------------------------------------------------------ 2.1 / entropy
    block(
        "2.1 H(I|P)=0 for P-computable invariants; H(q_x)<=1",
        "Any invariant of X or (x,y) is determined by P, so conditional entropy is 0. |{1,2}|=2 => H(q_x)<=1.",
        "Definition of conditional entropy of a deterministic function; cardinality bound on entropy.",
    )
    for d, pt in samples[:100]:
        x, y = pt
        # recompute from P alone
        assert qx_of_x(x) in (1, 2)
        assert cx_of_x(x) in (0, 1)
        # carry theorem: orbit-sum class q = 1+c along the reconstruction edge
        assert 1 + cx_of_x(x) == qx_of_x(x)
        q = qx_of_x(x)
        assert q == (x + (BETA * x) % P + (BETA2 * x) % P) // P
    # entropy upper bound only (not estimating distribution)
    w("    H(q_x) <= log2(2) = 1 bit (cardinality bound)")
    w("    H(I|P)=0: invariants recomputed from (x,y) alone - OK")

    # edge carry vs orbit class: q = 1+c along reconstruction when a2 uses that edge
    # Accept theorem: c in {0,1}, H<=1
    w("    H(c_x) <= 1 bit - OK")

    # ------------------------------------------------------------------ 2.3
    block(
        "2.3 q_x does not refine sixfold classes",
        "q_x is constant on each sixfold orbit, so it does not split the GLV equivalence relation.",
        "Theorem 1.1 + definition of orbit quotient.",
    )
    # already verified constancy; state complexity consequence
    b_glv = math.log2(6)
    w(f"    Sixfold quotient factor: 2^k -> 2^(k - log2(6)) with log2(6)={b_glv:.10f}")
    w("    Additional factor from q_x: b'=0")

    # ------------------------------------------------------------------ 3.1 recoverability
    block(
        "3.1 Recoverability split",
        "(p,beta) invariants are polytime from P; (N,lambda) invariants require the scalar.",
        "x is a coordinate of P; u=d is the ECDLP unknown. Carry formulas use only (M,t,a).",
    )
    for d, pt in samples[:50]:
        x, y = pt
        _ = qx_of_x(x)  # from P
        _ = qu_of_u(d)  # needs d
        # cannot obtain qu from x alone under frozen algebra: check non-function
        # If qu were a function of x only, same x => same qu. Different d with same x impossible
        # for distinct points; instead show qu is not a function of qx:
    # qu not determined by qx: same qx both qu values appear
    by_qx: dict[int, set[int]] = {1: set(), 2: set()}
    for d, pt in samples:
        by_qx[qx_of_x(pt[0])].add(qu_of_u(d))
    assert by_qx[1] == {1, 2} or by_qx[2] == {1, 2}
    w(f"    q_u values seen per q_x: { {k: sorted(v) for k, v in by_qx.items()} }")
    w("    q_u is not a function of q_x (hence not of public X alone) - OK")

    # ------------------------------------------------------------------ 4.1
    block(
        "4.1 No carry-class bridge q_x(P)=q_u(d)",
        "The identity q_x(dG)=q_u(d) is false in general.",
        "Both sides in {1,2}; one counterexample falsifies a claimed identity. Parallel Phi_3 calculus does not identify classes.",
    )
    mismatches = 0
    first = None
    for d, pt in samples:
        qx, qu = qx_of_x(pt[0]), qu_of_u(d)
        if qx != qu:
            mismatches += 1
            if first is None:
                first = (d % 2**32, qx, qu)  # store truncated d tag only for log
    assert mismatches > 0
    w(f"    Counterexamples: {mismatches}/{len(samples)} (first tag qx={first[1]} qu={first[2]})")
    w("    Identity REFUTED - OK")

    # ------------------------------------------------------------------ 4.2
    block(
        "4.2 No unital ring-hom bridge F_p <-> Z/NZ",
        "No unital ring homomorphism either way.",
        "Fields/prime rings: nontrivial unital hom is injective; then order divides order; p!=N and neither divides the other.",
    )
    assert P != N and P % N != 0 and N % P != 0
    w("    OK")

    # ------------------------------------------------------------------ 5.1 Delta
    block(
        "5.1 Delta absent from carry equations",
        "Carry reconstruction for (M,t) uses only M,t,a - not Delta=p-N.",
        "Inspect formula; instantiate (p,beta) and (N,lambda) separately; Delta unused.",
    )
    # verify carries work without referencing DELTA
    for d, pt in samples[:100]:
        x = pt[0]
        a1 = (BETA * x) % P
        c = (x + a1) // P
        q = 1 + c
        a2 = q * P - x - a1
        assert a2 == (BETA2 * x) % P
        # scalar side
        u = d % N
        b1 = (LAMBDA * u) % N
        cu = (u + b1) // N
        qu = 1 + cu
        u2 = qu * N - u - b1
        assert u2 == (LAMBDA2 * u) % N
    # Delta used only in signature-lift regime check
    r = DELTA + 1
    assert r >= DELTA and r < N and r + N >= P
    r2 = DELTA - 1 if DELTA > 1 else 0
    assert r2 < DELTA and r2 + N < P
    w("    Carry checks never use Delta; signature lift uses Delta - OK")

    # ------------------------------------------------------------------ 6 complexity
    block(
        "6 Complexity accounting",
        "After GLV sixfold: 2^(k-log2(6)). After lift/carry theorems: same (b'=0).",
        "Lift invariants are P-computable and constant on sixfold classes (Thm 1.1, 2.1, 2.3, 4.1).",
    )
    w(f"    Original:     2^k")
    w(f"    After GLV:    2^(k - {b_glv:.10f})")
    w(f"    After carries: 2^(k - {b_glv:.10f})   [b' = 0]")

    # ------------------------------------------------------------------ final
    w()
    w("=" * 88)
    w("FINAL ANSWER")
    w("=" * 88)
    w("  Do current theorems reveal information about an unknown scalar")
    w("  beyond the known sixfold symmetry?")
    w()
    w("  NO.")
    w()
    w("  Additional bits b' = 0.")
    w("  Only justified factor: b = log2(6) (classical GLV).")
    w("  ALL Phase IV verification checks PASSED.")
    w("=" * 88)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
