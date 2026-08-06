#!/usr/bin/env python3
"""Test: does frac(3x^2 / 2y) == lambda_mod_p / p for EC doubling?"""
import time

p  = 115792089237316195423570985008687907853269984665640564039457584007908834671663
N  = 115792089237316195423570985008687907852837564279074904382605163141518161494337
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424

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
print("FRACTIONAL EC DOUBLING TEST: frac(3x^2/2y) vs lambda mod p")
print("="*90)
print()

G = (Gx, Gy)
print("Precomputing points...")
pts = {}
for d in range(1, 201):
    pts[d] = ec_mul(d, G)
print(f"  Done. {len(pts)} points.\n")

# ─── TEST A: Single doubling — frac(3x^2/2y) vs lambda/p ───
print("TEST A: Single EC doubling — does frac(3x^2 / 2y) = lambda / p ?")
print("-"*90)

for d in [1, 2, 3, 5, 7, 10, 50, 100]:
    x, y = pts[d]
    
    # Actual EC doubling
    two_P = ec_add(pts[d], pts[d])
    if two_P is None:
        print(f"  d={d}: 2*P = O (point at infinity)")
        continue
    x_new_actual = two_P[0]
    
    # Modular lambda (standard EC)
    num_mod = (3 * x * x) % p
    den_mod = (2 * y) % p
    lam_mod = num_mod * pow(den_mod, -1, p) % p
    
    # Verify: lam_mod should give correct x_new
    x_from_lam = (lam_mod * lam_mod - 2 * x) % p
    assert x_from_lam == x_new_actual, f"lambda check failed for d={d}"
    
    # Fractional lambda (real number)
    num_real = 3 * x * x      # ~512 bit integer
    den_real = 2 * y           # ~257 bit integer
    
    # frac(3x^2 / 2y) = (3x^2 mod 2y) / (2y)
    frac_num = num_real % den_real   # numerator of fractional part
    frac_den = den_real               # denominator of fractional part
    
    # Does frac(3x^2/2y) == lam_mod / p ?
    # Cross-multiply: frac_num * p == lam_mod * frac_den ?
    lhs = (frac_num * p) % (frac_den * p)
    rhs = (lam_mod * frac_den) % (frac_den * p)
    match = lhs == rhs
    
    # Simpler: does frac_num / frac_den == lam_mod / p ?
    # i.e., frac_num * p == lam_mod * frac_den (exact, not mod)?
    exact_match = frac_num * p == lam_mod * frac_den
    
    # Distance
    if not exact_match:
        diff = abs(frac_num * p - lam_mod * frac_den)
        err_bits = diff.bit_length()
    else:
        err_bits = 0
    
    print(f"  d={d:>3}: exact_match={exact_match}  err_bits={err_bits}")
    print(f"         lam_mod/p = {lam_mod/p:.15f}")
    print(f"         frac(3x^2/2y) = {frac_num/frac_den:.15f}")
    print(f"         diff = {abs(lam_mod/p - frac_num/frac_den):.2e}")
    print()

# ─── TEST B: EC addition — frac((y2-y1)/(x2-x1)) vs lambda/p ───
print("\nTEST B: EC addition — does frac((y2-y1)/(x2-x1)) = lambda/p ?")
print("-"*90)

for d1, d2 in [(1,2), (1,3), (2,3), (5,10), (10,20), (50,100)]:
    x1, y1 = pts[d1]
    x2, y2 = pts[d2]
    
    # Modular lambda
    dy_mod = (y2 - y1) % p
    dx_mod = (x2 - x1) % p
    lam_mod = dy_mod * pow(dx_mod, -1, p) % p
    
    # Fractional lambda
    dy_real = y2 - y1   # can be negative!
    dx_real = x2 - x1   # can be negative!
    
    if dx_real == 0:
        print(f"  d1={d1}, d2={d2}: dx=0 (same x), skip")
        continue
    
    # frac(dy/dx) — handle signs
    sign = 1
    a, b = abs(dy_real), abs(dx_real)
    if (dy_real < 0) != (dx_real < 0):
        sign = -1
    
    frac_num = sign * (a % b)
    frac_den = b
    
    exact = (frac_num * p == lam_mod * frac_den)
    if not exact:
        diff = abs(frac_num * p - lam_mod * frac_den)
        err = diff.bit_length()
    else:
        err = 0
    
    print(f"  d1={d1}, d2={d2}: exact={exact}  err_bits={err}")
    print(f"         lam_mod/p = {lam_mod/p:.15f}")
    print(f"         frac(dy/dx) = {float(frac_num)/float(frac_den):.15f}")
    print()

# ─── TEST C: THE KEY — work in base 2^256, not base p ───
print("\nTEST C: Work in base 2^256 — does frac(3x^2/2y) in base 2^256 match?")
print("-"*90)

B = 2**256
for d in [1, 2, 3, 5, 10, 50, 100]:
    x, y = pts[d]
    
    # EC doubling
    two_P = ec_add(pts[d], pts[d])
    if two_P is None: continue
    x_new = two_P[0]
    
    # Modular lambda
    lam_mod = (3*x*x % p) * pow(2*y % p, -1, p) % p
    
    # Fractional in base B=2^256
    num = 3 * x * x
    den = 2 * y
    frac_B = (num % den) / den   # frac in [0,1)
    lam_B = lam_mod / p           # lambda normalized by p
    
    # Also try: lambda * B / p (lambda in base B)
    lam_in_B = lam_mod * B // p
    
    # What is 3x^2 / 2y in base B?
    # 3x^2 has ~512 bits, 2y has ~257 bits
    # quotient has ~255 bits, remainder has ~257 bits
    q, r = divmod(num, den)
    
    print(f"  d={d:>3}:")
    print(f"    3x^2 / 2y = {q} + {r}/{den}")
    print(f"    quotient bits = {q.bit_length()}, remainder bits = {r.bit_length()}")
    print(f"    frac = {r/den:.15f}")
    print(f"    lam_mod/p = {lam_mod/p:.15f}")
    print(f"    match (frac == lam/p)? {abs(r/den - lam_mod/p) < 1e-30}")
    print()

# ─── TEST D: What if we use the INTEGER QUOTIENT? ───
print("\nTEST D: Integer quotient q = 3x^2 // 2y — does q mod p = lambda?")
print("-"*90)

for d in [1, 2, 3, 5, 10, 50, 100]:
    x, y = pts[d]
    num = 3 * x * x
    den = 2 * y
    q = num // den
    r = num % den
    
    lam_mod = (3*x*x % p) * pow(2*y % p, -1, p) % p
    
    q_mod_p = q % p
    match = q_mod_p == lam_mod
    
    print(f"  d={d:>3}: q mod p == lam_mod? {match}  (q mod p bits={q_mod_p.bit_length()}, lam bits={lam_mod.bit_length()})")
print()

# ─── TEST E: What does q = floor(3x^2 / 2y) LOOK like? ───
print("\nTEST E: Analyzing the quotient q = floor(3x^2 / 2y)")
print("-"*90)

for d in range(1, 21):
    x, y = pts[d]
    num = 3 * x * x
    den = 2 * y
    q, r = divmod(num, den)
    
    two_P = ec_add(pts[d], pts[d])
    x_actual = two_P[0] if two_P else 0
    
    # Is q related to x_actual?
    q_mod = q % p
    
    print(f"  d={d:>2}: q bits={q.bit_length():>4}  q mod p bits={q_mod.bit_length():>4}  x_new bits={x_actual.bit_length():>4}  q_mod==x_new? {q_mod == x_actual}")
print()

# ─── TEST F: THE INSIGHT — q = floor(3x^2/2y) IS x_new + k*p for some k? ───
print("\nTEST F: Does q = x_new + k*p for some integer k?")
print("-"*90)

for d in range(1, 21):
    x, y = pts[d]
    num = 3 * x * x
    den = 2 * y
    q = num // den
    
    two_P = ec_add(pts[d], pts[d])
    x_actual = two_P[0]
    
    diff = q - x_actual
    if diff >= 0 and diff % p == 0:
        k = diff // p
        print(f"  d={d:>2}: q = x_new + {k}*p  MATCH!")
    else:
        print(f"  d={d:>2}: q - x_new = {diff}  (not a multiple of p)")
print()

# ─── TEST G: Extended — q = floor(3x^2/2y) vs lambda ───
print("\nTEST G: Does q = lambda + k*p?")
print("-"*90)

for d in range(1, 21):
    x, y = pts[d]
    num = 3 * x * x
    den = 2 * y
    q = num // den
    
    lam = (3*x*x % p) * pow(2*y % p, -1, p) % p
    
    diff = q - lam
    if diff >= 0 and diff % p == 0:
        k = diff // p
        print(f"  d={d:>2}: q = lam + {k}*p  MATCH!  k bits={k.bit_length()}")
    else:
        print(f"  d={d:>2}: q - lam = {diff.bit_length() if diff else 0} bits  (not a multiple of p)")
print()

# ─── TEST H: FULL DOUBLING CHAIN using fractional arithmetic ───
print("\nTEST H: Can we double 10 times using ONLY frac(3x^2/2y)?")
print("-"*90)
print("  Algorithm: start with (x0, y0) = G")
print("  At each step: compute frac(3x^2/2y), use as new x")
print("  Then recover y from curve equation y^2 = x^3 + 7")
print()

x_cur, y_cur = Gx, Gy
x_actual, y_actual = Gx, Gy

print(f"  {'step':>4}  {'frac_x matches':>15}  {'x_frac bits':>12}  {'x_actual bits':>13}")

for step in range(1, 11):
    # Actual doubling
    actual = ec_add((x_actual, y_actual), (x_actual, y_actual))
    if actual:
        x_actual, y_actual = actual
    
    # Fractional doubling
    num = 3 * x_cur * x_cur
    den = 2 * y_cur
    q, r = divmod(num, den)
    
    # New x = q mod p (the integer part mod p)
    x_frac_new = q % p
    
    # Recover y from curve equation
    y_sq = (pow(x_frac_new, 3, p) + 7) % p
    y_frac_new = pow(y_sq, (p+1)//4, p)
    
    # Check if this point is on the curve
    on_curve = (y_frac_new * y_frac_new) % p == y_sq
    
    match = x_frac_new == x_actual
    
    print(f"  {step:>4}  {str(match):>15}  {x_frac_new.bit_length():>12}  {x_actual.bit_length():>13}")
    
    x_cur, y_cur = x_frac_new, y_frac_new

print()

# ─── TEST I: What if the answer is simpler? ───
# Maybe the user means: d is stored as a fraction, and 
# "scalar addition" is just d1 + d2 as fractions (real addition)
print("\nTEST I: d as fraction — is the answer just real-number d1+d2?")
print("-"*90)
print("  If d is represented as d/2^256 (a fraction in [0,1)),")
print("  then (d1+d2)/2^256 = d1/2^256 + d2/2^256 — trivial addition.")
print("  The question is whether this fraction maps to (d*G).x/p somehow.")
print()

# For each d, compute d/2^256 and (d*G).x/p and see if there's a relationship
for d in [1,2,3,5,10,20,50,100]:
    px = pts[d][0]
    d_frac = d / (2**256)
    px_frac = px / p
    ratio = px_frac / d_frac if d_frac > 0 else 0
    print(f"  d={d:>3}: d/2^256 = {d_frac:.6e}  (d*G).x/p = {px_frac:.6e}  ratio = {ratio:.6f}")
print()

# ─── TEST J: The ACTUAL insight — what is 3x^2/(2y) in bits? ───
print("\nTEST J: 3x^2/(2y) — full analysis for G")
print("-"*90)
x, y = Gx, Gy
num = 3 * x * x
den = 2 * y
q, r = divmod(num, den)
lam = (3*x*x % p) * pow(2*y % p, -1, p) % p

print(f"  3*Gx^2 = {num}")
print(f"  2*Gy   = {den}")
print(f"  q = floor(3x^2/2y) = {q}")
print(f"  r = 3x^2 mod 2y     = {r}")
print(f"  q bits = {q.bit_length()}")
print(f"  lam (mod p) = {lam}")
print(f"  lam bits = {lam.bit_length()}")
print(f"  q == lam? {q == lam}")
print(f"  q mod p == lam? {q % p == lam}")
print(f"  q - lam = {q - lam}")
print(f"  (q - lam) / p = {(q - lam) / p}")
print(f"  Is (q - lam) a multiple of p? {(q - lam) % p == 0}")
print()

# What about the remainder?
print(f"  Remainder analysis:")
print(f"  r = {r}")
print(f"  r * p = {r * p}")
print(f"  lam * den = {lam * den}")
print(f"  r*p == lam*den? {r * p == lam * den}")
print(f"  3x^2 = q*den + r = {q*den + r} == {num}? {q*den + r == num}")
print(f"  3x^2 mod p = {num % p}")
print(f"  lam * den mod p = {(lam * den) % p}")
print(f"  These should be equal: {num % p == (lam * den) % p}")
print()

# THE KEY RELATIONSHIP
print("  The modular identity:")
print(f"  3x^2 mod p = lam * 2y mod p")
print(f"  {num % p} = {(lam * den) % p}")
print(f"  => 3x^2 = lam * 2y + k*p for some integer k")
k_val = (num - lam * den) // p
print(f"  k = {k_val}")
print(f"  k bits = {k_val.bit_length()}")
print(f"  Verify: lam * 2y + k*p == 3x^2? {lam * den + k_val * p == num}")
print()
print(f"  So: 3x^2 / 2y = lam + k*p/(2y)")
print(f"  The FRACTIONAL PART is: k*p/(2y) = {k_val * p / den:.15f}")
print(f"  And lam/p = {lam/p:.15f}")
print(f"  Sum = {lam/p + k_val*p/den:.15f} (should be 3x^2/(2y) = {num/den:.15f})")
