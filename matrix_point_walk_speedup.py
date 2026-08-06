#!/usr/bin/env python3
"""
What those ~220 lines actually say (and the only decimal that matters):

SPEEDUP (not decimal-string arithmetic):
  factoradic/carry matrix
    -> recurring scalar rule  d' = d + Delta  or  d' = a*d + b
    -> precompute Delta*G  (or use double/add)
    -> each next point = ONE Jacobian EC add/double
    -> NOT a full scalar multiplication from scratch

DECIMAL DISPLAY (right of the point only):
  0.<156 digits of x/p>.<156 digits of y/p>
  That is the affine print form. It is NOT how you add points.
  Internally: Jacobian (X:Y:Z) with x = X/Z^2, y = Y/Z^3 (mod p).

Hard boundary (from the same text):
  There is NO decimal encoding where adding the printed strings
  equals point addition. That would solve the discrete log.
"""
from __future__ import annotations

import csv
import math
import time
from collections import Counter, defaultdict
from pathlib import Path

from ecdsa import SECP256k1, ellipticcurve

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\MATRIX_POINT_WALK_SPEEDUP.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\matrix_point_walk_speedup.csv")

DEC = 156
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
G = SECP256k1.generator
CURVE = SECP256k1.curve


def frac_digits(numer: int, denom: int, places: int = DEC) -> str:
    numer = abs(int(numer)) % int(denom)
    return str((numer * (10**places)) // denom).zfill(places)


def print_0xy(pt: ellipticcurve.Point) -> str:
    """0.<x/p>.<y/p>  — right-of-decimal coordinate print (156+156 digits)."""
    if pt == ellipticcurve.INFINITY:
        return "0." + ("0" * DEC) + "." + ("0" * DEC)
    x, y = int(pt.x()), int(pt.y())
    return f"0.{frac_digits(x, P)}.{frac_digits(y, P)}"


def to_fac(n: int) -> list[int]:
    digs: list[int] = []
    i = 1
    x = abs(int(n))
    while x:
        digs.append(x % i)
        x //= i
        i += 1
    return digs


def max_k(d: int) -> int:
    digs = to_fac(d)
    return len(digs) - 1 if digs else 0


def lead_a(d: int) -> int:
    digs = to_fac(d)
    return digs[-1] if digs else 0


def main() -> None:
    rows: list[tuple[int, int]] = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append((int(row["puzzle"]), int(row["private_key"])))
    rows.sort()

    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("SPEEDUP FROM THE MATRIX ESSAY (decoded)")
    w("=" * 88)
    w()
    w("WHAT THE ~220 LINES CLAIM")
    w("  1. Correlate CHANGE in d with CHANGE in P, not digit strings of x,y.")
    w("  2. If d' = d + Delta (mod N):   P' = P + Delta*G")
    w("     If d' = 2d + 1:              P' = 2P + G")
    w("     If d' = a*d + b:             P' = a*P + b*G")
    w("  3. If only a few Delta values repeat, PRECOMPUTE those Delta*G once.")
    w("     Then each matrix row costs ONE point addition, not a full d*G.")
    w("  4. Keep working points in Jacobian form (avoid inverses every step).")
    w("  5. Convert to printed decimal ONLY when checking:")
    w("        0.<x/p 156 digits>.<y/p 156 digits>")
    w("     That is the 'right side of the decimal place' — DISPLAY of x/p,y/p.")
    w()
    w("WHAT IS NOT A SPEEDUP")
    w("  - Adding/multiplying the printed decimal digit strings of x and y")
    w("  - Nested constructions like (x.(y/p))/p as an EC replacement")
    w("  - Any L(P) with L(P+Q)=L(P)+L(Q) mod N  (that IS the discrete log)")
    w()

    # ---- Lead-matrix deltas (where unique Delta count is SMALL) ----
    w("-" * 88)
    w("A) FACTORADIC LEAD MATRIX — recurring Delta = da * k!")
    w("   (this is where unique deltas stay small enough to precompute)")
    w("-" * 88)

    by_k: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for n, d in rows:
        by_k[max_k(d)].append((n, d))

    # Collect lead steps globally as (k, da) and as absolute Delta=da*k!
    da_counter: Counter[int] = Counter()
    lead_steps: list[dict] = []
    for k, grp in sorted(by_k.items()):
        if len(grp) < 2:
            continue
        fk = math.factorial(k)
        prev_n, prev_d = grp[0]
        prev_a = lead_a(prev_d)
        for n, d in grp[1:]:
            a = lead_a(d)
            da = a - prev_a
            Delta = da * fk
            da_counter[da] += 1
            lead_steps.append(
                {
                    "max_k": k,
                    "n0": prev_n,
                    "n1": n,
                    "da": da,
                    "Delta_lead": Delta,
                    "k_fact": fk,
                }
            )
            prev_n, prev_d, prev_a = n, d, a

    w(f"  lead steps = {len(lead_steps)}")
    w(f"  unique da  = {len(da_counter)}  values={dict(sorted(da_counter.items()))}")
    w(f"  unique |Delta_lead| = {len({abs(s['Delta_lead']) for s in lead_steps})}")
    w()
    w("  PRECOMPUTE BUDGET (lead walk):")
    w("    For each active order k, store T = k!*G once.")
    w("    Observed da in {0,1,2,...,13} — at most ~14 multiples of T needed,")
    w("    or just add T repeatedly da times (da is tiny).")
    w("    Full-key jumps between puzzles: 81 unique huge Deltas — NO precompute win.")
    w("    Lead climb inside an order class: SMALL da — YES precompute win.")

    # ---- Timing demo: full scalar mul vs incremental lead add ----
    w()
    w("-" * 88)
    w("B) TIMING DEMO — full d*G vs incremental P + da*(k!*G)")
    w("-" * 88)

    # Use max_k=21 plateau (P67-P70) as demo
    demo_k = 21
    demo = by_k[demo_k]
    fk = math.factorial(demo_k)
    T = fk * G  # precompute once

    # cold start
    d0 = demo[0][1]
    t0 = time.perf_counter()
    P_cur = d0 * G
    t_full0 = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(1, len(demo)):
        _ = demo[i][1] * G
    t_full_each = time.perf_counter() - t0

    # incremental from P_cur using only lead deltas (NOTE: rem also changes,
    # so lead-only does NOT equal full P walk — we time the LEAD component op cost)
    t0 = time.perf_counter()
    P_lead = (lead_a(d0) * fk) * G
    for i in range(1, len(demo)):
        da = lead_a(demo[i][1]) - lead_a(demo[i - 1][1])
        if da:
            P_lead = P_lead + (da * T)
    t_incr = time.perf_counter() - t0

    w(f"  plateau max_k={demo_k} puzzles={[n for n,_ in demo]}")
    w(f"  precompute T=k!*G once (excluded from incremental loop cost above setup)")
    w(f"  time first full d0*G           = {t_full0*1e3:.3f} ms")
    w(f"  time {len(demo)-1} separate full di*G = {t_full_each*1e3:.3f} ms")
    w(f"  time {len(demo)-1} lead increments     = {t_incr*1e3:.3f} ms")
    if t_incr > 0:
        w(f"  ratio full/incremental (lead ops) ~ {t_full_each/t_incr:.1f}x")
    w()
    w("  NOTE: lead-only increment is the cheap recurring piece the matrix exposes.")
    w("  Remainder (d - a*k!) still changes and still needs its own rule/walk.")
    w("  The essay's win is: replace FULL scalar muls with adds when Delta repeats.")

    # ---- Correct decimal print of a real incremental FULL walk (puzzle consecutive) ----
    w()
    w("-" * 88)
    w("C) FULL INCREMENTAL WALK with decimal PRINT (right-of-point = x/p and y/p)")
    w("   P_{i+1} = P_i + Delta*G ; print 0.<x/p>.<y/p>")
    w("-" * 88)

    csv_rows: list[dict] = []
    # start
    n0, d0 = rows[0]
    P_cur = d0 * G
    d_cur = d0
    w(f"P{n0:03d} d={d0}")
    w(f"  print {print_0xy(P_cur)}")

    verify_ok = 0
    for n1, d1 in rows[1:]:
        Delta = (d1 - d_cur) % N
        # one incremental add (still a scalar mul of Delta if Delta is huge —
        # this demonstrates CORRECTNESS of P'=P+Delta*G and decimal print.
        # The essay speedup applies when Delta is from a SMALL precomputed set.)
        P_next = P_cur + (Delta * G)
        P_check = d1 * G
        ok = (int(P_next.x()) == int(P_check.x())) and (int(P_next.y()) == int(P_check.y()))
        verify_ok += int(ok)
        w(f"P{n1:03d} Delta_bits={Delta.bit_length()} verify={ok}")
        w(f"  print {print_0xy(P_next)}")
        csv_rows.append(
            {
                "n": n1,
                "Delta": str(Delta),
                "Delta_bits": Delta.bit_length(),
                "verify": ok,
                "print_0_xoverp_yoverp": print_0xy(P_next),
            }
        )
        P_cur, d_cur = P_next, d1

    w()
    w(f"  verified incremental adds: {verify_ok}/{len(rows)-1}")

    # ---- Map essay table to operations ----
    w()
    w("-" * 88)
    w("D) SCALAR RULE -> POINT RULE (from the essay)")
    w("-" * 88)
    w("  d+1     -> P+G")
    w("  d-1     -> P-G")
    w("  2d      -> 2P          (EC double)")
    w("  2d+1    -> 2P+G        (double then add G)")
    w("  3d+c    -> 3P+cG")
    w("  d+Delta -> P+Delta*G   (precompute Delta*G if Delta repeats)")
    w()
    w("  Printed form after each EC op:")
    w("    0.<right: x/p>.<right: y/p>")
    w("  The speedup is on the EC op count (left: d-side recurrence),")
    w("  not on arithmetic of the digit strings to the right of the decimal.")

    w()
    w("=" * 88)
    w("BOTTOM LINE")
    w("=" * 88)
    w("  Right side of the decimal = DISPLAY of field elements as x/p and y/p.")
    w("  Speedup = fewer EC scalar muls via recurring Delta/(a,b) from the matrix.")
    w("  Jacobian internally; 0.<x/p>.<y/p> only at check/print time.")
    w("  Nested (x.(y/p))/p was a formatting digression — not the essay's speedup.")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        wr.writeheader()
        wr.writerows(csv_rows)

    w()
    w(f"Wrote {OUT}")
    w(f"Wrote {CSV_OUT}")


if __name__ == "__main__":
    main()
