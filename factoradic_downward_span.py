#!/usr/bin/env python3
"""
Downward factoradic span to CREATE each key.

From lead max_k downward: max_k!, (max_k-1)!, ... until the consecutive
nonzero run breaks (first zero digit). That is 'how many factoradics back'.
"""
from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_DOWNWARD_SPAN.txt")


def to_fac(n: int) -> list[int]:
    digs: list[int] = []
    i = 1
    x = abs(int(n))
    while x:
        digs.append(x % i)
        x //= i
        i += 1
    return digs


def downward_run(digs: list[int]) -> tuple[int, int, int, list[tuple[int, int]]]:
    """
    From max_k down, collect consecutive nonzero a_k until first zero.
    Returns (max_k, stop_k_exclusive, run_len, [(k,a), ...]).
    Example: if digits nonzero at 28..24 then 0 at 23 -> run uses 28!..24! (len 5),
    breaks before 23!.
    """
    if not digs:
        return 0, 0, 0, []
    mk = len(digs) - 1
    terms: list[tuple[int, int]] = []
    for k in range(mk, -1, -1):
        a = digs[k]
        if a == 0:
            break
        terms.append((k, a))
    run_len = len(terms)
    stop = terms[-1][0] - 1 if terms else mk  # first broken (zero) level, or -1
    return mk, stop, run_len, terms


def mass_top(digs: list[int], r: int) -> float:
    """Fraction of d sitting in the top r factoradic orders (max_k .. max_k-r+1)."""
    if not digs:
        return 0.0
    mk = len(digs) - 1
    total = sum(digs[k] * math.factorial(k) for k in range(len(digs)))
    if total == 0:
        return 0.0
    top = 0
    for off in range(r):
        k = mk - off
        if k < 0:
            break
        top += digs[k] * math.factorial(k)
    return top / total


def main() -> None:
    rows = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = int(row["puzzle"])
            d = int(row["private_key"])
            digs = to_fac(d)
            mk, stop, run, terms = downward_run(digs)
            rows.append(
                {
                    "n": n,
                    "d": d,
                    "digs": digs,
                    "max_k": mk,
                    "stop": stop,
                    "run": run,
                    "terms": terms,
                    "span_lo": terms[-1][0] if terms else mk,
                    "mass5": mass_top(digs, 5),
                    "mass_run": mass_top(digs, run) if run else 0.0,
                }
            )

    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("DOWNWARD SPAN TO CREATE EACH KEY")
    w("lead k! -> (k-1)! -> (k-2)! -> ... until first ZERO digit (break)")
    w("=" * 88)
    w()
    w(f"{'n':>3} {'max_k':>5} {'run':>4} {'span':>12}  chain (a*k! ... until break)")
    w("-" * 88)
    for r in rows:
        if r["terms"]:
            hi = r["max_k"]
            lo = r["span_lo"]
            span = f"{hi}!..{lo}!"
            chain = " + ".join(f"{a}*{k}!" for k, a in r["terms"])
            br = f"  | break at {r['stop']}!" if r["stop"] >= 0 else "  | unbroken to 0!"
        else:
            span = "-"
            chain = "0"
            br = ""
        w(f"{r['n']:3d} {r['max_k']:5d} {r['run']:4d} {span:>12}  {chain}{br}")

    runs = [r["run"] for r in rows]
    c = Counter(runs)
    w()
    w("-" * 88)
    w("Run-length histogram (how many factoradics back before break)")
    w("-" * 88)
    for g in sorted(c):
        w(f"  back {g:2d}: {c[g]:3d}  {'#' * min(c[g], 60)}")
    w()
    w(f"N = {len(rows)}")
    w(f"mean run = {sum(runs)/len(runs):.2f}")
    w(f"median run = {sorted(runs)[len(runs)//2]}")
    w(f"mode run = {c.most_common(1)[0]}")
    w(f"run == 5: {sum(1 for x in runs if x == 5)}/{len(runs)} = {sum(1 for x in runs if x == 5)/len(runs):.1%}")
    w(f"run <= 5: {sum(1 for x in runs if x <= 5)}/{len(runs)} = {sum(1 for x in runs if x <= 5)/len(runs):.1%}")
    w(f"run >= 5: {sum(1 for x in runs if x >= 5)}/{len(runs)} = {sum(1 for x in runs if x >= 5)/len(runs):.1%}")
    w(f"run in 4..6 (near 5): {sum(1 for x in runs if 4 <= x <= 6)}/{len(runs)} = {sum(1 for x in runs if 4 <= x <= 6)/len(runs):.1%}")

    w()
    w("-" * 88)
    w("Mass in top-5 orders (whether or not a zero sits inside)")
    w("-" * 88)
    m5 = [r["mass5"] for r in rows]
    w(f"mean mass in top 5 factorials = {sum(m5)/len(m5):.3f}")
    w(f"median = {sorted(m5)[len(m5)//2]:.3f}")
    w(f"mass5 >= 0.99: {sum(1 for x in m5 if x >= 0.99)}/{len(m5)}")
    w(f"mass5 >= 0.90: {sum(1 for x in m5 if x >= 0.90)}/{len(m5)}")

    # highlight examples matching user style 28!..21!
    w()
    w("-" * 88)
    w("Examples (user-style downward lists)")
    w("-" * 88)
    for want_n in (66, 70, 71, 100, 110, 130):
        # 71 may be missing from solved CSV
        hit = next((r for r in rows if r["n"] == want_n), None)
        if not hit:
            w(f"  P{want_n}: not in solved CSV")
            continue
        mk = hit["max_k"]
        lo = hit["span_lo"]
        seq = " ".join(f"{k}!" for k in range(mk, lo - 1, -1))
        w(f"  P{want_n}: max_k={mk} run={hit['run']}  {seq}  then break")
        w(f"         terms: " + " + ".join(f"{a}*{k}!" for k, a in hit["terms"]))

    # hypothetical P71 / P135 band construction windows
    w()
    w("-" * 88)
    w("Band construction windows (possible max_k, then downward)")
    w("-" * 88)
    import math as _m

    def band_orders(n: int) -> list[int]:
        lo, hi = 1 << (n - 1), (1 << n) - 1
        out = []
        k = 1
        while _m.factorial(k) <= hi:
            fk = _m.factorial(k)
            fkp = _m.factorial(k + 1)
            if max(lo, fk) <= min(hi, fkp - 1):
                out.append(k)
            k += 1
        return out

    for n in (71, 135):
        ks = band_orders(n)
        w(f"  P{n}: possible lead orders {ks}")
        for k in ks:
            # show a 5-back construction window ending near prior plateaus
            window = list(range(k, max(k - 5, 0), -1))
            w(f"    from {k}!  five-back window: " + " ".join(f"{j}!" for j in window))

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    w()
    w(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
