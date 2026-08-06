#!/usr/bin/env python3
"""
TRUE71: R-point orbit as a filter on d for Puzzle 135.

For a candidate d:
  k = (z + r*d) * s^-1 mod N
  R = k*G
  R.x cube-root orbit should contain +1 sector (for Omega=+1)

Quantify: 
  1. How many candidates pass by chance?
  2. Can we avoid EC mult and use mod-9 linearity?
  3. Is this any stronger than the existing mod-9 phase filter?
"""
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
delta = p - N

omega_p = 55594575648329892869085402983802832744385952214688224221778511981742606582254
omega2_p = pow(omega_p, 2, p)

# Puzzle 135 params
r = 0x86bec9faea4892fd98d718bdfc770d0d11c3d6bfd4328f25fe9b06bfadb9650
s = 0x224a322e81c044d341521f65fabdfa86d84673fb55ed7533862e37f7724931fa
z = 0x92886faaf53f90a5c03d6af773a726e75097179306b980e5d28772e612e00fc7

def inv_mod(a, m):
    return pow(a % m, -1, m)

def ec_add(P1, P2):
    if P1 is None: return P2
    if P2 is None: return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2:
        if y1 == y2:
            lam = (3 * x1 * x1) * inv_mod(2 * y1, p) % p
        else:
            return None
    else:
        lam = (y2 - y1) * inv_mod(x2 - x1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)

Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G = (Gx, Gy)

def ec_mul(k, P):
    k %= N
    result = None
    addend = P
    while k:
        if k & 1:
            result = ec_add(result, addend)
        addend = ec_add(addend, addend)
        k >>= 1
    return result

def orbit_has_plus1(x):
    """Check if the cube-root orbit of x mod p contains +1 sector residue."""
    if x is None: return False
    vals = [x % 9, (x * omega_p) % p % 9, (x * omega2_p) % p % 9]
    return any(v in {1, 4, 7} for v in vals)

def orbit_has_plus1_at_pos2(x):
    """Check if position 2 of the orbit has +1 sector."""
    if x is None: return False
    v = (x * omega_p) % p % 9
    return v in {1, 4, 7}

print("=" * 80)
print("R-POINT ORBIT FILTER ANALYSIS")
print("=" * 80)

# Step 1: Test on solved puzzles
print("\n1. Testing on solved puzzles (known k):")
print("-" * 50)

# Puzzle data with known k from earlier TRUE57_TRUE58
puzzle_data = {
    # (d, r, s, z, expected_Omega)
    90:  (868012190417726402719548863, 69673304720876160075229624583547409885636207434161816957474172319527500474415, 97038951651984860535162953990839467775379668224703951115386138227640696288110, 108607603064108400354204638258399442578446802427847655697342082898377364957650, 0),
    100: (868221233689326498340379183142, 100182957009067260676129163398412919222496578752554197866304926759487636509729, 28135718596264842528026832512780199014590938928166564704017051320826227212364, 92658811528607241046615800185940848341501446227238040823641188964292429243346, -1),
    115: (31464123230573852164273674364426950, 62641386159082452201681958645023150433102249854530986013739112343764069317711, 57173300502008905547164461559156881131070769387074668282781609789424127766964, 25503591383824339903668991496043698383026651390680015855174297365908280645324, -1),
    120: (919343500840980333540511050618764323, 100480591869089994315869534883181916927590910231092411991845900661570178084117, 79710542396302313400402596614648379968891478395986995273506372852496691769412, 90708834597179240795497837125737623083285617848204160763007390135961413413786, 1),
    125: (37650549717742544505774009877315221420, 63833400142572548270929737909115586706553550972272560806111166328807706465903, 86777844952265629243632214806708945515546825149465734937061438392076484952394, 114685814202658958114869362395063184268140526153753635517334369058997879218236, -1),
    130: (1103873984953507439627945351144005829577, 6276493284178792263728042533158666787380597239988507667129682066325892829262, 44144285110210404363535680397465912091779523554376824160174040814929564634369, 32021882259886928322342858832383403585000823395929942343563162622448315056855, -1),
}

for pnum, (d, rp, sp, zp, omega_exp) in sorted(puzzle_data.items()):
    k = ((zp + rp * d) % N) * inv_mod(sp, N) % N
    R = ec_mul(k, G)
    Rx = R[0]
    has_plus1 = orbit_has_plus1(Rx)
    has_p2 = orbit_has_plus1_at_pos2(Rx)
    expected_ok = "+1" if omega_exp == 1 else "0" if omega_exp == 0 else "-1"
    print(f"  Puzzle {pnum}: Omega={omega_exp} Rx mod9={Rx % 9} orbit_has+1={has_plus1} pos2+1={has_p2} expected={expected_ok}")

# Step 2: Quantify the filter strength
print("\n2. Filter strength analysis for Puzzle 135:")
print("-" * 50)

# For a RANDOM candidate d:
# k = A + B*d mod N (linear in d)
# R = k*G = (A + B*d)*G
# R.x is distributed like a random curve point
# Under the assumption R.x is uniform mod p:
#   P(any of 3 values in {1,4,7}) = 1 - (6/9)^3 = 19/27 ≈ 70.4%
#   P(position 2 in {1,4,7}) = 3/9 = 33.3%

import random
random.seed(42)
NUM_SAMPLES = 1000

# Generate random d candidates in P135 range [2^134, 2^135)
lower = 1 << 134
upper = (1 << 135) - 1

A = (z * inv_mod(s, N)) % N
B = (r * inv_mod(s, N)) % N

pass_any = 0
pass_pos2 = 0
for _ in range(NUM_SAMPLES):
    d_cand = random.randint(lower, upper)
    k_cand = (A + B * d_cand) % N
    R_cand = ec_mul(k_cand, G)
    Rx = R_cand[0]
    if orbit_has_plus1(Rx):
        pass_any += 1
    if orbit_has_plus1_at_pos2(Rx):
        pass_pos2 += 1

print(f"  Sampled {NUM_SAMPLES} random d candidates in [2^134, 2^135)")
print(f"  Expected pass rate (any pos): ~70.4%")
print(f"  Actual pass rate (any pos):   {100*pass_any/NUM_SAMPLES:.1f}%")
print(f"  Expected pass rate (pos 2):   ~33.3%")
print(f"  Actual pass rate (pos 2):     {100*pass_pos2/NUM_SAMPLES:.1f}%")

# Step 3: Compare to existing mod-9 phase filter
print("\n3. Comparison to existing phase filter:")
print("-" * 50)
print(f"  Phase filter: (r*d - z) mod N mod 9 in {{1,4,7}} → 3/9 = 33.3% survive")
print(f"  R.x orbit (any pos):  1 - (6/9)^3 = 70.4% survive")
print(f"  R.x orbit (pos 2):    3/9 = 33.3% survive")
print(f"  Combined (phase + pos2): 33.3% * 33.3% = 11.1% survive")
print(f"  Combined (phase + any):  33.3% * 70.4% = 23.5% survive")
print()
print(f"  Combined filter eliminates ~89% of candidates.")
print(f"  But requires EC mult per candidate = O(2^134) EC operations.")
print(f"  Even with 89% elimination: 0.11 * 2^134 ≈ 2^131 candidates remain.")
print()
print(f"  Pollard kangaroo already runs in O(2^67) without any filter.")
print(f"  The filters don't reduce the EXPONENT — they're at best a constant factor.")

# Step 4: Can we avoid EC mult?
print("\n4. Can we check the orbit WITHOUT computing k*G?")
print("-" * 50)
print(f"  k = {hex(A)} + {hex(B)} * d mod N")
print(f"  R.x = ( (A + B*d) * G ).x")
print(f"  This requires point multiplication — no way to extract R.x")
print(f"  from d without EC operations.")
print()
print(f"  R.x mod 9 depends on d in a nonlinear way (EC group law).")
print(f"  No linear shortcut for R.x % 9.")
print()
print(f"  Theoretical approach: precompute A*G and B*G, then for")
print(f"  each d compute A*G + d*(B*G) via point addition chain.")
print(f"  But this is still O(2^134) additions.")
