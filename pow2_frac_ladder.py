#!/usr/bin/env python3
"""
High-precision ladder: 2^(n + f) for n = hi .. lo

  f = log2(N) - 255   (N = secp256k1 curve order)

So:
  2^255.999... = N
  2^254.999... = N/2
  ...
  2^1.999...   = N / 2^254

Identity: 2^(n + f) = N * 2^(n - 255)

Requires: pip install mpmath
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from mpmath import mp, log, power, floor, ceil, nstr
except ImportError:
    print("Install mpmath:  pip install mpmath", file=sys.stderr)
    sys.exit(1)

# secp256k1 scalar field order
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# Literal fractional tail (log2(N) - 255); script also recomputes from N
FRAC_LITERAL = (
    "0.99999999999999999999999999999999999999461231979328931570871878708855078033045033577273800644526266767913779409199905351569508"
)


def log2_frac_from_n(precision: int) -> str:
    """Return log2(N) - 255 as a decimal string."""
    mp.dps = precision + 20
    frac = log(N) / log(2) - 255
    return nstr(frac, precision)


def fmt_fixed(x, precision: int) -> str:
    """Decimal string without scientific notation."""
    return format(x, f".{precision}f")


def pow2_ladder(
    hi: int = 255,
    lo: int = 1,
    precision: int = 120,
    use_literal_frac: bool = False,
    fixed: bool = True,
) -> list[dict]:
    mp.dps = precision + 30
    if use_literal_frac:
        frac = mp.mpf(FRAC_LITERAL)
    else:
        frac = log(N) / log(2) - 255

    rows = []
    for n in range(hi, lo - 1, -1):
        exp = mp.mpf(n) + frac
        # Exact ladder: N * 2^(n-255)  (n=255 -> N, n=254 -> N/2, ...)
        val = mp.mpf(N) * power(2, n - 255)
        exp_s = fmt_fixed(exp, precision) if fixed else nstr(exp, precision)
        val_s = fmt_fixed(val, precision) if fixed else nstr(val, precision)
        ratio_s = fmt_fixed(val / power(2, n), precision) if fixed else nstr(val / power(2, n), precision)

        rows.append(
            {
                "n": n,
                "exponent": exp_s,
                "value": val_s,
                "floor": int(floor(val)),
                "ceil": int(ceil(val)),
                "hex_floor": hex(int(floor(val))),
                "bits": int(floor(val)).bit_length() if floor(val) > 0 else 0,
                "n_over_2n": ratio_s,
            }
        )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(
        description="2^(n + log2(N)-255) ladder from n=255 down to n=1"
    )
    ap.add_argument("--hi", type=int, default=255, help="Start n (default 255)")
    ap.add_argument("--lo", type=int, default=1, help="End n (default 1)")
    ap.add_argument(
        "--precision", "-p", type=int, default=120, help="Decimal digits (default 120)"
    )
    ap.add_argument(
        "--literal-frac",
        action="store_true",
        help="Use hardcoded FRAC_LITERAL instead of log2(N)-255 from N",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write full table to file (UTF-8)",
    )
    ap.add_argument(
        "--csv",
        action="store_true",
        help="CSV output (n, exponent, value, floor, hex_floor)",
    )
    ap.add_argument(
        "--scientific",
        action="store_true",
        help="Use scientific notation instead of fixed decimal",
    )
    ap.add_argument(
        "--show-frac",
        action="store_true",
        help="Print fractional part log2(N)-255 and exit",
    )
    args = ap.parse_args()

    if args.show_frac:
        mp.dps = args.precision + 20
        computed = log2_frac_from_n(args.precision)
        print(f"log2(N) - 255 (computed, {args.precision} digits):")
        print(computed)
        print(f"\nliteral FRAC_LITERAL:")
        print(FRAC_LITERAL)
        print(f"\nN = {N}")
        return

    rows = pow2_ladder(
        args.hi, args.lo, args.precision, args.literal_frac, fixed=not args.scientific
    )

    lines: list[str] = []
    if args.csv:
        lines.append("n,exponent,value,floor,hex_floor,value_over_2^n")
        for r in rows:
            lines.append(
                f'{r["n"]},{r["exponent"]},{r["value"]},{r["floor"]},{r["hex_floor"]},{r["n_over_2n"]}'
            )
    else:
        lines += [
            f"2^(n + log2(N)-255)  |  N = {N}",
            f"range n = {args.hi} .. {args.lo}  |  precision = {args.precision}",
            "",
        ]
        for r in rows:
            lines += [
                f"n = {r['n']}",
                f"  exponent = {r['exponent']}",
                f"  2^exp    = {r['value']}",
                f"  floor    = {r['floor']}",
                f"  hex floor= {r['hex_floor']}",
                f"  value/2^n= {r['n_over_2n']}",
                "",
            ]

    text = "\n".join(lines) + "\n"

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out} ({len(rows)} rows)", file=sys.stderr)

    sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
