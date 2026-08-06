#!/usr/bin/env python3
"""Factoradic pattern scan across all known Bitcoin puzzle private keys."""
from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_PATTERN_REPORT.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_full_digits.csv")


def to_factoradic(n: int) -> list[int]:
    """digits[k] = coeff of k!, with 0 <= digits[k] <= k."""
    digits: list[int] = []
    i = 1
    while n:
        digits.append(n % i)
        n //= i
        i += 1
    return digits


def main() -> None:
    rows = list(csv.DictReader(CSV_IN.open(newline="", encoding="utf-8")))
    records = []
    for row in rows:
        n = int(row["puzzle"])
        d = int(row["private_key"])
        digs = to_factoradic(d)
        max_k = len(digs) - 1 if digs else 0
        nonzero = [(k, a) for k, a in enumerate(digs) if a]
        leading_k, leading_a = (max_k, digs[max_k]) if digs else (0, 0)
        density = len(nonzero) / max(max_k, 1)
        # expected max_k for a random n-bit number: roughly where k! ~ 2^n
        # Stirling: k log k ~ n log 2
        records.append(
            {
                "puzzle": n,
                "d": d,
                "bits": d.bit_length(),
                "max_k": max_k,
                "leading_a": leading_a,
                "leading_cap": max_k,  # a_k <= k
                "leading_frac": leading_a / max_k if max_k else 0,
                "nonzero": len(nonzero),
                "density": density,
                "digits": digs,
                "has_0!": False,  # we start at 0! coeff always 0 in this encoding for n>0? digits[0]=n%1=0
            }
        )

    lines: list[str] = []
    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 80)
    w(f"FACTORADIC PATTERN REPORT — {len(records)} known puzzle keys")
    w("=" * 80)
    w()
    w("Encoding: d = sum a_k * k!  with  0 <= a_k <= k")
    w("(unique representation of every integer)")
    w()

    # Table: puzzle vs max_k vs bits
    w("-" * 80)
    w(f"{'n':>4} {'bits':>5} {'max_k':>6} {'a_max':>5} {'a/k':>6} {'nnz':>4} {'dens':>6}  leading")
    w("-" * 80)
    for r in records:
        lead = f"{r['leading_a']}*{r['max_k']}!"
        w(
            f"{r['puzzle']:4d} {r['bits']:5d} {r['max_k']:6d} {r['leading_a']:5d} "
            f"{r['leading_frac']:6.3f} {r['nonzero']:4d} {r['density']:6.3f}  {lead}"
        )

    w()
    w("=" * 80)
    w("SEMI-PATTERNS (what actually shows up)")
    w("=" * 80)

    # 1. max_k vs bits
    w()
    w("1) max_k tracks bit-length (Stirling): k! ~ 2^bits")
    w("   Roughly max_k ~ bits / log2(k) - grows slower than bits.")
    # fit: for each, bits / max_k
    ratios = [r["bits"] / r["max_k"] for r in records if r["max_k"]]
    w(f"   bits/max_k: min={min(ratios):.2f} median={sorted(ratios)[len(ratios)//2]:.2f} max={max(ratios):.2f}")

    # 2. leading coefficient distribution
    w()
    w("2) Leading digit a_max (coeff of max_k!) — should look 'random' in 1..max_k")
    # normalize leading_frac
    fracs = [r["leading_frac"] for r in records if r["max_k"] >= 2]
    buckets = Counter(int(f * 10) for f in fracs)  # 0..9
    w("   leading_a/max_k decile counts (0=small leading, 9=near max):")
    w("   " + " ".join(f"{i}:{buckets.get(i,0)}" for i in range(10)))

    # 3. density of nonzero terms
    w()
    w("3) Nonzero-term density = nnz / max_k")
    dens = [r["density"] for r in records]
    w(f"   dens: min={min(dens):.3f} median={sorted(dens)[len(dens)//2]:.3f} max={max(dens):.3f}")
    w("   (random integers tend toward dens ~ 0.63 of digits nonzero in related bases;")
    w("    here nnz/max_k is high because most low digits are used)")

    # 4. Is max_k monotone in puzzle number?
    w()
    w("4) max_k vs puzzle index n (should rise with n, with plateaus)")
    jumps = []
    for i in range(1, len(records)):
        if records[i]["max_k"] != records[i - 1]["max_k"]:
            jumps.append(
                (records[i - 1]["puzzle"], records[i]["puzzle"],
                 records[i - 1]["max_k"], records[i]["max_k"])
            )
    w(f"   max_k changes {len(jumps)} times across the list")
    w("   first few jumps (n_prev -> n, k_prev -> k):")
    for j in jumps[:15]:
        w(f"     puzzle {j[0]}->{j[1]}: max_k {j[2]}->{j[3]}")

    # 5. Consecutive puzzle digit correlation (leading)
    w()
    w("5) Do consecutive puzzles share leading structure? (usually NO — keys are independent)")
    same_maxk = 0
    close_lead = 0
    pairs = 0
    for i in range(1, len(records)):
        a, b = records[i - 1], records[i]
        if b["puzzle"] != a["puzzle"] + 1:
            continue  # skip gaps (every-5th only later)
        pairs += 1
        if a["max_k"] == b["max_k"]:
            same_maxk += 1
            if abs(a["leading_a"] - b["leading_a"]) <= 1:
                close_lead += 1
    w(f"   consecutive pairs checked: {pairs}")
    w(f"   same max_k: {same_maxk}/{pairs}")
    w(f"   same max_k AND |delta leading_a|<=1: {close_lead}/{pairs}")

    # 6. Band structure: d in [2^{n-1}, 2^n)
    w()
    w("6) Band check: puzzle n key should satisfy 2^{n-1} <= d < 2^n (for sequential 1..70)")
    band_ok = 0
    band_fail = []
    for r in records:
        n = r["puzzle"]
        if n > 70 and n % 5 == 0:
            # every-5th still n-bit band
            pass
        lo, hi = 1 << (n - 1), (1 << n)
        if lo <= r["d"] < hi:
            band_ok += 1
        else:
            band_fail.append(n)
    w(f"   in-band: {band_ok}/{len(records)}")
    if band_fail:
        w(f"   out-of-band puzzles: {band_fail[:20]}")

    # 7. Semi-pattern summary
    w()
    w("=" * 80)
    w("WHAT COUNTS AS A 'SEMI-PATTERN'")
    w("=" * 80)
    w("YES (structural, expected for ANY integers in growing bands):")
    w("  - max_k rises with puzzle n / bit-length (factorial scale)")
    w("  - unique digits 0..k for each place (factoradic law)")
    w("  - nnz grows roughly with max_k")
    w()
    w("NO (not a creator recipe / not predictive for unsolved keys):")
    w("  - leading coefficients look scattered, not a simple sequence")
    w("  - consecutive puzzles do not share a simple digit progression")
    w("  - factoradic of random-looking band keys always looks 'patterned'")
    w("    because the *representation* is structured, not the keys")
    w()
    w("USEFUL framing:")
    w("  factoradic = change of base to mixed radix (1,2,3,...,k+1)")
    w("  Comparing digit vectors across n shows SCALE growth, not a")
    w("  shared secret polynomial. For unsolved n, you still need d first")
    w("  (or a model of the wallet), then factoradic is just a rewrite.")

    # write full digits CSV
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        # find global max_k
        K = max(r["max_k"] for r in records)
        fieldnames = ["puzzle", "bits", "max_k", "leading_a", "nonzero", "density"] + [
            f"a{k}" for k in range(K + 1)
        ]
        wr = csv.DictWriter(f, fieldnames=fieldnames)
        wr.writeheader()
        for r in records:
            row = {
                "puzzle": r["puzzle"],
                "bits": r["bits"],
                "max_k": r["max_k"],
                "leading_a": r["leading_a"],
                "nonzero": r["nonzero"],
                "density": f"{r['density']:.4f}",
            }
            for k in range(K + 1):
                row[f"a{k}"] = r["digits"][k] if k < len(r["digits"]) else 0
            wr.writerow(row)

    OUT.write_text("\n".join(lines), encoding="utf-8")
    w()
    w(f"Wrote {OUT}")
    w(f"Wrote {CSV_OUT} (full digit matrix)")


if __name__ == "__main__":
    main()
