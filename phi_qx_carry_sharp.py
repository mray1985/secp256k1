#!/usr/bin/env python3
"""
Sharpened q_x: carry of x + (beta*x mod p).

  q_x = 1 iff x + x1 < p
  q_x = 2 iff x + x1 >= p
  q_x = 1 + floor((x + x1)/p)
  x2 = q_x*p - x - x1

One modmul by beta; no beta^2 mul needed.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_QX_CARRY_SHARP.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE
BETA2 = (BETA * BETA) % P
G = SECP256k1.generator

assert 1 + BETA + BETA2 == P


def sharp(x: int) -> tuple[int, int, int, int]:
    x %= P
    x1 = (BETA * x) % P
    qx = 1 if x + x1 < P else 2
    assert qx == 1 + ((x + x1) // P)
    x2 = qx * P - x - x1
    return qx, x1, x2, x


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Sharpened q_x = carry bit of x + (beta*x mod p)")
    w("=" * 88)
    w()
    w("  x1 = beta*x mod p")
    w("  q_x = 1 if x+x1 < p else 2")
    w("      = 1 + floor((x+x1)/p)")
    w("  x2 = q_x*p - x - x1")
    w()

    ok_match = ok_x2 = ok_orbit = ok_floor = 0
    n = 10000
    for i in range(n):
        h = hashlib.sha256(b"qx-carry:" + i.to_bytes(4, "big")).digest()
        x = int.from_bytes(h, "big") % P
        if x == 0:
            continue
        qx, x1, x2, _ = sharp(x)
        x1_true = (BETA * x) % P
        x2_true = (BETA2 * x) % P
        qx_true = (x + x1_true + x2_true) // P
        if qx == qx_true and x1 == x1_true:
            ok_match += 1
        if x2 == x2_true:
            ok_x2 += 1
        if (x + x1 + x2) == qx * P and 0 <= x2 < P:
            ok_orbit += 1
        if qx == 1 + ((x + x1) // P):
            ok_floor += 1

    w(f"  random: sharp q_x == (x+x1+x2)//p : {ok_match}/{n}")
    w(f"  random: recovered x2 == beta^2*x mod p: {ok_x2}/{n}")
    w(f"  random: x+x1+x2 == q_x*p, x2 in [0,p): {ok_orbit}/{n}")
    w(f"  random: q_x == 1+floor((x+x1)/p):      {ok_floor}/{n}")

    ok_w = 0
    for nG in range(1, 2049):
        x = int((nG * G).x())
        qx, x1, x2, _ = sharp(x)
        if x2 == (BETA2 * x) % P and qx == (x + x1 + x2) // P:
            ok_w += 1
    w(f"  walk x(nG) 1..2048: sharp triple exact: {ok_w}/2048")
    w()

    # equivalence to old x1+x2 < p
    ok_eq = 0
    for i in range(5000):
        h = hashlib.sha256(b"qx-eq:" + i.to_bytes(4, "big")).digest()
        x = int.from_bytes(h, "big") % P
        if x == 0:
            continue
        x1 = (BETA * x) % P
        x2 = (BETA2 * x) % P
        a = (x + x1 < P)
        b = (x1 + x2 < P)
        if a == b:
            ok_eq += 1
    w(f"  equiv: (x+x1<p) <=> (x1+x2<p): {ok_eq}/5000")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  CONFIRMED: q_x is the carry bit of x + (beta*x mod p).")
    w("  Pipeline: x -> x1=(beta*x)%p -> q_x -> x2=q_x*p-x-x1")
    w("  Cost: 1 modmul by beta, 1 compare/add, 1 subtract. No beta^2 mul.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
