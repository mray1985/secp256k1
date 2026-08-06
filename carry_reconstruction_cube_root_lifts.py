#!/usr/bin/env python3
"""
Corrected theorem: Carry Reconstruction for Reduced Primitive Cube-Root Orbits

- General edge case a+a1=M requires a2=0 (not 2M-(a+a1)=M).
- For M prime and nontrivial cube root t: a+a1=M is impossible for a != 0.
- Carry BIT is c = floor((a+a1)/M) in {0,1}; orbit class q = 1+c.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\CARRY_RECONSTRUCTION_CUBE_ROOT_LIFTS.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE
BETA2 = (BETA * BETA) % P
LAMBDA = 0x5363AD4CC05C30E0A5261C028812645A122E22EA20816678DF02967C1B23BD72
LAMBDA2 = (LAMBDA * LAMBDA) % N


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("THEOREM — Carry Reconstruction for Reduced Primitive Cube-Root Orbits")
    w("=" * 88)
    w("(corrected: equality case a+a1=M; carry bit c vs orbit class q=1+c)")
    w()

    w("-" * 88)
    w("LEMMA (Forced lift)")
    w("-" * 88)
    w("  M >= 2, t in [0,M), t^2+t+1 == 0 (mod M), t2=(t*t)%M in [0,M).")
    w("  Then 1+t+t2 = M.")
    w("  PROOF: 1 <= 1+t+t2 <= 2M-1 and == 0 mod M => equals M. QED.")
    w()

    w("-" * 88)
    w("LEMMA (No equality a+a1=M when M prime, t nontrivial)")
    w("-" * 88)
    w("  Assume M prime, a in {1,...,M-1}, a1=(t*a) mod M.")
    w("  Suppose a+a1 = M. Then a+t*a == 0 (mod M), i.e. (1+t)a == 0.")
    w("  Since a != 0 and M prime, 1+t == 0 (mod M), i.e. t == -1.")
    w("  But t^2+t+1==0 and t==-1 => 1-1+1=1 != 0. Contradiction.")
    w("  Equiv: nontrivial cube root => 1+t != 0 => gcd(1+t,M)=1 when M prime.")
    w("  Therefore a+a1 != M for all nonzero a. QED.")
    w()

    w("-" * 88)
    w("GENERAL reconstruction (any M; includes equality edge)")
    w("-" * 88)
    w("  From t^2 = -t-1 (mod M): a2_true = (t2*a) mod M = (-a-a1) mod M.")
    w("  Piecewise canonical lift:")
    w("    a2 = M-a-a1           if 0 < a+a1 < M")
    w("    a2 = 0                if a+a1 = M")
    w("    a2 = 2M-a-a1          if M < a+a1 < 2M")
    w("  (Bug fixed: when a+a1=M, use 0, not 2M-(a+a1)=M which is outside [0,M).)")
    w("  Always: a2 = (-a-a1) mod M.")
    w()

    w("-" * 88)
    w("THEOREM (prime M / nontrivial cube-root case — secp256k1)")
    w("-" * 88)
    w("  Let M be prime, and let t be a nontrivial solution of")
    w("    t^2 + t + 1 = 0  (mod M).")
    w("  Let t2 = t^2 mod M, representatives in [0,M).")
    w("  For any a in {1,...,M-1}, define")
    w("    a1 = (t*a) mod M")
    w("    c  = floor((a+a1)/M)     # carry BIT in {0,1}")
    w("    q  = 1 + c               # orbit-sum CLASS in {1,2}")
    w("    a2 = q*M - a - a1")
    w("  Then:")
    w("    a2 = (t2*a) mod M")
    w("    a + a1 + a2 = q*M")
    w("    q in {1,2}")
    w("  The equality a+a1=M cannot occur (previous lemma), so the clean")
    w("  two-branch formula never hits the a2=0 edge.")
    w()
    w("  PROOF sketch: polynomial => a2 == -(a+a1) (mod M); lift with")
    w("  c=floor((a+a1)/M) in {0,1} only (equality excluded); a2=(1+c)M-a-a1.")
    w()
    w("  Terminology:")
    w("    c = carry bit of a+a1 across M")
    w("    q = 1+c = orbit sum class (a+a1+a2)/M")
    w()

    w("-" * 88)
    w("COROLLARIES (secp256k1)")
    w("-" * 88)
    w("  Field:  c_x = floor((x+(beta*x mod p))/p)")
    w("          q_x = 1 + c_x")
    w("          x2  = q_x*p - x - x1")
    w("  Scalar: c_u = floor((u+(lambda*u mod N))/N)")
    w("          q_u = 1 + c_u")
    w("          u2  = q_u*N - u - u1")
    w()

    # ---- verify no equality + theorem ----
    w("-" * 88)
    w("Confirmation")
    w("-" * 88)

    def confirm(M: int, t: int, t2: int, tag: str, n: int = 8000) -> None:
        assert 1 + t + t2 == M
        assert (1 + t) % M != 0  # nontrivial
        eq_hits = 0
        ok = 0
        for i in range(n):
            h = hashlib.sha256(f"corr-{tag}:{i}".encode()).digest()
            a = int.from_bytes(h, "big") % M
            if a == 0:
                continue
            a1 = (t * a) % M
            if a + a1 == M:
                eq_hits += 1
            c = (a + a1) // M
            q = 1 + c
            a2 = q * M - a - a1
            if (
                c in (0, 1)
                and q in (1, 2)
                and a2 == (t2 * a) % M
                and a + a1 + a2 == q * M
                and 0 <= a2 < M
            ):
                ok += 1
        w(f"  {tag}: theorem {ok}/{n}; equality a+a1=M hits: {eq_hits}")

    confirm(P, BETA, BETA2, "p/beta")
    confirm(N, LAMBDA, LAMBDA2, "N/lambda")

    # exhaustive impossibility check on small analog? skip
    # also verify general piecewise for a synthetic composite where 1+t shares factor
    w()
    w("  General edge (illustration): if a+a1=M were allowed, a2 must be 0,")
    w("  and a+a1+a2=M (q=1), not 2M. secp primes never enter that branch.")
    w()

    w("=" * 88)
    w("STATUS")
    w("=" * 88)
    w("  Abstract theorem requires M prime (or gcd(1+t,M)=1) for clean q=1+c form.")
    w("  Carry bit c distinguished from orbit class q=1+c.")
    w("  Equality bug documented and excluded for secp256k1 instances.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
