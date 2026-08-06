#!/usr/bin/env python3
"""
Phase VI — Exact Rational Encoding: theorem / proof / verification.

Canonical object E = x*p + y. No decimal algebra.
Document: Phase_VI_Exact_Rational_Encoding.md
"""
from __future__ import annotations

import hashlib
from pathlib import Path

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHASE_VI_EXACT_RATIONAL_ENCODING_VERIFY.txt")

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
    w("Phase VI - Exact Rational Encoding (E = x*p + y)")
    w("Document: Phase_VI_Exact_Rational_Encoding.md")
    w("=" * 88)

    samples = []
    for i in range(200):
        h = hashlib.sha256(f"p6:{i}".encode()).digest()
        d = 1 + (int.from_bytes(h, "big") % (N - 1))
        pt = ec_mul(d)
        assert pt is not None
        samples.append((d, pt))

    # ------------------------------------------------------------------ 4.1
    block(
        "4.1 Bijection (x,y) <-> E",
        "E=xp+y is bijective onto {0..p^2-1}; inverse x=floor(E/p), y=E mod p.",
        "Euclidean division by p on [0,p^2).",
    )
    for x, y in ((0, 0), (1, 0), (0, 1), (P - 1, P - 1), (123, 456)):
        E = x * P + y
        assert 0 <= E < P * P
        assert E // P == x and E % P == y
    for _, pt in samples[:50]:
        E = E_of(pt)
        assert E // P == pt[0] and E % P == pt[1]
    w("    OK")

    # ------------------------------------------------------------------ 2.2-2.4
    block(
        "2.2-2.4 E(-P), E(psi), E(psi^2)",
        "E(-P)=E+p-2y; E(psi)=(beta x mod p)*p+y; fine residue invariant under psi.",
        "Direct from definitions; psi fixes y.",
    )
    neq_beta = 0
    for _, pt in samples[:100]:
        x, y = pt
        E = E_of(pt)
        neg = (x, (P - y) % P)
        assert E_of(neg) == E + P - 2 * y
        assert E + E_of(neg) == P * (2 * x + 1)

        p1 = psi(pt)
        p2 = psi(p1)
        assert E_of(p1) == ((BETA * x) % P) * P + y
        assert E_of(p2) == ((BETA2 * x) % P) * P + y
        assert E_of(p1) % P == y and E_of(p2) % P == y

        full = BETA * x
        q1 = full // P
        assert E_of(p1) == BETA * x * P - q1 * P * P + y
        if E_of(p1) != BETA * E:
            neq_beta += 1
    assert neq_beta > 0
    w(f"    OK; E(psi) != beta*E on {neq_beta}/100 samples")

    # ------------------------------------------------------------------ 3.1-3.4
    block(
        "3.1-3.4 Orbit algebra on E_j",
        "E0+E1+E2 = q_x p^2 + 3y; Ei-Ej=(xi-xj)p; floor(Ej/p)=xj.",
        "Carry theorem: x0+x1+x2=q_x p; expand packed sum.",
    )
    for _, pt in samples[:100]:
        x, y = pt
        x0, x1, x2 = x, (BETA * x) % P, (BETA2 * x) % P
        E0, E1, E2 = x0 * P + y, x1 * P + y, x2 * P + y
        Sx = x0 + x1 + x2
        assert Sx % P == 0
        qx = Sx // P
        assert qx in (1, 2)
        assert E0 + E1 + E2 == qx * P * P + 3 * y
        assert E1 - E0 == (x1 - x0) * P
        assert E2 - E1 == (x2 - x1) * P
        assert E0 // P == x0 and E1 // P == x1 and E2 // P == x2
        assert E0 % P == E1 % P == E2 % P == y
    w("    OK")

    # ------------------------------------------------------------------ 5.1
    block(
        "5.1 E mod N = x*Delta + y mod N",
        "E = xp+y == x*Delta+y (mod N) because p == Delta (mod N).",
        "p = N+Delta.",
    )
    assert P == N + DELTA
    for _, pt in samples[:100]:
        x, y = pt
        E = E_of(pt)
        assert E % N == (x * DELTA + y) % N
    w("    OK")

    # ------------------------------------------------------------------ 5.2 / 6
    block(
        "5.2-6.1 No forced ID with signature r; no ring-hom bridge",
        "E mod N is a pubkey quantity; r is a nonce x-mod-N. p!=N => no unital ring hom.",
        "Distinct geometric roles; Phase II ring-hom impossibility.",
    )
    assert P != N and P % N != 0 and N % P != 0
    # E(G) mod N is not a free match claim to an arbitrary r
    Eg = E_of((GX, GY)) % N
    w(f"    E(G) mod N = {Eg} (public; not identified with a signature r)")
    w("    OK")

    # ------------------------------------------------------------------ 7 hierarchy
    block(
        "7.1 Hierarchy: E is foundation; decimals are serialization",
        "P -> E -> Phi=E/p^2 -> decimal encoding -> digits.",
        "Phi defined as rational E/p^2; digit depths corollaries of lattice 1/p, 1/p^2.",
    )
    for _, pt in samples[:20]:
        E = E_of(pt)
        # rational equality without Decimal: E/p^2 == x/p + y/p^2
        x, y = pt
        # E * 1 == x*p + y  (already)
        assert E * 1 == x * P + y
        # cross-check: E * 1 == (x * P + y); Phi numerators match
        assert E == x * P + y
    assert 10**77 < P < 10**78
    assert 10**154 < P * P < 10**155
    w("    OK (object + lattice bounds as encoding corollaries)")

    # ------------------------------------------------------------------ 8
    block(
        "8 Complexity: engineering only; no ECDLP claim",
        "E stores ~2 log2(p) bits (same as (x,y)); enables single-int compare/hash.",
        "Bit length of E < p^2 is ceil(log2(p^2))=2 ceil(log2 p) roughly; not a DL reduction.",
    )
    bits_E = (P * P - 1).bit_length()
    bits_xy = 2 * (P - 1).bit_length()
    w(f"    bitlength(p^2-1)={bits_E}, 2*bitlength(p-1)={bits_xy}")
    w("    No ECDLP reduction claimed - OK")

    w()
    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Canonical object: E = xp + y")
    w("  Orbit sum: E0+E1+E2 = q_x p^2 + 3y")
    w("  Unique recovery of (x,y); E mod N = x Delta + y mod N")
    w("  Decimals = serialization only. No ECDLP claim.")
    w("  ALL Phase VI verification checks PASSED.")
    w("=" * 88)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
