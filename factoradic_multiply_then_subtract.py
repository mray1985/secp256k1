#!/usr/bin/env python3
"""Correct factoradic lead: term = a * k!, then subtract from d (or add when rebuilding).

Old probe used bare digit_frac = a/k without forming a*k!.
This script:
  1. Verifies reconstruction sum(a_i * i!) == d
  2. Defines plateau measures AFTER multiply-then-subtract
  3. Recomputes hi/lo correlations under those defs
"""
from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_MULTIPLY_THEN_SUBTRACT.txt")

N_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def to_factoradic(n: int) -> list[int]:
    digits: list[int] = []
    i = 1
    x = abs(int(n))
    while x:
        digits.append(x % i)
        x //= i
        i += 1
    return digits


def reconstruct(digs: list[int]) -> int:
    return sum(a * math.factorial(k) for k, a in enumerate(digs))


def lead_pack(n: int) -> dict:
    """
    Correct lead step:
      a = leading digit of max_k
      term = a * max_k!          # multiply
      rem  = n - term            # subtract from d
    """
    digs = to_factoradic(n)
    if not digs:
        return {
            "k": 0,
            "a": 0,
            "term": 0,
            "rem": 0,
            "digit_frac": 0.0,
            "mass_frac": 0.0,
            "cell_frac": 0.0,
            "plateau_frac": 0.0,
            "ok": True,
        }
    k = len(digs) - 1
    a = digs[k]
    fk = math.factorial(k)
    term = a * fk  # multiply n! by how many times
    rem = n - term  # subtract from d
    ok = reconstruct(digs) == n
    digit_frac = (a / k) if k else 1.0
    mass_frac = (term / n) if n else 0.0
    cell_frac = (rem / fk) if fk else 0.0  # residue inside the a*k! cell
    # position inside the full k-plateau [k!, (k+1)!)
    plateau_frac = ((n - fk) / (k * fk)) if (k and n >= fk) else 0.0
    return {
        "k": k,
        "a": a,
        "term": term,
        "rem": rem,
        "digit_frac": digit_frac,
        "mass_frac": mass_frac,
        "cell_frac": cell_frac,
        "plateau_frac": plateau_frac,
        "ok": ok,
    }


def pub_x(d: int) -> int:
    sk = SigningKey.from_secret_exponent(d % N_ORDER, curve=SECP256k1, hashfunc=hashlib.sha256)
    return int.from_bytes(sk.get_verifying_key().to_string()[:32], "big")


def lead_native(x: int, m: int) -> int:
    L = max(x.bit_length(), m)
    return x >> (L - m)


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    denx = sum((a - mx) ** 2 for a in xs) ** 0.5
    deny = sum((b - my) ** 2 for b in ys) ** 0.5
    return num / (denx * deny) if denx and deny else 0.0


def hits(xs: list[float], ys: list[float], thr: float = 0.1) -> int:
    return sum(1 for a, b in zip(xs, ys) if abs(a - b) < thr)


def main() -> None:
    puzzles: list[tuple[int, int]] = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = int(row["puzzle"])
            d = int(row["private_key"])
            if n > 70:
                continue
            puzzles.append((n, d))

    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("FACTORADIC: multiply k! by a, THEN subtract from d (or add when rebuilding)")
    w("=" * 88)
    w()
    w("Correct lead step:")
    w("  term = a * k!")
    w("  rem  = d - term")
    w("  rebuild: d = sum_i (a_i * i!)")
    w()

    bad = [(n, d) for n, d in puzzles if not lead_pack(d)["ok"]]
    w(f"Reconstruction check: {len(puzzles) - len(bad)}/{len(puzzles)} exact  failures={len(bad)}")
    w()
    w(f"{'n':>3} {'d':>16} {'a*k!':>18} {'rem=d-term':>12} {'dig':>6} {'cell':>6} {'plat':>6} {'mass':>6}")
    w("-" * 88)
    for n, d in puzzles[:20]:
        p = lead_pack(d)
        w(
            f"{n:3d} {d:16d} {p['a']}*{p['k']}!={p['term']:<10d} "
            f"{p['rem']:12d} {p['digit_frac']:6.3f} {p['cell_frac']:6.3f} "
            f"{p['plateau_frac']:6.3f} {p['mass_frac']:6.3f}"
        )
    w("  ...")

    w()
    w("Building pubkeys...")
    pubs = [(n, d, pub_x(d)) for n, d in puzzles]

    defs = ["digit_frac", "cell_frac", "plateau_frac", "mass_frac"]
    w()
    w("=" * 88)
    w("HI vs LO under each definition")
    w("=" * 88)
    w(f"{'def':<14} {'r_hi':>8} {'r_lo':>8} {'H_hi':>8} {'H_lo':>8} {'gap_r':>8}")
    w("-" * 88)
    for name in defs:
        d_f: list[float] = []
        hi_f: list[float] = []
        lo_f: list[float] = []
        for n, d, px in pubs:
            pd = lead_pack(d)
            phi = lead_pack(lead_native(px, n))
            plo = lead_pack(px & ((1 << n) - 1))
            d_f.append(float(pd[name]))
            hi_f.append(float(phi[name]))
            lo_f.append(float(plo[name]))
        rh = pearson(d_f, hi_f)
        rl = pearson(d_f, lo_f)
        Hh = hits(d_f, hi_f)
        Hl = hits(d_f, lo_f)
        w(f"{name:<14} {rh:+8.3f} {rl:+8.3f} {Hh:5d}/70 {Hl:5d}/70 {rh-rl:+8.3f}")

    w()
    w("READOUT")
    w("  digit_frac = a/k              (old; ignores multiply)")
    w("  cell_frac  = (d - a*k!)/k!    (AFTER multiply-then-subtract)")
    w("  plateau_frac = (d - k!)/(k*k!)  position in [k!,(k+1)!)")
    w("  mass_frac  = (a*k!)/d         lead term weight in d")
    w()
    w("  The multiply step is mandatory: term = a*k! before rem = d - term.")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    w()
    w(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
