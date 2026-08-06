#!/usr/bin/env python3
"""How do plateaus 3-5, 26-29, 57-61, 95 correlate?"""
from __future__ import annotations

import csv
import math
from pathlib import Path

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_PLATEAU_3_11_19_27.txt")


def to_fac(n: int) -> list[int]:
    digs: list[int] = []
    i = 1
    x = abs(int(n))
    while x:
        digs.append(x % i)
        x //= i
        i += 1
    return digs


def pack(d: int) -> dict:
    digs = to_fac(d)
    mk = len(digs) - 1
    a = digs[mk]
    fk = math.factorial(mk)
    term = a * fk
    rem = d - term
    return {
        "digs": digs,
        "max_k": mk,
        "a": a,
        "digit_frac": a / mk if mk else 1.0,
        "cell_frac": rem / fk if fk else 0.0,
        "plateau_frac": (d - fk) / (mk * fk) if mk and d >= fk else 0.0,
        "mass_frac": term / d if d else 0.0,
    }


def main() -> None:
    solved: dict[int, int] = {}
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            solved[int(row["puzzle"])] = int(row["private_key"])

    by_k: dict[int, list[int]] = {}
    for n, d in solved.items():
        by_k.setdefault(pack(d)["max_k"], []).append(n)
    for k in by_k:
        by_k[k].sort()

    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 80)
    w("CORRELATION: 3-5  /  26-29  /  57-61  /  95")
    w("=" * 80)

    # Primary: same arithmetic progression on max_k
    w()
    w("1) FACTORADIC ORDER LADDER  max_k = 3 + 8t")
    w("-" * 80)
    for t, k in enumerate([3, 11, 19, 27]):
        ps = by_k.get(k, [])
        w(f"  t={t}  max_k={k:2d} = 3+8*{t}   puzzles={ps}  (len={len(ps)})")
    w("  next: t=4  max_k=35 = 3+8*4   <- Puzzle 135 band lead order")
    w("  next: t=5  max_k=43")

    w()
    w("2) PLATEAU START / END PROGRESSION")
    w("-" * 80)
    starts = [3, 26, 57, 95]
    ends = [5, 29, 61]  # 95 is singleton in CSV
    w(f"  starts: {starts}")
    d1 = [starts[i] - starts[i - 1] for i in range(1, len(starts))]
    w(f"  start deltas: {d1}   (23, 31, 38)")
    w(f"  start 2nd diff: {[d1[i]-d1[i-1] for i in range(1,len(d1))]}   (~+7..+8)")
    w(f"  ends:   {ends}")
    w(f"  end deltas: {[ends[i]-ends[i-1] for i in range(1,len(ends))]}")
    w("  Rough law: plateau for max_k=3+8t begins near n ~ growing ~+8 each step")

    # Fit start ~ a + b*t + c*t^2
    # t=0,1,2,3 -> 3,26,57,95
    w()
    w("  Quadratic fit start(t) ~ 3 + 19.5 t + 3.5 t^2 ? check:")
    for t, s in enumerate(starts):
        pred = 3 + 19 * t + 4 * t * t  # try integers
        pred2 = 3 + 20 * t + 3 * t * t
        pred3 = round(3 + 19.333 * t + 3.5 * t * t)
        w(f"    t={t} real={s}  3+19t+4t^2={pred}  3+20t+3t^2={pred2}")

    w()
    w("3) PER-KEY PHASES INSIDE EACH PLATEAU")
    w("-" * 80)
    w(f"{'n':>4} {'k':>3} {'lead':>8} {'dig':>6} {'plat':>6} {'cell':>6} {'mass':>6} {'band':>6}")
    for k in [3, 11, 19, 27]:
        w(f"  -- max_k={k} --")
        for n in by_k.get(k, []):
            d = solved[n]
            p = pack(d)
            lo = 1 << (n - 1)
            hi = 1 << n
            bf = (d - lo) / (hi - lo)
            lead = f"{p['a']}*{k}!"
            w(
                f"{n:4d} {k:3d} {lead:>8} {p['digit_frac']:6.3f} {p['plateau_frac']:6.3f} "
                f"{p['cell_frac']:6.3f} {p['mass_frac']:6.3f} {bf:6.3f}"
            )

    w()
    w("4) LEAD DIGIT CLIMB WITHIN PLATEAU (the sawtooth)")
    w("-" * 80)
    for k in [3, 11, 19, 27]:
        seq = []
        for n in by_k.get(k, []):
            p = pack(solved[n])
            seq.append(f"P{n}:{p['a']}/{k}={p['digit_frac']:.2f}")
        w(f"  k={k}: {' -> '.join(seq)}")
    w("  Pattern: within a fixed max_k, leading coeff a usually CLIMBS across")
    w("  successive puzzles, then order jumps (+8 on this ladder) and a resets low.")

    w()
    w("5) WHY THESE FOUR LINE UP")
    w("-" * 80)
    w("  They are not an arbitrary n-correlation.")
    w("  They are successive plateaus on the sparse order chain:")
    w("      max_k in {3, 11, 19, 27, 35, ...} = {3+8t}")
    w("  Adjacent solved plateaus in the CSV often differ by ~1 in max_k,")
    w("  but THIS subsequence steps by +8 — every 8th order rung.")
    w("  Puzzle-height spans widen because Stirling: n ~ k log2 k, so")
    w("  Delta n between k and k+8 grows with k (matches 23->31->38 starts).")

    # Stirling check
    w()
    w("6) STIRLING: bit-height vs max_k")
    w("-" * 80)
    for k in [3, 11, 19, 27, 35]:
        bits = math.factorial(k).bit_length()
        w(f"  {k}! bit_length={bits}  (puzzle bands near this height use max_k={k})")

    w()
    w("7) P135 LINK")
    w("-" * 80)
    w("  Same ladder continues: 3+8*4 = 35")
    w("  P135 lead in {2,3,4}x35!  — next cousin of 3-5 / 26-29 / 57-61 / 95")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    w()
    w(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
