#!/usr/bin/env python3
"""
Phase VII — Packed-E bridge or obstruction.

theorem / proof / verification.
Document: Phase_VII_Packed_E_Bridge_or_Obstruction.md
Frozen prior phases: do not reopen.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHASE_VII_PACKED_E_VERIFY.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
DELTA = P - N
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE
BETA2 = (BETA * BETA) % P
LAMBDA = 0x5363AD4CC05C30E0A5261C028812645A122E22EA20816678DF02967C1B23BD72
LAMBDA2 = (LAMBDA * LAMBDA) % N
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


def E_of(pt) -> int:
    x, y = pt
    return x * P + y


def e_of(pt) -> int:
    return E_of(pt) % N


def qx_of_x(x: int) -> int:
    S = x + (BETA * x) % P + (BETA2 * x) % P
    assert S % P == 0
    q = S // P
    assert q in (1, 2)
    return q


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
    w("Phase VII - Packed-E bridge or obstruction")
    w("Document: Phase_VII_Packed_E_Bridge_or_Obstruction.md")
    w("=" * 88)

    assert P == N + DELTA

    samples = []
    for i in range(200):
        h = hashlib.sha256(f"p7:{i}".encode()).digest()
        d = 1 + (int.from_bytes(h, "big") % (N - 1))
        pt = ec_mul(d)
        assert pt is not None
        samples.append((d, pt))

    # ------------------------------------------------------------------ A
    block(
        "A.1-A.4 e formulas",
        "e=x*Delta+y; e(-P)=e+Delta-2y; e(psi)=x1*Delta+y; e(psi2)=x2*Delta+y (mod N).",
        "E=xp+y; p=N+Delta; psi fixes y and multiplies x by beta mod p.",
    )
    for _, pt in samples[:120]:
        x, y = pt
        e0 = e_of(pt)
        assert e0 == (x * DELTA + y) % N

        neg = (x, (P - y) % P)
        assert e_of(neg) == (e0 + DELTA - 2 * y) % N
        assert e_of(neg) == (x * DELTA + DELTA - y) % N

        p1, p2 = psi(pt), psi(psi(pt))
        x1, x2 = (BETA * x) % P, (BETA2 * x) % P
        assert e_of(p1) == (x1 * DELTA + y) % N
        assert e_of(p2) == (x2 * DELTA + y) % N
    w("    OK")

    # ------------------------------------------------------------------ B
    block(
        "B.1 Orbit sum mod N",
        "E0+E1+E2 == q_x*Delta^2 + 3y (mod N).",
        "E0+E1+E2=q_x p^2+3y and p^2 == Delta^2 (mod N).",
    )
    assert (P * P) % N == (DELTA * DELTA) % N
    for _, pt in samples[:120]:
        x, y = pt
        x0, x1, x2 = x, (BETA * x) % P, (BETA2 * x) % P
        E0, E1, E2 = x0 * P + y, x1 * P + y, x2 * P + y
        qx = qx_of_x(x)
        assert (E0 + E1 + E2) % N == (qx * (DELTA * DELTA) + 3 * y) % N
        # mu3-half constancy of Se
        Se = (E0 + E1 + E2) % N
        assert (E_of(psi(pt)) + E_of(psi(psi(pt))) + E0) % N == Se
        # sign sensitivity of Se
        yn = (P - y) % P
        Se_neg = (qx * (DELTA * DELTA) + 3 * yn) % N
        assert (3 * yn) % N == (3 * DELTA - 3 * y) % N
        if (3 * y) % N != (3 * yn) % N:
            assert Se != Se_neg
        # Se_neg matches packed sum for -P orbit
        En0 = x0 * P + yn
        En1 = x1 * P + yn
        En2 = x2 * P + yn
        assert (En0 + En1 + En2) % N == Se_neg
    w("    OK (identity + mu3 constancy + sign sensitivity)")

    # ------------------------------------------------------------------ C
    block(
        "C Negation pair does not refine sixfold",
        "e(-P) determined by e(P),y,Delta; P and -P same GLV class.",
        "Phase VI formula + definition of ~_GLV.",
    )
    for d, pt in samples[:60]:
        neg = (pt[0], (P - pt[1]) % P)
        assert e_of(neg) == (e_of(pt) + DELTA - 2 * pt[1]) % N
        # -d maps to -P
        assert ec_mul((-d) % N) == neg
    w("    OK")

    # ------------------------------------------------------------------ D
    block(
        "D Differences Ei-Ej == (xi-xj)*Delta mod N",
        "Set of differences is function of unordered X; ordered diffs lambda-sensitive.",
        "Ei-Ej=(xi-xj)*p and p==Delta mod N.",
    )
    for _, pt in samples[:100]:
        x, y = pt
        xs = [x, (BETA * x) % P, (BETA2 * x) % P]
        Es = [xj * P + y for xj in xs]
        d01 = (Es[1] - Es[0]) % N
        d12 = (Es[2] - Es[1]) % N
        d20 = (Es[0] - Es[2]) % N
        assert d01 == ((xs[1] - xs[0]) * DELTA) % N
        assert d12 == ((xs[2] - xs[1]) * DELTA) % N
        assert d20 == ((xs[0] - xs[2]) * DELTA) % N
        # permute labels under psi: cycle differences
        xs1 = [xs[1], xs[2], xs[0]]
        Es1 = [xj * P + y for xj in xs1]
        assert (Es1[1] - Es1[0]) % N == d12
    w("    OK")

    # ------------------------------------------------------------------ E
    block(
        "E Nonce: E_R == r*Delta + R_y mod N for both lifts",
        "Independent of R_x in {r, r+N}; Ry recovered with Delta-lift ambiguity.",
        "Expand (r+N)*Delta + Ry == r*Delta + Ry mod N.",
    )
    for i in range(80):
        h = hashlib.sha256(f"p7-nonce:{i}".encode()).digest()
        k = 1 + (int.from_bytes(h, "big") % (N - 1))
        R = ec_mul(k)
        assert R is not None
        Rx, Ry = R
        r = Rx % N
        eR = E_of(R) % N
        assert eR == (r * DELTA + Ry) % N
        if r < DELTA:
            alt = r + N
            assert alt < P
            E_alt = alt * P + Ry
            assert E_alt % N == eR
        # recover Ry
        rho = (eR - r * DELTA) % N
        if rho >= DELTA:
            assert Ry == rho
        else:
            assert Ry in (rho, rho + N)
    w("    OK")

    # ------------------------------------------------------------------ F
    block(
        "F.1 Packed-E mod N obstruction: b'=0",
        "Symmetric invariants of {e(+/- psi^j P)} are orbit-only; raw e is fn of P; H(.|P)=0.",
        "Phase IV-V + explicit formulas A.",
    )
    for d, pt in samples[:50]:
        orbit = []
        for s in (1, -1):
            for ell in (1, LAMBDA, LAMBDA2):
                orbit.append(ec_mul((s * ell * d) % N))
        assert len(set(orbit)) == 6
        eset = frozenset(e_of(q) for q in orbit)
        # Se for positive mu3 half depends on y of representative
        # symmetric set of all six e-values is orbit invariant
        for q in orbit:
            eset2 = frozenset(e_of(qq) for qq in [
                q, psi(q), psi(psi(q)),
                (q[0], (P - q[1]) % P),
                psi((q[0], (P - q[1]) % P)),
                psi(psi((q[0], (P - q[1]) % P))),
            ])
            assert eset2 == eset
        # raw e(pt) determined by pt
        assert e_of(pt) == (pt[0] * DELTA + pt[1]) % N
    b = math.log2(6)
    w(f"    Sixfold accounting only: 2^(k - {b:.10f}); b'=0 for packed-E mod N family")
    w("    OK")

    w()
    w("=" * 88)
    w("SUCCESS CRITERION: B")
    w("=" * 88)
    w("  Entire packed-E modulo-N family gives b' = 0.")
    w("  Key identity: E0+E1+E2 == q_x*Delta^2 + 3y (mod N) — public/orbit.")
    w("  ALL Phase VII verification checks PASSED.")
    w("=" * 88)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
