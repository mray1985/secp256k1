#!/usr/bin/env python3
"""
Exact criterion for q_x in {1,2} on x in [0,p).

  beta*x = k1*p + x1,  beta^2*x = k2*p + x2
  q_x = (x + x1 + x2)/p = x - k1 - k2

Derive piecewise / fractional-part characterization. Verify on random x.
No q_d correlation.
"""
from __future__ import annotations

import hashlib
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_QX_EXACT_CRITERION.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE
BETA2 = (BETA * BETA) % P
G = SECP256k1.generator

assert 1 + BETA + BETA2 == P


def qx_parts(x: int) -> dict:
    x %= P
    k1, x1 = divmod(BETA * x, P)
    k2, x2 = divmod(BETA2 * x, P)
    S = x + x1 + x2
    assert S % P == 0
    qx = S // P
    assert qx == x - k1 - k2
    return {
        "x": x,
        "k1": k1,
        "k2": k2,
        "x1": x1,
        "x2": x2,
        "q_x": qx,
        "frac_sum": Fraction(x1 + x2, P),  # {beta x/p}+{beta2 x/p}
    }


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Exact partition of x-field by q_x")
    w("=" * 88)
    w()
    w("Setup:")
    w("  1 + beta + beta^2 = p  (integer)")
    w("  k1 = floor(beta*x / p),  x1 = beta*x mod p")
    w("  k2 = floor(beta^2*x / p), x2 = beta^2*x mod p")
    w("  q_x = x - k1 - k2 = (x + x1 + x2)/p in {1,2} for x in 1..p-1")
    w()

    w("-" * 88)
    w("1) Derivation")
    w("-" * 88)
    w("  Let y = beta*x/p, z = beta^2*x/p  (rationals).")
    w("  Then y + z = (beta + beta^2)*x/p = (p-1)*x/p = x - x/p.")
    w("  For integer x in 1..p-1:  0 < x/p < 1, so")
    w("    floor(y+z) = floor(x - x/p) = x - 1.")
    w()
    w("  Classical identity:")
    w("    floor(y)+floor(z) = floor(y+z)     iff  {y}+{z} < 1")
    w("    floor(y)+floor(z) = floor(y+z) - 1 iff  {y}+{z} >= 1")
    w()
    w("  Therefore k1+k2 in {x-1, x-2}, and")
    w("    q_x = x - (k1+k2) in {1, 2}.")
    w()
    w("  Exact criteria (equivalent for x in 1..p-1):")
    w()
    w("    q_x = 1  <=>  {beta*x/p} + {beta^2*x/p} < 1")
    w("            <=>  x1 + x2 < p")
    w("            <=>  x1 + x2 = p - x")
    w("            <=>  k1 + k2 = x - 1")
    w()
    w("    q_x = 2  <=>  {beta*x/p} + {beta^2*x/p} >= 1")
    w("            <=>  x1 + x2 >= p")
    w("            <=>  x1 + x2 = 2p - x")
    w("            <=>  k1 + k2 = x - 2")
    w()
    w("  Boundary hypersurface in the torus: {beta x/p} + {beta^2 x/p} = 1,")
    w("  i.e. (beta*x mod p) + (beta^2*x mod p) = p.")
    w()

    w("-" * 88)
    w("2) Piecewise constancy of (k1,k2)")
    w("-" * 88)
    w("  k1 jumps at x where beta*x is divisible by p:")
    w("    x = ceil(m*p / beta) for m = 1..beta-1, clipped to [1,p-1]")
    w("  k2 jumps at x = ceil(n*p / beta^2) for n = 1..beta^2-1 (reps).")
    w("  On each open cell of this arrangement, (k1,k2) is constant,")
    w("  hence q_x = x - k1 - k2 is an affine function of x with slope 1,")
    w("  taking only values in {1,2} — so within a cell, q_x flips at most")
    w("  when x crosses k1+k2+1.5, i.e. the cell may split into at most two")
    w("  q_x-regions (often one).")
    w()
    w("  Practical decision procedure (exact, O(1) mul/div):")
    w("    x1 = (beta * x) % p")
    w("    x2 = (beta2 * x) % p")
    w("    q_x = 1 if x1 + x2 < p else 2")
    w("  Or: q_x = (x + x1 + x2) // p")
    w()

    # verify
    w("-" * 88)
    w("3) Verification on random x and on walk x(nG)")
    w("-" * 88)
    ok_frac = ok_sum = ok_k = ok_boundary = 0
    n_rand = 5000
    for i in range(n_rand):
        h = hashlib.sha256(b"qx-crit:" + i.to_bytes(4, "big")).digest()
        x = int.from_bytes(h, "big") % P
        if x == 0:
            continue
        r = qx_parts(x)
        qx = r["q_x"]
        # frac criterion
        frac_lt = (r["x1"] + r["x2"]) < P
        if (qx == 1 and frac_lt) or (qx == 2 and not frac_lt):
            ok_frac += 1
        if qx == 1 and r["x1"] + r["x2"] == P - x:
            ok_sum += 1
        elif qx == 2 and r["x1"] + r["x2"] == 2 * P - x:
            ok_sum += 1
        if qx == 1 and r["k1"] + r["k2"] == x - 1:
            ok_k += 1
        elif qx == 2 and r["k1"] + r["k2"] == x - 2:
            ok_k += 1
        # boundary identity always
        if r["x1"] + r["x2"] in (P - x, 2 * P - x):
            ok_boundary += 1

    w(f"  random x: frac criterion <-> q_x : {ok_frac}/{n_rand}")
    w(f"  random x: x1+x2 = q_x*p - x     : {ok_sum}/{n_rand}")
    w(f"  random x: k1+k2 = x - q_x        : {ok_k}/{n_rand}")
    w(f"  random x: x1+x2 in {{p-x,2p-x}}  : {ok_boundary}/{n_rand}")

    ok_w = 0
    for n in range(1, 1025):
        x = int((n * G).x())
        r = qx_parts(x)
        frac_lt = (r["x1"] + r["x2"]) < P
        if (r["q_x"] == 1 and frac_lt) or (r["q_x"] == 2 and not frac_lt):
            ok_w += 1
    w(f"  walk x(nG) n=1..1024: frac criterion: {ok_w}/1024")
    w()

    # density
    w("-" * 88)
    w("4) Measure of regions (empirical)")
    w("-" * 88)
    c1 = c2 = 0
    Nsamp = 20000
    for i in range(Nsamp):
        h = hashlib.sha256(b"qx-dens:" + i.to_bytes(4, "big")).digest()
        x = int.from_bytes(h, "big") % P
        if x == 0:
            continue
        r = qx_parts(x)
        if r["q_x"] == 1:
            c1 += 1
        else:
            c2 += 1
    tot = c1 + c2
    w(f"  sample {tot}: q_x=1 -> {c1} ({100*c1/tot:.2f}%)  q_x=2 -> {c2} ({100*c2/tot:.2f}%)")
    w("  (Expect ~1/2 each if {y},{z} behave like uniform with y+z = x-x/p constraint.)")
    w()

    # x=0
    w("-" * 88)
    w("5) Edge case x=0")
    w("-" * 88)
    r0 = qx_parts(0)
    w(f"  x=0: k1={r0['k1']} k2={r0['k2']} x1={r0['x1']} x2={r0['x2']} q_x={r0['q_x']}")
    w("  (degenerate; not an affine curve x-coordinate for finite points)")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Exact rule:")
    w("    q_x = 1  <=>  (beta*x mod p) + (beta^2*x mod p) < p")
    w("    q_x = 2  <=>  (beta*x mod p) + (beta^2*x mod p) >= p")
    w("  Equiv: q_x = 1 <=> {beta x/p}+{beta^2 x/p} < 1.")
    w("  Equiv: q_x = x - floor(beta x/p) - floor(beta^2 x/p).")
    w("  Regions = cells of the floor arrangement of beta x/p and beta^2 x/p,")
    w("  cut by the antidiagonal {y}+{z}=1 on the unit torus.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
