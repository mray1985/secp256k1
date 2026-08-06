#!/usr/bin/env python3
"""Part 4-7: Chain test and remaining analysis at 100-digit precision."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from mpmath import mp, mpf
mp.dps = 100

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

def encode_mp(Px, Py):
    s = str(abs(Py))
    B = 10 ** len(s)
    return (mpf(Px) + mpf(Py) / mpf(B)) / mpf(p)

Rx = 0xC86BEC9FAEA4892FD98D718BDFC770D0D11C3D6BFD4328F25FE9B06BFADB9650
Ry = 49714739208247555872780528359092797866261457510155690641636464864972500227644
Qx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Qy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
Px_f = 9210836494447108270027136741376870869791784014198948301625976867708124077590
Py_f = 46351506704828816385393879789131775975171267756561783641521771795450741674800

# PART 4: Chain from P
print("=" * 80)
print("PART 4: ENCODING GROUP CHAIN")
print("=" * 80)

cx, cy = Px_f, Py_f
ep_prev = encode_mp(cx, cy)
print(f"\nP         = {str(ep_prev)}")

for i in range(1, 9):
    cx, cy = ec_add(cx, cy, Qx, Qy)
    ep = encode_mp(cx, cy)
    x = (ep + 1) / ep_prev
    print(f"P+{i}Q      = {str(ep)}")
    print(f"  x       = {str(x)}")
    ep_prev = ep

# Subtract Q chain
print("\n--- Subtract Q ---")
cx, cy = Px_f, Py_f
ep_prev = encode_mp(cx, cy)
for i in range(1, 5):
    cx, cy = ec_add(cx, cy, Qx, p - Qy)
    ep = encode_mp(cx, cy)
    x = (ep + 1) / ep_prev
    print(f"P-{i}Q      = {str(ep)}")
    print(f"  x       = {str(x)}")
    ep_prev = ep

# PART 6: G - Q analysis
print(f"\n{'='*80}")
print("PART 6: G - Q ANALYSIS")
print("=" * 80)

GmQx, GmQy = ec_add(Gx, Gy, Qx, p - Qy)
print(f"\nG - Q x = {GmQx}")
print(f"G - Q y = {GmQy}")

# Check if G-Q = k*G for k up to 10000
print("\nChecking G-Q = k*G for k=1..10000...")
kx, ky = Gx, Gy
for k in range(1, 10001):
    if kx == GmQx:
        print(f"  FOUND: G - Q = {k}*G  =>  Q = (1-{k})*G = ({(1-k) % N})*G")
        break
    kx, ky = ec_add(kx, ky, Gx, Gy)
else:
    print("  NOT FOUND for k=1..10000")

# PART 7: R chain from file Section 1
print(f"\n{'='*80}")
print("PART 7: R CHAIN (file Section 1)")
print("=" * 80)

ER = encode_mp(Rx, Ry)
print(f"\nE(R)  = {str(ER)}")

# 2R
Rx2, Ry2 = ec_add(Rx, Ry, Rx, Ry)
ER2 = encode_mp(Rx2, Ry2)
x_d = (ER2 + 1) / ER
print(f"E(2R) = {str(ER2)}")
print(f"x_double_R = {str(x_d)}")

# R+Q
RxQ, RyQ = ec_add(Rx, Ry, Qx, Qy)
ERxQ = encode_mp(RxQ, RyQ)
x_a = (ERxQ + 1) / ER
print(f"E(R+Q) = {str(ERxQ)}")
print(f"x_addQ_R = {str(x_a)}")

# R-Q
RxmQ, RymQ = ec_add(Rx, Ry, Qx, p - Qy)
ERxmQ = encode_mp(RxmQ, RymQ)
x_s = (ERxmQ + 1) / ER
print(f"E(R-Q) = {str(ERxmQ)}")
print(f"x_subQ_R = {str(x_s)}")

# 2R+Q
R2xQ, R2yQ = ec_add(Rx2, Ry2, Qx, Qy)
ER2xQ = encode_mp(R2xQ, R2yQ)
print(f"\nE(2R+Q) = {str(ER2xQ)}")

# R+2Q (R + Q + Q)
Rx2Q, Ry2Q = ec_add(RxQ, RyQ, Qx, Qy)
ERx2Q = encode_mp(Rx2Q, Ry2Q)
print(f"E(R+2Q) = {str(ERx2Q)}")

# PART 8: Key insight - multipliers for R chain
print(f"\n{'='*80}")
print("PART 8: MULTIPLIER CHAIN FROM R")
print("=" * 80)

# R -> 2R -> 3R -> 4R -> 5R
points_R = [("R", Rx, Ry)]
cx, cy = Rx, Ry
for i in range(1, 6):
    cx, cy = ec_add(cx, cy, Rx, Ry)
    points_R.append((f"{i+1}R", cx, cy))

ep_prev = encode_mp(Rx, Ry)
for name, px, py in points_R[1:]:
    ep = encode_mp(px, py)
    x = (ep + 1) / ep_prev
    print(f"E({name}) = {str(ep)}")
    print(f"  x from prev = {str(x)}")
    ep_prev = ep

# PART 9: Does E(k*R) have a closed form?
print(f"\n{'='*80}")
print("PART 9: E(k*R) VALUES AND RATIOS")
print("=" * 80)

for k in range(1, 11):
    # compute k*R
    kx, ky = None, None
    cx, cy = Rx, Ry
    kk = k
    while kk > 0:
        if kk & 1: kx, ky = ec_add(kx, ky, cx, cy)
        cx, cy = ec_add(cx, cy, cx, cy)
        kk >>= 1
    ek = encode_mp(kx, ky)
    print(f"E({k}R) = {str(ek)}")
