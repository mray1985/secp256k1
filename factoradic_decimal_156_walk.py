#!/usr/bin/env python3
"""
Scalar-delta / incremental point walk in TRUE DECIMAL format.

Every integer field is written with at least DEC_PLACES decimal digits
(zero-padded on the left). No hex.

Point display:
  0.<x>.<y>           affine
  0.<X>.<Y>.<Z>       Jacobian (Z=1 for affine lift)

Walk rule:
  d_{i+1} = d_i + Delta
  P_{i+1} = P_i + Delta*G
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from ecdsa import SECP256k1, ellipticcurve

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_DECIMAL_156_WALK.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_decimal_156_walk.csv")

DEC_PLACES = 156
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
G = SECP256k1.generator
CURVE = SECP256k1.curve


def D(n: int, width: int = DEC_PLACES) -> str:
    """True decimal, minimum `width` digits, sign preserved for negatives."""
    n = int(n)
    if n < 0:
        return "-" + D(-n, width)
    s = str(n)
    if len(s) < width:
        s = s.zfill(width)
    return s


def affine_point(d: int) -> ellipticcurve.Point:
    d = d % N
    if d == 0:
        return ellipticcurve.INFINITY
    return d * G


def xy(pt: ellipticcurve.Point) -> tuple[int, int]:
    if pt == ellipticcurve.INFINITY:
        return (0, 0)
    return (int(pt.x()), int(pt.y()))


def fmt_affine(pt: ellipticcurve.Point) -> str:
    x, y = xy(pt)
    return f"0.{D(x)}.{D(y)}"


def fmt_jacobi(pt: ellipticcurve.Point) -> str:
    """Affine lift into Jacobian decimal triple with Z=1."""
    x, y = xy(pt)
    return f"0.{D(x)}.{D(y)}.{D(1)}"


def to_fac(n: int) -> list[int]:
    digs: list[int] = []
    i = 1
    x = abs(int(n))
    while x:
        digs.append(x % i)
        x //= i
        i += 1
    return digs


def max_k_of(d: int) -> int:
    digs = to_fac(d)
    return len(digs) - 1 if digs else 0


def lead_a(d: int) -> int:
    digs = to_fac(d)
    return digs[-1] if digs else 0


def signed_delta(a: int, b: int) -> int:
    d = (b - a) % N
    if d > N // 2:
        d -= N
    return d


def main() -> None:
    rows: list[tuple[int, int]] = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append((int(row["puzzle"]), int(row["private_key"])))
    rows.sort()

    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        # console: keep short headers only; full body goes to file
        if len(s) < 200:
            print(s)
        elif s.startswith("P") or s.startswith("=") or s.startswith("-") or s.startswith(" "):
            print(s[:180] + " ...")

    w("=" * 88)
    w(f"TRUE DECIMAL FORMAT  —  minimum {DEC_PLACES} decimal digits per field")
    w("No hex. Scalars mod N, coordinates mod p.")
    w("Affine point:   0.<x>.<y>")
    w("Jacobian point: 0.<X>.<Y>.<Z>   (Z=1 lift here)")
    w(f"p = {D(P)}")
    w(f"N = {D(N)}")
    w("=" * 88)

    # ---- full solved table ----
    w()
    w("A) EVERY SOLVED KEY — decimal d and P = dG")
    w("-" * 88)
    csv_rows: list[dict] = []
    points: dict[int, ellipticcurve.Point] = {}
    for n, d in rows:
        pt = affine_point(d)
        points[n] = pt
        x, y = xy(pt)
        mk = max_k_of(d)
        a = lead_a(d)
        w(f"P{n:03d} max_k={mk} lead_a={a}")
        w(f"  d  = {D(d)}")
        w(f"  P  = {fmt_affine(pt)}")
        w(f"  J  = {fmt_jacobi(pt)}")
        csv_rows.append(
            {
                "puzzle": n,
                "max_k": mk,
                "lead_a": a,
                "d_dec": D(d),
                "x_dec": D(x),
                "y_dec": D(y),
                "affine_0_x_y": fmt_affine(pt),
                "jacobi_0_X_Y_Z": fmt_jacobi(pt),
            }
        )

    # ---- consecutive walk with verified point addition ----
    w()
    w("B) INCREMENTAL WALK  P_{i+1} =? P_i + Delta*G   (decimal Delta)")
    w("-" * 88)
    walk_rows: list[dict] = []
    for i in range(1, len(rows)):
        n0, d0 = rows[i - 1]
        n1, d1 = rows[i]
        Delta = signed_delta(d0, d1)
        Delta_mod = Delta % N
        P0 = points[n0]
        P1 = points[n1]
        pred = P0 + (Delta_mod * G)
        ok = xy(pred) == xy(P1)
        w(f"P{n0:03d} -> P{n1:03d}  verify_add={ok}")
        w(f"  d0     = {D(d0)}")
        w(f"  d1     = {D(d1)}")
        w(f"  Delta  = {D(Delta)}")
        w(f"  DeltaN = {D(Delta_mod)}")
        w(f"  P0     = {fmt_affine(P0)}")
        w(f"  P1     = {fmt_affine(P1)}")
        w(f"  P0+DG  = {fmt_affine(pred)}")
        walk_rows.append(
            {
                "n0": n0,
                "n1": n1,
                "d0_dec": D(d0),
                "d1_dec": D(d1),
                "Delta_signed_dec": D(Delta),
                "Delta_modN_dec": D(Delta_mod),
                "P0_0_x_y": fmt_affine(P0),
                "P1_0_x_y": fmt_affine(P1),
                "P0_plus_DeltaG_0_x_y": fmt_affine(pred),
                "verify": ok,
            }
        )

    # ---- lead-only plateau walk in decimal ----
    w()
    w("C) ORDER-CLASS LEAD WALK  Delta_lead = da * k!   (decimal)")
    w("-" * 88)
    by_k: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for n, d in rows:
        by_k[max_k_of(d)].append((n, d))

    import math

    lead_walk_rows: list[dict] = []
    for k in sorted(by_k):
        grp = by_k[k]
        if len(grp) < 2:
            continue
        fk = math.factorial(k)
        w(f"max_k={k}   k! = {D(fk)}")
        # precompute base T = k! * G once (shown in decimal)
        T = fk * G
        w(f"  T = k!*G = {fmt_affine(T)}")
        for i in range(1, len(grp)):
            n0, d0 = grp[i - 1]
            n1, d1 = grp[i]
            a0 = lead_a(d0)
            a1 = lead_a(d1)
            da = a1 - a0
            Delta_lead = da * fk
            rem0 = d0 - a0 * fk
            rem1 = d1 - a1 * fk
            # lead-point shift only (not full P)
            P0 = points[n0]
            # full delta still
            Delta_full = signed_delta(d0, d1)
            w(f"  P{n0} -> P{n1}  da={da:+d}")
            w(f"    a0*k!       = {D(a0 * fk)}")
            w(f"    a1*k!       = {D(a1 * fk)}")
            w(f"    Delta_lead  = {D(Delta_lead)}")
            w(f"    rem0        = {D(rem0)}")
            w(f"    rem1        = {D(rem1)}")
            w(f"    Delta_full  = {D(Delta_full)}")
            w(f"    P0          = {fmt_affine(P0)}")
            w(f"    P1          = {fmt_affine(points[n1])}")
            lead_walk_rows.append(
                {
                    "max_k": k,
                    "n0": n0,
                    "n1": n1,
                    "da": da,
                    "k_factorial_dec": D(fk),
                    "a0_times_kfact_dec": D(a0 * fk),
                    "a1_times_kfact_dec": D(a1 * fk),
                    "Delta_lead_dec": D(Delta_lead),
                    "rem0_dec": D(rem0),
                    "rem1_dec": D(rem1),
                    "Delta_full_dec": D(Delta_full),
                    "P0_0_x_y": fmt_affine(P0),
                    "P1_0_x_y": fmt_affine(points[n1]),
                    "T_kfactG_0_x_y": fmt_affine(T),
                }
            )

    # write outputs
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        fields = list(csv_rows[0].keys())
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        wr.writerows(csv_rows)

    walk_csv = OUT.parent / "factoradic_decimal_156_incremental_walk.csv"
    with walk_csv.open("w", newline="", encoding="utf-8") as f:
        fields = list(walk_rows[0].keys())
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        wr.writerows(walk_rows)

    lead_csv = OUT.parent / "factoradic_decimal_156_lead_walk.csv"
    with lead_csv.open("w", newline="", encoding="utf-8") as f:
        if lead_walk_rows:
            fields = list(lead_walk_rows[0].keys())
            wr = csv.DictWriter(f, fieldnames=fields)
            wr.writeheader()
            wr.writerows(lead_walk_rows)

    print()
    print(f"Wrote {OUT}")
    print(f"Wrote {CSV_OUT}")
    print(f"Wrote {walk_csv}")
    print(f"Wrote {lead_csv}")
    print(f"All numeric fields use >= {DEC_PLACES} decimal digits.")


if __name__ == "__main__":
    main()
