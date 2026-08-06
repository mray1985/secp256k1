#!/usr/bin/env python3
"""
FULL ENCODING FRAMEWORK with mpmath at 100-digit precision.
Tests: E(G) vs E(Q), group operations in encoded domain, multiplier structure.
From 'something hmm.txt' discovery.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from mpmath import mp, mpf, mpmathify
mp.dps = 100  # 100 decimal digits of precision

p  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 55066263022277343669578718895168534326250603453777594175500187370337470445376
Gy = 32670510020758816978083085130507043184471273990662936571112854751101534055349

def modinv(a, m):
    if a < 0: a = a % m
    g, x, _ = extended_gcd(a, m)
    return x % m

def extended_gcd(a, b):
    if a == 0: return b, 0, 1
    g, x, y = extended_gcd(b % a, a)
    return g, y - (b // a) * x, x

def ec_add(x1, y1, x2, y2):
    if x1 is None: return x2, y2
    if x2 is None: return x1, y1
    if x1 == x2 and y1 == y2:
        lam = (3 * x1 * x1 * modinv(2 * y1, p)) % p
    elif x1 == x2:
        return None, None
    else:
        lam = ((y2 - y1) * modinv((x2 - x1) % p, p)) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return x3, y3

def ec_mul(k, x=Gx, y=Gy):
    rx, ry = None, None
    qx, qy = x, y
    while k > 0:
        if k & 1: rx, ry = ec_add(rx, ry, qx, qy)
        qx, qy = ec_add(qx, qy, qx, qy)
        k >>= 1
    return rx, ry

def encode_mp(Px, Py):
    """E(P) = (Px + Py/B) / p using mpmath at 100-digit precision"""
    s = str(abs(Py))
    B = 10 ** len(s)
    Px_mp = mpf(Px)
    Py_mp = mpf(Py)
    B_mp = mpf(B)
    p_mp = mpf(p)
    return (Px_mp + Py_mp / B_mp) / p_mp

# ============================================================
# POINTS
# ============================================================
Rx = 0xC86BEC9FAEA4892FD98D718BDFC770D0D11C3D6BFD4328F25FE9B06BFADB9650
Ry = 49714739208247555872780528359092797866261457510155690641636464864972500227644

# The "unit" point Q (= add1 - P from the file)
Qx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Qy = 32670510020758816978083085130507043184471273380659243275938904335757337482424

# The file's "multiply by 2" point P
Px_f = 9210836494447108270027136741376870869791784014198948301625976867708124077590
Py_f = 46351506704828816385393879789131775975171267756561783641521771795450741674800

print("=" * 80)
print("PART 1: E(G) vs E(Q) AT FULL 100-DIGIT PRECISION")
print("=" * 80)

EG = encode_mp(Gx, Gy)
EQ = encode_mp(Qx, Qy)
ER = encode_mp(Rx, Ry)
EP = encode_mp(Px_f, Py_f)

print(f"\nE(G) = {EG}")
print(f"\nE(Q) = {EQ}")
print(f"\nE(R) = {ER}")
print(f"\nE(P) = {EP}")

# The difference
diff = EG - EQ
print(f"\nE(G) - E(Q) = {diff}")
print(f"E(G) - E(Q) == 0? {diff == 0}")

# What is the difference numerically?
print(f"\n|E(G) - E(Q)| = {abs(diff)}")
print(f"This is approximately {(mp.log10(abs(diff)) if diff != 0 else 'zero')} powers of 10 from 1")

# File says E(R) = rp = 0.78289679430476346015545710430795985714967923686492941619055694132527630802774
rp_file = mpf("0.78289679430476346015545710430795985714967923686492941619055694132527630802774")
print(f"\nE(R) matches file rp? {abs(ER - rp_file) < mpf(10)**(-76)}")
print(f"  E(R)   = {ER}")
print(f"  rp     = {rp_file}")
print(f"  diff   = {ER - rp_file}")

# ============================================================
# PART 2: THE E(P)*x - 1 = E(Q) PATTERN AT FULL PRECISION
# ============================================================
print(f"\n{'='*80}")
print("PART 2: GROUP OPERATIONS IN ENCODED DOMAIN")
print("=" * 80)

# Compute 2P, P+Q, P-Q
Px2, Py2 = ec_add(Px_f, Py_f, Px_f, Py_f)
PxQ, PyQ = ec_add(Px_f, Py_f, Qx, Qy)
PxmQ, PymQ = ec_add(Px_f, Py_f, Qx, p - Qy)

EP2 = encode_mp(Px2, Py2)
EPQ = encode_mp(PxQ, PyQ)
EPmQ = encode_mp(PxmQ, PymQ)

print(f"\nE(P)     = {EP}")
print(f"E(2P)    = {EP2}")
print(f"E(P+Q)   = {EPQ}")
print(f"E(P-Q)   = {EPmQ}")

# Multipliers: x = (E(Q) + 1) / E(P)
x_double = (EP2 + 1) / EP
x_addQ = (EPQ + 1) / EP
x_subQ = (EPmQ + 1) / EP

print(f"\nMultiplier for doubling: x = {x_double}")
print(f"Multiplier for +Q:       x = {x_addQ}")
print(f"Multiplier for -Q:       x = {x_subQ}")

# Verify the pattern
print(f"\nVerify E(P)*x - 1 = E(Q):")
print(f"  E(P)*x_double - 1 = {EP * x_double - 1}")
print(f"  E(2P)             = {EP2}")
print(f"  Match: {abs(EP * x_double - 1 - EP2) < mpf(10)**(-95)}")

print(f"  E(P)*x_addQ - 1   = {EP * x_addQ - 1}")
print(f"  E(P+Q)            = {EPQ}")
print(f"  Match: {abs(EP * x_addQ - 1 - EPQ) < mpf(10)**(-95)}")

print(f"  E(P)*x_subQ - 1   = {EP * x_subQ - 1}")
print(f"  E(P-Q)            = {EPmQ}")
print(f"  Match: {abs(EP * x_subQ - 1 - EPmQ) < mpf(10)**(-95)}")

# ============================================================
# PART 3: MULTIPLIER STRUCTURE ANALYSIS
# ============================================================
print(f"\n{'='*80}")
print("PART 3: MULTIPLIER STRUCTURE")
print("=" * 80)

# Do the multipliers have a clean form?
# x_double = 18.160415624444111112...
# x_addQ = 14.986893053634258...
# x_subQ = 16.503490259771123...

# Check: x_double - x_addQ, x_double - x_subQ
print(f"\nx_double - x_addQ = {x_double - x_addQ}")
print(f"x_double - x_subQ = {x_double - x_subQ}")
print(f"x_addQ + x_subQ   = {x_addQ + x_subQ}")
print(f"x_addQ * x_subQ   = {x_addQ * x_subQ}")

# Check: is x_double = (x_addQ + x_subQ) / something?
print(f"(x_addQ + x_subQ) / 2 = {(x_addQ + x_subQ) / 2}")

# The y^2/p multipliers
yP_sq = (Py_f * Py_f) % p
y2P_sq = (Py2 * Py2) % p
yPQ_sq = (PyQ * PyQ) % p
yPmQ_sq = (PymQ * PymQ) % p

x_y2_double = mpf(y2P_sq + p) / mpf(yP_sq)
x_y2_addQ = mpf(yPQ_sq + p) / mpf(yP_sq)
x_y2_subQ = mpf(yPmQ_sq + p) / mpf(yP_sq)

print(f"\ny^2/p multiplier for doubling: {x_y2_double}")
print(f"y^2/p multiplier for +Q:       {x_y2_addQ}")
print(f"y^2/p multiplier for -Q:       {x_y2_subQ}")

# ============================================================
# PART 4: CHAIN TEST - does the encoding preserve group structure?
# ============================================================
print(f"\n{'='*80}")
print("PART 4: ENCODING GROUP CHAIN (from the file)")
print("=" * 80)

# The file shows a chain starting from P:
# P -> P+Q -> P+2Q -> P-Q -> etc.
# Let me verify the chain

# Starting from P, add Q repeatedly
points = [("P", Px_f, Py_f)]
cx, cy = Px_f, Py_f
for i in range(8):
    cx, cy = ec_add(cx, cy, Qx, Qy)
    ec = encode_mp(cx, cy)
    points.append((f"P+{i+1}Q", cx, cy))

# Also subtract Q from P
cx, cy = Px_f, Py_f
for i in range(1, 5):
    cx, cy = ec_add(cx, cy, Qx, p - Qy)
    ec = encode_mp(cx, cy)
    points.insert(0, (f"P-{i}Q", cx, cy))

# Print the chain
print(f"\n{'Name':<12} {'E(point)':<80} {'Multiplier x':<40}")
print("-" * 132)
for i, (name, px, py) in enumerate(points):
    ep = encode_mp(px, py)
    if i > 0:
        prev_name, prev_px, prev_py = points[i-1]
        ep_prev = encode_mp(prev_px, prev_py)
        x_mult = (ep + 1) / ep_prev
        print(f"{name:<12} {str(ep):<80} {str(x_mult):<40}")
    else:
        print(f"{name:<12} {str(ep):<80} {'---':<40}")

# ============================================================
# PART 5: y^2/p DOUBLING IDENTITY AT FULL PRECISION
# ============================================================
print(f"\n{'='*80}")
print("PART 5: y^2/p DOUBLING IDENTITY (FULL PRECISION)")
print("=" * 80)

# From the file: (y_P^2/p) * (3*a)/(2*b) = (y_{2P}^2/p)
# where a and b are "small" numbers

# For the file's point P:
yP_sq_mp = mpf(yP_sq)
y2P_sq_mp = mpf(y2P_sq)
p_mp = mpf(p)

print(f"\ny_P^2 mod p / p = {yP_sq_mp / p_mp}")
print(f"y_{{2P}}^2 mod p / p = {y2P_sq_mp / p_mp}")

# The ratio
ratio = (y2P_sq_mp + p_mp) / yP_sq_mp
print(f"(y_{{2P}}^2 + p) / y_P^2 = {ratio}")

# Small numbers from file
small_x = 111346819475903196082328522632160357855
small_y = 136520009634680542597373775009631809128

lhs = (yP_sq_mp / p_mp) * mpf(3 * small_x) / mpf(2 * small_y)
rhs = y2P_sq_mp / p_mp
print(f"\n(y_P^2/p) * (3*{small_x})/(2*{small_y}) = {lhs}")
print(f"y_{{2P}}^2/p = {rhs}")
print(f"Match: {abs(lhs - rhs) < mpf(10)**(-95)}")

# ============================================================
# PART 6: WHAT IS THE DIFFERENCE G - Q?
# ============================================================
print(f"\n{'='*80}")
print("PART 6: G - Q ANALYSIS")
print("=" * 80)

GmQx, GmQy = ec_add(Gx, Gy, Qx, p - Qy)
print(f"\nG - Q = ({GmQx}, {GmQy})")

# Check if G-Q = n*G for some small n
# Actually, n*G = O, so that's not useful.
# Check if G-Q = k*G for small k (meaning Q = (1-k)*G)
for k in range(1, 100):
    kx, ky = ec_mul(k)
    if kx == GmQx:
        print(f"G - Q = {k}*G  =>  Q = (1-{k})*G = ({1-k} mod N)*G")
        break
else:
    print("G - Q is NOT k*G for k=1..99")

# Check if G-Q = k*Q for some k (meaning G = (k+1)*Q)
for k in range(1, 100):
    kx, ky = ec_mul(k, Qx, Qy)
    if kx == GmQx:
        print(f"G - Q = {k}*Q  =>  G = ({k+1}*Q)")
        break
else:
    print("G - Q is NOT k*Q for k=1..99")

# ============================================================
# PART 7: ENCODING WITH R AS GENERATOR
# ============================================================
print(f"\n{'='*80}")
print("PART 7: CHAIN FROM R (from the file's Section 1)")
print("=" * 80)

# R -> 2R -> 3R -> ... in encoded domain
ER_val = encode_mp(Rx, Ry)
print(f"\nE(R) = {ER_val}")

# Double R
Rx2, Ry2 = ec_add(Rx, Ry, Rx, Ry)
ER2 = encode_mp(Rx2, Ry2)
x_d_R = (ER2 + 1) / ER_val
print(f"E(2R) = {ER2}")
print(f"x_double_R = {x_d_R}")

# Add Q to R
RxQ, RyQ = ec_add(Rx, Ry, Qx, Qy)
ERxQ = encode_mp(RxQ, RyQ)
x_aQ_R = (ERxQ + 1) / ER_val
print(f"E(R+Q) = {ERxQ}")
print(f"x_addQ_R = {x_aQ_R}")

# The file's section 1 shows E(R)*x - 1 = 0.696024... = E(2R)
# Let me verify at full precision
rp_file = mpf("0.78289679430476346015545710430795985714967923686492941619055694132527630802774")
target_file = mpf("0.69602445036432832816185257041676344029580382941145666353103251048242625419589")
x_file = (target_file + 1) / rp_file
print(f"\nFile section 1:")
print(f"  E(R) = {rp_file}")
print(f"  target = {target_file}")
print(f"  x = {x_file}")
print(f"  My E(2R) = {ER2}")
print(f"  Match target? {abs(ER2 - target_file) < mpf(10)**(-70)}")

# ============================================================
# PART 8: THE COMPLETE FRAMEWORK
# ============================================================
print(f"\n{'='*80}")
print("PART 8: COMPLETE ENCODING FRAMEWORK SUMMARY")
print("=" * 80)

print("""
ENCODING: E(P) = (Px + Py/B) / p
  where B = 10^(number of digits of Py)
  Output: real number in (0, 1) with ~77 digits of precision

GROUP OPERATIONS IN ENCODED DOMAIN:
  E(P) * x - 1 = E(Q)  where Q = op(P)
  
  Doubling:  x_d = (E(2P) + 1) / E(P)
  Add unit:  x_a = (E(P+Q) + 1) / E(P)  
  Sub unit:  x_s = (E(P-Q) + 1) / E(P)

y^2/p DOUBLING IDENTITY:
  (y_P^2 mod p / p) * (3*a)/(2*b) = (y_{2P}^2 mod p / p)
  
  where a/b encodes the doubling slope lambda = 3x^2/(2y)

KEY RELATIONSHIP:
  E(G) and E(Q) are ALMOST IDENTICAL (differ at ~digit 25)
  G - Q is a specific curve point (NOT small multiple of G or Q)
""")

# Final: what E(G) and E(Q) look like at full precision
print(f"\nE(G) at 100 digits:")
print(f"  {EG}")
print(f"\nE(Q) at 100 digits:")
print(f"  {EQ}")
print(f"\nFirst 25 digits match: {str(EG)[:25] == str(EQ)[:25]}")
print(f"Digit 25 onward differs: ...G={str(EG)[24:40]}... vs ...Q={str(EQ)[24:40]}...")
