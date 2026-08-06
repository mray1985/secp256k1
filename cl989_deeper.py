#!/usr/bin/env python3
"""
Deeper cl989 analysis: CF coefficients as sequence, 
check if convergent denominators relate to puzzle x-coordinates
beyond mod-9 coincidences.
"""
from math import floor
from decimal import Decimal, getcontext
getcontext().prec = 200

Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

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

known_d = {
    65: 30568377312064202855,
    90: 868012190417726402719548863,
    100: 868221233689326498340379183142,
    115: 31464123230573852164273674364426950,
    120: 919343500840980333540511050618764323,
    125: 37650549717742544505774009877315221420,
    130: 1103873984953507439627945351144005829577,
}

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

# Compute CF
x = Decimal(2 * Gy) / Decimal(3 * Gx * Gx)
terms = []
tmp = x
for _ in range(80):
    a = int(floor(tmp))
    terms.append(a)
    frac = tmp - a
    if frac == 0:
        break
    tmp = Decimal(1) / frac

print("CF coefficients (excluding a0=0):")
print(terms[1:])
print()

# Compute convergents
convs = []
h_pp, h_p = 0, 1
k_pp, k_p = 1, 0
for i, a in enumerate(terms):
    h = a * h_p + h_pp
    k = a * k_p + k_pp
    convs.append((h, k))
    h_pp, h_p = h_p, h
    k_pp, k_p = k_p, k

# For each puzzle, check if any convergent relates 
print("=" * 80)
print("CHECK: Does any convergent numerator mod p relate to puzzle x?")
print("=" * 80)
for pnum, comp in known_pub.items():
    x_pub, y_pub = decompress(comp)
    for i in range(1, len(convs)):
        h, k = convs[i]
        # Check: x_pub = k * inverse(h, p) mod p ?  (k/h mod p)
        try:
            ratio = k * pow(h, -1, p) % p
        except:
            continue
        # Check if ratio relates to x_pub
        if (ratio - x_pub) % p < 100 or (x_pub - ratio) % p < 100:
            pass  # unlikely
        # Check ratio * x_pub mod p
        prod = (ratio * x_pub) % p
        # Check if prod matches something
        
print()

# KEY: the CF of inverse tangent slope at G
# What if this is encoding the relationship between G and some other point?
# The convergents give us increasingly good rational approximations to 2*Gy/(3*Gx^2)
# 
# Convergent h/k means: h/k ≈ 2*Gy/(3*Gx^2)
# => h * 3*Gx^2 ≈ k * 2*Gy
# => k * 2*Gy - h * 3*Gx^2 = error
#
# As error -> 0, h/k -> 2*Gy/(3*Gx^2)
#
# The first few convergents give very specific h,k pairs.
# Each k * 2*Gy is almost equal to h * 3*Gx^2.
# 
# What if k (mod something) acts as a "filter" ?

print("=" * 80)
print("CHECK: denominators k at mod-9 boundaries")
print("=" * 80)
for i in range(1, min(30, len(convs))):
    h, k = convs[i]
    print(f"  Conv {i:2d}: k mod 9 = {k % 9}, k mod 720 = {k % 720}, h mod 9 = {h % 9}")

print()

# Check: is there a specific convergent whose denominator k 
# equals or divides any puzzle range boundary?
print("=" * 80)
print("CHECK: denominators vs puzzle bands")
print("=" * 80)
for i in range(1, len(convs)):
    h, k = convs[i]
    # For each puzzle, check if d == k or d % k == 0 etc.
    for pnum, d in known_d.items():
        if k != 0 and d % k == 0:
            print(f"  Conv {i}: k={k} divides Puzzle {pnum} d={d} (d/k = {d//k})")
        if h != 0 and d % h == 0:
            print(f"  Conv {i}: h={h} divides Puzzle {pnum} d={d} (d/h = {d//h})")
        if k == d:
            print(f"  Conv {i}: k = Puzzle {pnum} d!")

print()

# Hmm: what if we look at the CF not of 2*Gy/(3*Gx^2) but of 
# the MODULAR inverse? i.e., CF of 2*Gy * inv(3*Gx^2, p) ?
print("=" * 80)
print("CF of MODULAR 2*Gy * inverse(3*Gx^2, p)  (not real division)")
print("=" * 80)
lam_mod_val = (2 * Gy) * pow(3 * Gx * Gx, -1, p) % p
print(f"  (2*Gy) * (3*Gx^2)^-1 mod p = {lam_mod_val}")
print()

# CF of lam_mod_val / p (as rational)
val_mod = Decimal(lam_mod_val) / Decimal(p)
print(f"  That value / p = {float(val_mod):.15e}")
print()

terms_mod = []
tmp = val_mod
for _ in range(30):
    a = int(floor(tmp))
    terms_mod.append(a)
    frac = tmp - a
    if frac == 0:
        break
    tmp = Decimal(1) / frac

print(f"  CF: {terms_mod}")
print()

# The modular value divided by p is about 0.794... so CF starts with [0; 1, ...]
# Let's compare to the real CF

print("=" * 80)
print("COMPARISON: real-valued CF vs modular CF")
print("=" * 80)
print(f"  Real CF (2*Gy/(3*Gx^2)):   [0; {terms[1]}, {terms[2]}, {terms[3]}, ...]")
print(f"  Mod CF (inv mod p / p):    [0; {terms_mod[1]}, {terms_mod[2]}, {terms_mod[3]}, ...]")
print()

# Check: do the mod CF convergents relate to anything?
print("=" * 80)
print("Mod CF convergents vs puzzle x-coords")
print("=" * 80)
conv_mod = []
h_pp, h_p = 0, 1
k_pp, k_p = 1, 0
for a in terms_mod:
    h = a * h_p + h_pp
    k = a * k_p + k_pp
    conv_mod.append((h, k))
    h_pp, h_p = h_p, h
    k_pp, k_p = k_p, k

for i in range(1, min(15, len(conv_mod))):
    h, k = conv_mod[i]
    # k/h approx = that value = lam_mod/p
    # So k*inverse(h, p) mod p = ?
    try:
        ratio = k * pow(h, -1, p) % p
        print(f"  Repr {i}: k/h mod p = {ratio}")
    except:
        continue

print()
print("=" * 80)
print("One more angle: do the CF terms themselves encode the tangent")
print("doubling chain? Each term a_n in the CF of 2*Gy/(3*Gx^2)")
print("could represent a step in a Euclidean algorithm computation")
print("between 2*Gy and 3*Gx^2.")
print("=" * 80)

# The Euclidean algorithm on 2*Gy and 3*Gx^2:
a = 2 * Gy
b = 3 * Gx * Gx
steps = []
while b != 0:
    q = a // b
    steps.append(q)
    a, b = b, a % b

print(f"Euclidean algorithm steps for gcd(2*Gy, 3*Gx^2):")
print(f"  Steps: {steps}")
print()

# First step: 3*Gx^2 / (2*Gy) floor gives first quotient
# The rest of the CF continues from the remainder
print(f"  Step 0: floor(b/a) = {b // a if a != 0 else 'N/A'}")
print(f"  Step 1: floor(3*Gx^2 / (2*Gy)) = {3*Gx*Gx // (2*Gy)}")
print(f"  a_1 of CF = {terms[1]}")
print(f"  Match: {3*Gx*Gx // (2*Gy) == terms[1]}")
