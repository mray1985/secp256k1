#!/usr/bin/env python3
"""Fractional-domain scalar addition: is there a fraction op for EC scalar mult?"""
import time

p  = 115792089237316195423570985008687907853269984665640564039457584007908834671663
N  = 115792089237316195423570985008687907852837564279074904382605163141518161494337
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
delta = p - N

def ec_add(P, Q):
    if P is None: return Q
    if Q is None: return P
    x1,y1 = P; x2,y2 = Q
    if x1==x2 and y1!=y2: return None
    if x1==x2:
        lam = 3*x1*x1*pow(2*y1,-1,p) % p
    else:
        lam = (y2-y1)*pow(x2-x1,-1,p) % p
    x3 = (lam*lam-x1-x2) % p
    y3 = (lam*(x1-x3)-y1) % p
    return (x3,y3)

def ec_mul(d, P):
    R = None; Q = P; d = d % N
    while d:
        if d&1: R = ec_add(R, Q)
        Q = ec_add(Q, Q); d >>= 1
    return R

print("="*90)
print("FRACTIONAL-DOMAIN SCALAR ADDITION TEST")
print("="*90)
print()

# Precompute
print("Precomputing d*G for d=1..200 ...")
t0 = time.time()
pts = {}
G = (Gx, Gy)
for d in range(1, 201):
    pts[d] = ec_mul(d, G)
print(f"  Done in {time.time()-t0:.1f}s\n")

# Find wrap point
d_wrap = next(d for d in range(1, 10000) if d * Gx >= p)
print(f"d where d*Gx first exceeds p: d_wrap = {d_wrap}")
print(f"  For d < {d_wrap}: integer d*Gx == d*Gx mod p (no modular wrap of product)")
print()

# =====================================================================
# TEST 1: Does (d*G).x == d * Gx mod p?  (simple scalar * coordinate)
# =====================================================================
print("TEST 1: (d*G).x vs d*Gx mod p")
print("-"*90)
print(f"  {'d':>5}  {'match':>6}  {'(d*G).x':>20}  {'d*Gx mod p':>20}  {'diff_bits':>10}")
for d in [1,2,3,4,5,6,7,8,9,10,15,20,50,100,150,200]:
    px = pts[d][0]
    pred = (d * Gx) % p
    m = px == pred
    diff = 0 if m else (px - pred) % p
    print(f"  {d:>5}  {str(m):>6}  ...{str(px)[-18:]:>20}  ...{str(pred)[-18:]:>20}  {diff.bit_length() if diff else 0:>10}")
print()

# =====================================================================
# TEST 2: Does (d*G).x^3 == d^3 * Gx^3 mod p?  (cubing preserves linearity?)
# =====================================================================
print("TEST 2: (d*G).x^3 vs d^3 * Gx^3 mod p  [cubic linearity]")
print("-"*90)
for d in [1,2,3,5,10,20,50,100]:
    px = pts[d][0]
    a = pow(px, 3, p)
    b = (pow(d,3,p) * pow(Gx,3,p)) % p
    print(f"  d={d:>3}: match={a==b}  err={0 if a==b else ((a-b)%p).bit_length()} bits")
print()

# =====================================================================
# TEST 3: Does Gx^d mod p == (d*G).x?  (multiplicative exp = EC scalar mult?)
# =====================================================================
print("TEST 3: Gx^d mod p vs (d*G).x  [Fp* exp = EC scalar mult?]")
print("-"*90)
for d in [1,2,3,5,10,20,50,100]:
    px = pts[d][0]
    pred = pow(Gx, d, p)
    print(f"  d={d:>3}: match={px==pred}  err={0 if px==pred else ((px-pred)%p).bit_length()} bits")
print()

# =====================================================================
# TEST 4: Fractional approach — what IS the operation?
# Key insight: EC addition is x3 = lam^2 - x1 - x2 where lam = (y2-y1)/(x2-x1) mod p
# Can we express this as an operation on fractions a=x1/p, b=x2/p?
# =====================================================================
print("TEST 4: EC addition structure analysis")
print("-"*90)
print("  EC add: x3 = ((y2-y1)/(x2-x1))^2 - x1 - x2  (mod p)")
print("  This requires modular inverse of (x2-x1), which is NOT 1/((x2-x1)/p)")
print("  because (x2-x1)^{-1} mod p != p/(x2-x1) as a real number.")
print()
# Show the gap
for d1,d2 in [(1,2),(1,3),(2,5),(10,20)]:
    x1,y1 = pts[d1]; x2,y2 = pts[d2]
    dx = (x2-x1) % p
    mod_inv = pow(dx, -1, p)
    real_div = p / dx if dx else 0
    print(f"  d1={d1}, d2={d2}: (x2-x1)^-1 mod p = ...{str(mod_inv)[-15:]}")
    print(f"               p/(x2-x1) as float = {real_div:.6f}")
    print(f"               ratio = {mod_inv / real_div:.6f}  (should be ~1 if equivalent)")
print()

# =====================================================================
# TEST 5: THE KEY TEST — concatenate as integer, divide by d, see if result
# is on the curve (i.e., reconstructs the point)
# =====================================================================
print("TEST 5: concat(P) / d  [does the integer concat divide cleanly?]")
print("-"*90)
concat_G = Gx * p + Gy
for d in [1,2,3,5,10,20,50,100]:
    px,py = pts[d]
    concat_P = px * p + py
    q, r = divmod(concat_P, d)
    match = (r == 0) and (q == concat_G)
    print(f"  d={d:>3}: div_exact={r==0}  q==concat_G={q==concat_G}  remainder={r.bit_length() if r else 0} bits")
print()

# =====================================================================
# TEST 6: THE REAL INSIGHT — look at the x-coordinate as d varies
# =====================================================================
print("TEST 6: x-coordinate trajectory for d=1..30")
print("-"*90)
print(f"  {'d':>4}  {'(d*G).x mod 2^32':>18}  {'d*Gx mod 2^32':>18}  {'diff mod 2^32':>15}  {'wrap':>5}")
wrap_count = 0
for d in range(1, 31):
    px = pts[d][0]
    pred = (d * Gx) % p
    diff = (px - pred) % (2**32)
    wrap = "YES" if d * Gx >= p else "no"
    if d * Gx >= p:
        wrap_count += 1
    print(f"  {d:>4}  {px % (2**32):>18}  {pred % (2**32):>18}  {diff:>15}  {wrap:>5}")
print(f"  Wraps in d=1..30: {wrap_count}")
print()

# =====================================================================
# TEST 7: The ACTUAL fractional operation — work mod 2^256 (not mod p)
# =====================================================================
print("TEST 7: Working mod 2^256 instead of mod p")
print("-"*90)
print("  If we replace mod p with mod 2^256, does d*Gx mod 2^256 == (d*G).x mod 2^256?")
for d in [1,2,3,5,10,20,50,100,200]:
    px = pts[d][0]
    a = px % (2**256)
    b = (d * Gx) % (2**256)
    print(f"  d={d:>3}: match={a==b}  err_bits={(a-b)%(2**256).bit_length() if a!=b else 0}")
print()

# =====================================================================
# TEST 8: What if we work with the Y coordinate instead?
# =====================================================================
print("TEST 8: y-coordinate — (d*G).y vs d*Gy mod p")
print("-"*90)
for d in [1,2,3,5,10,20,50,100]:
    py = pts[d][1]
    pred = (d * Gy) % p
    print(f"  d={d:>3}: match={py==pred}  err={0 if py==pred else ((py-pred)%p).bit_length()} bits")
print()

# =====================================================================
# TEST 9: The REAL answer — scalar mult in the EXPONENT of the Weil/Tate pairing
# =====================================================================
print("TEST 9: Pairing-style — does a^d mod p relate to (d*G).x?")
print("-"*90)
print("  If e(P,Q) is a pairing, then e(dP,Q) = e(P,Q)^d")
print("  But secp256k1 pairings are expensive and defined on extension fields.")
print()
print("  Quick check: pick random a. Does a^(d*G).x mod p == (a^Gx)^d mod p?")
import random
random.seed(42)
a = random.randrange(2, p-1)
for d in [1,2,3,5,7,10]:
    px = pts[d][0]
    lhs = pow(a, px, p)
    rhs = pow(pow(a, Gx, p), d, p)
    print(f"  d={d}: match={lhs==rhs}")
print()

# =====================================================================
# TEST 10: Bridge Lambda as fractional operation
# Lambda = Px * rx^-1 mod p
# If we define f(P) = Px * Gx^-1 mod p, does f(d*G) have a pattern?
# =====================================================================
print("TEST 10: f(d) = (d*G).x * Gx^{-1} mod p  [normalize by base]")
print("-"*90)
Gx_inv = pow(Gx, -1, p)
vals = []
for d in range(1, 51):
    px = pts[d][0]
    f = (px * Gx_inv) % p
    vals.append(f)
    if d <= 15 or d in (20,30,50):
        print(f"  d={d:>3}: f(d) = {f}")
print()
print("  Is f(d) == d?  NO (that would be the discrete log)")
print("  Is f(d) == d * f(1) mod p?  f(1) = 1, so f(d) == d?  NO")
print("  Is there a recurrence f(d+1) = g(f(d), f(1))?  Let's check...")
print()
# Check if f(d+1) can be expressed as a polynomial in f(d)
print("  f(d+1) vs f(d):")
for d in range(1, 10):
    print(f"    f({d})={vals[d-1]}, f({d+1})={vals[d]}, ratio mod p={vals[d]*pow(vals[d-1],-1,p)%p}")
print()

# =====================================================================
# TEST 11: Direct scalar addition on frac — what does it MEAN?
# If f(P) = Px/p, then f(P) + f(Q) = (Px+Qx)/p
# But (P+Q).x != Px+Qx. The question is: what IS (Px+Qx)/p?
# =====================================================================
print("TEST 11: Px + Qx mod p vs (P+Q).x  [coordinate addition = EC add?]")
print("-"*90)
for d1,d2 in [(1,2),(1,3),(2,3),(5,10),(10,20)]:
    x1 = pts[d1][0]; x2 = pts[d2][0]
    add_coord = (x1 + x2) % p
    d3 = d1 + d2
    ec_x = pts[d3][0]
    print(f"  d1={d1}+d2={d2}: coord_add={add_coord == ec_x}  EC_add={ec_x}  coord={add_coord}")
print()

# =====================================================================
# SUMMARY
# =====================================================================
print("="*90)
print("CONCLUSION")
print("="*90)
print("""
  EC scalar multiplication d*G uses the CHORD-AND-TANGENT group law over Fp.
  The x-coordinate is a NON-LINEAR projection from the curve to Fp.

  No simple operation on fractions (Px/p) can replace EC point addition:
    - d * (Gx/p)      != (d*G).x/p         [linear scaling fails]
    - (Gx/p)^d         != (d*G).x/p         [exponentiation fails]
    - (Gx^d) mod p     != (d*G).x           [Fp* exp != EC mult]
    - d*Gx mod p       != (d*G).x           [coordinate scaling fails]
    - (Px+Qx) mod p    != (P+Q).x           [coordinate add != EC add]

  The bottleneck is the MODULAR INVERSE in the EC addition formula:
    lambda = (y2-y1) * (x2-x1)^{-1} mod p
  This modular inverse has no real-number equivalent.

  WHAT DOES WORK: if we could compute (d*G).x from d and Gx WITHOUT
  the chord-and-tangent formula, we'd break ECDLP.

  The CS cubic structure (Gx1, Gx2, Gx3 and their products) provides
  algebraic RELATIONS between coordinates, but these are identities
  (like IP = CP1^3 * IG), not alternative computation methods.

  FRACTIONAL SCALAR ADDITION IS EQUIVALENT TO SOLVING ECDLP.
""")
