#!/usr/bin/env python3
"""
True decimal RATIOS — not zero-padded integers.

  x/p , y/p , x/N , y/N , d/N   =   0.<156 decimal digits>

Also emit:
  x.<156-digit fractional of x/p>   style label as x.ddddd...
  y.<156-digit fractional of y/p>
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from decimal import Decimal, getcontext
from pathlib import Path

from ecdsa import SECP256k1, ellipticcurve

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_RATIO_DECIMAL_156.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_ratio_decimal_156.csv")
WALK_CSV = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_ratio_decimal_156_walk.csv")
LEAD_CSV = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_ratio_decimal_156_lead.csv")

DEC_PLACES = 156
# extra guard digits for rounding correctness
getcontext().prec = DEC_PLACES + 32

N_INT = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
P_INT = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = Decimal(N_INT)
P = Decimal(P_INT)
G = SECP256k1.generator


def frac_digits(numer: int, denom: Decimal, places: int = DEC_PLACES) -> str:
    """
    Exactly `places` digits AFTER the decimal point for numer/denom,
    truncated (not banker's rounded) via integer arithmetic:
      floor(numer * 10^places / denom) as zero-padded digit string.
    """
    numer = int(numer)
    den = int(denom)
    if den <= 0:
        raise ValueError("denom must be positive")
    # allow numer any non-negative; if numer >= den, this is {numer/den} fractional? 
    # User asked for y/p as decimal number — full rational value in [0,1) when y<p.
    # Use absolute value for digit body.
    sign_neg = numer < 0
    numer = abs(numer)
    if numer >= den:
        numer = numer % den
    scaled = (numer * (10**places)) // den
    body = str(scaled).zfill(places)
    if len(body) > places:
        body = body[-places:]
    return ("-" + body) if sign_neg else body


def ratio_0(numer: int, denom: Decimal, places: int = DEC_PLACES) -> str:
    """Full 0.<places> decimal string for numer/denom."""
    return "0." + frac_digits(numer, denom, places)


def label_dot(prefix: str, numer: int, denom: Decimal, places: int = DEC_PLACES) -> str:
    """x.<156 digits of x/p>  or y.<156 digits of y/p>."""
    return f"{prefix}." + frac_digits(numer, denom, places)


def affine_point(d: int) -> ellipticcurve.Point:
    d = d % N_INT
    if d == 0:
        return ellipticcurve.INFINITY
    return d * G


def xy(pt: ellipticcurve.Point) -> tuple[int, int]:
    if pt == ellipticcurve.INFINITY:
        return (0, 0)
    return (int(pt.x()), int(pt.y()))


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
    d = (b - a) % N_INT
    if d > N_INT // 2:
        d -= N_INT
    return d


def emit_point_block(tag: str, pt: ellipticcurve.Point, lines: list[str]) -> dict:
    x, y = xy(pt)
    row = {
        f"{tag}_x_int": str(x),
        f"{tag}_y_int": str(y),
        f"{tag}_x_over_p": ratio_0(x, P),
        f"{tag}_y_over_p": ratio_0(y, P),
        f"{tag}_x_over_N": ratio_0(x, N),
        f"{tag}_y_over_N": ratio_0(y, N),
        f"{tag}_x_dot_pfrac": label_dot("x", x, P),
        f"{tag}_y_dot_pfrac": label_dot("y", y, P),
        f"{tag}_x_dot_Nfrac": label_dot("x", x, N),
        f"{tag}_y_dot_Nfrac": label_dot("y", y, N),
    }
    lines.append(f"  {tag} integer x = {x}")
    lines.append(f"  {tag} integer y = {y}")
    lines.append(f"  {tag} x/p = {row[f'{tag}_x_over_p']}")
    lines.append(f"  {tag} y/p = {row[f'{tag}_y_over_p']}")
    lines.append(f"  {tag} x/N = {row[f'{tag}_x_over_N']}")
    lines.append(f"  {tag} y/N = {row[f'{tag}_y_over_N']}")
    lines.append(f"  {tag} {row[f'{tag}_x_dot_pfrac']}   (x.<digits of x/p>)")
    lines.append(f"  {tag} {row[f'{tag}_y_dot_pfrac']}   (y.<digits of y/p>)")
    lines.append(f"  {tag} {row[f'{tag}_x_dot_Nfrac']}   (x.<digits of x/N>)")
    lines.append(f"  {tag} {row[f'{tag}_y_dot_Nfrac']}   (y.<digits of y/N>)")
    return row


def main() -> None:
    rows: list[tuple[int, int]] = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append((int(row["puzzle"]), int(row["private_key"])))
    rows.sort()

    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        if len(s) <= 120:
            print(s)

    w("=" * 88)
    w(f"RATIO DECIMAL FORMAT — exactly {DEC_PLACES} digits after the point")
    w("  x/p = 0.<156 digits>")
    w("  y/p = 0.<156 digits>")
    w("  x/N = 0.<156 digits>")
    w("  y/N = 0.<156 digits>")
    w("  d/N = 0.<156 digits>")
    w("  labels: x.<156 digits of x/p>   y.<156 digits of y/p>")
    w("=" * 88)
    w(f"p = {P_INT}")
    w(f"N = {N_INT}")

    points: dict[int, ellipticcurve.Point] = {}
    csv_rows: list[dict] = []

    w()
    w("A) EVERY SOLVED KEY")
    w("-" * 88)
    for n, d in rows:
        pt = affine_point(d)
        points[n] = pt
        w(f"P{n:03d}  max_k={max_k_of(d)}  lead_a={lead_a(d)}")
        w(f"  d   = {d}")
        w(f"  d/N = {ratio_0(d, N)}")
        w(f"  d/p = {ratio_0(d, P)}")
        block = emit_point_block("P", pt, lines)
        rec = {
            "puzzle": n,
            "max_k": max_k_of(d),
            "lead_a": lead_a(d),
            "d": str(d),
            "d_over_N": ratio_0(d, N),
            "d_over_p": ratio_0(d, P),
            **block,
        }
        csv_rows.append(rec)

    w()
    w("B) INCREMENTAL WALK  P1 =? P0 + Delta*G")
    w("-" * 88)
    walk_rows: list[dict] = []
    for i in range(1, len(rows)):
        n0, d0 = rows[i - 1]
        n1, d1 = rows[i]
        Delta = signed_delta(d0, d1)
        Delta_mod = Delta % N_INT
        P0 = points[n0]
        P1 = points[n1]
        pred = P0 + (Delta_mod * G)
        ok = xy(pred) == xy(P1)
        w(f"P{n0:03d} -> P{n1:03d}  verify_add={ok}")
        w(f"  Delta      = {Delta}")
        w(f"  Delta/N    = {ratio_0(Delta_mod, N)}")
        w(f"  Delta/p    = {ratio_0(abs(Delta), P)}")
        b0 = emit_point_block("P0", P0, lines)
        b1 = emit_point_block("P1", P1, lines)
        bp = emit_point_block("P0+DG", pred, lines)
        walk_rows.append(
            {
                "n0": n0,
                "n1": n1,
                "verify": ok,
                "Delta": str(Delta),
                "Delta_modN": str(Delta_mod),
                "Delta_over_N": ratio_0(Delta_mod, N),
                "Delta_abs_over_p": ratio_0(abs(Delta), P),
                **{f"P0{k[1:]}": v for k, v in b0.items()},
                **{f"P1{k[1:]}": v for k, v in b1.items()},
                **{f"Padd{k[4:]}": v for k, v in bp.items()},
            }
        )

    # Fix walk csv keys cleanly
    walk_rows_clean: list[dict] = []
    for i in range(1, len(rows)):
        n0, d0 = rows[i - 1]
        n1, d1 = rows[i]
        Delta = signed_delta(d0, d1)
        Delta_mod = Delta % N_INT
        P0 = points[n0]
        P1 = points[n1]
        pred = P0 + (Delta_mod * G)
        ok = xy(pred) == xy(P1)
        x0, y0 = xy(P0)
        x1, y1 = xy(P1)
        xp, yp = xy(pred)
        walk_rows_clean.append(
            {
                "n0": n0,
                "n1": n1,
                "verify": ok,
                "Delta": str(Delta),
                "Delta_modN": str(Delta_mod),
                "Delta_over_N": ratio_0(Delta_mod, N),
                "P0_x_over_p": ratio_0(x0, P),
                "P0_y_over_p": ratio_0(y0, P),
                "P0_x_over_N": ratio_0(x0, N),
                "P0_y_over_N": ratio_0(y0, N),
                "P1_x_over_p": ratio_0(x1, P),
                "P1_y_over_p": ratio_0(y1, P),
                "P1_x_over_N": ratio_0(x1, N),
                "P1_y_over_N": ratio_0(y1, N),
                "P0_x_dot": label_dot("x", x0, P),
                "P0_y_dot": label_dot("y", y0, P),
                "P1_x_dot": label_dot("x", x1, P),
                "P1_y_dot": label_dot("y", y1, P),
                "Padd_x_over_p": ratio_0(xp, P),
                "Padd_y_over_p": ratio_0(yp, P),
            }
        )

    w()
    w("C) LEAD WALK INSIDE ORDER CLASS  Delta_lead = da * k!")
    w("-" * 88)
    by_k: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for n, d in rows:
        by_k[max_k_of(d)].append((n, d))

    lead_rows: list[dict] = []
    for k in sorted(by_k):
        grp = by_k[k]
        if len(grp) < 2:
            continue
        fk = math.factorial(k)
        T = fk * G
        tx, ty = xy(T)
        w(f"max_k={k}")
        w(f"  k!   = {fk}")
        w(f"  k!/N = {ratio_0(fk, N)}")
        w(f"  k!/p = {ratio_0(fk, P)}")
        w(f"  T=k!G x/p = {ratio_0(tx, P)}")
        w(f"  T=k!G y/p = {ratio_0(ty, P)}")
        for i in range(1, len(grp)):
            n0, d0 = grp[i - 1]
            n1, d1 = grp[i]
            a0 = lead_a(d0)
            a1 = lead_a(d1)
            da = a1 - a0
            Delta_lead = da * fk
            rem0 = d0 - a0 * fk
            rem1 = d1 - a1 * fk
            x0, y0 = xy(points[n0])
            x1, y1 = xy(points[n1])
            w(f"  P{n0} -> P{n1}  da={da:+d}")
            w(f"    Delta_lead/N = {ratio_0(abs(Delta_lead) % N_INT, N)}")
            w(f"    Delta_lead/p = {ratio_0(abs(Delta_lead), P)}")
            w(f"    rem0/N = {ratio_0(rem0, N)}")
            w(f"    rem1/N = {ratio_0(rem1, N)}")
            w(f"    P0 y/p = {ratio_0(y0, P)}")
            w(f"    P1 y/p = {ratio_0(y1, P)}")
            w(f"    P0 x/p = {ratio_0(x0, P)}")
            w(f"    P1 x/p = {ratio_0(x1, P)}")
            lead_rows.append(
                {
                    "max_k": k,
                    "n0": n0,
                    "n1": n1,
                    "da": da,
                    "k_factorial": str(fk),
                    "k_fact_over_N": ratio_0(fk, N),
                    "k_fact_over_p": ratio_0(fk, P),
                    "Delta_lead": str(Delta_lead),
                    "Delta_lead_over_N": ratio_0(abs(Delta_lead) % N_INT, N),
                    "Delta_lead_over_p": ratio_0(abs(Delta_lead), P),
                    "rem0_over_N": ratio_0(rem0, N),
                    "rem1_over_N": ratio_0(rem1, N),
                    "P0_x_over_p": ratio_0(x0, P),
                    "P0_y_over_p": ratio_0(y0, P),
                    "P1_x_over_p": ratio_0(x1, P),
                    "P1_y_over_p": ratio_0(y1, P),
                    "P0_x_dot": label_dot("x", x0, P),
                    "P0_y_dot": label_dot("y", y0, P),
                    "P1_x_dot": label_dot("x", x1, P),
                    "P1_y_dot": label_dot("y", y1, P),
                    "T_x_over_p": ratio_0(tx, P),
                    "T_y_over_p": ratio_0(ty, P),
                }
            )

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def dump_csv(path: Path, recs: list[dict]) -> None:
        if not recs:
            return
        with path.open("w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=list(recs[0].keys()))
            wr.writeheader()
            wr.writerows(recs)

    # clean main csv keys from emit_point_block
    main_csv: list[dict] = []
    for n, d in rows:
        pt = points[n]
        x, y = xy(pt)
        main_csv.append(
            {
                "puzzle": n,
                "max_k": max_k_of(d),
                "lead_a": lead_a(d),
                "d": str(d),
                "d_over_N": ratio_0(d, N),
                "d_over_p": ratio_0(d, P),
                "x": str(x),
                "y": str(y),
                "x_over_p": ratio_0(x, P),
                "y_over_p": ratio_0(y, P),
                "x_over_N": ratio_0(x, N),
                "y_over_N": ratio_0(y, N),
                "x_dot_pfrac": label_dot("x", x, P),
                "y_dot_pfrac": label_dot("y", y, P),
                "x_dot_Nfrac": label_dot("x", x, N),
                "y_dot_Nfrac": label_dot("y", y, N),
            }
        )

    dump_csv(CSV_OUT, main_csv)
    dump_csv(WALK_CSV, walk_rows_clean)
    dump_csv(LEAD_CSV, lead_rows)

    # sanity: digit counts
    sample = main_csv[-1]["y_over_p"]
    frac = sample.split(".", 1)[1]
    w()
    w(f"Wrote {OUT}")
    w(f"Wrote {CSV_OUT}")
    w(f"Wrote {WALK_CSV}")
    w(f"Wrote {LEAD_CSV}")
    w(f"sanity y/p sample digits after point: {len(frac)}  (want {DEC_PLACES})")
    w(f"sample y/p = {sample[:40]}...{sample[-20:]}")


if __name__ == "__main__":
    main()
