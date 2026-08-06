#!/usr/bin/env python3
"""
Analyze cl989.txt: continued fraction of 2*Gy/(3*Gx^2) = 1/lambda(G)
"""
from decimal import Decimal, getcontext
getcontext().prec = 200

# secp256k1 generator
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F

# Real-valued 2y/(3x^2) (not mod p)
val = Decimal(2 * Gy) / Decimal(3 * Gx * Gx)
print(f"2*Gy/(3*Gx^2) = {val}")
print(f"             = {float(val):.15e}")
print()

# Continued fraction
from math import floor

def continued_fraction(x, max_terms=100):
    terms = []
    for i in range(max_terms):
        a = int(floor(x))
        terms.append(a)
        frac = x - a
        if frac == 0:
            break
        x = Decimal(1) / frac
    return terms

# Compute CF of 2*Gy/(3*Gx^2)
x = Decimal(2 * Gy) / Decimal(3 * Gx * Gx)
terms = continued_fraction(x, 80)
print(f"Continued fraction: {terms}")
print()

# Compute convergents
def convergents(terms):
    h_prev2, h_prev1 = 0, 1
    k_prev2, k_prev1 = 1, 0
    convs = []
    for a in terms:
        h = a * h_prev1 + h_prev2
        k = a * k_prev1 + k_prev2
        convs.append((h, k, Decimal(h)/Decimal(k) if k != 0 else None))
        h_prev2, h_prev1 = h_prev1, h
        k_prev2, k_prev1 = k_prev1, k
    return convs

convs = convergents(terms)
print("First 30 convergents:")
print(f"{'n':<4} {'a_n':<10} {'num':<70} {'den':<70} {'val':<30}")
print("-"*184)
for i in range(min(30, len(convs))):
    h, k, v = convs[i]
    if k < 1000000:  # only print manageable ones
        print(f"{i:<4} {terms[i]:<10} {h:<70} {k:<70} {float(v):<30.15e}")
    else:
        print(f"{i:<4} {terms[i]:<10} (convergent too large to display)")

print()

# The first convergent is 1/1392215787867366754807929040557734082468141581209811809...
# This is basically 1 / (huge number) = the value itself.
# Let's check some puzzle keys against the denominators

known = [
    (90,  868012190417726402719548863),
    (100, 868221233689326498340379183142),
    (115, 31464123230573852164273674364426950),
    (120, 919343500840980333540511050618764323),
    (125, 37650549717742544505774009877315221420),
    (130, 1103873984953507439627945351144005829577),
]

print("Checking puzzle keys against CF convergents...")
for pnum, d in known:
    for i, (h, k, v) in enumerate(convs[:50]):
        if k == 0:
            continue
        # Check if d * h ≡ something mod k (modular relationship)
        # Or check if d is near some function of h/k
        # This is speculative
        pass

# Now let's compute the modular tangent slope at G:
lam = (3 * Gx * Gx) * pow(2 * Gy, -1, p) % p
print(f"Slope lambda at G (mod p) = {lam}")
print(f"lambda mod 9 = {lam % 9}")
print(f"lambda mod 7 = {lam % 7}")
print(f"lambda mod 11 = {lam % 11}")
print()

# The real-valued 1/lambda expanded as CF:
print("Real-valued inverse slope CF encodes rational approximations.")
print("Key observation: 2*Gy/(3*Gx^2) ~ 7.18279e-78")
print("  = 1 / 139221578786736675480792904055773408246814158120981180980253974860784918464552")
print()
print("This huge denominator is ~ 2^256 - something")
print(f"  2^256 = {2**256}")
print(f"  denom = {terms[1]}")
print(f"  diff  = {2**256 - terms[1]}")
print()

# Compare to p and N
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
P = p
d1 = terms[1]
print("Compare first CF term to curve constants:")
print(f"  diff from N = {N - d1}")
print(f"  diff from p = {P - d1}")
print(f"  diff from 2^256 = {2**256 - d1}")
print()

# Interesting relationship?
import hashlib
# The value 2y/3x^2 might be related to a hash or the actual continued 
# fraction convergents might correspond to something

# Let's see: the convergent denominators are denominators of 1/lambda
# If we think of this as a Fourier/Diophantine approximation problem...
print("Denominator of 1st convergent:")
print(f"  a_1 = {terms[1]}")
print(f"  bits = {terms[1].bit_length()}")
print(f"  2^255 = {2**255}")
print(f"  diff from 2^255 = {abs(2**255 - terms[1])}")
print(f"  diff from N = {abs(115792089237316195423570985008687907852837564279074904382605163141518161494337 - terms[1])}")
print(f"  diff from p = {abs(115792089237316195423570985008687907853269984665640564039457584007908834671663 - terms[1])}")
