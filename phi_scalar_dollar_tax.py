#!/usr/bin/env python3
"""
Scalar-as-dollars tax: d=$1, 2=$2, 2^134=$2^134 — rate/levy scales with d.

Not storewide 10%. Ask whether a d-dependent levy links to Phi layers / r*=p/y-2.
"""
from __future__ import annotations

import csv
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_SCALAR_DOLLAR_TAX.txt")
KEYS = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = SECP256k1.generator


def phi(x: int, y: int) -> Fraction:
    return Fraction(x * P + y, P * P)


def r_star(y: int) -> Fraction:
    """Fine sales-tax rate that implements negation: Fine*(1+r*) = 1/p - Fine."""
    return Fraction(P, y) - 2


def load_solved() -> list[tuple[int, int]]:
    rows = []
    with KEYS.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pn = int(r["puzzle"])
            if pn == 135:
                continue
            raw = r["private_key"].strip()
            d = int(raw, 16) if any(c in raw.lower() for c in "abcdef") else int(raw)
            d %= N
            if d:
                rows.append((pn, d))
    return rows


def corr(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = sum((a - mx) ** 2 for a in xs) ** 0.5
    dy = sum((b - my) ** 2 for b in ys) ** 0.5
    if dx == 0 or dy == 0:
        return float("nan")
    return num / (dx * dy)


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Scalar-as-dollars: levy scales with d (not storewide %)")
    w("=" * 88)
    w("  Metaphor: d=1 -> $1, d=2 -> $2, d=2^134 -> $2^134")
    w("  r*(P) = p/y - 2 still comes from y of d*G, not from d as cash.")
    w()

    # --- walk: r* vs d ---
    w("-" * 88)
    w("1) Walk d=1..128: is r* a simple function of dollar-scalar d?")
    w("-" * 88)
    ds, rs, ys, logd = [], [], [], []
    for d in range(1, 129):
        pt = d * G
        y = int(pt.y())
        r = r_star(y)
        ds.append(float(d))
        rs.append(float(r))
        ys.append(float(y))
        logd.append(float(d.bit_length()))

    w(f"  corr(d, r*):       {corr(ds, rs):.6f}")
    w(f"  corr(log2(d), r*): {corr(logd, rs):.6f}")
    w(f"  corr(y, r*):       {corr(ys, rs):.6f}  (exact monotone in 1/y by construction)")
    w()
    w("  samples:")
    for d in (1, 2, 3, 5, 10, 64, 100, 128):
        pt = d * G
        y = int(pt.y())
        r = r_star(y)
        w(f"    d=${d:<4d}  y_mod_p bits~{y.bit_length():3d}  r*=p/y-2 = {float(r):+.6e}")
    w()

    # --- powers of two dollars ---
    w("-" * 88)
    w("2) Dollar ladder d = 2^k  (puzzle-sized wallets)")
    w("-" * 88)
    for k in list(range(0, 16)) + [32, 64, 80, 100, 120, 134]:
        d = pow(2, k)
        if d % N == 0:
            continue
        pt = (d % N) * G
        y = int(pt.y())
        r = r_star(y)
        # also check Fine*(1+r) == neg Fine
        x = int(pt.x())
        Fine = Fraction(y, P * P)
        ok = Fine * (1 + r) == Fraction(1, P) - Fine
        w(f"  $2^{k:<3d} = d~2^{k:<3d}  r*={float(r):+.6e}  neg-tax-exact={ok}")
    w()

    # --- candidate: tax_amount = alpha * d mapped into Fine somehow ---
    w("-" * 88)
    w("3) Candidate dollar levies into Phi (exact hit rates)")
    w("-" * 88)
    w("  A) C_tax = C + d/p^2          (add $d into Fine units)")
    w("  B) C_tax = C * (1 + d/N)      (tax proportional to wealth / order)")
    w("  C) Fine_tax = Fine * (1 + d)  (absurd scale)")
    w("  D) r = d                      (use scalar itself as Fine tax rate)")
    hits = {"A_neg": 0, "B_neg": 0, "D_neg": 0, "D_rstar": 0}
    n_walk = 64
    for d in range(1, n_walk + 1):
        pt = d * G
        x, y = int(pt.x()), int(pt.y())
        C = phi(x, y)
        C_neg = phi(x, (-y) % P)
        X = Fraction(x, P)
        Fine = Fraction(y, P * P)
        A = C + Fraction(d, P * P)
        B = C * (1 + Fraction(d, N))
        D = X + Fine * (1 + d)
        if A == C_neg:
            hits["A_neg"] += 1
        if B == C_neg:
            hits["B_neg"] += 1
        if D == C_neg:
            hits["D_neg"] += 1
        if Fraction(d) == r_star(y):
            hits["D_rstar"] += 1
    w(f"  walk 1..{n_walk}: A==Phi(-P) {hits['A_neg']}/{n_walk}")
    w(f"  walk 1..{n_walk}: B==Phi(-P) {hits['B_neg']}/{n_walk}")
    w(f"  walk 1..{n_walk}: Fine*(1+d)==neg {hits['D_neg']}/{n_walk}")
    w(f"  walk 1..{n_walk}: d == r*=p/y-2     {hits['D_rstar']}/{n_walk}")
    w()

    # solved keys: r* vs puzzle index / log d
    w("-" * 88)
    w("4) Solved keys: r* vs puzzle n and bit-length of d")
    w("-" * 88)
    solved = load_solved()
    pn_l, r_l, bits_l = [], [], []
    for pn, d in solved:
        if pn > 120:  # skip huge mul slow? 135 skipped; 130s ok with ecdsa
            pass
        pt = d * G
        y = int(pt.y())
        r = float(r_star(y))
        pn_l.append(float(pn))
        r_l.append(r)
        bits_l.append(float(d.bit_length()))
    w(f"  n_keys={len(solved)}  corr(puzzle, r*)={corr(pn_l, r_l):.6f}")
    w(f"  corr(bitlen(d), r*)={corr(bits_l, r_l):.6f}")
    for pn, d in solved:
        if pn in (1, 2, 10, 20, 40, 70, 100, 105, 110, 115, 120, 125, 130):
            y = int((d * G).y())
            w(f"    puzzle {pn}: $d~2^{d.bit_length()-1}..  r*={float(r_star(y)):+.6e}")
    w()

    w("-" * 88)
    w("5) What the dollar metaphor gets right / wrong")
    w("-" * 88)
    w("  RIGHT: scalars have magnitude — $1 vs $2^134 is meaningful for search cost.")
    w("  WRONG: r* is not a tax on that wallet size. r* = p/y-2 uses curve y of d*G.")
    w("  y(d*G) is pseudorandom in F_p; it does not track d or 2^k smoothly.")
    w("  So bigger dollar d does not imply bigger (or smoother) Fine-tax rate.")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Per-point / per-dollar scaling was understood: levy may depend on d.")
    w("  But the negation Fine rate r* depends on y(dG), not on d as cash.")
    w("  corr(d, r*) ~ 0 on the walk; 2^k ladder jumps around with no trend.")
    w("  Dollar size of d is real for puzzles; it is not the Phi Fine tax dial.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
