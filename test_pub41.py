"""Test pubkey decimal projections vs page/d on solved puzzles."""
from decimal import Decimal, getcontext

getcontext().prec = 250

p = Decimal(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F)
N = Decimal(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141)

from puzzle_keys_53125 import parse_53125
from puzzle_echo_ratio_scan import PAGE


def norm_frac(x: Decimal, total_places: int = 130) -> str:
    """Like 53125: 0.000...000<significant> with fixed total width."""
    s = format(x, "f")
    if "." not in s:
        s += ".0"
    intpart, frac = s.split(".")
    # strip leading zeros from integer part for small values
    if int(intpart) == 0:
        # count leading zeros needed so significant starts at same column as priv in notes
        sig = intpart + frac
        sig = sig.lstrip("0") or "0"
        zeros = total_places - len(sig)
        return "0." + "0" * zeros + sig
    return s


def head41_decimal(x: Decimal) -> str:
    """Top 41 decimal digits of integer x."""
    s = str(int(x))
    return s[:41]


def head41_norm(x: Decimal, denom_power: int) -> str:
    """First 41 digits after decimal when x / 10^denom_power."""
    val = x / (Decimal(10) ** denom_power)
    frac = format(val, ".120f").split(".")[1]
    return frac[:41]


for n in [120, 125, 130]:
    k = parse_53125()[n]
    x, y, d = Decimal(k.px), Decimal(k.py), Decimal(k.d)
    pg = Decimal(PAGE[n])
    echo = (x**3 + 7) % p

    print(f"\n=== P{n} ===")
    print(f"d digits={len(str(int(d)))} page digits={len(str(int(pg)))}")
    print(f"head41(Px)={head41_decimal(x)}")
    print(f"head41(page)={head41_decimal(pg)}")
    print(f"head41(d)   ={head41_decimal(d)}")

    for name, val in [
        ("x/p+y/p2", x / p + y / (p * p)),
        ("x/p", x / p),
        ("Px/2^256", x / (Decimal(2) ** 256)),
        ("echo/p", echo / p),
    ]:
        frac41 = format(val, ".100f").split(".")[1][:41]
        print(f"{name:12} frac41={frac41}")

    # ratio tests
    if int(pg) > 0:
        r = int(x) // int(pg)
        print(f"Px // page = {r}")
        print(f"head41(Px)/head41(page) approx? {Decimal(head41_decimal(x)) / Decimal(head41_decimal(pg)):.6f}")
