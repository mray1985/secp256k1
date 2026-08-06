#!/usr/bin/env python3
"""
Triple identity harness: nG + mG = (n+m)G in Phi space.

Right side (truth): C_s = Phi((n+m)G)
Exact left side:    encode(decode(C_n) + decode(C_m))  == C_s

Also falsify naive decimal combines C_n ⊕ C_m ?= C_s on train/holdout.
"""
from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_TRIPLE_ADD.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
G = SECP256k1.generator
MAX_N = 200
TRAIN_S_MAX = 120  # triples with s=n+m <= this for "train"
HOLD_S_MIN = 121
HOLD_S_MAX = 200


def modinv(a: int, m: int = P) -> int:
    return pow(a % m, -1, m)


def phi(x: int, y: int) -> Fraction:
    return Fraction(x * P + y, P * P)


def decode(c: Fraction) -> tuple[int, int]:
    cp = c * P
    x = int(cp)
    y = int((cp - x) * P)
    return x, y


def encode(x: int, y: int) -> Fraction:
    return phi(x % P, y % P)


def ec_add(x1: int, y1: int, x2: int, y2: int) -> tuple[int, int]:
    """Affine add; assumes P1+P2 != O and finite."""
    if x1 == x2:
        if (y1 + y2) % P == 0:
            raise ValueError("sum is infinity")
        lam = (3 * x1 * x1) * modinv(2 * y1) % P
    else:
        lam = (y2 - y1) * modinv((x2 - x1) % P) % P
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return x3, y3


def phi_add_exact(ca: Fraction, cb: Fraction) -> Fraction:
    """Exact left side: decode -> EC add -> encode."""
    x1, y1 = decode(ca)
    x2, y2 = decode(cb)
    x3, y3 = ec_add(x1, y1, x2, y2)
    return encode(x3, y3)


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Phi triple add: left decode+EC+encode  vs  right C_{n+m}")
    w("=" * 88)

    Cs: list[Fraction] = []
    pt = G
    for _ in range(MAX_N):
        Cs.append(phi(int(pt.x()), int(pt.y())))
        pt = pt + G

    # Explicit 1G+2G=3G
    w("-" * 88)
    w("Example: 1G + 2G = 3G")
    w("-" * 88)
    left = phi_add_exact(Cs[0], Cs[1])
    right = Cs[2]
    w(f"  C1={float(Cs[0]):.12f}")
    w(f"  C2={float(Cs[1]):.12f}")
    w(f"  right C3={float(right):.12f}")
    w(f"  left  encode(decode(C1)+decode(C2))={float(left):.12f}")
    w(f"  left == right: {left == right}")
    w(f"  naive (C1+C2) mod 1 == right: {(Cs[0]+Cs[1]) % 1 == right}")
    w()

    # All triples
    triples = []
    for n in range(1, MAX_N):
        for m in range(1, MAX_N):
            s = n + m
            if s > MAX_N:
                continue
            # skip if nG == mG and would double — still fine via ec_add
            # skip  nG = -mG => infinity: (n+m)G=O => s ≡ 0 mod N, impossible for s<=200
            triples.append((n, m, s))

    train = [(n, m, s) for n, m, s in triples if s <= TRAIN_S_MAX]
    hold = [(n, m, s) for n, m, s in triples if HOLD_S_MIN <= s <= HOLD_S_MAX]

    w("-" * 88)
    w("Exact left side on all triples")
    w("-" * 88)
    exact_ok = 0
    for n, m, s in triples:
        if phi_add_exact(Cs[n - 1], Cs[m - 1]) == Cs[s - 1]:
            exact_ok += 1
    w(f"  encode(decode(Cn)+decode(Cm)) == C_{{n+m}}: {exact_ok}/{len(triples)}")
    w()

    def mod1(x: Fraction) -> Fraction:
        num, den = x.numerator, x.denominator
        return Fraction(num % den, den)

    candidates = {
        "(Ca+Cb) mod 1": lambda a, b: mod1(a + b),
        "(Ca+Cb)/2": lambda a, b: (a + b) / 2,
        "Ca*Cb": lambda a, b: a * b,
        "|Ca-Cb|": lambda a, b: abs(a - b),
        "max(Ca,Cb)": lambda a, b: max(a, b),
        "min(Ca,Cb)": lambda a, b: min(a, b),
        "(Ca+Cb) mod 1 avg mix": lambda a, b: mod1((a + b) / 2 + a * b),
        # layer toy: treat as float only for digit experiment — skip
    }

    w("-" * 88)
    w(f"Naive combine falsify  train s<= {TRAIN_S_MAX}  holdout s in [{HOLD_S_MIN},{HOLD_S_MAX}]")
    w("-" * 88)

    def score(fn, subset):
        exact = 0
        abs_err = 0.0
        for n, m, s in subset:
            pred = fn(Cs[n - 1], Cs[m - 1])
            act = Cs[s - 1]
            if pred == act:
                exact += 1
            abs_err += float(abs(pred - act))
        mae = abs_err / len(subset)
        return exact, mae

    for name, fn in candidates.items():
        te, tmae = score(fn, train)
        he, hmae = score(fn, hold)
        w(
            f"  {name:28s}  train exact {te}/{len(train)} MAE={tmae:.4f}  "
            f"hold exact {he}/{len(hold)} MAE={hmae:.4f}"
        )

    # Numerators as integers mod p^2
    den = P * P

    def num_of(c: Fraction) -> int:
        return (c.numerator * den) // c.denominator  # == x*p+y

    def num_add_mod(a, b):
        return Fraction((num_of(a) + num_of(b)) % den, den)

    te, tmae = score(num_add_mod, train)
    he, hmae = score(num_add_mod, hold)
    w(
        f"  {'(num_a+num_b) mod p^2':28s}  train exact {te}/{len(train)} MAE={tmae:.4f}  "
        f"hold exact {he}/{len(hold)} MAE={hmae:.4f}"
    )
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Keep the right: C_{n+m} is ground truth.")
    w("  Exact left encode(decode(Cn)+decode(Cm)) matches 100% — that IS EC add.")
    w("  Decimal combines (sum mod 1, product, num add mod p^2, ...): 0 exact on holdout.")
    w("  Wrap-at-1 is field geometry for x/p, not the group law on Phi.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    w(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
