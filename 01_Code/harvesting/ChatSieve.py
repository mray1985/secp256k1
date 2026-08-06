# dual_sieve_test.py
# Dual-sieve test: D/8 corridor + N-8 reflection checksum

from decimal import Decimal, getcontext
import math

getcontext().prec = 100

# secp256k1 constants
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
G = (Gx, Gy)

O = None


def inv_mod(a, m):
    return pow(a % m, -1, m)


def point_add(P, Q):
    if P is None:
        return Q
    if Q is None:
        return P

    x1, y1 = P
    x2, y2 = Q

    if x1 == x2 and (y1 + y2) % p == 0:
        return None

    if P == Q:
        lam = (3 * x1 * x1) * inv_mod(2 * y1, p) % p
    else:
        lam = (y2 - y1) * inv_mod(x2 - x1, p) % p

    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)


def scalar_mult(k, P=G):
    k %= N
    result = None
    addend = P

    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1

    return result


def log2_decimal(n):
    return Decimal(n).ln() / Decimal(2).ln()


def frac_power_int(n, numerator, denominator):
    # high precision approximate integer floor of n^(numerator/denominator)
    return int((Decimal(n).ln() * Decimal(numerator) / Decimal(denominator)).exp())


def test_puzzle(height, priv=None, pub=None):
    print("=" * 90)
    print(f"Puzzle height: {height}")

    lower = 2 ** (height - 1)
    upper = 2 ** height - 1
    D = upper - lower + 1
    D8 = D // 8
    mid = lower + D // 2

    lanes = {
        "A_mid_minus_D8": mid - D8,
        "B_mid": mid,
        "C_mid_plus_D8": mid + D8,
    }

    print(f"lower = {lower}")
    print(f"upper = {upper}")
    print(f"D     = {D}")
    print(f"D/8   = {D8}")
    print(f"mid   = {mid}")

    if priv is not None:
        P = scalar_mult(priv)
    elif pub is not None:
        P = pub
    else:
        print("Need priv or pub.")
        return

    x, y = P
    print(f"\nPublic x = {x}")
    print(f"Public y = {y}")

    # N-8 reflection checksum
    P8 = scalar_mult(8, P)
    PN8 = scalar_mult(N - 8, P)

    print("\n[N-8 REFLECTION CHECK]")
    print(f"8P.x      = {P8[0]}")
    print(f"(N-8)P.x  = {PN8[0]}")
    print(f"same x?   = {P8[0] == PN8[0]}")
    print(f"y sum=p?  = {(P8[1] + PN8[1]) % p == 0}")

    # coordinate echoes
    x_echo = frac_power_int(x, height, 256)
    y_echo = frac_power_int(y, height, 256)
    curve_val = (pow(x, 3, p) + 7) % p
    curve_echo = frac_power_int(curve_val, height, 256)

    print("\n[ECHO VALUES]")
    print(f"x^(h/256)       = {x_echo}")
    print(f"y^(h/256)       = {y_echo}")
    print(f"(x^3+7 mod p)^(h/256) = {curve_echo}")

    print("\n[LANE SCORE TABLE]")
    for name, lane in lanes.items():
        dx = abs(lane - x_echo)
        dy = abs(lane - y_echo)
        dc = abs(lane - curve_echo)

        ratio_x = Decimal(lane) / Decimal(x_echo) if x_echo else Decimal(0)
        ratio_y = Decimal(lane) / Decimal(y_echo) if y_echo else Decimal(0)
        log_drift_x = log2_decimal(lane) - log2_decimal(x_echo)
        log_drift_y = log2_decimal(lane) - log2_decimal(y_echo)

        if priv:
            priv_dist = abs(lane - priv)
            priv_ratio = Decimal(lane) / Decimal(priv)
        else:
            priv_dist = None
            priv_ratio = None

        print("-" * 90)
        print(name)
        print(f"lane              = {lane}")
        print(f"|lane - x_echo|   = {dx}")
        print(f"|lane - y_echo|   = {dy}")
        print(f"|lane - curve|    = {dc}")
        print(f"lane / x_echo     = {ratio_x}")
        print(f"lane / y_echo     = {ratio_y}")
        print(f"log2 drift x      = {log_drift_x}")
        print(f"log2 drift y      = {log_drift_y}")

        if priv is not None:
            print(f"|lane - priv|     = {priv_dist}")
            print(f"lane / priv       = {priv_ratio}")


# Known solved examples
PUZZLES = {
    70: 970436974005023690481,
    75: 22538323240989823823367,
    80: 1105520030589234487939456,
    85: 21090315766411506144426920,
    90: 868012190417726402719548863,
    100: 868221233689326498340379183142,
    110: 1090246098153987172547740458951748,
    120: 919343500840980333540511050618764323,
    125: 37650549717742544505774009877315221420,
    130: 1103873984953507439627945351144005829577,
}


if __name__ == "__main__":
    for height, priv in PUZZLES.items():
        test_puzzle(height, priv=priv)

    # Puzzle 135 public key only
    puzzle135_pub = (
        9210836494447108270027136741376870869791784014198948301625976867708124077590,
        46351506704828816385393879789131775975171267756561783641521771795450741674800,
    )

    test_puzzle(135, pub=puzzle135_pub)