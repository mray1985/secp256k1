#!/usr/bin/env python3
"""
LOCKED hypothesis (discovery on walk 1..512; do not retune):

  q_x predicts orientation of directed-gap RANKING between x-orbit and scalar orbit:
    q_x == 1  =>  orientation = +1  (cyclic)
    q_x == 2  =>  orientation = -1  (reverse-cyclic)

Orientation of (ranks_dx, ranks_dd):
  +1 if ranks_dx is a cyclic shift of ranks_dd
  -1 if ranks_dx is a cyclic shift of reverse(ranks_dd)
  0  otherwise
  (if both, count as +1 and flag overlap)

Fresh test: random scalars, exclude discovery set {1..512} and solved keys.
Exact ints/Fractions. Wilson CI on rates.
"""
from __future__ import annotations

import csv
import hashlib
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_ORIENTATION_HOLDOUT.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\phi_orientation_holdout.csv")
KEYS = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LAMBDA = 0x5363AD4CC05C30E0A5261C028812645A122E22EA20816678DF02967C1B23BD72
LAMBDA2 = (LAMBDA * LAMBDA) % N
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE
BETA2 = (BETA * BETA) % P

G = SECP256k1.generator
DISCOVERY_MAX = 512
FRESH_N = 20000


def ranks(t: tuple[int, int, int]) -> tuple[int, int, int]:
    order = sorted(range(3), key=lambda i: (t[i], i))
    r = [0, 0, 0]
    for rank, i in enumerate(order):
        r[i] = rank
    return (r[0], r[1], r[2])


def cyclic_eq(a: tuple[int, ...], b: tuple[int, ...]) -> bool:
    return any(a[i:] + a[:i] == b for i in range(len(a)))


def orientation(ranks_x: tuple[int, int, int], ranks_d: tuple[int, int, int]) -> tuple[int, bool]:
    """Return (ori in {+1,-1,0}, overlap_both)."""
    cyc = cyclic_eq(ranks_x, ranks_d)
    rev = cyclic_eq(ranks_x, tuple(reversed(ranks_d)))
    if cyc and rev:
        return +1, True
    if cyc:
        return +1, False
    if rev:
        return -1, False
    return 0, False


def directed_gaps(v0: int, v1: int, v2: int, mod: int) -> tuple[int, int, int]:
    return ((v1 - v0) % mod, (v2 - v1) % mod, (v0 - v2) % mod)


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, centre - half), min(1.0, centre + half)


def load_solved() -> set[int]:
    out: set[int] = set()
    with KEYS.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if int(r["puzzle"]) == 135:
                continue
            raw = r["private_key"].strip()
            d = int(raw, 16) if any(c in raw.lower() for c in "abcdef") else int(raw)
            d %= N
            if d:
                out.add(d)
                out.add((-d) % N)
    return out


def fresh_scalars(n: int, exclude: set[int]) -> list[int]:
    """Deterministic fresh stream from SHA256(seed); seeds start at 1_000_000."""
    out: list[int] = []
    seed = 1_000_000
    while len(out) < n:
        h = hashlib.sha256(b"phi-ori-holdout-v1:" + seed.to_bytes(8, "big")).digest()
        d = int.from_bytes(h, "big") % N
        seed += 1
        if d == 0 or d in exclude or d <= DISCOVERY_MAX:
            continue
        out.append(d)
        exclude.add(d)  # unique
    return out


def analyze_d(d: int) -> dict:
    d0 = d % N
    d1 = (LAMBDA * d0) % N
    d2 = (LAMBDA2 * d0) % N
    x0 = int((d0 * G).x())
    x1 = (BETA * x0) % P
    x2 = (BETA2 * x0) % P
    qx = (x0 + x1 + x2) // P
    dx = directed_gaps(x0, x1, x2, P)
    dd = directed_gaps(d0, d1, d2, N)
    rx = ranks(dx)
    rd = ranks(dd)
    ori, overlap = orientation(rx, rd)
    Sx = sum(dx)
    Sd = sum(dd)
    rx_bar = tuple(Fraction(z, Sx) for z in dx)
    rd_bar = tuple(Fraction(z, Sd) for z in dd)
    # quantitative: under predicted alignment, compare barycentric vectors
    pred = +1 if qx == 1 else -1
    aligned = None
    max_abs = None
    prop_ok = False
    if pred == +1:
        # try cyclic shifts of rd_bar to match rx_bar ranks alignment on values
        best = None
        for s in range(3):
            cand = tuple(rd_bar[(i + s) % 3] for i in range(3))
            err = sum(abs(rx_bar[i] - cand[i]) for i in range(3))
            if best is None or err < best[0]:
                best = (err, cand, s)
        aligned = best[1]
        max_abs = max(abs(rx_bar[i] - aligned[i]) for i in range(3))
        # exact equality?
        prop_ok = rx_bar == aligned
    else:
        rev = tuple(reversed(rd_bar))
        best = None
        for s in range(3):
            cand = tuple(rev[(i + s) % 3] for i in range(3))
            err = sum(abs(rx_bar[i] - cand[i]) for i in range(3))
            if best is None or err < best[0]:
                best = (err, cand, s)
        aligned = best[1]
        max_abs = max(abs(rx_bar[i] - aligned[i]) for i in range(3))
        prop_ok = rx_bar == aligned

    return {
        "d": d0,
        "q_x": qx,
        "ori": ori,
        "overlap": overlap,
        "pred": pred,
        "hit": ori == pred,
        "ranks_dx": rx,
        "ranks_dd": rd,
        "exact_aligned_bary": prop_ok,
        "max_abs_aligned": max_abs,
    }


def report_block(name: str, rows: list[dict], w) -> None:
    n = len(rows)
    hits = sum(1 for r in rows if r["hit"])
    p, lo, hi = wilson_ci(hits, n)
    w(f"  [{name}] n={n}")
    w(f"    locked accuracy (ori==pred(q_x)): {hits}/{n} = {100*p:.2f}%  CI95%[{100*lo:.2f}, {100*hi:.2f}]")
    # confusion-style
    c = Counter((r["q_x"], r["ori"]) for r in rows)
    w("    counts (q_x, ori):")
    for qx in (1, 2):
        for ori in (+1, -1, 0):
            w(f"      q_x={qx} ori={ori:+d}: {c[(qx, ori)]}")
    # conditional rates
    for qx in (1, 2):
        sub = [r for r in rows if r["q_x"] == qx]
        m = len(sub)
        if m == 0:
            continue
        cyc = sum(1 for r in sub if r["ori"] == +1)
        rev = sum(1 for r in sub if r["ori"] == -1)
        nei = sum(1 for r in sub if r["ori"] == 0)
        p1, lo1, hi1 = wilson_ci(cyc, m)
        p2, lo2, hi2 = wilson_ci(rev, m)
        w(f"    given q_x={qx}: cyclic={100*p1:.1f}%[{100*lo1:.1f},{100*hi1:.1f}]  "
          f"rev-cyc={100*p2:.1f}%[{100*lo2:.1f},{100*hi2:.1f}]  neither={100*nei/m:.1f}%")
    overlap = sum(1 for r in rows if r["overlap"])
    w(f"    orientation overlap (+1 and -1 both true): {overlap}/{n}")
    # chance baseline: if ori independent of q_x with observed ori margins
    ori_c = Counter(r["ori"] for r in rows)
    qx_c = Counter(r["q_x"] for r in rows)
    # expected hits under independence: sum_qx P(qx)*P(ori=pred(qx))
    exp = 0.0
    for qx in (1, 2):
        pred = +1 if qx == 1 else -1
        exp += qx_c[qx] * (ori_c[pred] / n if n else 0)
    w(f"    indep baseline expected accuracy: {100*exp/n:.2f}%")
    # quantitative exact bary match under predicted align
    exact_b = sum(1 for r in rows if r["exact_aligned_bary"])
    w(f"    exact barycentric match under predicted align: {exact_b}/{n}")
    # among hits, mean max_abs — use Fraction average carefully
    hit_rows = [r for r in rows if r["hit"] and r["max_abs_aligned"] is not None]
    if hit_rows:
        # report how often max_abs == 0 and median of float for scale only in text
        zero = sum(1 for r in hit_rows if r["max_abs_aligned"] == 0)
        w(f"    among orientation hits: exact vector match {zero}/{len(hit_rows)}")
    w()


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("LOCKED orientation hypothesis — fresh holdout")
    w("=" * 88)
    w("  Hyp: q_x=1 => ori=+1 (cyclic); q_x=2 => ori=-1 (reverse-cyclic)")
    w("  Discovery set: d=1..512 (reported separately; NOT used to retune)")
    w(f"  Fresh: {FRESH_N} SHA256 scalars, exclude discovery & solved keys")
    w()

    solved = load_solved()
    exclude = set(range(0, DISCOVERY_MAX + 1)) | solved

    # discovery replication
    w("-" * 88)
    w("0) Discovery replication (d=1..512) — expect ~65%/69% style split")
    w("-" * 88)
    disc = [analyze_d(d) for d in range(1, DISCOVERY_MAX + 1)]
    report_block("discovery", disc, w)

    # fresh
    w("-" * 88)
    w(f"1) FRESH holdout n={FRESH_N}")
    w("-" * 88)
    fresh_ds = fresh_scalars(FRESH_N, exclude)
    fresh = []
    csv_rows = []
    for i, d in enumerate(fresh_ds):
        r = analyze_d(d)
        fresh.append(r)
        csv_rows.append(
            {
                "split": "fresh",
                "d": str(r["d"]),
                "q_x": r["q_x"],
                "ori": r["ori"],
                "pred": r["pred"],
                "hit": int(r["hit"]),
                "overlap": int(r["overlap"]),
                "ranks_dx": "".join(map(str, r["ranks_dx"])),
                "ranks_dd": "".join(map(str, r["ranks_dd"])),
                "exact_aligned_bary": int(r["exact_aligned_bary"]),
            }
        )
        if (i + 1) % 2000 == 0:
            print(f"  ... {i+1}/{FRESH_N}")
    report_block("fresh", fresh, w)

    # also solved keys as second unseen-ish check (not used in discovery walk)
    w("-" * 88)
    w("2) Solved keys (excluded from fresh; not discovery walk)")
    w("-" * 88)
    solved_pos = []
    with KEYS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pn = int(row["puzzle"])
            if pn == 135:
                continue
            raw = row["private_key"].strip()
            d = int(raw, 16) if any(c in raw.lower() for c in "abcdef") else int(raw)
            d %= N
            if d and d > DISCOVERY_MAX:
                solved_pos.append(analyze_d(d))
    report_block("solved_d>512", solved_pos, w)

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Hypothesis FROZEN. Decision from fresh CI vs ~50% indep baseline.")
    w("  If fresh accuracy CI excludes baseline and conditional rates stay split,")
    w("  signal is real; else exploratory artifact.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        wr.writeheader()
        wr.writerows(csv_rows)
    print(f"Wrote {OUT}")
    print(f"Wrote {CSV_OUT}")


if __name__ == "__main__":
    main()
