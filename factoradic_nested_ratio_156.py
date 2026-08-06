#!/usr/bin/env python3
"""
Correct nested decimal format:

  step 1:  y/p  = 0.<156 digits>     (or y/N)
  step 2:  form the mixed decimal x.(y/p)  = x.<those 156 digits>
  step 3:  x.(y/p)/p  = 0.<156 digits>   (or x.(y/N)/N)

Same for N-side.
"""
from __future__ import annotations

import csv
from decimal import Decimal, getcontext
from pathlib import Path

from ecdsa import SECP256k1, ellipticcurve

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_NESTED_RATIO_156.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_nested_ratio_156.csv")

DEC_PLACES = 156
getcontext().prec = DEC_PLACES + 64

N_INT = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
P_INT = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = Decimal(N_INT)
P = Decimal(P_INT)
G = SECP256k1.generator


def frac_digits(numer: int, denom: int, places: int = DEC_PLACES) -> str:
    """Exactly `places` digits after the point for (numer % denom)/denom, truncated."""
    numer = abs(int(numer)) % int(denom)
    scaled = (numer * (10**places)) // int(denom)
    return str(scaled).zfill(places)


def ratio_0(numer: int, denom: int, places: int = DEC_PLACES) -> str:
    return "0." + frac_digits(numer, denom, places)


def mixed_x_dot_frac(x: int, frac: str) -> Decimal:
    """x.<frac digits> as a Decimal."""
    return Decimal(int(x)) + Decimal("0." + frac)


def nested_x_frac_over_mod(x: int, y: int, mod: int, places: int = DEC_PLACES) -> tuple[str, str, str]:
    """
    Returns:
      y_over_mod_str     = 0.<156> of y/mod
      x_dot_yfrac_str    = x.<156 digits of y/mod>
      nested_over_mod    = 0.<156> of (x.(y/mod))/mod
    """
    yfrac = frac_digits(y, mod, places)
    y_over = "0." + yfrac
    x_dot = f"{int(x)}." + yfrac
    mixed = mixed_x_dot_frac(x, yfrac)
    # (x.(y/mod)) / mod  -> 156 digits after point (full rational, may be >= 1)
    q = mixed / Decimal(mod)
    # emit absolute value with exactly `places` fractional digits (truncate)
    # If q >= 1, keep integer part in the string.
    neg = q < 0
    q = abs(q)
    whole = int(q)
    frac_part = q - Decimal(whole)
    # frac digits from frac_part
    scaled = int(frac_part * (Decimal(10) ** places))
    frac_s = str(scaled).zfill(places)[:places]
    nested = f"{whole}.{frac_s}"
    if neg:
        nested = "-" + nested
    # Prefer 0. form when whole==0
    if whole == 0 and not neg:
        nested = "0." + frac_s
    elif whole == 0 and neg:
        nested = "-0." + frac_s
    return y_over, x_dot, nested


def affine_point(d: int) -> ellipticcurve.Point:
    d = d % N_INT
    if d == 0:
        return ellipticcurve.INFINITY
    return d * G


def xy(pt: ellipticcurve.Point) -> tuple[int, int]:
    if pt == ellipticcurve.INFINITY:
        return (0, 0)
    return (int(pt.x()), int(pt.y()))


def main() -> None:
    rows: list[tuple[int, int]] = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append((int(row["puzzle"]), int(row["private_key"])))
    rows.sort()

    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        if len(s) <= 140:
            print(s)

    w("=" * 88)
    w("NESTED RATIO DECIMAL (correct)")
    w("  1) y/p  = 0.<156>")
    w("  2) x.(y/p)  = x.<156 digits of y/p>")
    w("  3) x.(y/p)/p  = <decimal with 156 fractional digits>")
    w("Same triple with N:  y/N , x.(y/N) , x.(y/N)/N")
    w("=" * 88)

    csv_rows: list[dict] = []

    for n, d in rows:
        pt = affine_point(d)
        x, y = xy(pt)

        yp, x_dot_p, nested_p = nested_x_frac_over_mod(x, y, P_INT)
        yN, x_dot_N, nested_N = nested_x_frac_over_mod(x, y, N_INT)

        w(f"P{n:03d}")
        w(f"  x = {x}")
        w(f"  y = {y}")
        w(f"  y/p          = {yp}")
        w(f"  x.(y/p)      = {x_dot_p}")
        w(f"  x.(y/p)/p    = {nested_p}")
        w(f"  y/N          = {yN}")
        w(f"  x.(y/N)      = {x_dot_N}")
        w(f"  x.(y/N)/N    = {nested_N}")

        csv_rows.append(
            {
                "puzzle": n,
                "d": str(d),
                "x": str(x),
                "y": str(y),
                "y_over_p": yp,
                "x_dot_y_over_p": x_dot_p,
                "x_dot_y_over_p__over_p": nested_p,
                "y_over_N": yN,
                "x_dot_y_over_N": x_dot_N,
                "x_dot_y_over_N__over_N": nested_N,
                # digit counts
                "y_over_p_digits": len(yp.split(".", 1)[1]),
                "nested_p_frac_digits": len(nested_p.replace("-", "").split(".", 1)[1]),
            }
        )

    # sanity on last row
    last = csv_rows[-1]
    w()
    w("SANITY P" + str(last["puzzle"]))
    w(f"  len(y/p digits) = {last['y_over_p_digits']}")
    w(f"  len(x.(y/p)/p frac digits) = {last['nested_p_frac_digits']}")
    w(f"  y/p head = {last['y_over_p'][:44]}...")
    w(f"  x.(y/p) head = {last['x_dot_y_over_p'][:60]}...")
    w(f"  x.(y/p)/p head = {last['x_dot_y_over_p__over_p'][:44]}...")

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
