#!/usr/bin/env python3
"""
If x1+x2+x3 = p (as integers), then X1+X2+X3 = 1 in the coarse channel.

Also probe GLV triples: x, beta*x mod p, beta^2*x mod p.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_X_TRIPLE_SUM.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE
BETA2 = (BETA * BETA) % P

G = SECP256k1.generator


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Coarse channel: if x1+x2+x3 = p then sum(xi/p) = 1")
    w("=" * 88)
    w()

    # algebraic identity
    w("-" * 88)
    w("1) Exact identity (any ints)")
    w("-" * 88)
    w("  (x1+x2+x3)/p = x1/p + x2/p + x3/p")
    w("  so x1+x2+x3 = p  <=>  sum Xi = 1   (exact in Q)")
    w("  similarly = 2p <=> sum Xi = 2, etc.")
    w()

    # beta relation
    s_beta = 1 + BETA + BETA2
    w("-" * 88)
    w("2) Field relation for beta")
    w("-" * 88)
    w(f"  (1 + beta + beta^2) mod p = {s_beta % P}")
    w(f"  1 + beta + beta^2 (as int) = {s_beta}")
    w(f"  (1+beta+beta^2)/p = {Fraction(s_beta, P)}")
    w()

    # GLV triples on walk
    w("-" * 88)
    w("3) GLV triples on nG: S = x + (beta*x mod p) + (beta^2*x mod p)")
    w("-" * 88)
    counts = {1: 0, 2: 0, 0: 0, "other": 0}
    sum_X_is_int = 0
    examples = []
    for n in range(1, 257):
        pt = n * G
        x = int(pt.x())
        x1 = x
        x2 = (BETA * x) % P
        x3 = (BETA2 * x) % P
        S = x1 + x2 + x3
        # how many p's?
        q, r = divmod(S, P)
        Xsum = Fraction(S, P)
        if Xsum.denominator == 1:
            sum_X_is_int += 1
        if r == 0 and q in (0, 1, 2):
            counts[q] += 1
        elif r == 0:
            counts["other"] += 1
            if len(examples) < 3:
                examples.append((n, S, q, r, Xsum))
        else:
            counts["other"] += 1
            if len(examples) < 5:
                examples.append((n, S, q, r, Xsum))

        if n in (1, 2, 5, 17) or (q == 1 and r == 0 and len([e for e in examples if e[2] == 1]) < 2):
            examples.append((n, S, q, r, Xsum))

    w(f"  walk 1..256: S = q*p + r")
    w(f"    q=0 (S=0):     {counts[0]}")
    w(f"    q=1 (S=p):     {counts[1]}   <-- sum Xi = 1 exactly")
    w(f"    q=2 (S=2p):    {counts[2]}   <-- sum Xi = 2 exactly")
    w(f"    other:         {counts['other']}")
    w(f"  sum Xi is integer: {sum_X_is_int}/256")
    w()
    w("  samples (n, S, q, r, sum Xi):")
    seen = set()
    for n, S, q, r, Xsum in examples:
        if n in seen:
            continue
        seen.add(n)
        w(f"    n={n}: S/p = {Xsum}  (q={q}, r={r})")
        if len(seen) >= 12:
            break
    w()

    # When is S=p? related to wrap counts
    w("-" * 88)
    w("4) Wrap accounting")
    w("-" * 88)
    w("  Before reduction: x + beta*x + beta^2*x = x*(1+beta+beta^2)")
    w(f"  1+beta+beta^2 = {s_beta} = {Fraction(s_beta,P)}*p")
    w("  After reduction: xi' = beta^i*x - qi*p")
    w("  S = x*(1+beta+beta^2) - (q1+q2)*p")
    w("  If 1+beta+beta^2 = p, then S = p*x - (q1+q2)*p = p*(x - q1 - q2)")
    w("  so sum Xi = x - q1 - q2  (an integer; often 1 or 2 depending on wraps)")
    w()

    # verify wrap formula for n=1..64
    match_wrap = 0
    for n in range(1, 65):
        x = int((n * G).x())
        raw2 = BETA * x
        raw3 = BETA2 * x
        q2, x2 = divmod(raw2, P)
        q3, x3 = divmod(raw3, P)
        S = x + x2 + x3
        # predicted
        # S = x*(1+beta+beta2) - (q2+q3)*p but beta,beta2 are already reduced reps
        # Use field: 1+BETA+BETA2 = s_beta
        pred = x * s_beta - (q2 + q3) * P
        # wait: raw2 = BETA*x exactly with BETA in 0..p-1, so q2 = floor(BETA*x/P)
        # pred should equal S
        # Actually x + (BETA*x - q2*P) + (BETA2*x - q3*P) = x*(1+BETA+BETA2) - (q2+q3)*P
        pred = x * (1 + BETA + BETA2) - (q2 + q3) * P
        if pred == S:
            match_wrap += 1
    w(f"  wrap formula S = x(1+beta+beta2)-(q2+q3)p : {match_wrap}/64 exact")
    w()

    # distribution of sum Xi = x - q2 - q3 when s_beta = p?
    w("-" * 88)
    w("5) If user rule: x1+x2+x3=p => sum Xi=1")
    w("-" * 88)
    hit = 0
    for n in range(1, 257):
        x = int((n * G).x())
        x2 = (BETA * x) % P
        x3 = (BETA2 * x) % P
        if x + x2 + x3 == P:
            hit += 1
            assert Fraction(x, P) + Fraction(x2, P) + Fraction(x3, P) == 1
    w(f"  walk 1..256: triples with x1+x2+x3 == p : {hit}/256")
    w(f"  (all of those have sum Xi == 1 by construction)")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  YES: x1+x2+x3=p  =>  X1+X2+X3=1 exactly in the coarse channel.")
    w("  GLV orbit sums to q*p with q usually 1 or 2 (wrap-dependent), not always p.")
    w("  When q=1, the three coarse channels sum to exactly 1 — a closed circle mod 1.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
