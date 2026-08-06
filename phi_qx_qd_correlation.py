#!/usr/bin/env python3
"""
q_x in {1,2} for GLV x-orbit vs q_d in {1,2} for scalar lambda-orbit.

  q_x = (x + (beta*x mod p) + (beta^2*x mod p)) / p
  q_d = (d + (lambda*d mod N) + (lambda^2*d mod N)) / N

Test: q_x == q_d ?  q_x + q_d == 3 ?
Negation: q_d(-d)=3-q_d(d); q_x(-P)=q_x(P)
Exact ints only.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_QX_QD_CORRELATION.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\phi_qx_qd.csv")
KEYS = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LAMBDA = 0x5363AD4CC05C30E0A5261C028812645A122E22EA20816678DF02967C1B23BD72
LAMBDA2 = (LAMBDA * LAMBDA) % N
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE
BETA2 = (BETA * BETA) % P

G = SECP256k1.generator

assert (1 + BETA + BETA2) == P
assert (1 + LAMBDA + LAMBDA2) % N == 0  # may equal N or 2N as int sum of reps


def q_x_of_x(x: int) -> tuple[int, int, int]:
    """Return (q_x, k1, k2) with q_x = x - k1 - k2."""
    raw1 = BETA * x
    raw2 = BETA2 * x
    k1, x1 = divmod(raw1, P)
    k2, x2 = divmod(raw2, P)
    S = x + x1 + x2
    assert S % P == 0
    qx = S // P
    assert qx == x - k1 - k2
    assert qx in (1, 2)
    return qx, k1, k2


def q_d_of_d(d: int) -> tuple[int, int, int]:
    d = d % N
    raw1 = LAMBDA * d
    raw2 = LAMBDA2 * d
    m1, d1 = divmod(raw1, N)
    m2, d2 = divmod(raw2, N)
    S = d + d1 + d2
    # 1+LAMBDA+LAMBDA2 as ints
    s_lam = 1 + LAMBDA + LAMBDA2
    # S = d*s_lam - (m1+m2)*N ; should be q*N
    assert S % N == 0
    qd = S // N
    # may be 1 or 2 (or theoretically more if s_lam/N > 1 and d large — check)
    return qd, m1, m2


def load_keys() -> list[tuple[int, int]]:
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


def contingency(pairs: list[tuple[int, int]]) -> dict[tuple[int, int], int]:
    c: dict[tuple[int, int], int] = Counter()
    for qd, qx in pairs:
        c[(qd, qx)] += 1
    return c


def print_table(c: dict[tuple[int, int], int], n: int, w) -> None:
    w(f"  {'qd\\\\qx':>8} | {'qx=1':>8} | {'qx=2':>8} | {'row':>8}")
    w("  " + "-" * 44)
    for qd in (1, 2):
        a = c.get((qd, 1), 0)
        b = c.get((qd, 2), 0)
        w(f"  {qd:>8} | {a:>8} | {b:>8} | {a+b:>8}")
    col1 = c.get((1, 1), 0) + c.get((2, 1), 0)
    col2 = c.get((1, 2), 0) + c.get((2, 2), 0)
    w(f"  {'col':>8} | {col1:>8} | {col2:>8} | {n:>8}")
    eq = c.get((1, 1), 0) + c.get((2, 2), 0)
    sum3 = c.get((1, 2), 0) + c.get((2, 1), 0)
    w(f"  q_x == q_d : {eq}/{n} ({100*eq/n:.1f}%)")
    w(f"  q_x + q_d == 3 : {sum3}/{n} ({100*sum3/n:.1f}%)")
    # chance baseline if independent with observed margins
    p_qd1 = (c.get((1, 1), 0) + c.get((1, 2), 0)) / n if n else 0
    p_qx1 = col1 / n if n else 0
    # under independence P(eq) = P(qd1)P(qx1)+P(qd2)P(qx2)
    p_eq_ind = p_qd1 * p_qx1 + (1 - p_qd1) * (1 - p_qx1)
    p_sum3_ind = p_qd1 * (1 - p_qx1) + (1 - p_qd1) * p_qx1
    w(f"  indep baseline: P(eq)~{100*p_eq_ind:.1f}%  P(sum3)~{100*p_sum3_ind:.1f}%")
    w()


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Cross-domain: q_x (mod p GLV) vs q_d (mod N lambda)")
    w("=" * 88)
    w(f"  1+beta+beta^2 = {1+BETA+BETA2}  (== p? {1+BETA+BETA2==P})")
    s_lam = 1 + LAMBDA + LAMBDA2
    w(f"  1+lambda+lambda^2 = {s_lam}")
    w(f"  (1+lambda+lambda^2)/N = {s_lam // N}  rem {s_lam % N}")
    w()

    # sanity: qd always in {1,2}?
    w("-" * 88)
    w("0) Sanity: q_d, q_x range on walk")
    w("-" * 88)
    qd_vals = Counter()
    qx_vals = Counter()
    bad = 0
    for d in range(1, 513):
        qd, _, _ = q_d_of_d(d)
        x = int((d * G).x())
        qx, _, _ = q_x_of_x(x)
        qd_vals[qd] += 1
        qx_vals[qx] += 1
        if qd not in (1, 2) or qx not in (1, 2):
            bad += 1
    w(f"  d=1..512: q_d histogram {dict(qd_vals)}")
    w(f"  d=1..512: q_x histogram {dict(qx_vals)}")
    w(f"  outside {{1,2}}: {bad}")
    w()

    # walk correlation
    w("-" * 88)
    w("1) Walk d=1..512 contingency")
    w("-" * 88)
    pairs = []
    csv_rows = []
    for d in range(1, 513):
        qd, m1, m2 = q_d_of_d(d)
        x = int((d * G).x())
        qx, k1, k2 = q_x_of_x(x)
        pairs.append((qd, qx))
        csv_rows.append(
            {
                "source": "walk",
                "d": str(d),
                "puzzle": "",
                "q_d": qd,
                "q_x": qx,
                "m1": str(m1),
                "m2": str(m2),
                "k1": str(k1),
                "k2": str(k2),
            }
        )
    print_table(contingency(pairs), len(pairs), w)

    # negation
    w("-" * 88)
    w("2) Negation laws")
    w("-" * 88)
    neg_d_ok = neg_x_ok = 0
    for d in range(1, 257):
        qd, _, _ = q_d_of_d(d)
        qd_n, _, _ = q_d_of_d((-d) % N)
        if qd_n == 3 - qd:
            neg_d_ok += 1
        x = int((d * G).x())
        qx, _, _ = q_x_of_x(x)
        # -P has same x
        qx_n, _, _ = q_x_of_x(x)
        if qx_n == qx:
            neg_x_ok += 1
    w(f"  d=1..256: q_d(-d) == 3 - q_d(d) : {neg_d_ok}/256")
    w(f"  d=1..256: q_x(-P) == q_x(P)     : {neg_x_ok}/256  (x unchanged)")
    w()

    # sixfold: q_d for orbit mates
    w("-" * 88)
    w("3) Sixfold scalar orbit: q_d pattern")
    w("-" * 88)
    # for d, lam d, lam2 d, -d, -lam d, -lam2 d
    pattern_ok = 0
    for d in range(1, 129):
        mates = [
            d % N,
            (LAMBDA * d) % N,
            (LAMBDA2 * d) % N,
            (-d) % N,
            (-LAMBDA * d) % N,
            (-LAMBDA2 * d) % N,
        ]
        qs = [q_d_of_d(m)[0] for m in mates]
        # positive half should share? actually each has own - check
        # expected: q(-m)=3-q(m); lam rotates within?
        ok = (
            qs[3] == 3 - qs[0]
            and qs[4] == 3 - qs[1]
            and qs[5] == 3 - qs[2]
        )
        # do lambda mates preserve q_d?
        same_pos = qs[0] == qs[1] == qs[2]
        if ok:
            pattern_ok += 1
        if d <= 5:
            w(f"  d={d}: q_d orbit {qs}  neg_flip_ok={ok}  pos_triple_equal={same_pos}")
    w(f"  d=1..128: neg-flip on all three pairs: {pattern_ok}/128")
    # does lambda preserve q_d?
    lam_pres = sum(
        1
        for d in range(1, 257)
        if q_d_of_d(d)[0] == q_d_of_d((LAMBDA * d) % N)[0]
    )
    w(f"  d=1..256: q_d(d)==q_d(lambda d): {lam_pres}/256")
    w()

    # q_x under lambda (point psi): same x-orbit, same q_x
    w("-" * 88)
    w("4) q_x invariant on GLV x-orbit / psi")
    w("-" * 88)
    qx_inv = 0
    for d in range(1, 257):
        x = int((d * G).x())
        qx = q_x_of_x(x)[0]
        x1 = (BETA * x) % P
        x2 = (BETA2 * x) % P
        if q_x_of_x(x1)[0] == qx and q_x_of_x(x2)[0] == qx:
            qx_inv += 1
    w(f"  d=1..256: q_x same on {{x, beta x, beta2 x}}: {qx_inv}/256")
    w()

    # solved keys
    w("-" * 88)
    w("5) Solved keys (skip 135): cal n<=100 vs holdout n>100")
    w("-" * 88)
    keys = load_keys()
    cal = [(pn, d) for pn, d in keys if pn <= 100]
    hold = [(pn, d) for pn, d in keys if pn > 100]

    def eval_set(label: str, rows: list[tuple[int, int]]) -> None:
        pairs = []
        for pn, d in rows:
            qd = q_d_of_d(d)[0]
            x = int((d * G).x())
            qx = q_x_of_x(x)[0]
            pairs.append((qd, qx))
            csv_rows.append(
                {
                    "source": label,
                    "d": str(d),
                    "puzzle": str(pn),
                    "q_d": qd,
                    "q_x": qx,
                    "m1": "",
                    "m2": "",
                    "k1": "",
                    "k2": "",
                }
            )
        w(f"  --- {label} n={len(pairs)} ---")
        print_table(contingency(pairs), len(pairs), w)

    eval_set("cal", cal)
    eval_set("holdout", hold)

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  q_x, q_d well-defined in {1,2}.")
    w("  Negation: q_d flips 3-q; q_x invariant (x-orbit).")
    w("  See contingency vs independence baseline for alignment.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        fields = list(csv_rows[0].keys())
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        wr.writerows(csv_rows)
    print(f"Wrote {OUT}")
    print(f"Wrote {CSV_OUT}")


if __name__ == "__main__":
    main()
