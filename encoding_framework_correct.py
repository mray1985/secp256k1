#!/usr/bin/env python3
"""
CORRECTED encoding framework with actual secp256k1 G.
Q = G. All prior computations with wrong G were invalid.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from mpmath import mp, mpf
mp.dps = 100

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# CORRECT G from hex
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

def egcd(a, b):
    if a == 0: return b, 0, 1
    g, x, y = egcd(b % a, a)
    return g, y - (b // a) * x, x

def ec_add(x1, y1, x2, y2):
    if x1 is None: return x2, y2
    if x2 is None: return x1, y1
    if x1 == x2 and y1 == y2:
        lam = (3 * x1 * x1 * egcd(2 * y1, p)[1]) % p
    elif x1 == x2:
        return None, None
    else:
        lam = ((y2 - y1) * egcd((x2 - x1) % p, p)[1]) % p
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
    s = str(abs(Py))
    B = 10 ** len(s)
    return (mpf(Px) + mpf(Py) / mpf(B)) / mpf(p)

def r_P(Py):
    return (Py * Py) % p

print("=" * 80)
print("PART 1: VERIFICATION — Q = G")
print("=" * 80)

Qx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Qy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
print(f"Qx == Gx? {Qx == Gx}")
print(f"Qy == Gy? {Qy == Gy}")

# Verify r_G matches file
rG = r_P(Gy)
print(f"\nr_G = {rG}")
print(f"File = 32748224938747404814623910738487752935528512903530129802856995983256684603122")
print(f"Match: {rG == 32748224938747404814623910738487752935528512903530129802856995983256684603122}")

print(f"\n{'='*80}")
print("PART 2: DOUBLING RECURRENCE ON t_P = x_P^3 = r_P - 7")
print("=" * 80)

def t_P_from_r(r):
    return (r - 7) % p

def double_r(r):
    """r_{2P} from r_P using the closed formula"""
    t = t_P_from_r(r)
    num = (t * t + 140 * t - 392) % p
    num_sq = (num * num) % p
    den = (64 * pow(t + 7, 3, p)) % p
    return (num_sq * egcd(den, p)[1]) % p

def double_t(t):
    """t_{2P} from t_P"""
    num = (t * pow(t - 56, 3, p)) % p
    den = (64 * pow(t + 7, 3, p)) % p
    return (num * egcd(den, p)[1]) % p

# Iterate the doubling recurrence
r = rG
t = t_P_from_r(r)
print(f"\nIterating r_{{2^k * G}} from r_G:")
print(f"r_G = {r}")
print(f"t_G = {t}")

for k in range(1, 8):
    r_next = double_r(r)
    t_next = double_t(t)
    # Verify against direct EC computation
    kx, ky = ec_mul(2**k)
    r_actual = r_P(ky)
    t_actual = (kx * kx * kx) % p
    print(f"\nr_{{{2**k}G}} = {r_next}")
    print(f"  Direct: {r_actual}")
    print(f"  Match: {r_next == r_actual}")
    print(f"  t match: {t_next == t_actual}")
    r = r_next
    t = t_next

print(f"\n{'='*80}")
print("PART 3: E(P)*x - 1 = E(P+G) WITH CORRECT G")
print("=" * 80)

# R point from the file
Rx = 0xC86BEC9FAEA4892FD98D718BDFC770D0D11C3D6BFD4328F25FE9B06BFADB9650
Ry = 49714739208247555872780528359092797866261457510155690641636464864972500227644

ER = encode_mp(Rx, Ry)
EG = encode_mp(Gx, Gy)
RGx, RGy = ec_add(Rx, Ry, Gx, Gy)
ERG = encode_mp(RGx, RGy)

x_R = (ERG + 1) / ER
print(f"\nE(R) = {ER}")
print(f"E(G) = {EG}")
print(f"E(R+G) = {ERG}")
print(f"x_R = (E(R+G)+1)/E(R) = {x_R}")
print(f"Verify E(R)*x_R - 1 = E(R+G): {abs(ER * x_R - 1 - ERG) < mpf(10)**(-95)}")

# For the file's P
Px_f = 9210836494447108270027136741376870869791784014198948301625976867708124077590
Py_f = 46351506704828816385393879789131775975171267756561783641521771795450741674800

EP = encode_mp(Px_f, Py_f)
PGx, PGy = ec_add(Px_f, Py_f, Gx, Gy)
EPG = encode_mp(PGx, PGy)
x_P = (EPG + 1) / EP

print(f"\nE(P) = {EP}")
print(f"E(P+G) = {EPG}")
print(f"x_P = {x_P}")

# Check the file's add1 result
add1x = 22249732239474094348466092315309562856730738575753278567813732843809780498344
add1y = 115427358652607272490899347240407297202113746595418657560191322078971184540847
print(f"\nP+G computed: ({PGx}, {PGy})")
print(f"File add1:    ({add1x}, {add1y})")
print(f"Match: {PGx == add1x and PGy == add1y}")

print(f"\n{'='*80}")
print("PART 4: MULTIPLIER STRUCTURE WITH CORRECT G")
print("=" * 80)

# For G itself
GGx, GGy = ec_add(Gx, Gy, Gx, Gy)
EGG = encode_mp(GGx, GGy)
x_G = (EGG + 1) / EG
print(f"\nE(2G) = {EGG}")
print(f"x_G = (E(2G)+1)/E(G) = {x_G}")

# Chain: G, 2G, 3G, 4G in encoded domain
print(f"\n--- G chain ---")
points = [(1, Gx, Gy)]
cx, cy = Gx, Gy
for i in range(2, 11):
    cx, cy = ec_add(cx, cy, Gx, Gy)
    points.append((i, cx, cy))

ep_prev = EG
for n, px, py in points[1:]:
    ep = encode_mp(px, py)
    x = (ep + 1) / ep_prev
    print(f"E({n}G) = {str(ep)}")
    print(f"  x from E({n-1}G) = {str(x)}")
    ep_prev = ep

print(f"\n{'='*80}")
print("PART 5: M(P) MULTIPLIER FROM y^2/p SYSTEM")
print("=" * 80)

# The file's M(P) formula:
# r_{2P} = M(P) * r_P mod p
# M(P) = [(t_P^2 + 140*t_P - 392)^2 / (64*(t_P+7)^4)]_p

def M_from_r(r):
    t = t_P_from_r(r)
    num = (t * t + 140 * t - 392) % p
    num_sq = (num * num) % p
    den = (64 * pow(t + 7, 4, p)) % p  # power 4 for ratio r_{2P}/r_P
    return (num_sq * egcd(den, p)[1]) % p

rG = r_P(Gy)
MG = M_from_r(rG)
r2G = double_r(rG)
print(f"\nM_G = {MG}")
print(f"r_G = {rG}")
print(f"M_G * r_G mod p = {(MG * rG) % p}")
print(f"r_{{2G}}        = {r2G}")
print(f"Match: {(MG * rG) % p == r2G}")

# For the file's P
rP = r_P(Py_f)
MP = M_from_r(rP)
r2P = double_r(rP)
print(f"\nM_P = {MP}")
print(f"r_P = {rP}")
print(f"M_P * r_P mod p = {(MP * rP) % p}")
print(f"r_{{2P}}        = {r2P}")
print(f"Match: {(MP * rP) % p == r2P}")

print(f"\n{'='*80}")
print("PART 6: CAN WE RECOVER d FROM THE RECURRENCE?")
print("=" * 80)

# For a known d, compute d*G and check if the recurrence can be reversed
d = 71  # test scalar
dGx, dGy = ec_mul(d)
rdG = r_P(dGy)
tdG = t_P_from_r(rdG)

print(f"\nd = {d}")
print(f"r_{{dG}} = {rdG}")
print(f"t_{{dG}} = {tdG}")

# Given r_G, can we reach r_{dG} by repeated doubling + the G-addition formula?
# The recurrence gives r_{2P} from r_P. 
# For dG = d*G, we need the addition step r_{P+G} from r_P and r_G.
# 
# The question: is there a formula for r_{P+G} in terms of r_P and r_G only?

# Compute r_{P+G} for P = G (i.e. r_{2G}) and P = 2G (i.e. r_{3G})
r3G = double_r(double_r(rG))  # no wait, 3G = 2G + G, not 4G
# 3G properly
G3x, G3y = ec_mul(3)
r3G_actual = r_P(G3y)

# r_{2G} from doubling
r2G_val = double_r(rG)

# What is r_{2G+G} = r_{3G}?
# Need addition formula for r
# r_{P+G} from r_P, r_G, and some cross term

# Let me check: is r_{P+G} expressible as a function of r_P and r_G?
# For P = G: r_{2G} = double_r(rG) ✓
# For P = 2G: r_{3G} should equal some function of r_{2G} and r_G

# Try: r_{3G} = double_r(rG) ??? No, that's r_{4G}
# r_{3G} requires addition, not just doubling

# Let me just compute r_{P+G} for several P values and see if there's a pattern
print(f"\n--- Testing r_{{P+G}} from r_P ---")
test_points = [
    (1, Gx, Gy),
    (2, *ec_mul(2)),
    (3, *ec_mul(3)),
    (4, *ec_mul(4)),
    (5, *ec_mul(5)),
]

for n, px, py in test_points:
    rP_val = r_P(py)
    # Compute P+G
    pGx, pGy = ec_add(px, py, Gx, Gy)
    rPG = r_P(pGy)
    # Also compute 2P (doubling)
    r2P = double_r(rP_val)
    print(f"P = {n}G: r_P = {rP_val}")
    print(f"  r_{{P+G}} = {rPG}")
    print(f"  r_{{2P}}  = {r2P}")
    # Is r_{P+G} = double_r(r_P)?  (i.e. is 2P = P+G for all P?)
    print(f"  r_{{P+G}} == r_{{2P}}? {rPG == r2P}")

print(f"\n{'='*80}")
print("PART 7: CUBIC STRUCTURE — THREE x PER t")
print("=" * 80)

# beta = primitive cube root of unity mod p
# beta^3 = 1 mod p, 1 + beta + beta^2 = 0 mod p
beta = 64210534554274298161830248813031902839242514793520991344606881260072802101480
print(f"beta = {beta}")
print(f"beta^3 mod p = {pow(beta, 3, p)}")
print(f"(1 + beta + beta^2) mod p = {(1 + beta + beta*beta) % p}")

# For Gx, the three cube roots of t_G = Gx^3 mod p are:
# x1 = Gx, x2 = Gx*beta mod p, x3 = Gx*beta^2 mod p
tG = (Gx * Gx * Gx) % p
x1 = Gx
x2 = (Gx * beta) % p
x3 = (Gx * beta * beta) % p

print(f"\nt_G = Gx^3 mod p = {tG}")
print(f"x1 = Gx          = {x1}")
print(f"x2 = Gx*beta mod p = {x2}")
print(f"x3 = Gx*beta^2 mod p = {x3}")

# Verify all three cube to the same t
print(f"\nx1^3 mod p = {pow(x1, 3, p)}")
print(f"x2^3 mod p = {pow(x2, 3, p)}")
print(f"x3^3 mod p = {pow(x3, 3, p)}")
print(f"All equal t_G: {pow(x1,3,p) == pow(x2,3,p) == pow(x3,3,p) == tG}")

# The user says: x1 + x2 + x3 = 2p
s = x1 + x2 + x3
print(f"\nx1 + x2 + x3 = {s}")
print(f"2*p = {2*p}")
print(f"== 2p? {s == 2*p}")
print(f"== p?  {s == p}")
print(f"sum mod p = {s % p}")

# All three points (xi, Gy) are on the curve (same y)
for i, xi in enumerate([x1, x2, x3], 1):
    on_curve = (xi*xi*xi + 7) % p == (Gy*Gy) % p
    print(f"\n(x{i}, Gy) on curve: {on_curve}")
    ei = encode_mp(xi, Gy)
    print(f"E(x{i}, Gy) = {ei}")

print(f"\n{'='*80}")
print("PART 8: ENCODING OF ALL THREE CUBE ROOTS")
print("=" * 80)

e1 = encode_mp(x1, Gy)
e2 = encode_mp(x2, Gy)
e3 = encode_mp(x3, Gy)
print(f"\nE(x1, Gy) = {e1}")
print(f"E(x2, Gy) = {e2}")
print(f"E(x3, Gy) = {e3}")
print(f"\nAll have same r_G = y^2 mod p = {rG}")
print(f"All have same t_G = x^3 mod p = {tG}")
print(f"But different encodings because x differs")

# The 6 points identified by the encoding
print(f"\n--- The 6-tuple identified by U(P) = r_P ---")
for sign in [1, -1]:
    for mult in [1, beta, beta*beta % p]:
        xi = (Gx * mult) % p
        yi = (sign * Gy) % p
        ei = encode_mp(xi, yi)
        print(f"  ({xi}, {yi}) -> E = {str(ei)[:50]}...")

# KEY: the doubling recurrence on t
print(f"\n{'='*80}")
print("PART 9: WHAT t ENCODES — DIRECT RECOVERY")
print("=" * 80)

# Given t = x^3 mod p, we can recover x by taking cube root mod p
# Then we get three candidates for x, and combined with y^2 = t+7, we get 6 points
# The private key d is identified mod {±1, ±lambda, ±lambda^2}

# lambda = the GLV scalar
lam = 64210534554274298161830248813031902839242514793520991344606881260072802101480
print(f"lambda = {lam}")
print(f"lambda^2 + lambda + 1 mod N = {(lam*lam + lam + 1) % N}")

# For d, the 6 equivalent scalars
d_test = 12345678901234567890
equiv = set()
for s in [1, -1]:
    for m in [1, lam % N, (lam*lam) % N]:
        equiv.add((s * m * d_test) % N)
equiv = sorted(equiv)
print(f"\nFor d = {d_test}, the 6 equivalent scalars mod N are:")
for e in equiv:
    print(f"  {e}")
print(f"Count: {len(equiv)} (expected 6 unless collisions)")

