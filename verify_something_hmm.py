#!/usr/bin/env python3
"""
Investigate Q vs G - the modified generator from the file.
Q = the point that gets added/subtracted in the file's operations.
Q is ALMOST G but offset by ~10^13 in x-coordinate.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

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

def encode(Px, Py):
    s = str(abs(Py))
    B = 10 ** len(s)
    return (Px + Py / B) / p

# ============================================================
# The "unit" point Q (from add1 - P computation)
# ============================================================
Qx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Qy = 32670510020758816978083085130507043184471273380659243275938904335757337482424

print("=" * 80)
print("Q vs G ANALYSIS")
print("=" * 80)

print(f"\nGx = {Gx}")
print(f"Qx = {Qx}")
print(f"Gx - Qx = {Gx - Qx}")
print(f"Gx - Qx bits = {(Gx - Qx).bit_length()}")

print(f"\nGy = {Gy}")
print(f"Qy = {Qy}")
print(f"Gy - Qy = {Gy - Qy}")
print(f"Gy - Qy bits = {(Gy - Qy).bit_length()}")

# Is Q on the curve?
lhs = (Qy * Qy) % p
rhs = (Qx * Qx * Qx + 7) % p
print(f"\nQ on curve: {lhs == rhs}")

# ============================================================
# G - Q (the difference point)
# ============================================================
print(f"\n{'='*80}")
print("G - Q (difference point)")
print("=" * 80)

GmQx, GmQy = ec_add(Gx, Gy, Qx, p - Qy)
print(f"G - Q x = {GmQx}")
print(f"G - Q y = {GmQy}")

# Is this a "small" point? i.e., is it k*G for small k?
for k in range(1, 50):
    kx, ky = ec_mul(k)
    if kx == GmQx:
        print(f"G - Q = {k}*G!")
        break
else:
    # Check if it's the identity (point at infinity)
    if GmQx is None:
        print("G - Q = O (identity)")
    else:
        print(f"G - Q is NOT k*G for k=1..49")

# ============================================================
# Q - G (the other direction)
# ============================================================
QmGx, QmGy = ec_add(Qx, Qy, Gx, p - Gy)
print(f"\nQ - G x = {QmGx}")
print(f"Q - G y = {QmGy}")

# ============================================================
# The R point from the file
# ============================================================
print(f"\n{'='*80}")
print("R POINT vs Q")
print("=" * 80)

Rx = 0xC86BEC9FAEA4892FD98D718BDFC770D0D11C3D6BFD4328F25FE9B06BFADB9650
Ry = 49714739208247555872780528359092797866261457510155690641636464864972500227644

# Is R related to Q?
# R - Q = ?
RmQx, RmQy = ec_add(Rx, Ry, Qx, p - Qy)
print(f"R - Q x = {RmQx}")
print(f"R - Q y = {RmQy}")

# Is R = k*Q for some k?
# Check E(R) vs E(Q)
ER = encode(Rx, Ry)
EQ = encode(Qx, Qy)
print(f"\nE(R) = {ER}")
print(f"E(Q) = {EQ}")
print(f"E(R) / E(Q) = {ER / EQ}")

# ============================================================
# KEY: What if Q IS G but the file uses slightly wrong coordinates?
# Or: what if Q is the "Complexity Simplified" modified generator?
# ============================================================
print(f"\n{'='*80}")
print("NUMERICAL RELATIONSHIP G <-> Q")
print("=" * 80)

# The difference in x:
dx = Gx - Qx
print(f"Gx - Qx = {dx}")

# Is this related to any known constant?
# Check: dx mod N, dx mod small primes
print(f"dx mod N = {dx % N}")
print(f"dx mod 7 = {dx % 7}")
print(f"dx mod 3 = {dx % 3}")

# The difference in y:
dy = Gy - Qy
print(f"\nGy - Qy = {dy}")
print(f"dy mod N = {dy % N}")

# ============================================================
# MULTIPLICATIVE STRUCTURE: is Q = G * (1 + epsilon)?
# ============================================================
print(f"\n{'='*80}")
print("IS Q = G * k for some scalar k?")
print("=" * 80)

# We can't easily compute discrete log, but let's check some things
# If Q = k*G, then n*Q = n*k*G = (nk mod N)*G = O when nk = 0 mod N
# So k = N / gcd(k, N)... no, that's not right.
# Actually, ord(Q) divides N. If Q = k*G, then ord(Q) = N / gcd(k, N).

# Check: does N*Q = O?
NxQ, NyQ = ec_mul(N, Qx, Qy)
print(f"N*Q = O? {NxQ is None}")

# Check: what is 2*Q?
Q2x, Q2y = ec_add(Qx, Qy, Qx, Qy)
print(f"\n2*Q x = {Q2x}")
print(f"2*Q y = {Q2y}")

# Is 2*Q = 2*G?
G2x, G2y = ec_add(Gx, Gy, Gx, Gy)
print(f"2*G x = {G2x}")
print(f"2*G y = {G2y}")
print(f"2*Q == 2*G? {Q2x == G2x}")

# ============================================================
# The REAL test: is the file using Q as generator, and the
# "multiply by 2" point is 2*Q (not 2*R)?
# ============================================================
print(f"\n{'='*80}")
print("IS THE FILE'S POINT P = k*Q?")
print("=" * 80)

Px_file = 9210836494447108270027136741376870869791784014198948301625976867708124077590
Py_file = 46351506704828816385393879789131775975171267756561783641521771795450741674800

# Check small multiples of Q
for k in range(1, 30):
    kx, ky = ec_mul(k, Qx, Qy)
    if kx == Px_file:
        print(f"P = {k}*Q!")
        break
    if kx == Rx:
        print(f"R = {k}*Q!")
else:
    print("P is not k*Q for k=1..29")

# ============================================================
# ENCODING COMPARISON: E(G) vs E(Q)
# ============================================================
print(f"\n{'='*80}")
print("ENCODING COMPARISON")
print("=" * 80)

EG = encode(Gx, Gy)
EQ_val = encode(Qx, Qy)
ER_val = encode(Rx, Ry)

print(f"E(G) = {EG}")
print(f"E(Q) = {EQ_val}")
print(f"E(R) = {ER_val}")

# The file says E(R) = rp = 0.782896...
# What is E(G)?
print(f"\nE(G) matches file rp? {abs(EG - 0.78289679430476346015545710430795985714967923686492941619055694132527630802774) < 1e-30}")

# ============================================================
# THE E(P)*x-1=E(Q) MULTIPLIER STRUCTURE
# ============================================================
print(f"\n{'='*80}")
print("MULTIPLIER vs DOUBLING SLOPE")
print("=" * 80)

# For the file's point P, doubling slope:
lam_P = (3 * Px_file * Px_file * modinv(2 * Py_file, p)) % p
print(f"lambda_P = {lam_P}")
print(f"lambda_P / p = {lam_P / p}")

# The multiplier for E(P)*x-1 = E(2P):
EP = encode(Px_file, Py_file)
Px2, Py2 = ec_add(Px_file, Py_file, Px_file, Py_file)
EP2 = encode(Px2, Py2)
x_double = (EP2 + 1) / EP
print(f"\nx_double = {x_double}")

# The multiplier for E(P)*x-1 = E(P+Q) (add 1):
PxQ, PyQ = ec_add(Px_file, Py_file, Qx, Qy)
EPQ = encode(PxQ, PyQ)
x_addQ = (EPQ + 1) / EP
print(f"x_addQ = {x_addQ}")

# The multiplier for E(P)*x-1 = E(P-Q) (subtract 1):
PxmQ, PymQ = ec_add(Px_file, Py_file, Qx, p - Qy)
EPmQ = encode(PxmQ, PymQ)
x_subQ = (EPmQ + 1) / EP
print(f"x_subQ = {x_subQ}")

# Check: is x_double = 2*x_addQ - 1? Or some other relationship?
print(f"\n2*x_addQ - 1 = {2*x_addQ - 1}")
print(f"x_double = {x_double}")

# ============================================================
# THE y^2/p DOUBLING SLOPE CONNECTION
# ============================================================
print(f"\n{'='*80}")
print("y^2/p DOUBLING: FULL ANALYSIS")
print("=" * 80)

# For P:
yP_sq = (Py_file * Py_file) % p
y2P_sq = (Py2 * Py2) % p

print(f"y_P^2 mod p = {yP_sq}")
print(f"y_P^2 mod p / p = {yP_sq / p}")

print(f"\ny_{{2P}}^2 mod p = {y2P_sq}")
print(f"y_{{2P}}^2 mod p / p = {y2P_sq / p}")

# The identity: (y_P^2/p) * x - 1 = (y_{2P}^2/p)
# x = (y_{2P}^2/p + 1) / (y_P^2/p)
x_y2 = (y2P_sq/p + 1) / (yP_sq/p)
print(f"\nx from y^2/p pattern = {x_y2}")

# Now compare to x from E(P)*x-1=E(2P)
print(f"x from E(P) pattern = {x_double}")

# These should be DIFFERENT
print(f"Are they the same? {abs(x_y2 - x_double) < 1e-30}")

# But wait - let me check for R
ER_val = encode(Rx, Ry)
Rx2, Ry2 = ec_add(Rx, Ry, Rx, Ry)
ER2 = encode(Rx2, Ry2)
x_double_R = (ER2 + 1) / ER_val

yR_sq = (Ry * Ry) % p
y2R_sq = (Ry2 * Ry2) % p
x_y2_R = (y2R_sq/p + 1) / (yR_sq/p)

print(f"\nFor R:")
print(f"x_double_R = {x_double_R}")
print(f"x_y2_R = {x_y2_R}")
print(f"Are they the same? {abs(x_y2_R - x_double_R) < 1e-30}")
