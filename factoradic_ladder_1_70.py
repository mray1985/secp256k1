#!/usr/bin/env python3
"""Clean factoradic ladder for puzzles 1-70 — full key + lower bits."""
from __future__ import annotations

import csv
from pathlib import Path

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_LADDER_1_70.txt")


def to_factoradic(n: int) -> list[int]:
    digits: list[int] = []
    i = 1
    while n:
        digits.append(n % i)
        n //= i
        i += 1
    return digits


def fmt_top(digs: list[int], m: int = 6) -> str:
    terms = [(k, a) for k, a in enumerate(digs) if a]
    terms = terms[::-1][:m]
    if not terms:
        return "0"
    return " + ".join(f"{a}*{k}!" for k, a in terms)


def main() -> None:
    rows = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = int(row["puzzle"])
            d = int(row["private_key"])
            if n > 70:
                continue
            digs = to_factoradic(d)
            lo = 1 << (n - 1)
            lower = d - lo
            ld = to_factoradic(lower) if lower else [0]
            rows.append((n, d, digs, lower, ld))

    out: list[str] = []
    out.append("PUZZLE 1-70  —  FACTORADIC LADDER")
    out.append("=" * 88)
    out.append("")
    out.append("A) FULL KEY  d = sum a_k * k!")
    out.append(f"{'n':>3} {'max_k':>5} {'lead':>8}  top terms")
    out.append("-" * 88)
    prev_k = None
    for n, d, digs, lower, ld in rows:
        mk = len(digs) - 1
        lead = f"{digs[mk]}*{mk}!"
        mark = "  << k jumps" if prev_k is not None and mk != prev_k else ""
        out.append(f"{n:3d} {mk:5d} {lead:>8}  {fmt_top(digs)}{mark}")
        prev_k = mk

    out.append("")
    out.append("B) LOWER BITS ONLY  (d - 2^(n-1))  — band MSB stripped")
    out.append(f"{'n':>3} {'low_bits':>8} {'max_k':>5} {'lead':>8}  top terms")
    out.append("-" * 88)
    for n, d, digs, lower, ld in rows:
        mk = len(ld) - 1 if ld else 0
        lead = f"{ld[mk]}*{mk}!" if ld else "0"
        lb = lower.bit_length() if lower else 0
        out.append(f"{n:3d} {lb:8d} {mk:5d} {lead:>8}  {fmt_top(ld) if lower else '0'}")

    out.append("")
    out.append("C) LEADING COEFF a_max/max_k  (0% ..... 50% ..... 100%)")
    for n, d, digs, lower, ld in rows:
        mk = len(digs) - 1
        a = digs[mk]
        frac = a / mk if mk else 1.0
        width = 40
        pos = min(width, int(round(frac * width)))
        bar = "." * pos + "#" + "." * (width - pos)
        out.append(f"{n:3d} |{bar}| {a}/{mk}")

    out.append("")
    out.append("D) HOW TO READ THIS")
    out.append("  - Section A: whole key as factorial digits. max_k steps up as the band grows.")
    out.append("  - Within a plateau (same max_k), leading coeff often climbs, then k jumps.")
    out.append("  - Section B: strip the forced high bit 2^(n-1). That lower integer is the")
    out.append("    'payload' fingerprint — closer to whatever the wallet contributed.")
    out.append("  - Section C: leading digit as a fraction of its legal max (0..k).")
    out.append("    Scattered = no simple arithmetic progression of leading terms.")
    n, d, digs, lower, ld = rows[-1]
    out.append("")
    out.append(f"  P70 full lead: {digs[-1]}*{len(digs)-1}!")
    out.append(f"  P70 lower     = {lower}")
    out.append(f"  P70 lower top = {fmt_top(ld, 12)}")

    text = "\n".join(out)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(text)
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
