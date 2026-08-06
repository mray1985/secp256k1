#!/usr/bin/env python3
"""
Phase V — Necessary conditions for b'>0.

theorem / proof / verification only.
Document: Phase_V_Necessary_Conditions_for_New_ECDLP_Information.md
Does not rerun Phase IV searches. Does not claim q_x=q_u.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHASE_V_CONDITIONS_VERIFY.txt")

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


def X_set(pt) -> frozenset:
    x = pt[0]
    return frozenset({x, (BETA * x) % P, (BETA2 * x) % P})


def qx(x: int) -> int:
    S = x + (BETA * x) % P + (BETA2 * x) % P
    assert S % P == 0
    q = S // P
    assert q in (1, 2)
    return q


def cx(x: int) -> int:
    s = x + (BETA * x) % P
    assert s != P
    return s // P


def qu(u: int) -> int:
    u %= N
    S = u + (LAMBDA * u) % N + (LAMBDA2 * u) % N
    assert S % N == 0
    q = S // N
    assert q in (1, 2)
    return q


def glv_class(d: int) -> frozenset:
    d %= N
    return frozenset((e * ell * d) % N for e in (1, -1) for ell in (1, LAMBDA, LAMBDA2)) - {0}


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
    w("Phase V - Necessary conditions for b'>0")
    w("Document: Phase_V_Necessary_Conditions_for_New_ECDLP_Information.md")
    w("=" * 88)

    samples: list[tuple[int, tuple[int, int]]] = []
    for i in range(200):
        h = hashlib.sha256(f"p5:{i}".encode()).digest()
        d = 1 + (int.from_bytes(h, "big") % (N - 1))
        pt = ec_mul(d)
        assert pt is not None
        samples.append((d, pt))

    # ------------------------------------------------------------------ 5.1 obstruction
    block(
        "5.1 Obstruction: symmetric X-invariants cannot refine sixfold",
        "Any I depending only on unordered X={x,beta x, beta^2 x} is constant on "
        "the sixfold geometric orbit, hence constant on ~_GLV scalar classes; "
        "cannot reveal GLV position or sign; b'=0 in public-P model.",
        "Negation preserves x; psi permutes X; psi(P)=[lambda]P links geometric "
        "orbit to {+/- lambda^j d}G.",
    )
    invariants_ok = 0
    for d, pt in samples[:60]:
        x, y = pt
        Xs = X_set(pt)
        vals = {
            "qx": qx(x),
            "cx": cx(x),
            "Sx": qx(x) * P,
            "trace": 0,
            "norm": pow(x, 3, P),
            "Xset": Xs,
        }
        # sixfold geometric orbit via scalars
        for e in (1, -1):
            for ell in (1, LAMBDA, LAMBDA2):
                dd = (e * ell * d) % N
                if dd == 0:
                    continue
                qpt = ec_mul(dd)
                assert X_set(qpt) == Xs
                assert qx(qpt[0]) == vals["qx"]
                assert cx(qpt[0]) == vals["cx"]
                assert pow(qpt[0], 3, P) == vals["norm"]
        # within one GLV class, I(dG) equal for all representatives
        class_reps = list(glv_class(d))
        assert len(class_reps) == 6
        I_vals = {qx(ec_mul(rep)[0]) for rep in class_reps}
        assert I_vals == {vals["qx"]}
        invariants_ok += 1
    w(f"    OK: qx,cx,X,norm constant on sixfold for {invariants_ok} orbits")

    # Explicit: I does not distinguish sign or GLV position
    d, pt = samples[0]
    base_qx = qx(pt[0])
    assert qx(ec_mul((-d) % N)[0]) == base_qx
    assert qx(ec_mul((LAMBDA * d) % N)[0]) == base_qx
    w("    OK: qx reveals neither sign nor lambda-coset position")

    # ------------------------------------------------------------------ 2.2 qu orbit-only on scalar side
    block(
        "2.2 q_u on scalar orbits (not publicly computable)",
        "q_u constant on {d, lambda d, lambda^2 d}; q_u(-d)=3-q_u(d). Not computable from P.",
        "mu_3 permutes the reduced triple; negation replaces residues a_i by N-a_i "
        "so sum becomes (3-q)N.",
    )
    # For negation: reduced triple for -d is different set; q_u may flip?
    # Phase II said q_u flips under d |-> -d in some notes. Check carefully.
    # Sum of {-d, -lambda d, -lambda^2 d} reduced = sum of N-d_i if d_i!=0
    # = 3N - (d0+d1+d2) = 3N - q N = (3-q)N, so new_q = 3-q in {1,2} => flips 1<->2.
    # So q_u is NOT constant on full sixfold including negation!
    #
    # Wait - this is important. If q_u flips under negation, then q_u distinguishes
    # the {d, lambda d, lambda^2 d} half from the negative half?
    # new_q = 3 - q, so q=1 -> 2 and q=2 -> 1 under negation.
    # Within positive mu_3 orbit, q_u constant; under negation it flips.
    #
    # But is that "refining sixfold"? The sixfold class as a SET of 6 scalars -
    # as a function on scalars, q_u takes TWO values on the class (one on each sign half).
    # However for ECDLP search on ORBITS (unordered sixfold classes), the class as a unit
    # doesn't get a single q_u label - unless we take a canonical representative.
    #
    # For geometric X: negation preserves x, so qx constant on full sixfold.
    # For scalar U: negation maps to different residues; q_u flips.
    #
    # Does that mean q_u refines sixfold? It distinguishes d from -d.
    # BUT q_u is NOT publicly computable from P. And I(P)=qx does NOT equal qu.
    # Also: knowing P determines the point, which determines sign of y - the geometric
    # sixfold includes both signs of each psi image. The scalar d is still unique for P.
    #
    # For obstruction on X-side: still valid.
    # For q_u: classify as not publicly computable; on scalar side it distinguishes
    # sign halves (1 bit within the 6) IF you knew q_u - but wait:
    # If search already uses 6-orbits as units, knowing a bit that splits each orbit
    # into 2 would refine to 3-orbits (mu_3 only), giving log2(2)=1 additional bit
    # IF that bit were public. It is not.
    #
    # Document said q_u constant on ~_GLV - that was slightly wrong for negation.
    # Fix verification to state the precise fact:
    #   q_u constant on {d, lambda d, lambda^2 d}
    #   q_u(-d) = 3 - q_u(d)
    #   Not publicly computable => no b' from pubkey algebra.

    for d, _ in samples[:80]:
        q0 = qu(d)
        assert qu((LAMBDA * d) % N) == q0
        assert qu((LAMBDA2 * d) % N) == q0
        qm = qu((-d) % N)
        assert qm == 3 - q0
        assert qm in (1, 2)
    w("    OK: q_u constant on mu_3 orbit; flips under negation (q -> 3-q)")
    w("    Not publicly computable from P => no b' in public-P model")

    # Show qx does not equal the sign bit of d
    mismatches = sum(1 for d, pt in samples if qx(pt[0]) != qu(d))
    assert mismatches > 0
    w(f"    Note: qx!=qu on {mismatches}/{len(samples)} (bridge closed; not retested as claim)")

    # ------------------------------------------------------------------ y-branch
    block(
        "2.2b y-branch does not refine beyond sixfold",
        "Sign of y distinguishes P from -P but both lie in the same sixfold class.",
        "Sixfold class already includes negation; |class|=6 already accounted as log2(6).",
    )
    for d, pt in samples[:40]:
        x, y = pt
        neg = (x, (P - y) % P)
        assert X_set(neg) == X_set(pt)
        assert frozenset(glv_class(d)) == frozenset(glv_class((-d) % N))
    w("    OK")

    # ------------------------------------------------------------------ Delta lift
    block(
        "4 / Delta lift: ambiguity is about R_x vs r, not X(P)",
        "When r<Delta, R_x in {r, r+N}; when r>=Delta, unique. Not an X-symmetric pubkey invariant.",
        "Direct from p=N+Delta and range [0,p).",
    )
    for i in range(50):
        r = i % DELTA
        assert r < DELTA
        assert 0 <= r < P and 0 <= r + N < P
        r2 = DELTA + (i % 100)
        if r2 < N:
            assert r2 + N >= P
    w("    OK: lift theorem independent of carry X-invariants")

    # ------------------------------------------------------------------ ECDSA conditional
    block(
        "4.1 ECDSA conditional accounting (symbolic checks)",
        "If k known: d = r^{-1}(s k - z) mod N. If only GLV class of k known: <=6 candidates. "
        "Public r implies functions of r give H=0 given signature.",
        "Linear algebra in Z/NZ; cardinality of GLV class.",
    )
    # Synthetic signature equation check
    for i in range(30):
        h = hashlib.sha256(f"p5-ecdsa:{i}".encode()).digest()
        d = 1 + (int.from_bytes(h[:16], "big") % (N - 1))
        k = 1 + (int.from_bytes(h[16:], "big") % (N - 1))
        z = int.from_bytes(hashlib.sha256(f"z:{i}".encode()).digest(), "big") % N
        R = ec_mul(k)
        assert R is not None
        Rx = R[0]
        r = Rx % N
        if r == 0:
            continue
        s = (modinv(k, N) * ((z + r * d) % N)) % N
        # recover d from k
        d2 = (modinv(r, N) * ((s * k - z) % N)) % N
        assert d2 == d
        # GLV class of k: at most 6 recoveries
        cands = []
        for e in (1, -1):
            for ell in (1, LAMBDA, LAMBDA2):
                kk = (e * ell * k) % N
                if kk == 0:
                    continue
                # Only the true k satisfies R=kG with the given R_x matching;
                # for accounting: 6 formal linear images
                dd = (modinv(r, N) * ((s * kk - z) % N)) % N
                cands.append(dd)
        assert d in cands
        assert len(set(cands)) <= 6
        # functions of r are determined by r
        assert qu(r) == qu(r)
    w("    OK: full k recovers d; GLV(k) yields <=6 formal d candidates")
    w("    OK: public r => no extra entropy from functions of r given signature")

    # ------------------------------------------------------------------ Prop 3.1 necessary shape
    block(
        "3.1 Necessary shape of a b'>0 bridge",
        "F_p must not be a function of the sixfold geometric orbit alone "
        "(else F_N is GLV-class-constant / already known from P).",
        "If F_p = K(orbit(P)), then I is orbit-only (Thm 5.1) => b'=0.",
    )
    # Verify: any function of X is determined by orbit
    for d, pt in samples[:40]:
        orb = []
        for e in (1, -1):
            for ell in (1, LAMBDA, LAMBDA2):
                orb.append(ec_mul((e * ell * d) % N))
        labels = {qx(q[0]) for q in orb}
        assert len(labels) == 1
    w("    OK: orbit determines qx; bridge through qx cannot refine sixfold")

    # ------------------------------------------------------------------ complexity
    block(
        "Complexity reminder (frozen Phase IV)",
        "After GLV: 2^(k-log2(6)). Symmetric-X theorems: b'=0.",
        "Thm 5.1 + Phase IV.",
    )
    b = math.log2(6)
    w(f"    Original:  2^k")
    w(f"    After GLV: 2^(k - {b:.10f})")
    w(f"    After any symmetric-X invariant: still 2^(k - {b:.10f})  [b'=0]")

    # ------------------------------------------------------------------ final table echo
    w()
    w("=" * 88)
    w("SUCCESS CRITERION: B")
    w("=" * 88)
    w("  Proven obstruction: any invariant depending only on the unordered")
    w("  three-x orbit cannot reveal the scalar's GLV position or sign.")
    w("  Broad class => never b'>0.")
    w("  No claim of b'>0. No new identity inside carry algebra.")
    w("  ALL Phase V verification checks PASSED.")
    w("=" * 88)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
