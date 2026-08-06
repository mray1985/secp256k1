#!/usr/bin/env python3
"""
Algebraic derivation from t^2 + t + 1 = 0  (no correlation hunting).

Two rings, same polynomial:
  F_p :  beta^2 + beta + 1 ≡ 0  (mod p),  chosen reps with 1+beta+beta^2 = p
  Z/NZ:  lambda^2 + lambda + 1 ≡ 0 (mod N), chosen reps with 1+lambda+lambda^2 = N

Derive carry-bit orbit reconstruction symbolically, then verify.
Closed: q_x<->q_d, orientation, naive Phi, r*=p/y-2 vs d.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_POLY_T2_T_1_DERIVATION.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE
BETA2 = (BETA * BETA) % P
LAMBDA = 0x5363AD4CC05C30E0A5261C028812645A122E22EA20816678DF02967C1B23BD72
LAMBDA2 = (LAMBDA * LAMBDA) % N

G = SECP256k1.generator


def derive_generic(name: str, mod: int, t: int, t2: int, w) -> None:
    """Symbolic derivation for a root t of X^2+X+1 over Z/modZ with lift 1+t+t2=mod."""
    w(f"--- Ring Z/{name}Z, root t, lift 1+t+t^2 = {name} ---")
    w(f"  Polynomial: t^2 + t + 1 == 0 (mod {name})")
    w(f"  Integer lifts: check (1+t+t2) % {name} == 0")
    w(f"  Chosen nonnegative reps: 1+t+t2 == {name}?  {1 + t + t2 == mod}")
    w()
    w("  THEOREM (orbit sum).")
    w(f"    Let a in 1..{name}-1, a1=(t*a) %{name}, a2=(t2*a) %{name}.")
    w("    Then a + a1 + a2 = q*{name} with q in {1,2}.")
    w("  PROOF.")
    w("    t*a = k1*{name} + a1,  t2*a = k2*{name} + a2.")
    w("    a+a1+a2 = a + t*a + t2*a - (k1+k2)*{name}")
    w("             = a(1+t+t2) - (k1+k2)*{name}")
    w(f"             = a*{name} - (k1+k2)*{name}   [using 1+t+t2={name}]")
    w("             = {name}*(a - k1 - k2).")
    w("    For a in 1..mod-1, classical floor(y)+floor(z) vs floor(y+z) with")
    w("    y=t*a/mod, z=t2*a/mod, y+z = a - a/mod, floor(y+z)=a-1,")
    w("    hence a-k1-k2 in {1,2}. QED.")
    w()
    w("  THEOREM (carry reconstruction; no t^2 mul).")
    w("    a1 = (t*a) mod {name}")
    w("    q  = 1 if a+a1 < {name} else 2")
    w("       = 1 + floor((a+a1)/{name})")
    w("    a2 = q*{name} - a - a1")
    w("  PROOF.")
    w("    From 1+t+t2=0 mod {name}:  t2 == -1-t  =>  t2*a == -a - t*a  (mod {name}).")
    w("    So a2 == -(a+a1) (mod {name}).")
    w("    Canonical lift in [0,{name}):")
    w("      if a+a1 < {name}:  a2 = {name} - (a+a1) = {name}-a-a1  => q=1")
    w("      if a+a1 >= {name}: a2 = 2*{name}-(a+a1)           => q=2")
    w("    Equiv: q = 1 + floor((a+a1)/{name}), a2 = q*{name}-a-a1.")
    w("    Meaning: q is the carry bit of adding a and a1 across {name}. QED.")
    w()
    w("  COROLLARY.")
    w("    Computing t2*a mod {name} is redundant once (a1,q) are known.")
    w("    Pipeline: a --*t--> a1 --carry--> q --sub--> a2.")
    w()


def verify_ring(mod: int, t: int, t2: int, samples: int, tag: str) -> tuple[int, int, int]:
    ok_q = ok_a2 = ok_poly = 0
    assert (t * t) % mod == t2
    assert (1 + t + t2) % mod == 0
    # prefer exact lift == mod for secp constants
    lift = 1 + t + t2
    for i in range(samples):
        h = hashlib.sha256(f"{tag}:{i}".encode()).digest()
        a = int.from_bytes(h, "big") % mod
        if a == 0:
            continue
        a1 = (t * a) % mod
        q = 1 + ((a + a1) // mod)
        a2 = q * mod - a - a1
        a2_true = (t2 * a) % mod
        q_true = (a + a1 + a2_true) // mod
        if q == q_true and q in (1, 2):
            ok_q += 1
        if a2 == a2_true:
            ok_a2 += 1
        if (a + a1 + a2) == q * mod:
            ok_poly += 1
    return ok_q, ok_a2, ok_poly


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("From polynomial t^2 + t + 1 = 0  - dual rings (p) and (N)")
    w("=" * 88)
    w()
    w("CLOSED (do not revisit): naive Phi ops; q_x<->q_d; orientation; r*~d.")
    w("METHOD: derive from the polynomial; numerical checks only confirm.")
    w()

    w("-" * 88)
    w("0) Same minimal polynomial, two rings")
    w("-" * 88)
    w("  t^2 + t + 1 = 0")
    w("  Roots are primitive cube roots of unity (order 3).")
    w("  Field side:  t |-> beta  in F_p")
    w("  Scalar side: t |-> lambda in Z/NZ")
    w(f"  beta^2+beta+1 == 0 mod p?  {(BETA2 + BETA + 1) % P == 0}")
    w(f"  lambda^2+lambda+1 == 0 mod N? {(LAMBDA2 + LAMBDA + 1) % N == 0}")
    w(f"  beta^3 == 1 mod p?   {pow(BETA, 3, P) == 1}")
    w(f"  lambda^3 == 1 mod N? {pow(LAMBDA, 3, N) == 1}")
    w(f"  Integer lift 1+beta+beta2 = p?  {1 + BETA + BETA2 == P}")
    w(f"  Integer lift 1+lambda+lambda2 = N? {1 + LAMBDA + LAMBDA2 == N}")
    w()

    w("-" * 88)
    w("1) Symbolic derivation (identical in both rings)")
    w("-" * 88)
    derive_generic("p", P, BETA, BETA2, w)
    derive_generic("N", N, LAMBDA, LAMBDA2, w)

    w("-" * 88)
    w("2) Dual dictionary")
    w("-" * 88)
    w("  polynomial root     beta (mod p)          lambda (mod N)")
    w("  base element        x  (field coord)      u  (scalar / r-orbit)")
    w("  first image         x1 = beta*x mod p     u1 = lambda*u mod N")
    w("  carry bit           q_x                   q_u  (or q_r if u=r)")
    w("  third member        x2 = q_x*p - x - x1   u2 = q_u*N - u - u1")
    w("  orbit sum           x+x1+x2 = q_x*p       u+u1+u2 = q_u*N")
    w("  meaning of q        carry of x+x1 / p     carry of u+u1 / N")
    w()
    w("  KEEP SEPARATE until each side is fully derived.")
    w("  Do NOT identify q_x with q_u / q_d without a new exact theorem.")
    w()

    w("-" * 88)
    w("3) Numerical confirmation only (not discovery)")
    w("-" * 88)
    n = 8000
    oq, oa, op = verify_ring(P, BETA, BETA2, n, "p")
    w(f"  p-side random: q match {oq}/{n}  a2 match {oa}/{n}  sum identity {op}/{n}")
    oq, oa, op = verify_ring(N, LAMBDA, LAMBDA2, n, "N")
    w(f"  N-side random: q match {oq}/{n}  a2 match {oa}/{n}  sum identity {op}/{n}")

    # curve x samples
    ok = 0
    for i in range(1, 1025):
        x = int((i * G).x())
        x1 = (BETA * x) % P
        qx = 1 + ((x + x1) // P)
        x2 = qx * P - x - x1
        if x2 == (BETA2 * x) % P:
            ok += 1
    w(f"  p-side on x(nG) 1..1024: {ok}/1024")
    w()

    w("-" * 88)
    w("4) What this does NOT claim")
    w("-" * 88)
    w("  - No map q_x -> q_u / q_d (closed as statistical; no theorem).")
    w("  - No orientation bridge (falsified).")
    w("  - No Phi decimal group law.")
    w("  - Signature r-orbits: same N-side algebra if u=r; still separate from x.")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Structure comes from t^2+t+1=0 over two rings with lift 1+t+t^2 = modulus.")
    w("  Carry reconstruction is the same theorem twice (p with beta, N with lambda).")
    w("  Duality is algebraic parallelism, not a numerical bridge.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
