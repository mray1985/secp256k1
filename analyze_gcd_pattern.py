#!/usr/bin/env python3
"""Verify GCD patterns from discretelog69.txt and explore coordinate relationships."""
from __future__ import annotations
import sys, math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from puzzle_keys_53125 import parse_53125

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

pkeys = parse_53125()

# P135 x-coordinate
px_135 = 0x145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16

# Compute both possible y values for P135
x3_7 = (px_135**3 + 7) % p
y_135_pos = pow(x3_7, (p + 1) // 4, p)
y_135_neg = p - y_135_pos

print("=== P135 GCD ANALYSIS ===")
print(f"px_135 = {px_135}")
print(f"y_pos  = {y_135_pos}")
print(f"y_neg  = {y_135_neg}")
print(f"Gy     = {Gy}")
print()
print(f"GCD(Gy, y_pos) = {math.gcd(Gy, y_135_pos)}")
print(f"GCD(Gy, y_neg) = {math.gcd(Gy, y_135_neg)}")
print(f"Expected from discretelog69.txt: GCD(Gy, y_135) = 8")
print()

# The y matching GCD=8 gives us which y P135 uses
match_pos = math.gcd(Gy, y_135_pos) == 8
match_neg = math.gcd(Gy, y_135_neg) == 8
print(f"y_pos gives GCD=8? {match_pos}")
print(f"y_neg gives GCD=8? {match_neg}")
print()

# Verify y/Gy ratio from discretelog69.txt
y_p135 = y_135_pos if match_pos else y_135_neg
k_y_num = 5793938338103602048174234973641471996896408469570222955190221474431342709350
k_y_den = 4083813752594852122260385641313380398058909172582405409492363041969667185303
computed_k_y_num = y_p135 // math.gcd(y_p135, Gy)
computed_k_y_den = Gy // math.gcd(y_p135, Gy)
print(f"y_p135 = {y_p135}")
print(f"y_p135/Gy reduced: num={computed_k_y_num}, den={computed_k_y_den}")
print(f"Expected num: {k_y_num}")
print(f"Expected den: {k_y_den}")
print(f"Match numerator? {computed_k_y_num == k_y_num}")
print(f"Match denominator? {computed_k_y_den == k_y_den}")
print()

# Also verify x/Gx ratio
k_x_num = 307027883148236942334237891379229028993059467139964943387532562256937469253
k_x_den = 1835542100742578122319290629838951144208353448459253139183339578679637224308
g = math.gcd(px_135, Gx)
computed_k_x_num = px_135 // g
computed_k_x_den = Gx // g
print(f"px_135 = {px_135}")
print(f"Gx = {Gx}")
print(f"GCD(px_135, Gx) = {g}")
print(f"px_135/Gx reduced: num={computed_k_x_num}, den={computed_k_x_den}")
print(f"Expected num: {k_x_num}")
print(f"Expected den: {k_x_den}")
print(f"Match numerator? {computed_k_x_num == k_x_num}")
print(f"Match denominator? {computed_k_x_den == k_x_den}")
print()

# Now compute GCD patterns across ALL solved puzzles
print("=== GCD(Gy, y_puzzle) ACROSS SOLVED PUZZLES ===")
print(f"{'Puzzle':>6} {'GCD(Gy,y)':>10} {'GCD(Gx,x)':>10} {'d mod Gy':>12}")
for n in sorted(pkeys.keys()):
    if n > 130:
        continue
    rec = pkeys[n]
    gcd_y = math.gcd(Gy, rec.py)
    gcd_x = math.gcd(Gx, rec.px)
    d_mod = rec.d % Gy if Gy > rec.d else rec.d
    print(f"{n:6d} {gcd_y:10d} {gcd_x:10d} {d_mod:12d}")

# P135 prediction
print(f"{'135':>6} {math.gcd(Gy, y_p135):10d} {'?':>10} {'?':>12}")
print()

# Factorize the GCDs and check pattern
print("=== FACTORIZATION OF GCD(Gy, y) ===")
for n in sorted(pkeys.keys()):
    if n > 130:
        continue
    rec = pkeys[n]
    gcd_y = math.gcd(Gy, rec.py)
    if gcd_y > 1:
        factors = []
        tmp = gcd_y
        for pr in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]:
            cnt = 0
            while tmp % pr == 0:
                tmp //= pr
                cnt += 1
            if cnt:
                factors.append(f"{pr}^{cnt}")
        print(f"P{n:3d}: GCD={gcd_y} = {' × '.join(factors)}")
