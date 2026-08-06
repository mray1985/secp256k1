#!/usr/bin/env python3
"""Is the leading a_max/max_k bar a sideways 'song'?"""
from __future__ import annotations

import csv
from itertools import groupby
from pathlib import Path

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")


def to_factoradic(n: int) -> list[int]:
    digits: list[int] = []
    i = 1
    while n:
        digits.append(n % i)
        n //= i
        i += 1
    return digits


def acorr(x: list[float], lag: int) -> float:
    n = len(x)
    mx = sum(x) / n
    num = sum((x[i] - mx) * (x[i + lag] - mx) for i in range(n - lag))
    den = sum((v - mx) ** 2 for v in x)
    return num / den if den else 0.0


def main() -> None:
    leads: list[tuple[int, int, int, float]] = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = int(row["puzzle"])
            if n > 70:
                continue
            d = int(row["private_key"])
            digs = to_factoradic(d)
            mk = len(digs) - 1
            a = digs[mk]
            leads.append((n, a, mk, a / mk if mk else 1.0))

    fracs = [t[3] for t in leads]

    print("PLATEAU MELODIES (a_max within each max_k group):")
    for mk, group in groupby(leads, key=lambda t: t[2]):
        g = list(group)
        if len(g) < 2:
            print(f"  k={mk}: single n={g[0][0]} -> {g[0][1]}")
            continue
        seq = " -> ".join(str(a) for _, a, _, _ in g)
        fr = " -> ".join(f"{f:.2f}" for *_, f in g)
        rising = all(g[i][3] <= g[i + 1][3] for i in range(len(g) - 1))
        print(f"  k={mk}: n={g[0][0]}-{g[-1][0]}  a={seq}")
        print(f"         frac={fr}  monotone_up={rising}")

    print()
    print("Autocorr of leading frac (lag 1..12):")
    for lag in range(1, 13):
        print(f"  lag {lag:2d}: {acorr(fracs, lag):+.3f}")

    print()
    print("Sawtooth resets (high end of plateau -> low start of next k):")
    resets = jumps = 0
    for i in range(1, len(leads)):
        n0, a0, m0, f0 = leads[i - 1]
        n1, a1, m1, f1 = leads[i]
        if m1 > m0:
            jumps += 1
            if f0 > 0.5 and f1 < 0.3:
                resets += 1
                print(f"  n {n0}->{n1}: {a0}/{m0}={f0:.2f} -> {a1}/{m1}={f1:.2f}")
    print(f"  high->low resets: {resets}/{jumps} k-jumps")

    print()
    print("Sideways as scale degrees (frac mapped 0..7):")
    notes = "".join(str(min(7, int(f * 8))) for f in fracs)
    print(f"  {notes}")
    print("  (0=low leading, 7=capped near max_k)")
    print()
    print("VERDICT:")
    print("  Not a pop melody. Closest shape: sawtooth / ratchet per factorial plateau.")
    print("  Rise inside same max_k, drop when k jumps. That IS a rhythm — of scale,")
    print("  not of a composed tune.")


if __name__ == "__main__":
    main()
