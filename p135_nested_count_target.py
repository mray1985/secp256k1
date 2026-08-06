#!/usr/bin/env python3
"""
P135 nested decimal target and the COUNT metric.

Target form (user):
  n . ( x_135 . (y_135 / p) ) / p

Build:
  1) y/p          -> 156 frac digits
  2) x.(y/p)      -> mixed decimal
  3) (x.(y/p))/p  -> core fingerprint C
  4) n.(C) / p    -> full target at step/count n

The walk metric: count n = 1,2,3,... (or incremental EC steps)
until the running state prints/matches that nested value.
For known solved keys we can also ask: which count n makes
  (n . (x.(y/p))) / p
land nearest a simple pattern — but the definition itself is the target.

Here we compute C for P135 and show targets for n in a useful range,
plus how many incremental lead-steps appear in the solved matrix
as a calibration of 'how many times'.
"""
from __future__ import annotations

import csv
from decimal import Decimal, getcontext
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\P135_NESTED_COUNT_TARGET.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\p135_nested_count_target.csv")

DEC = 156
getcontext().prec = DEC + 64

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# Puzzle 135 compressed 02||x
X135 = 0x145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16


def mod_sqrt_secp(a: int) -> int | None:
    """sqrt for p % 4 == 3."""
    return pow(a % P, (P + 1) // 4, P)


def y_from_x(x: int, even: bool) -> int:
    a = (pow(x, 3, P) + 7) % P
    y = mod_sqrt_secp(a)
    if y is None:
        raise ValueError("x not on curve")
    if (y % 2 == 0) != even:
        y = (-y) % P
    return y


def frac_digits(numer: int, denom: int, places: int = DEC) -> str:
    numer = abs(int(numer)) % int(denom)
    return str((numer * (10**places)) // denom).zfill(places)


def ratio_0(numer: int, denom: int, places: int = DEC) -> str:
    return "0." + frac_digits(numer, denom, places)


def mixed_int_dot_frac(integer: int, frac: str) -> Decimal:
    return Decimal(int(integer)) + Decimal("0." + frac)


def div_mod_decimal(val: Decimal, denom: int, places: int = DEC) -> str:
    """val/denom as decimal string with exactly `places` fractional digits (truncate)."""
    q = val / Decimal(denom)
    neg = q < 0
    q = abs(q)
    whole = int(q)
    frac = q - Decimal(whole)
    scaled = int(frac * (Decimal(10) ** places))
    body = str(scaled).zfill(places)[:places]
    if whole == 0:
        out = "0." + body
    else:
        out = f"{whole}.{body}"
    return ("-" + out) if neg else out


def build_core(x: int, y: int, mod: int = P) -> tuple[str, str, str, Decimal]:
    """
    Returns y/mod, x.(y/mod), (x.(y/mod))/mod strings and the Decimal of the core.
    """
    yfrac = frac_digits(y, mod)
    y_over = "0." + yfrac
    x_dot = f"{x}." + yfrac
    mixed = mixed_int_dot_frac(x, yfrac)
    core_dec = mixed / Decimal(mod)
    core_str = div_mod_decimal(mixed, mod)
    return y_over, x_dot, core_str, core_dec


def nest_n_over_mod(n: int, core: Decimal, mod: int = P) -> tuple[str, str]:
    """
    n.(core) / mod
    Take 156 fractional digits of core (if core in [0,1)) or of {core},
    form n.<digits>, divide by mod.
    """
    # fractional digits of core in [0,1) sense
    if core < 0:
        core = abs(core)
    # use fractional part of core for the dotted mix
    whole_c = int(core)
    frac_c = core - Decimal(whole_c)
    # if core already < 1, whole_c=0 and frac_c=core
    scaled = int(frac_c * (Decimal(10) ** DEC))
    # If core >= 1, user may still want digits of the full core string —
    # primary interpretation for C=(x.(y/p))/p on secp is C in (0,1).
    frac_digits_c = str(scaled).zfill(DEC)[:DEC]
    n_dot = f"{n}." + frac_digits_c
    mixed = mixed_int_dot_frac(n, frac_digits_c)
    out = div_mod_decimal(mixed, mod)
    return n_dot, out


def main() -> None:
    y_even = y_from_x(X135, even=True)  # compressed 02 => even y
    # verify on curve
    assert pow(y_even, 2, P) == (pow(X135, 3, P) + 7) % P

    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        if len(s) <= 160:
            print(s)

    w("=" * 88)
    w("P135 TARGET: count n until you get  ( n . ( x . (y/p) ) ) / p")
    w("=" * 88)
    w()
    w("Puzzle 135 public point (compressed 02 => even y)")
    w(f"  x = {X135}")
    w(f"  y = {y_even}")
    w()

    yp, xdot, core_s, core = build_core(X135, y_even, P)
    w("STEP BUILD (p-side)")
    w(f"  1) y/p       = {yp}")
    w(f"  2) x.(y/p)   = {xdot[:80]}...  (len_int={str(X135).__len__()}, frac={DEC})")
    w(f"  3) (x.(y/p))/p = C = {core_s}")
    w()
    w("COUNT METRIC")
    w("  n = number of incremental steps (matrix row / EC add).")
    w("  At step n form:")
    w("      n.(C) / p")
    w("  where C = (x_135.(y_135/p))/p")
    w("  That is exactly:  n.(x_135.(y_135/p))/p  with the inner mix already reduced once.")
    w()

    # Also show the fully-expanded single mix reading:
    # (n . (x . (y/p))) / p  using y/p digits under x, then that whole under n? 
    # User wrote: n.(x_135(y_135/p))/p
    # Interpret A: (n . C) / p           with C=(x.(y/p))/p
    # Interpret B: (n . (x.(y/p))) / p   one division only at the end

    yfrac = frac_digits(y_even, P)
    x_dot_dec = mixed_int_dot_frac(X135, yfrac)

    w("INTERPRETATION A  (nested reduce then count):")
    w("  C = (x.(y/p))/p")
    w("  target(n) = (n.C)/p")
    w()
    w("INTERPRETATION B  (single final /p):")
    w("  M = n.(x.(y/p))   # integer n, then digits of x.(y/p) ?")
    w("  Better B1: M = n + (x.(y/p))/10^{digits(x)+?} — ambiguous.")
    w("  Practical B: M = n.(digits of x.(y/p) fractional? No.)")
    w("  Use B as: M = n . <156 digits of (x.(y/p))/1 truncated via x.(y/p) value's frac>")
    w("            target = M/p")
    w()

    rows = []
    # Show targets for n=1..20 and n=135
    show_n = list(range(1, 21)) + [135, 256, 1000]
    w("-" * 88)
    w("target_A(n) = (n.C)/p")
    w("-" * 88)
    for n in show_n:
        n_dot, targ = nest_n_over_mod(n, core, P)
        w(f"  n={n:<5d}  n.C = {n_dot[:60]}...")
        w(f"         (n.C)/p = {targ}")
        rows.append(
            {
                "n": n,
                "interp": "A",
                "n_dot_C": n_dot,
                "target": targ,
            }
        )

    w()
    w("-" * 88)
    w("target_B(n) = (n.(x.(y/p)))/p   with frac digits from fractional part of x.(y/p)")
    w("-" * 88)
    # fractional part of x.(y/p) = {x + y/p} = fractional part
    xp_frac = x_dot_dec - Decimal(int(x_dot_dec))
    scaled = int(xp_frac * (Decimal(10) ** DEC))
    xdot_frac_digits = str(scaled).zfill(DEC)[:DEC]
    for n in show_n:
        n_dot = f"{n}." + xdot_frac_digits
        mixed = mixed_int_dot_frac(n, xdot_frac_digits)
        targ = div_mod_decimal(mixed, P)
        w(f"  n={n:<5d}  (n.(x.(y/p)))/p = {targ}")
        rows.append(
            {
                "n": n,
                "interp": "B",
                "n_dot_C": n_dot,
                "target": targ,
            }
        )

    # Calibration: how many lead-matrix steps exist in solved set
    w()
    w("-" * 88)
    w("CALIBRATION: how many incremental lead steps exist in solved matrix")
    w("-" * 88)
    # quick count from csv if present
    lead_csv = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_scalar_deltas.csv")
    if lead_csv.exists():
        with lead_csv.open(encoding="utf-8") as f:
            nsteps = sum(1 for _ in csv.DictReader(f))
        w(f"  plateau lead steps recorded = {nsteps}")
        w(f"  That is the known-matrix 'how many times' on solved keys only.")
    w("  For P135 search: n is the step counter of the incremental walk;")
    w("  stop when the live point's nested print matches the fixed P135 C-target")
    w("  under the chosen interpretation (A recommended: stable C from pubkey).")

    w()
    w("FIXED FINGERPRINT C (independent of n)")
    w(f"  C = (x_135.(y_135/p))/p")
    w(f"  C = {core_s}")
    w()
    w("Then you ONLY count n until (n.C)/p is the quantity you want to report,")
    w("or until a walk's state hits a predicate involving that form.")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["n", "interp", "n_dot_C", "target"])
        wr.writeheader()
        wr.writerows(rows)

    w()
    w(f"Wrote {OUT}")
    w(f"Wrote {CSV_OUT}")


if __name__ == "__main__":
    main()
