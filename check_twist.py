#!/usr/bin/env python3
"""Check if P135 pubkey is on curve, verify curve equation."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from puzzle_keys_53125 import parse_53125

# secp256k1
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
a = 0
b = 7

def is_on_curve(x, y):
    return (y * y - (x * x * x + b)) % p == 0

def is_quadratic_residue(v):
    """Check if v is a quadratic residue mod p (Legendre symbol = 1)"""
    return pow(v, (p - 1) // 2, p) == 1

pkeys = parse_53125()

# P135 coordinates from 53125.txt
px_135 = 0x145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16
py2_135 = 0xDCAEFCEFFBBFEEAAFBBDDE

# Check if px_135 is on curve
x3_7 = (px_135 * px_135 * px_135 + 7) % p
print(f"P135 px = {hex(px_135)}")
print(f"P135 px bit length = {px_135.bit_length()}")
print(f"P135 x³+7 mod p = {x3_7}")
print(f"Is y² available? Only partial: {hex(py2_135)}")
print(f"y² bit length = {py2_135.bit_length()}")
print(f"Is y² a quadratic residue? {is_quadratic_residue(x3_7)}")
print(f"y² from curve eq = {x3_7}")
print(f"Do we have full y? No, only 107 bits of y²")

# Check known puzzles for curve membership
print("\n--- Known puzzles on curve check ---")
for n in [65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130]:
    if n not in pkeys:
        continue
    rec = pkeys[n]
    on_curve = is_on_curve(rec.px, rec.py)
    print(f"P{n:3d}: on_curve={on_curve}")

# Check if P135 might be on the quadratic twist
# For quadratic twist: y² = x³ + 7*d² (mod p) where d is a non-residue
# Or: the twist has equation dy² = x³ + 7 (mod p)
# The twist curve: y² = x³ + 7*α (mod p) where α is a non-residue
# For secp256k1, α = 2 (a common non-residue) or α = some other value
# Actually the standard: t(x) = x³ + 7, and (x,y) is on curve if y² ≡ t(x) (mod p)
# (x,y) is on twist if vy² ≡ t(x) (mod p) and v is NOT a quadratic residue... hmm not quite
# The general quadratic twist is: y² = x³ + a·x/ω² + b/ω³ for some non-square ω
# For a=0: y² = x³ + b/ω³ (mod p)
# Let me just check if the curve equation is satisfied

# For P135, we need to check if there exists y such that y² = x³ + 7 (mod p)
# py2_135 is only 107 bits of the y-coordinate (from 53125.txt ladder)
# The full y would be: y = sqrt(x³+7) mod p
# We can compute it
from hashlib import sha256

# Compute sqrt of x³+7 mod p
# Tonelli-Shanks for p = 3 mod 4: sqrt(a) = a^{(p+1)/4} mod p
assert p % 4 == 3
y_computed = pow(x3_7, (p + 1) // 4, p)

# Both y and p-y are valid
print(f"\n--- P135 sqrt(x³+7) ---")
print(f"y1 = {hex(y_computed)}")
print(f"y1 bit length = {y_computed.bit_length()}")
print(f"y2 (p-y) = {hex(p - y_computed)}")
print(f"py2_135 (partial) = {hex(py2_135)}")

# Check if either y matches the partial py2
y1_low = y_computed & ((1 << 107) - 1)
y2_low = (p - y_computed) & ((1 << 107) - 1)
print(f"\ny1 low 107 bits = {hex(y1_low)}")
print(f"y2 low 107 bits = {hex(y2_low)}")
print(f"py2_135 (partial) = {hex(py2_135)}")
print(f"Match y1? {y1_low == py2_135}")
print(f"Match y2? {y2_low == py2_135}")
