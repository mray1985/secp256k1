"""Test 61425-style x/2^n decimal head vs page/priv."""
from decimal import Decimal, getcontext

getcontext().prec = 300

from puzzle_keys_53125 import parse_53125
from puzzle_echo_ratio_scan import PAGE

# exponents from 61425.txt
EXP = {
    120: {"page": 113, "priv": 119, "x": 255, "y": 253, "echo": 255},
    125: {"page": 118, "priv": 124, "x": 253, "y": 253, "echo": 255},
    130: {"page": 123, "priv": 129, "x": 254, "y": 255, "echo": 255},
    135: {"x": 252, "y": 254, "echo": 255},  # unsolved
}

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F


def norm_dec(val: int, exp: int) -> str:
    d = Decimal(val) / (Decimal(2) ** exp)
    return format(d, ".200f")


def top41(s: str, skip_leading_one_dot: bool = False) -> str:
    if skip_leading_one_dot and s.startswith("1."):
        body = s[2:]
    else:
        body = s.replace(".", "")
    return body[:41]


def top41_chars(s: str) -> str:
    """First 41 characters of decimal string as written."""
    return s[:41]


keys = parse_53125()
print("=== 61425 normalized decimals: first 41 CHARACTERS of string ===\n")
for n in [120, 125, 130]:
    k = keys[n]
    e = EXP[n]
    pg = PAGE[n]
    echo = pow(k.px, 3, p) + 7
    if echo >= p:
        echo %= p

    sx = norm_dec(k.px, e["x"])
    sp = norm_dec(pg, e["page"])
    sd = norm_dec(k.d, e["priv"])
    se = norm_dec(echo, e["echo"])

    print(f"P{n}")
    print(f"  x/2^{e['x']}     str41={top41_chars(sx)}")
    print(f"  page/2^{e['page']} str41={top41_chars(sp)}")
    print(f"  priv/2^{e['priv']} str41={top41_chars(sd)}")
    print(f"  echo/2^{e['echo']} str41={top41_chars(se)}")
    print(f"  frac41 x (after 1.): {top41(sx, True)}")
    print(f"  frac41 page:         {top41(sp, True)}")
    print(f"  frac41 priv:         {top41(sd, True)}")
    print()

# P135
Px = 9210836494447108270027136741376870869791784014198948301625976867708124077590
Py = 46351506704828816385393879789131775975171267756561783641521771795450741674800
echo = (pow(Px, 3, p) + 7) % p
e = EXP[135]
sx = norm_dec(Px, e["x"])
print("P135")
print(f"  x/2^{e['x']} str41={top41_chars(sx)}")
print(f"  frac41 x: {top41(sx, True)}")
print()

# B/N packing: x + y/N as decimal
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
print("=== B/N = Px + Py/N packing (carry layer) ===")
for n in [130]:
    k = keys[n]
    B = k.px * N + k.py
    q, rem = divmod(B, N)
    f = Decimal(rem) / Decimal(N)
    full = format(Decimal(q) + f, ".120f")
    print(f"P{n} B/N = {full[:90]}...")
    print(f"  int part (Px) first41: {str(k.px)[:41]}")
    print(f"  full decimal str first41 chars: {full[:41]}")
    print(f"  fractional tail first41: {full.split('.')[1][:41] if '.' in full else ''}")

# 53125 normalized priv format
print("\n=== 53125 fixed-width priv dec (leading zeros) ===")
for n in [130]:
    d = keys[n].d
    sd = str(d)
    # count leading zeros in 53125 format: total ~127 zero decimals before sig
    total = 130  # approximate field width from notes
    sig = sd
    zeros = total - len(sig)
    norm = "0." + "0" * zeros + sig
    print(f"P{n} norm priv dec first41 chars: {norm[:41]}")
    print(f"  sig starts at char {zeros+2}")
