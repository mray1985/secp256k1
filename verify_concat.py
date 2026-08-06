#!/usr/bin/env python3
"""
Verify the concatenation hypothesis: concat(dG) == d * concat(G)

Where concat(P) = Px * p + Py  (512-bit universe)

Also recompute all values from 'everything cubed plus and squared.txt'
"""

from __future__ import annotations
import csv
import io
import sys
import time
from pathlib import Path

# secp256k1 constants
p  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
Delta = N - p  # actually p - N, but |p - N|
Delta = p - N  # correct sign

def inv(a, m):
    """Modular inverse via extended Euclidean."""
    if a < 0:
        a = a % m
    g, x, _ = extended_gcd(a, m)
    if g != 1:
        raise ValueError(f"No inverse for {a} mod {m}")
    return x % m

def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    g, x, y = extended_gcd(b % a, a)
    return g, y - (b // a) * x, x

def ec_add(P, Q):
    """Add two points on secp256k1. P or Q can be None (point at infinity)."""
    if P is None:
        return Q
    if Q is None:
        return P
    Px, Py = P
    Qx, Qy = Q
    if Px == Qx and Py == Qy:
        # Point doubling
        lam = (3 * Px * Px) * inv(2 * Py, p) % p
    elif Px == Qx:
        return None  # Point at infinity
    else:
        lam = (Qy - Py) * inv(Qx - Px, p) % p
    Rx = (lam * lam - Px - Qx) % p
    Ry = (lam * (Px - Rx) - Py) % p
    return (Rx, Ry)

def ec_mul(k, P=None):
    """Scalar multiplication via double-and-add."""
    if P is None:
        P = (Gx, Gy)
    result = None
    addend = P
    while k > 0:
        if k & 1:
            result = ec_add(result, addend)
        addend = ec_add(addend, addend)
        k >>= 1
    return result

def concat(Px, Py):
    """Concatenate coordinates into the 512-bit universe."""
    return Px * p + Py

def unconcat(c, bits=256):
    """Split a 512-bit concatenated value back into (Px, Py)."""
    Py = c % p
    Px = c // p
    return Px, Py


def test_concatenation_hypothesis():
    """THE MAIN TEST: does concat(dG) == d * concat(G)?"""
    print("=" * 80)
    print("TEST 1: CONCATENATION HYPOTHESIS")
    print("  Claim: concat(dG) == d * concat(G)")
    print("  Where concat(P) = Px * p + Py")
    print("=" * 80)
    print()

    G_concat = concat(Gx, Gy)
    print(f"G_concat = Gx * p + Gy")
    print(f"  = {G_concat}")
    print(f"  bits = {G_concat.bit_length()}")
    print()

    # Test with Puzzle 130
    d130 = 1103873984953507439627945351144005829577
    dG130 = ec_mul(d130)
    dGx130, dGy130 = dG130
    P_concat_130 = concat(dGx130, dGy130)
    right_130 = d130 * G_concat

    print(f"Puzzle 130:")
    print(f"  d  = {d130}")
    print(f"  dGx = {dGx130}")
    print(f"  dGy = {dGy130}")
    print(f"  P_concat (dGx*p + dGy) = {P_concat_130}")
    print(f"  d * G_concat           = {right_130}")
    print(f"  EQUAL? {P_concat_130 == right_130}")
    print(f"  DIFF  = {P_concat_130 - right_130}")
    diff130 = P_concat_130 - right_130
    if diff130 != 0:
        print(f"  diff mod p = {diff130 % p}")
        print(f"  diff mod N = {diff130 % N}")
        print(f"  diff mod 2^256 = {diff130 % (2**256)}")
        print(f"  diff / p = {diff130 / p}")
        print(f"  diff / N = {diff130 / N}")
        # Check if diff is a simple function of d
        print(f"  diff / d = {diff130 / d130}")
        print(f"  diff / d^2 = {diff130 / (d130**2)}")
        print(f"  diff / (d*p) = {diff130 / (d130 * p)}")
    print()

    # Test with small multiples
    print("Testing small multiples of G:")
    print("-" * 60)
    for n in range(1, 11):
        nG = ec_mul(n)
        nGx, nGy = nG
        left = concat(nGx, nGy)
        right = n * G_concat
        eq = left == right
        diff = left - right
        print(f"  {n:3d}*G: concat = {left}  n*G_concat = {right}  "
              f"equal={eq}  diff={diff}")
    print()


def test_all_solved_puzzles():
    """Test the concatenation hypothesis on all solved puzzles from the CSV."""
    print("=" * 80)
    print("TEST 2: ALL SOLVED PUZZLES (from puzzle_catalog_160.csv)")
    print("=" * 80)
    print()

    csv_path = Path(__file__).resolve().parent / "ARCHIVE" / "puzzle_catalog_160.csv"
    if not csv_path.exists():
        print(f"  Catalog not found at {csv_path}")
        return

    text = csv_path.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(text))

    G_concat = concat(Gx, Gy)
    results = []

    for row in reader:
        n = int(row["bits"])
        priv_hex = (row.get("private_key") or "").strip()
        if not priv_hex or priv_hex == "0" * 64:
            continue  # unsolved

        d = int(priv_hex, 16)
        if d == 0:
            continue

        t0 = time.time()
        dG = ec_mul(d)
        dt = time.time() - t0

        if dG is None:
            print(f"  Puzzle {n:3d}: dG is point at infinity?! d={d}")
            continue

        dGx, dGy = dG
        left = concat(dGx, dGy)
        right = d * G_concat
        eq = left == right
        diff = left - right

        results.append((n, d, eq, diff, dt))
        status = "MATCH" if eq else f"diff={diff}"
        print(f"  Puzzle {n:3d}: d={d}, equal={eq}, {status}  [{dt:.1f}s]")

    print()
    match_count = sum(1 for _, _, eq, _, _ in results if eq)
    total = len(results)
    print(f"Results: {match_count}/{total} puzzles match the hypothesis")
    print()


def test_modular_values():
    """Recompute values from 'everything cubed plus and squared.txt'."""
    print("=" * 80)
    print("TEST 3: VERIFY 'everything cubed plus and squared.txt' VALUES")
    print("=" * 80)
    print()

    # Values from the file (Puzzle 130)
    r  = 90653255469745952335985143920649543885181555095025199315947044135806663628368
    s  = 15509729875763924304053419655647994379903175655107184284998698212653288468986
    z  = 66278737796829840734606014530466656889790152192829793669891337810330530090951
    x  = 9210836494447108270027136741376870869791784014198948301625976867708124077590
    y  = 46351506704828816385393879789131775975171267756561783641521771795450741674800

    # Expected values from file
    expected = {
        "r^2 mod N": 96562902533625897603460047735762010661189010928765698949452128026602155228106,
        "s^2 mod N": 96633062460232844275254534674908534018048927145047099657238266226722223949666,
        "z^2 mod N": 35443562081029757417737255448395220167299015248157600567782353293988236962354,
        "x^2 mod N": 82944941655207997329437648359552100174129976124682274592696069541747303193959,
        "y^2 mod N": 26369715013067173826580669186754858354769139257468225515508850790522022326173,
        "r^2 mod p": 48209571124613121796124994237081553895679906663951501372913070280429284794206,
        "s^2 mod p": 46115111352185024872505126293257558341945986386534255241146600900051545389002,
        "z^2 mod p": 87058042430072552971936713202452791860242696082700719672832256025724088668605,
        "x^2 mod p": 60527182355131945001990130378928253226530482133937349087135576501304139419179,
        "y^2 mod p": 80184233617433755134183875136831551618578922487806929476230322368028862899169,
    }

    computed = {
        "r^2 mod N": (r * r) % N,
        "s^2 mod N": (s * s) % N,
        "z^2 mod N": (z * z) % N,
        "x^2 mod N": (x * x) % N,
        "y^2 mod N": (y * y) % N,
        "r^2 mod p": (r * r) % p,
        "s^2 mod p": (s * s) % p,
        "z^2 mod p": (z * z) % p,
        "x^2 mod p": (x * x) % p,
        "y^2 mod p": (y * y) % p,
    }

    errors = 0
    for key in expected:
        match = expected[key] == computed[key]
        if not match:
            errors += 1
            print(f"  MISMATCH: {key}")
            print(f"    expected = {expected[key]}")
            print(f"    computed = {computed[key]}")
            print(f"    diff     = {expected[key] - computed[key]}")
        else:
            print(f"  OK: {key}")

    # Also check r^3+7, s^3+7, z^3+7, x^3+7, y^3+7 mod N and p
    expected_cubed = {
        "r^3+7 mod N": 24879821969881342698453870499117630300356777343725767668138372196708140311771,
        "s^3+7 mod N": 26273619879871536083438568099044811682915652410132285872874656696618406172173,
        "z^3+7 mod N": 64192327846994028407262959972350233514674523710249492451540342054648034963624,
        "x^3+7 mod N": 57563452117916498723007967691461129715157617201398411347467584363219451634490,
        "y^3+7 mod N": 83405604466436355153951664735341402617565540829087921666920820099474307048870,
        "r^3+7 mod p": 36128738557023842197460850546205429335937024355616500847429829845960355299841,
        "s^3+7 mod p": 59619708611871966815965381838721618880478032623972914091542513023560279269004,
        "z^3+7 mod p": 45130350292618377973791882267901314453805649777621286862218311678203929159743,
        "x^3+7 mod p": 80184233617433755134183875136831551618578922487806929476230322368028862899169,
        "y^3+7 mod p": 46971900760178163078217937648191106399491715078766300120465841945665243936006,
    }

    computed_cubed = {
        "r^3+7 mod N": (r**3 + 7) % N,
        "s^3+7 mod N": (s**3 + 7) % N,
        "z^3+7 mod N": (z**3 + 7) % N,
        "x^3+7 mod N": (x**3 + 7) % N,
        "y^3+7 mod N": (y**3 + 7) % N,
        "r^3+7 mod p": (r**3 + 7) % p,
        "s^3+7 mod p": (s**3 + 7) % p,
        "z^3+7 mod p": (z**3 + 7) % p,
        "x^3+7 mod p": (x**3 + 7) % p,
        "y^3+7 mod p": (y**3 + 7) % p,
    }

    print()
    for key in expected_cubed:
        match = expected_cubed[key] == computed_cubed[key]
        if not match:
            errors += 1
            print(f"  MISMATCH: {key}")
            print(f"    expected = {expected_cubed[key]}")
            print(f"    computed = {computed_cubed[key]}")
            print(f"    diff     = {expected_cubed[key] - computed_cubed[key]}")
        else:
            print(f"  OK: {key}")

    # Mod Delta
    expected_delta = {
        "r^2 mod D": 98864441863045483871394836549864174754,
        "s^2 mod D": 238118159901609525837556538308673541982,
        "z^2 mod D": 236583089977749261901463662705577781945,
        "x^2 mod D": 257571014067455514446071182887639299746,
        "y^2 mod D": 325568155499376329823863116466087240206,
    }

    computed_delta = {
        "r^2 mod D": (r * r) % Delta,
        "s^2 mod D": (s * s) % Delta,
        "z^2 mod D": (z * z) % Delta,
        "x^2 mod D": (x * x) % Delta,
        "y^2 mod D": (y * y) % Delta,
    }

    print()
    for key in expected_delta:
        match = expected_delta[key] == computed_delta[key]
        if not match:
            errors += 1
            print(f"  MISMATCH: {key}")
            print(f"    expected = {expected_delta[key]}")
            print(f"    computed = {computed_delta[key]}")
        else:
            print(f"  OK: {key}")

    print()
    if errors == 0:
        print("  ALL modular arithmetic values verified correctly!")
    else:
        print(f"  {errors} ERRORS found!")
    print()


def test_shadow_tracking():
    """Verify shadow tracking: x.y/p for successive point operations."""
    print("=" * 80)
    print("TEST 4: SHADOW TRACKING (x.y/p for point operations)")
    print("=" * 80)
    print()

    def shadow(point):
        """Compute x.y/p for a point."""
        if point is None:
            return "INF"
        Px, Py = point
        c = Px * p + Py
        return c / (p * p)

    def shadow_hex(point):
        """Shadow as hex."""
        if point is None:
            return "INF"
        Px, Py = point
        c = Px * p + Py
        return hex(c)

    # Start with G
    P0 = (Gx, Gy)
    print(f"G:        shadow = {shadow(P0):.77f}")
    print(f"          x      = {P0[0]}")
    print(f"          y      = {P0[1]}")
    print()

    # Double
    P2 = ec_add(P0, P0)
    print(f"2*G:      shadow = {shadow(P2):.77f}")
    print(f"          bridge: R_2P / R_P = {shadow(P2) / shadow(P0)}")
    print(f"          bridge: R_2P * x - 1 = R_2P => x = {(shadow(P2) + 1) / shadow(P0)}")
    print()

    # Triple (= 2G + G)
    P3 = ec_add(P2, P0)
    print(f"3*G:      shadow = {shadow(P3):.77f}")
    print(f"          bridge: R_3P / R_P = {shadow(P3) / shadow(P0)}")
    print()

    # 4G = 2*2G
    P4 = ec_add(P2, P2)
    print(f"4*G:      shadow = {shadow(P4):.77f}")
    print(f"          bridge: R_4P / R_2P = {shadow(P4) / shadow(P2)}")
    print()

    # 5G = 4G + G
    P5 = ec_add(P4, P0)
    print(f"5*G:      shadow = {shadow(P5):.77f}")
    print()

    # 8G = 2*4G
    P8 = ec_add(P4, P4)
    print(f"8*G:      shadow = {shadow(P8):.77f}")
    print()

    # 10G = 2*5G
    P10 = ec_add(P5, P5)
    print(f"10*G:     shadow = {shadow(P10):.77f}")
    print()

    # Check bridge equations from inthere.txt
    print("Bridge equation check (from inthere.txt):")
    print(f"  For doubling: R_new = a * R_old - 1")
    for n, Psucc in [(2, P2), (4, P4), (8, P8), (10, P10)]:
        n_half = n // 2
        Phalf = ec_mul(n_half)
        r_old = shadow(Phalf)
        r_new = shadow(Psucc)
        if r_old != 0:
            a = (r_new + 1) / r_old
            print(f"  {n}*G vs {n_half}*G: a = (R_{n} + 1) / R_{n_half} = {a:.77f}")
    print()


def test_np_verification():
    """Verify the NPV formulas from inthere.txt."""
    print("=" * 80)
    print("TEST 5: NPV FORMULA VERIFICATION")
    print("=" * 80)
    print()

    rp = 0.78289679430476346015545710430795985714967923686492941619055694132527630802774
    rN = 0.78289679430476346015545710430795985715260292998303562655283279749223513706442

    # r/p and r/N
    r_val = 90653255469745952335985143920649543885181555095025199315947044135806663628368
    actual_rp = r_val / p
    actual_rN = r_val / N

    print(f"rp (file)  = {rp}")
    print(f"rp (exact) = {actual_rp}")
    print(f"rp match = {abs(rp - actual_rp) < 1e-77}")
    print()
    print(f"rN (file)  = {rN}")
    print(f"rN (exact) = {actual_rN}")
    print(f"rN match = {abs(rN - actual_rN) < 1e-77}")
    print()

    # NPV formula: sum_{k=1}^{4} n / (1+r)^k
    # = n * [(1-(1+r)^{-4}) / r]
    for label, r in [("p", rp), ("N", rN)]:
        factor = sum(1 / (1 + r)**k for k in range(1, 5))
        print(f"NPV_{label}: sum{{1/(1+r)^k, k=1..4}} = {factor:.77f}")
        # The claim is NPV = 2^134 or 2^135-1
        for target_name, target in [("2^134", 2**134), ("2^135-1", 2**135 - 1)]:
            n_val = target / factor
            print(f"  if NPV = {target_name}: n = {n_val}")
            # Check if n is close to d
            d_known = 1103873984953507439627945351144005829577
            print(f"    n / d = {n_val / d_known}")
        print()

    # kN = (1.42e-77)^{-p/2^256}
    k_approx = 1.4217358348577939311963700876302699653049451897690192487679609440884413768933e-77
    exponent = -p / (2**256)
    kN_computed = k_approx ** (p / (2**256))  # file says ^{-(p/2^256)} but computes differently
    kp_computed = k_approx ** (p / (2**256))

    print(f"k_approx = {k_approx}")
    print(f"p/2^256  = {p / 2**256}")
    print(f"N/2^256  = {N / 2**256}")
    print(f"kN (from file) = 7.0336554476733917947090844104676338953710167025885525595807748590535416064e76")
    print(f"kN computed    = {kN_computed}")
    print(f"kp computed    = {kp_computed}")
    print()


def test_512bit_universe():
    """Analyze the 512-bit universe structure."""
    print("=" * 80)
    print("TEST 6: 512-BIT UNIVERSE STRUCTURE")
    print("=" * 80)
    print()

    G_concat = concat(Gx, Gy)
    print(f"p = {p}")
    print(f"  bits = {p.bit_length()}")
    print()
    print(f"Gx = {Gx}")
    print(f"  bits = {Gx.bit_length()}")
    print()
    print(f"Gy = {Gy}")
    print(f"  bits = {Gy.bit_length()}")
    print()
    print(f"G_concat = Gx * p + Gy")
    print(f"  = {G_concat}")
    print(f"  bits = {G_concat.bit_length()}")
    print()

    # For Puzzle 130
    d130 = 1103873984953507439627945351144005829577
    dG130 = ec_mul(d130)
    dGx, dGy = dG130
    P_concat = concat(dGx, dGy)

    print(f"Puzzle 130 P_concat = {P_concat}")
    print(f"  bits = {P_concat.bit_length()}")
    print(f"  dGx bits = {dGx.bit_length()}")
    print(f"  dGy bits = {dGy.bit_length()}")
    print()

    # Can we split P_concat back into dGx and dGy?
    recovered_Px = P_concat // p
    recovered_Py = P_concat % p
    print(f"Recovery test: unconcat(P_concat)")
    print(f"  recovered Px = {recovered_Px}")
    print(f"  actual dGx   = {dGx}")
    print(f"  match = {recovered_Px == dGx}")
    print(f"  recovered Py = {recovered_Py}")
    print(f"  actual dGy   = {dGy}")
    print(f"  match = {recovered_Py == dGy}")
    print()

    # Key question: if we know d and G_concat, can we recover dG?
    # d * G_concat = d * (Gx * p + Gy) = d*Gx*p + d*Gy
    product = d130 * G_concat
    print(f"d * G_concat = {product}")
    print(f"  bits = {product.bit_length()}")
    print()

    # Split the product
    prod_Px = product // p
    prod_Py = product % p
    print(f"Splitting d*G_concat at p boundary:")
    print(f"  upper part = {prod_Px}")
    print(f"  lower part = {prod_Py}")
    print(f"  actual dGx = {dGx}")
    print(f"  actual dGy = {dGy}")
    print(f"  Px match = {prod_Px == dGx}")
    print(f"  Py match = {prod_Py == dGy}")
    print()

    if prod_Px != dGx:
        print(f"  upper diff = {prod_Px - dGx}")
        print(f"  lower diff = {prod_Py - dGy}")
        print(f"  upper diff / p = {(prod_Px - dGx) / p}")
        print(f"  lower diff / p = {(prod_Py - dGy) / p}")
        # What if it's d*G_concat mod p^2?
        product_mod_p2 = (d130 * G_concat) % (p * p)
        mod_Px = product_mod_p2 // p
        mod_Py = product_mod_p2 % p
        print(f"\n  d*G_concat mod p^2:")
        print(f"    Px = {mod_Px}  match={mod_Px == dGx}")
        print(f"    Py = {mod_Py}  match={mod_Py == dGy}")

        # mod N^2
        product_mod_N2 = (d130 * G_concat) % (N * N)
        modNx = product_mod_N2 // p
        modNy = product_mod_N2 % p
        print(f"\n  d*G_concat mod N^2, split at p:")
        print(f"    Px = {modNx}  match={modNx == dGx}")
        print(f"    Py = {modNy}  match={modNy == dGy}")

        # mod N^2, split at N
        modNx2 = product_mod_N2 // N
        modNy2 = product_mod_N2 % N
        print(f"\n  d*G_concat mod N^2, split at N:")
        print(f"    Px = {modNx2}  match={modNx2 == dGx}")
        print(f"    Py = {modNy2}  match={modNy2 == dGy}")

    print()


if __name__ == "__main__":
    t_start = time.time()

    test_concatenation_hypothesis()
    test_512bit_universe()
    test_shadow_tracking()
    test_np_verification()
    test_modular_values()
    test_all_solved_puzzles()

    print(f"\nTotal time: {time.time() - t_start:.1f}s")
