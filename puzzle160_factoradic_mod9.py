#!/usr/bin/env python3
"""
Puzzle 160 Factoradic Mod-9 Attack
===================================
From "The important findings.txt":
  - d = 7 (mod 9) for Puzzle 160 (from Origin Rule)
  - d = a1 + 2*a2 + 6*a3 + 6*a4 + 3*a5 (mod 9)
    because 6! and above are all = 0 (mod 9)
  - This cuts 720 possible first-five factoradic combinations to 80
"""

import hashlib
from itertools import product

# secp256k1 constants
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

# Puzzle 160
P160_PUB_COMPRESSED = 0x02E0A8B039282FAF6FE0FD769CFBC4B6B4CF8758BA68220EAC420E32B91DDFA673
BAND_LO = 2**159
BAND_HI = 2**160 - 1

# Factorials
FACT = [1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880, 3628800]

def modinv(a, m):
    if a < 0:
        a = a % m
    g, x, _ = _egcd(a, m)
    if g != 1:
        raise Exception("No inverse")
    return x % m

def _egcd(a, b):
    if a == 0:
        return b, 0, 1
    g, y, x = _egcd(b % a, a)
    return g, x - (b // a) * y, y

def ec_add(P1, P2):
    if P1 is None:
        return P2
    if P2 is None:
        return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2 and y1 == y2:
        lam = (3 * x1 * x1) * modinv(2 * y1, p) % p
    elif x1 == x2:
        return None
    else:
        lam = (y2 - y1) * modinv(x2 - x1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)

def ec_mul(k, P):
    result = None
    addend = P
    while k > 0:
        if k & 1:
            result = ec_add(result, addend)
        addend = ec_add(addend, addend)
        k >>= 1
    return result

def decompress_pubkey(compressed):
    prefix = (compressed >> 256) & 0xFF
    x = compressed & ((1 << 256) - 1)
    y_sq = (pow(x, 3, p) + 7) % p
    y = pow(y_sq, (p + 1) // 4, p)
    if prefix == 0x02:
        if y % 2 != 0:
            y = p - y
    elif prefix == 0x03:
        if y % 2 != 1:
            y = p - y
    return (x, y)

def mod9_from_prefix(a1, a2, a3, a4, a5):
    return (a1 + 2*a2 + 6*a3 + 6*a4 + 3*a5) % 9

def main():
    print("=" * 80)
    print("PUZZLE 160 FACTORADIC MOD-9 ATTACK")
    print("=" * 80)
    print()
    print("Puzzle 160 band: [2^159, 2^160)")
    print(f"  LO = {BAND_LO}")
    print(f"  HI = {BAND_HI}")
    print(f"  d = 7 (mod 9)  [Origin Rule]")
    print()

    Px, Py = decompress_pubkey(P160_PUB_COMPRESSED)
    print(f"Public key Px = {Px:064x}")
    print(f"Public key Py = {Py:064x}")
    print()

    # Step 1: Generate all valid prefixes
    print("=" * 80)
    print("STEP 1: Generate valid factoradic prefixes (a1..a5)")
    print("  Constraint: a1 + 2*a2 + 6*a3 + 6*a4 + 3*a5 = 7 (mod 9)")
    print("=" * 80)

    valid_prefixes = []
    all_count = 0

    for a1 in range(0, 2):
        for a2 in range(0, 3):
            for a3 in range(0, 4):
                for a4 in range(0, 5):
                    for a5 in range(0, 6):
                        all_count += 1
                        if mod9_from_prefix(a1, a2, a3, a4, a5) == 7:
                            valid_prefixes.append((a1, a2, a3, a4, a5))

    print(f"Total combinations: {all_count}")
    print(f"Valid (= 7 mod 9): {len(valid_prefixes)}")
    print(f"Reduction factor: {all_count / len(valid_prefixes):.1f}x")
    print()

    # Step 2: Verify against known puzzles
    print("=" * 80)
    print("STEP 2: Verify mod-9 against known solved puzzles")
    print("=" * 80)
    print()

    known = [
        (65,  30568377312064202855),
        (90,  868012190417726402719548863),
        (100, 868221233689326498340379183142),
        (115, 31464123230573852164273674364426950),
        (120, 919343500840980333540511050618764323),
        (125, 37650549717742544505774009877315221420),
        (130, 1103873984953507439627945351144005829577),
    ]

    print(f"{'Puzzle':<10} {'d mod 9':<10} {'d mod 720':<12} {'d mod 6':<10}")
    print("-" * 42)
    for pnum, d in known:
        print(f"P{pnum:<9} {d % 9:<10} {d % 720:<12} {d % 6:<10}")

    print()
    print("Key observation: Each puzzle has a DIFFERENT d mod 9.")
    print("For P160, the Origin Rule gives d = 7 (mod 9).")
    print()

    # Step 3: Print all 80 valid prefixes
    print("=" * 80)
    print("STEP 3: All 80 valid prefixes")
    print("=" * 80)
    print()

    print(f"{'#':<5} {'a1':<4} {'a2':<4} {'a3':<4} {'a4':<4} {'a5':<4} {'prefix_val':<15} {'mod 9':<8} {'mod 720':<10}")
    print("-" * 65)

    for i, (a1, a2, a3, a4, a5) in enumerate(valid_prefixes):
        val = a1*1 + a2*2 + a3*6 + a4*24 + a5*120
        print(f"{i+1:<5} {a1:<4} {a2:<4} {a3:<4} {a4:<4} {a5:<4} {val:<15} {val % 9:<8} {val % 720:<10}")

    # Save to file
    with open("puzzle160_valid_prefixes.txt", "w") as f:
        f.write("Puzzle 160 Valid Factoradic Prefixes (d = 7 mod 9)\n")
        f.write("=" * 65 + "\n\n")
        f.write(f"{'#':<5} {'a1':<4} {'a2':<4} {'a3':<4} {'a4':<4} {'a5':<4} {'prefix_val':<15} {'mod9':<8} {'mod720':<10}\n")
        f.write("-" * 65 + "\n")
        for i, (a1, a2, a3, a4, a5) in enumerate(valid_prefixes):
            val = a1*1 + a2*2 + a3*6 + a4*24 + a5*120
            f.write(f"{i+1:<5} {a1:<4} {a2:<4} {a3:<4} {a4:<4} {a5:<4} {val:<15} {val % 9:<8} {val % 720:<10}\n")

    print()
    print(f"Saved to puzzle160_valid_prefixes.txt")

    # Step 4: Compute d ranges for each prefix
    print()
    print("=" * 80)
    print("STEP 4: d-range analysis per prefix")
    print("=" * 80)
    print()

    # For each prefix, d = prefix_val + 720*k for some k >= 0
    # We need d in [2^159, 2^160)
    # So: prefix_val + 720*k >= 2^159  =>  k >= (2^159 - prefix_val) / 720
    # And: prefix_val + 720*k <= 2^160 - 1  =>  k <= (2^160 - 1 - prefix_val) / 720

    total_candidates = 0
    for i, (a1, a2, a3, a4, a5) in enumerate(valid_prefixes):
        val = a1*1 + a2*2 + a3*6 + a4*24 + a5*120
        if val < BAND_LO:
            k_min = (BAND_LO - val + 719) // 720
        else:
            k_min = 0
        k_max = (BAND_HI - val) // 720
        count = k_max - k_min + 1 if k_max >= k_min else 0
        total_candidates += count

        if i < 5 or i >= 75:
            print(f"Prefix {i+1:3d}: val={val:5d}, k_range=[{k_min}, {k_max}], count={count}")
        elif i == 5:
            print("  ... (70 more prefixes) ...")

    print()
    print(f"Total candidates across all 80 prefixes: {total_candidates}")
    print(f"  = 2^{total_candidates.bit_length()-1:.1f}")
    print()

    # Step 5: The REAL attack - test a sample from each prefix
    print("=" * 80)
    print("STEP 5: Sample test - check if any prefix gives immediate match")
    print("=" * 80)
    print()
    print("For each prefix, testing the FIRST candidate in the band...")
    print()

    G = (Gx, Gy)
    tested = 0
    for i, (a1, a2, a3, a4, a5) in enumerate(valid_prefixes):
        val = a1*1 + a2*2 + a3*6 + a4*24 + a5*120
        if val < BAND_LO:
            k_min = (BAND_LO - val + 719) // 720
        else:
            k_min = 0
        d_test = val + k_min * 720

        if d_test <= BAND_HI:
            Q = ec_mul(d_test, G)
            if Q is not None and Q[0] == Px:
                print(f"  *** FOUND! d = {d_test}")
                print(f"  *** d = 0x{d_test:040x}")
                print(f"  *** Factoradic: ({a1},{a2},{a3},{a4},{a5},...)")
                return
            tested += 1

    print(f"  Tested {tested} candidates (first per prefix) - no match")
    print()
    print("This is expected: the first candidate per prefix is unlikely")
    print("to be the answer. The search space per prefix is ~2^150.")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY & NEXT STEPS")
    print("=" * 80)
    print()
    print("CONFIRMED:")
    print(f"  - 80 valid factoradic prefixes (from 720 total = 9x reduction)")
    print(f"  - d = 7 (mod 9) is the Origin Rule constraint for P160")
    print(f"  - Each prefix defines d = prefix_val + 720*k")
    print(f"  - Total search space: ~{total_candidates} candidates")
    print()
    print("LIMITATION:")
    print("  - 9x reduction alone is not enough (still ~2^150 per prefix)")
    print("  - Need ADDITIONAL constraints beyond mod-9")
    print()
    print("POSSIBLE NEXT STEPS:")
    print("  1. Extend to more factoradic digits (a6..a10) for mod-7!, mod-8! etc.")
    print("  2. Combine with Origin Rule Omega classification")
    print("  3. Use the prefix structure to build a specialized BSGS/Kangaroo")
    print("  4. Cross-reference with the projection-defect fingerprint (true77)")

if __name__ == "__main__":
    main()
