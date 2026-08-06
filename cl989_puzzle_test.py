#!/usr/bin/env python3
"""
Test cl989's continued fraction convergents against puzzle public keys.
CF of 2*Gy/(3*Gx^2) = 1/lam(G). Convergents h/k give rational approximations.
Check if k (denominator) or derived values relate to puzzle keys or publics.
"""
from math import floor, gcd
from decimal import Decimal, getcontext
getcontext().prec = 200

# secp256k1
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# Known puzzle private keys
known_d = {
    65: 30568377312064202855,
    90: 868012190417726402719548863,
    100: 868221233689326498340379183142,
    115: 31464123230573852164273674364426950,
    120: 919343500840980333540511050618764323,
    125: 37650549717742544505774009877315221420,
    130: 1103873984953507439627945351144005829577,
}

# Compute continued fraction of 2*Gy/(3*Gx^2)
x = Decimal(2 * Gy) / Decimal(3 * Gx * Gx)

def cf(x_val, max_terms=100):
    terms = []
    for i in range(max_terms):
        a = int(floor(x_val))
        terms.append(a)
        frac = x_val - a
        if frac == 0:
            break
        x_val = Decimal(1) / frac
    return terms

terms = cf(x, 80)
print(f"CF of 2*Gy/(3*Gx^2) (first 10): {terms[:10]}")
print()

# Compute convergents with their full values
convs = []
h_prev2, h_prev1 = 0, 1
k_prev2, k_prev1 = 1, 0
for i, a in enumerate(terms):
    h = a * h_prev1 + h_prev2
    k = a * k_prev1 + k_prev2
    val = Decimal(h) / Decimal(k) if k != 0 else None
    convs.append((i, a, h, k, val))
    h_prev2, h_prev1 = h_prev1, h
    k_prev2, k_prev1 = k_prev1, k

# For each convergent h/k = 2*Gy/(3*Gx^2) approx
# h * 3*Gx^2 approx = k * 2*Gy
# So k * 2*Gy - h * 3*Gx^2 is small
# The modular version: k * 2*Gy - h * 3*Gx^2 mod p

print("Checking convergents against known puzzle d values...")
for i in range(1, min(40, len(convs))):
    idx, a, h, k, val = convs[i]
    if k == 0:
        continue
    
    # Check if k (or h) matches any known d
    for pnum, d in known_d.items():
        if k == d:
            print(f"  *** CONVERGENT {idx}: k = {k} MATCHES Puzzle {pnum} d!")
        if h == d:
            print(f"  *** CONVERGENT {idx}: h = {h} MATCHES Puzzle {pnum} d!")
    
    # Check if k mod something relates
    # k * 2*Gy - h * 3*Gx^2 should be small (convergent property)
    error_real = abs(k * 2*Gy - h * 3*Gx * Gx)
    if error_real < 10**78:
        if i < 10 or error_real < 10**60:
            print(f"  Conv {idx}: |k*2Gy - h*3Gx^2| = {error_real}")

print()

# More interesting: compute the modular version
# lam_mod = 3*Gx^2 * (2*Gy)^-1 mod p
lam_mod = (3 * Gx * Gx) * pow(2 * Gy, -1, p) % p

# The CF tells us about the real-valued ratio
# But in ECC we work mod p
# What if we take the convergent and reduce mod p?

print("Checking convergents reduced mod p/n against puzzle d values...")
print(f"  lam(G) mod p = {lam_mod}")
print(f"  lam(G) mod 9 = {lam_mod % 9}")
print(f"  lam(G) mod N = {lam_mod % N}")
print()

# For each convergent: k/h approximates lam(G) in real numbers
# lam_mod = lam(G) mod p
# If k/h has the same remainder mod p as lam_mod...

for i in range(1, min(40, len(convs))):
    idx, a, h, k, val = convs[i]
    if k == 0:
        continue
    
    # k_mod = k mod something
    for pnum, d in known_d.items():
        # Check if d relates to this convergent
        # d * h % k or d * k % h or something
        val_mod_p = k * pow(h, -1, p) % p if h % p != 0 else -1
        val_mod_N = k * pow(h, -1, N) % N if h % N != 0 else -1
        
        if val_mod_p == lam_mod:
            print(f"  Conv {idx}: k/h mod p = lam_mod!")
        if val_mod_N == (3 * Gx * Gx) * pow(2 * Gy, -1, N) % N:
            print(f"  Conv {idx}: k/h mod N matches lam mod N!")
    
    # Check: does the convergent predict something about any puzzle key?
    for pnum, d in known_d.items():
        if d < k and k % d == 0:
            print(f"  Conv {idx}: k={k} is divisible by Puzzle {pnum} d={d}")
        if d < h and h % d == 0:
            print(f"  Conv {idx}: h={h} is divisible by Puzzle {pnum} d={d}")

print()

# Now check the actual puzzle PUBLIC KEYS
# Read from known locations
print("=" * 80)
print("TESTING AGAINST PUZZLE PUBLIC KEYS")
print("=" * 80)

# Load known public keys for solved puzzles
known_pub = {
    65: "02746b76f3d633cafdde3c676c1416e868362c03d1126b16bce6a96a5e6d68a40b",
    90: "02e2b8b6cda2bd76e4e78e5b29482a13a6d6405dbf504594d5544a503b8976c04c",
    100: "0376b1fce76c07f4bacc9df8dbe57278b8489b1e595c69ca6e26d87d0874b75531",
    115: "0372bf2e9c2afc92029539bbeb4bb1a78c1fddb1862b224098c6889a3f05a41323",
    120: "029f8666abe2e93e0c93b5cdf1ae52af32d49b3b4a52e9c5a4fba536c5a6ceb6b4",
    125: "0283e63c9de1bcf155b9249d1d636a3167ece1606aa8e47888f12b179e42808b89",
    130: "02ecc8097fd386b15cc167ad293a79f327bdd779dd9e5b7ba8f5bb837a0548af7b",
    160: "02e0a8b039282faf6fe0fd769cfbc4b6b4cf8758ba68220eac420e32b91ddfa673",
}

# Decompress and check convergents
def decompress(comp_hex):
    prefix = int(comp_hex[:2], 16)
    x = int(comp_hex[2:], 16)
    y_sq = (pow(x, 3, p) + 7) % p
    y = pow(y_sq, (p + 1) // 4, p)
    if prefix == 0x02 and y % 2 != 0:
        y = p - y
    elif prefix == 0x03 and y % 2 != 1:
        y = p - y
    return (x, y)

print("Testing if convergent denominators relate to public key x-coordinates...")
for i in range(1, min(30, len(convs))):
    idx, a, h, k, val = convs[i]
    if k == 0:
        continue
    
    for pnum, comp_hex in known_pub.items():
        x_pub, y_pub = decompress(comp_hex)
        
        # Check if k or h matches x_pub
        if k == x_pub:
            print(f"  *** CONV {idx}: k = x-coord of Puzzle {pnum}!")
        if h == x_pub:
            print(f"  *** CONV {idx}: h = x-coord of Puzzle {pnum}!")
        
        # Check if k and x_pub have same mod-9, mod-7, etc.
        conv_mod9 = k % 9
        pub_mod9 = x_pub % 9
        if conv_mod9 == pub_mod9 and i < 10:
            print(f"  Conv {idx}: k mod 9 = {conv_mod9} matches P{pnum} x mod 9 = {pub_mod9}")

print()

# KEY INSIGHT: What if the CF terms themselves encode the puzzle structure?
# The CF coefficients after a1: 4, 9, 1, 18, 3, 1, 235, 2, 1, 1, 2, 3, 1, 3, 8, 5, 9, ...
print("=" * 80)
print("DEEPER: checking if CF terms or convergents relate to (r*d - z) mod 9")
print("=" * 80)

# For each known puzzle, check if the d value has a factoradic/mod relationship
# with any convergent
for pnum, d in known_d.items():
    for i in range(1, min(20, len(convs))):
        idx, a, h, k, val = convs[i]
        if k == 0:
            continue
        
        # Check d * h mod k or something
        if k != 0:
            prod_mod = (d * h) % k
            # The tangent slope relates to doubling G
            # Could d * (2*Gy)/(3*Gx^2) mod something be meaningful?

print()

# The most promising angle: the CONVERGENT DENOMINATORS are numerators when inverted
# If h/k = 2*Gy/(3*Gx^2), then k/h = 3*Gx^2/(2*Gy) = lam(G) in real numbers
# lam_mod = lam(G) mod p
# So lam_mod = k/h mod p = k * h^{-1} mod p

print(f"lam_mod_p = {lam_mod}")
print()

# Check each convergent's k*h^{-1} mod p
for i in range(1, min(15, len(convs))):
    idx, a, h, k, val = convs[i]
    if h == 0 or h % p == 0:
        continue
    try:
        lam_from_cf = k * pow(h, -1, p) % p
    except:
        continue
    
    diff = (lam_mod - lam_from_cf) % p
    print(f"  Conv {idx}: k/h mod p = {lam_from_cf}")
    print(f"           diff from lam_mod = min({min(diff, p-diff)})")
    
    # Any puzzle key equal to the diff?
    for pnum, d in known_d.items():
        if d == diff:
            print(f"           *** DIFF = Puzzle {pnum} d!")
        if d == min(diff, p-diff):
            print(f"           *** MIN DIFF = Puzzle {pnum} d!")
