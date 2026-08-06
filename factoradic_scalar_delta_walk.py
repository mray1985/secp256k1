#!/usr/bin/env python3
"""
Extract recurring scalar deltas / affine rules from the solved-puzzle matrix.

Goal: turn factoradic/carry structure into an incremental point walk:
  P_{i+1} = P_i + Delta G     or     P_{i+1} = a P_i + b G

Reports:
  - consecutive deltas Delta = (d_{n'} - d_n) mod N  (by puzzle index order)
  - within max_k-plateau deltas
  - exact affine hits d' == a*d + b  for small a,b
  - unique |Delta| multiset -> precompute budget
"""
from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_SCALAR_DELTA_WALK.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_scalar_deltas.csv")

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


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


def mod_delta(a: int, b: int) -> int:
    """(b - a) mod N in [0, N)."""
    return (b - a) % N


def signed_delta(a: int, b: int) -> int:
    """Representative in (-N/2, N/2]."""
    d = mod_delta(a, b)
    if d > N // 2:
        d -= N
    return d


def try_affine(d: int, dp: int, a_max: int = 8, b_bits: int = 40) -> list[tuple[int, int]]:
    """
    Exact hits: dp == (a*d + b) mod N  with small a and |b| < 2^b_bits
    (or b in a small explicit set).
    """
    hits: list[tuple[int, int]] = []
    B = 1 << b_bits
    for a in range(0, a_max + 1):
        # b = dp - a*d  (mod N), take signed
        b = signed_delta((a * d) % N, dp)
        if abs(b) < B:
            hits.append((a, b))
        # also check a=0.. with exact small positive b from factorials
    return hits


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
    w("SCALAR DELTA / AFFINE EXTRACTION  ->  incremental point-walk budget")
    w("=" * 88)
    w("P_{i+1} = P_i + Delta G     when Delta = (d_{i+1}-d_i) mod N")
    w("P_{i+1} = a P_i + b G       when d_{i+1} = a d_i + b")
    w(f"solved keys = {len(rows)}")
    w()

    # ---- consecutive by puzzle index (not consecutive integers if gaps) ----
    deltas_idx: list[tuple[int, int, int, int]] = []  # n, n', Delta_signed, |Delta|
    for i in range(1, len(rows)):
        n0, d0 = rows[i - 1]
        n1, d1 = rows[i]
        sd = signed_delta(d0, d1)
        deltas_idx.append((n0, n1, sd, abs(sd)))

    w("-" * 88)
    w("A) Consecutive solved puzzles (index order): Delta = d_next - d_prev")
    w("-" * 88)
    w(f"{'n->n':>10} {'max_k':>7} {'signed_Delta':>24} {'|Delta| bits':>12}")
    dmap = dict(rows)
    for n0, n1, sd, ad in deltas_idx[:15]:
        w(
            f"{n0:3d}->{n1:<3d} {max_k(dmap[n0]):2d}->{max_k(dmap[n1]):<2d} "
            f"{sd:24d} {ad.bit_length():12d}"
        )
    if len(deltas_idx) > 15:
        w(f"  ... ({len(deltas_idx) - 15} more consecutive pairs)")
        # show a few large-gap ones
        for n0, n1, sd, ad in deltas_idx:
            if n1 - n0 > 1:
                w(
                    f"{n0:3d}->{n1:<3d} {max_k(dmap[n0]):2d}->{max_k(dmap[n1]):<2d} "
                    f"{sd:24d} {ad.bit_length():12d}  (gap)"
                )
                break
        for n0, n1, sd, ad in deltas_idx[-3:]:
            w(
                f"{n0:3d}->{n1:<3d} {max_k(dmap[n0]):2d}->{max_k(dmap[n1]):<2d} "
                f"{sd:24d} {ad.bit_length():12d}"
            )

    abs_deltas = [ad for *_, ad in deltas_idx]
    w()
    w(f"  unique |Delta| among consecutive solved: {len(set(abs_deltas))} / {len(abs_deltas)}")
    w(f"  |Delta| bit-length: min={min(x.bit_length() for x in abs_deltas)} "
      f"median={sorted(x.bit_length() for x in abs_deltas)[len(abs_deltas)//2]} "
      f"max={max(x.bit_length() for x in abs_deltas)}")
    w("  Verdict: index-consecutive puzzles have HUGE unique deltas (full-size).")
    w("  Precomputing those Delta*G does NOT compress the walk — each step is new.")

    # ---- within same max_k plateau ----
    w()
    w("-" * 88)
    w("B) Within same max_k plateau (order class): consecutive members")
    w("-" * 88)
    by_k: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for n, d in rows:
        by_k[max_k(d)].append((n, d))

    plat_deltas: list[int] = []
    plat_rows: list[dict] = []
    for k in sorted(by_k):
        grp = by_k[k]
        if len(grp) < 2:
            continue
        w(f"  max_k={k}  puzzles={[n for n,_ in grp]}")
        for i in range(1, len(grp)):
            n0, d0 = grp[i - 1]
            n1, d1 = grp[i]
            sd = signed_delta(d0, d1)
            ad = abs(sd)
            plat_deltas.append(ad)
            # affine probe
            aff = try_affine(d0, d1, a_max=4, b_bits=min(n1, 48))
            # also check classic 2d+1, 2d, d+1 relative to band — exact
            classics = []
            for a, bname, b in [
                (1, "+1", 1),
                (1, "-1", -1),
                (2, "0", 0),
                (2, "+1", 1),
                (2, "-1", -1),
                (3, "0", 0),
                (3, "+1", 1),
            ]:
                if (a * d0 + b) % N == d1 % N:
                    classics.append(f"{a}d{bname}")
            w(
                f"    {n0}->{n1}  |Delta| bits={ad.bit_length():3d}  "
                f"affine_small={aff[:3] if aff else []}  classic={classics or '-'}"
            )
            plat_rows.append(
                {
                    "n0": n0,
                    "n1": n1,
                    "max_k": k,
                    "delta_signed": sd,
                    "delta_abs": ad,
                    "delta_bits": ad.bit_length(),
                    "affine": ";".join(f"{a},{b}" for a, b in aff[:5]),
                    "classic": "|".join(classics),
                }
            )

    w()
    if plat_deltas:
        w(f"  plateau steps: {len(plat_deltas)}")
        w(f"  unique |Delta|: {len(set(plat_deltas))} / {len(plat_deltas)}")
        w(
            f"  |Delta| bits: min={min(x.bit_length() for x in plat_deltas)} "
            f"median={sorted(x.bit_length() for x in plat_deltas)[len(plat_deltas)//2]} "
            f"max={max(x.bit_length() for x in plat_deltas)}"
        )

    # ---- factoradic lead-only recurrence inside plateau ----
    w()
    w("-" * 88)
    w("C) Lead-term only: a*k! sequence inside plateau (cheap Delta on the LEAD)")
    w("-" * 88)
    lead_deltas: list[int] = []
    for k in sorted(by_k):
        grp = by_k[k]
        if len(grp) < 2:
            continue
        fk = math.factorial(k)
        leads = []
        for n, d in grp:
            a = to_fac(d)[k]
            leads.append((n, a, a * fk))
        w(f"  max_k={k}:")
        for i in range(1, len(leads)):
            n0, a0, L0 = leads[i - 1]
            n1, a1, L1 = leads[i]
            da = a1 - a0
            dL = L1 - L0  # exact integer, not mod N (both << N for these sizes)
            lead_deltas.append(abs(dL))
            w(
                f"    lead {n0}->{n1}: a {a0}->{a1} (da={da:+d})  "
                f"Delta_lead={da:+d}*{k}!  bits={abs(dL).bit_length()}"
            )
            # point rule for LEAD only: if rem stayed equal, P would shift by da*(k! G)
            # check how much rem changes
            rem0 = grp[i - 1][1] - L0
            rem1 = grp[i][1] - L1
            w(
                f"         rem bits {rem0.bit_length()}->{rem1.bit_length()}  "
                f"|drem| bits={(abs(rem1-rem0)).bit_length()}"
            )

    w()
    w("  Lead deltas ARE shared structure: Delta_lead = da * k!  with tiny da.")
    w("  Precompute once:  k!·G  (and maybe 2k!G, 3k!G, … up to k·k!G = (k+1)!/ (k+1) *k …)")
    w("  Then lead climb is:  P_lead <- P_lead + da·(k! G).")
    w("  Remainder still needs its own walk — that is where uniqueness lives.")

    # ---- unique small da across plateaus ----
    w()
    w("-" * 88)
    w("D) Precompute budget if we only walk LEAD coeffs")
    w("-" * 88)
    da_counter: Counter[int] = Counter()
    for k in sorted(by_k):
        grp = by_k[k]
        if len(grp) < 2:
            continue
        prev_a = to_fac(grp[0][1])[k]
        for n, d in grp[1:]:
            a = to_fac(d)[k]
            da_counter[a - prev_a] += 1
            prev_a = a
    w(f"  observed da values (lead coeff steps): {dict(sorted(da_counter.items()))}")
    w(f"  unique da: {len(da_counter)}")
    w("  For each plateau k, precompute {1,2,...,k}·(k! G) once — at most k points.")
    w("  Walking lead-only across a plateau: 1 point-add per step (using da*(k!G)).")

    # ---- check exact classic maps anywhere ----
    w()
    w("-" * 88)
    w("E) Exact classic maps d' = a d + b  across ALL ordered pairs in same plateau")
    w("-" * 88)
    classic_hits = 0
    for k in sorted(by_k):
        grp = by_k[k]
        for i, (n0, d0) in enumerate(grp):
            for n1, d1 in grp[i + 1 :]:
                for a in range(1, 5):
                    for b in range(-8, 9):
                        if (a * d0 + b) % N == d1 % N:
                            classic_hits += 1
                            w(f"  HIT max_k={k}  P{n0}->P{n1}: d' = {a}*d + ({b})")
    if classic_hits == 0:
        w("  No exact d' = a*d + b hits for a=1..4, |b|<=8 inside plateaus.")
        w("  Full private keys are NOT short affine of each other — only leads are.")

    # write csv of plateau steps
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "n0",
            "n1",
            "max_k",
            "delta_signed",
            "delta_abs",
            "delta_bits",
            "affine",
            "classic",
        ]
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        for r in plat_rows:
            wr.writerow(r)

    w()
    w("=" * 88)
    w("BOTTOM LINE")
    w("=" * 88)
    w("  Matrix -> point walk is real IF the matrix emits recurring Delta or (a,b).")
    w("  On the known solved key list:")
    w("    - full-d consecutive deltas: unique & huge -> no shared precompute win")
    w("    - lead-only inside order class: tiny da, Delta = da*k! -> REAL win")
    w("    - store points as Jacobian 0.X.Y.Z; affine 0.x.y only at check time")
    w("  Next extraction target: factoradic REMAINDER recurrences / carries,")
    w("  not the full d jump between puzzles.")
    w()
    w(f"Wrote {OUT}")
    w(f"Wrote {CSV_OUT}")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
