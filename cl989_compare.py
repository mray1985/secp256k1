#!/usr/bin/env python3
"""
Side-by-side comparison of the two continued fractions in cl989.txt.

Point 1: Generator G — CF of 2*Gy/(3*Gx^2)
Point 2: Point where Y^2 = A (A = true71 value) — CF of 2*Y/(3*X^2)

Compare waveforms, find shared subsequences, check if the
Euclidean algorithm encodes relationships between the two points.
"""
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# Point 1: Generator G
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424

# Point 2: from cl989.txt's second CF
X2 = 9210836494447108270027136741376870869791784014198948301625976867708124077590
Y2 = 46351506704828816385393879789131775975171267756561783641521771795450741674800

# Verify A = Y^2 mod p = X^3 + 7 mod p
A = (Y2 * Y2) % p
print(f"A (Y^2 mod p) = {A}")
print()

def euclidean_cf(a, b):
    """Return the continued fraction terms of a/b (a < b) using integer Euclidean algorithm."""
    terms = []
    while b != 0:
        q = a // b
        terms.append(q)
        a, b = b, a % b
    return terms

# Compute CFs via Euclidean algorithm on the integers
# CF of 2*y/(3*x^2) = Euclidean algorithm on (2*y, 3*x^2) with first term = 0
num1 = 2 * Gy
den1 = 3 * Gx * Gx
cf1_raw = euclidean_cf(num1, den1)

num2 = 2 * Y2
den2 = 3 * X2 * X2
cf2_raw = euclidean_cf(num2, den2)

print(f"Point 1 (G):        2*Gy = {num1}")
print(f"                   3*Gx^2 = {den1}")
print(f"                   CF terms: {cf1_raw}")
print()

print(f"Point 2 (A-point):  2*Y = {num2}")
print(f"                   3*X^2 = {den2}")
print(f"                   CF terms: {cf2_raw}")
print()

# Trim: both start with [0, huge, ...]
# The first term (0) is because a < b initially
cf1 = cf1_raw  # keep full
cf2 = cf2_raw 

print("=" * 80)
print("SIDE-BY-SIDE CF COEFFICIENTS (after initial 0)")
print("=" * 80)

max_len = max(len(cf1), len(cf2))
print(f"{'n':<6} {'CF1 (G)':<12} {'CF2 (A-pt)':<12} {'match':<8} {'ratio':<15}")
print("-" * 60)

for i in range(min(max_len, 60)):
    c1 = cf1[i] if i < len(cf1) else None
    c2 = cf2[i] if i < len(cf2) else None
    match = "Y" if c1 == c2 and c1 is not None else ""
    ratio = ""
    if c1 is not None and c2 is not None and c2 != 0:
        ratio = f"{c1/c2:.4f}"
    elif c1 is not None and c2 is None:
        ratio = "end CF2"
    elif c2 is not None and c1 is None:
        ratio = "end CF1"
    print(f"{i:<6} {str(c1):<12} {str(c2):<12} {match:<8} {ratio:<15}")

print()

# Find shared subsequences
print("=" * 80)
print("SHARED SUBSEQUENCES (3+ consecutive matching terms)")
print("=" * 80)

# Convert to strings for subsequence matching
s1 = ",".join(str(t) for t in cf1)
s2 = ",".join(str(t) for t in cf2)

# Find common subsequences of length >= 3
def find_common_subseq(arr1, arr2, min_len=3):
    matches = []
    for start1 in range(len(arr1)):
        for start2 in range(len(arr2)):
            length = 0
            while (start1 + length < len(arr1) and 
                   start2 + length < len(arr2) and
                   arr1[start1 + length] == arr2[start2 + length]):
                length += 1
            if length >= min_len:
                matches.append((start1, start2, length, arr1[start1:start1+length]))
    # Remove duplicates (keep longest)
    return matches

matches = find_common_subseq(cf1, cf2, 3)
# Deduplicate: keep only matches not contained in a longer match
deduped = []
for m in matches:
    s1, s2, l, seq = m
    contained = False
    for m2 in matches:
        s1b, s2b, lb, seqb = m2
        if lb > l and s1 >= s1b and s1 + l <= s1b + lb and s2 >= s2b and s2 + l <= s2b + lb:
            contained = True
            break
    if not contained:
        deduped.append(m)

deduped.sort(key=lambda x: -x[2])
print(f"Found {len(deduped)} shared subsequences (non-overlapping, longest first):")
for s1, s2, l, seq in deduped[:20]:
    print(f"  CF1[{s1}:{s1+l}] = CF2[{s2}:{s2+l}] = {seq}")

print()

# Compare the structure: what if we look at the ratios between adjacent terms?
print("=" * 80)
print("RATIO PATTERNS: adjacent term comparisons")
print("=" * 80)
print(f"{'n':<6} {'CF1 term':<10} {'CF2 term':<10} {'CF1 ratio':<12} {'CF2 ratio':<12}")
print("-" * 52)
for i in range(1, min(50, max_len)):
    r1 = cf1[i] / cf1[i-1] if cf1[i-1] != 0 else float('inf')
    r2 = cf2[i] / cf2[i-1] if cf2[i-1] != 0 and i < len(cf2) else float('inf')
    c1 = cf1[i] if i < len(cf1) else None
    c2 = cf2[i] if i < len(cf2) else None
    if c1 is not None and c2 is not None:
        print(f"{i:<6} {c1:<10} {c2:<10} {r1:<12.4f} {r2:<12.4f}")

print()

# Compare the modular tangent slopes
lam1 = (3 * Gx * Gx) * pow(2 * Gy, -1, p) % p
lam2 = (3 * X2 * X2) * pow(2 * Y2, -1, p) % p

print("=" * 80)
print("MODULAR TANGENT SLOPES")
print("=" * 80)
print(f"lam(G) mod p            = {lam1}")
print(f"lam(A-point) mod p      = {lam2}")
print(f"diff                    = {(lam1 - lam2) % p}")
print(f"lam(G) mod 9            = {lam1 % 9}")
print(f"lam(A-point) mod 9      = {lam2 % 9}")
print(f"lam(G) * lam(A-point) mod p = {(lam1 * lam2) % p}")
print()

# Check if the slopes relate to each other via known transformations
print("=" * 80)
print("CHECK: is the A-point related to G?")
print("=" * 80)

G = (Gx, Gy)
def ec_add(P1, P2):
    if P1 is None: return P2
    if P2 is None: return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2:
        if y1 == y2:
            lam = (3 * x1 * x1) * pow(2 * y1, -1, p) % p
        else:
            return None
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, p) % p
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

A_pt = (X2, Y2)

# Check with the known private keys
known_d = {
    65: 30568377312064202855,
    90: 868012190417726402719548863,
    100: 868221233689326498340379183142,
    115: 31464123230573852164273674364426950,
    120: 919343500840980333540511050618764323,
    125: 37650549717742544505774009877315221420,
    130: 1103873984953507439627945351144005829577,
}

# Check if A_pt = d*G for any known d
for pnum, d in known_d.items():
    Q = ec_mul(d, G)
    if Q and Q[0] == X2:
        print(f"  A-point = Puzzle {pnum} public key!")
        break

# Check if A_pt + G or A_pt - G gives a known point
for pnum, d in known_d.items():
    Q = ec_mul(d, G)
    if Q:
        # Check A_pt + Q
        S = ec_add(A_pt, Q)
        if S and S == ec_mul(d+1, G) if d+1 < 2**161 else False:
            pass  # not reliable to check

# Print the A-point compressed
print(f"A-point x-coord: {X2}")
print(f"A-point y-coord: {Y2}")
even_odd = "02" if Y2 % 2 == 0 else "03"
print(f"A-point compressed: {even_odd}{X2:064x}")
print()

# Lambda at A-point in real numbers vs modular
from decimal import Decimal, getcontext
getcontext().prec = 200
lam2_real = Decimal(3 * X2 * X2) / Decimal(2 * Y2)
print(f"lam(A-pt) in REAL numbers:")
print(f"  {lam2_real}")
print(f"  first CF term (floor): {int(lam2_real)}")
print(f"  matches CF[1]: {int(lam2_real) == cf2[1]}")
