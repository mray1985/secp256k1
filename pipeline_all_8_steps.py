"""
STEP 1-8: Complete secp256k1 ECDLP Bridge Analysis Pipeline
Puzzle 135 - r, s, z, A, x2 structural investigation
"""
import sys, time, math, random
from math import gcd

sys.set_int_max_str_digits(100000)

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

r_val = 90653255469745952335985143920649543885181555095025199315947044135806663628368
s_val = 15509729875763924304053419655647994379903175655107184284998698212653288468986
z_val = 66278737796829840734606014530466656889790152192829793669891337810330530090951

A = 80184233617433755134183875136831551618578922487806929476230322368028862899169
x2 = A - 7

def pollard_rho(n, max_iters=200000):
    if n % 2 == 0: return 2
    if n % 3 == 0: return 3
    x = 2; y = 2; d = 1; f = lambda z: (z*z + 1) % n
    for _ in range(max_iters):
        x = f(x); y = f(f(y)); d = gcd(abs(x - y), n)
        if d != 1 and d != n: return d
    return None

def trial_divide(n, limit=1000000):
    fac = []
    for p_ in range(2, limit):
        if p_ * p_ > n: break
        while n % p_ == 0:
            fac.append(p_); n //= p_
    if n > 1: fac.append(n)
    return fac

def full_factor(n):
    small = trial_divide(n, 1000000)
    # The last element might be composite
    result = []
    for f in small:
        if f == 1: continue
        # Check if f is really prime (trial divide up to sqrt)
        if f < 1e12:
            result.append(f)
        else:
            # Pollard Rho
            remaining = f
            sub = []
            while remaining > 1:
                g = pollard_rho(remaining)
                if g is None or g == remaining:
                    sub.append(remaining); break
                sub.append(g); remaining //= g
            result.extend(sub)
    return sorted(result)

print("=" * 72)
print("STEP 1: FACTOR r AND s (FULL)")
print("=" * 72)

print("\n--- Factoring r ---")
t0 = time.time()
rf = full_factor(r_val)
print(f"r = {rf}")
print(f"  verify: {eval('*'.join(str(f) for f in rf)) == r_val}")
print(f"  time: {time.time()-t0:.2f}s")

print("\n--- Factoring s ---")
t0 = time.time()
sf = full_factor(s_val)
print(f"s = {sf}")
ps = 1
for f in sf: ps *= f
print(f"  verify: {ps == s_val}")
print(f"  time: {time.time()-t0:.2f}s")

# ============================================================
# STEP 2: CUBE ROOT GROUP MOD s
# ============================================================
print("\n" + "=" * 72)
print("STEP 2: CUBE ROOT GROUP MOD s")
print("=" * 72)

# For each prime factor, count cube roots of unity
print("Factor analysis (cube roots):")
total_cu = 1
for f in sf:
    if f == 2:
        print(f"  factor 2: 1 cube root (x=1 mod 2)")
    elif f == 3:
        print(f"  factor 3: 3 cube roots? (special case)")
        # x^3 = 1 mod 3 -> x = 1 mod 3 (only 1)
        print(f"    Actual: 1 cube root (x=1 mod 3)")
    else:
        if (f-1) % 3 == 0:
            print(f"  factor {f}: 3 cube roots (p=1 mod 3)")
            total_cu *= 3
        else:
            print(f"  factor {f}: 1 cube root (p=2 mod 3)")

print(f"\nTotal cube roots of unity mod s (excluding 2^e): {total_cu}")

# Also check C1 = x2^3 mod s
C1_s = pow(x2, 3, s_val)
print(f"\nC1 = x2^3 mod s = {C1_s}")

# Check C1 per factor
print("\nC1 analysis per factor:")
for f in sf:
    C1_mod_f = C1_s % f
    print(f"  mod {f}: C1 = {C1_mod_f}")
    # Number of cube roots of C1 mod f
    if f == 2:
        print(f"    1 cube root (x=0 mod 2)")
    elif C1_mod_f == 0:
        print(f"    C1=0 -> x=0 is only root")
    else:
        if (f-1) % 3 == 0:
            # Check if C1^((f-1)/3) = 1 mod f
            check = pow(C1_mod_f, (f-1)//3, f)
            print(f"    C1^((f-1)/3) mod f = {check} = 1? {check==1}")
            if check == 1:
                print(f"    3 cube roots of C1 mod {f}")
            else:
                print(f"    0 cube roots of C1 mod {f}")
        else:
            print(f"    1 cube root mod {f} (since 3 does not divide f-1)")

# ============================================================
# STEP 3: CROSS-MODULUS VERIFY x2 = A-7
# ============================================================
print("\n" + "=" * 72)
print("STEP 3: CROSS-MODULUS VERIFY x2")
print("=" * 72)

x2_mod_p = x2 % p
y2_at_x2 = (pow(x2_mod_p, 3, p) + 7) % p
leg = pow(y2_at_x2, (p-1)//2, p)
print(f"x2 mod p = {x2_mod_p}")
print(f"Legendre = {leg % p} (1=QR, {p-1}=nonQR)")
if leg % p == 1:
    y = pow(y2_at_x2, (p+1)//4, p)
    print(f"x2 IS on curve -> y = {y}")
else:
    print(f"x2 NOT on curve")

# Compare to known values
X135 = 0x145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16
delta = p - N
x_kG = (r_val - delta) % p
print(f"\nx2 == X135? {x2_mod_p == X135}")
print(f"x2 == x_kG? {x2_mod_p == x_kG}")

# ============================================================
# STEP 4: N-SIDE AND P-SIDE VIETA INVARIANTS
# ============================================================
print("\n" + "=" * 72)
print("STEP 4: VIETA INVARIANTS")
print("=" * 72)

n1 = 40220395037450137658562871366385094182673796545182808438190875548898232062868
n2 = x2
n3 = 111179549819748498054395223514159169904422409525160070850789128366109228026644
C1N = pow(x2, 3, N)

print(f"C1N = {C1N}")
print(f"n1^3 = C1N? {pow(n1,3,N)==C1N}")
print(f"n2^3 = C1N? {pow(n2,3,N)==C1N}")
print(f"n3^3 = C1N? {pow(n3,3,N)==C1N}")
print(f"sum mod N = {(n1+n2+n3)%N} == 0? {(n1+n2+n3)%N==0}")
print(f"product mod N = {(n1*n2*n3)%N} == C1N? {(n1*n2*n3)%N==C1N}")

p1 = 9210836494447108270027136741376870869791784014198948301625976867708124077590
p2 = 51866120889717641461810659005716431188799022756838843706514074509901265629059
p3 = (p - p1 - p2) % p
C1_p = pow(x2, 3, p)
print(f"\nP-side:")
print(f"p1^3 = C1_p? {pow(p1,3,p)==C1_p}")
print(f"p2^3 = C1_p? {pow(p2,3,p)==C1_p}")
print(f"p3^3 = C1_p? {pow(p3,3,p)==C1_p}")
print(f"sum mod p = {(p1+p2+p3)%p} == 0? {(p1+p2+p3)%p==0}")

# ============================================================
# STEP 5: CONNECT x2 TO ECDSA
# ============================================================
print("\n" + "=" * 72)
print("STEP 5: x2 <-> ECDSA EQUATION")
print("=" * 72)

sinv_N = pow(s_val, -1, N)
k0 = (z_val * sinv_N) % N
r_sinv_N = (r_val * sinv_N) % N
print(f"k0 = z*s^-1 mod N = {k0}")
print(f"r*s^-1 mod N = {r_sinv_N}")
print(f"k(d) = k0 + d * r_sinv_N mod N")
print(f"x2 mod N = {x2 % N}")
print(f"k0 == x2? {k0 % N == x2 % N}")

# Check x2 against kG x-coordinate
print(f"\nx2 mod p = x_kG? {x2_mod_p == x_kG}")
print(f"x_kG = {x_kG}")

# Check: maybe x2 = x-coordinate of P135?
print(f"x2 == X135? {x2_mod_p == X135}")

# ============================================================
# STEP 6: d CONSTRAINTS FROM s-SIDE ROOTS
# ============================================================
print("\n" + "=" * 72)
print("STEP 6: d CONSTRAINTS")
print("=" * 72)

file_roots = [
    573607990413771774330660150338470777282684101820002707407326044178689925190,
    1037622267039375860770424440147576644036988876824633854748801820544033215852,
    2635584238614133613916776858591579719063044212271008051236831304762420554232,
    3099598515239737700356541148400685585817348987275639198578307081127763844894,
    4640324220577404408449972586882647982238828469966881796778592517750577015938,
    6702300468777766248036089295135756924019188580417887140608097778334307644980,
    7773744950252354499456455900312557616057608432512217286346144123929830284478,
    8237759226877958585896220190121663482811913207516848433687619900295173575140,
    11840461180415987133575768336856734821013752800659096375717410597501717375226,
]

# All should satisfy root^3 = C1 mod s
print("s-side root verification:")
for i, root in enumerate(file_roots):
    ok = pow(root, 3, s_val) == C1_s
    print(f"  root[{i}] OK: {ok}")

# d from omega criterion
print(f"\nOmega = +1 for Puzzle 135")
print(f"Phase filter: q = floor((r*d - z)/N), q mod 9 in {2,5,8}")

# ============================================================
# STEP 7: PHASE FILTER SIEVE
# ============================================================
print("\n" + "=" * 72)
print("STEP 7: PHASE FILTER")
print("=" * 72)

d_lo = 2**134
d_hi = 2**135 - 1

def q_mod9(d):
    return ((r_val * d - z_val) // N) % 9

# Scan a sample
sample = 10000
hits = 0
for j in range(sample):
    if q_mod9(d_lo + j) in {2, 5, 8}:
        hits += 1
print(f"Phase filter pass rate: {hits}/{sample} = {hits/sample*100:.1f}%")

# Check if q_mod9 has a pattern based on d mod something
print("\nq mod 9 pattern for first 30 d:")
for j in range(30):
    print(f"  d_lo+{j}: q mod 9 = {q_mod9(d_lo + j)}")
print("  ...")

# ============================================================
# STEP 8: KANGAROO PROTOTYPE
# ============================================================
print("\n" + "=" * 72)
print("STEP 8: TARGETED KANGAROO")
print("=" * 72)

def point_add(P, Q):
    x1, y1 = P; x2, y2 = Q
    if x1 is None: return Q
    if x2 is None: return P
    if x1 == x2 and (y1 == y2 or y1 == 0):
        if y1 == 0: return (None, None)
        return point_double(P)
    if x1 == x2:
        return (None, None)
    s = ((y2 - y1) * pow(x2 - x1, -1, p)) % p
    x3 = (s*s - x1 - x2) % p
    y3 = (s*(x1 - x3) - y1) % p
    return (x3, y3)

def point_double(P):
    x1, y1 = P
    if y1 == 0: return (None, None)
    s = (3 * x1 * x1 * pow(2 * y1, -1, p)) % p
    x3 = (s*s - 2*x1) % p
    y3 = (s*(x1 - x3) - y1) % p
    return (x3, y3)

def point_mul(k, P):
    if k == 0 or k % p == 0: return (None, None)
    if k < 0: return point_mul(-k, (P[0], (-P[1]) % p))
    R = (None, None); Q = P
    while k:
        if k & 1: R = point_add(R, Q)
        Q = point_double(Q); k >>= 1
    return R

G = (Gx, Gy)
X135 = 0x145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16
y_target = pow((pow(X135, 3, p) + 7) % p, (p+1)//4, p)
if y_target % 2 != 0: y_target = p - y_target
P_target = (X135, y_target)
print(f"Target point: ({X135}, {y_target})")
print(f"Search range: [{d_lo}, {d_hi})")
print(f"Range size: 2^{134}")
print(f"Kangaroo expected: O(2^67) ops -- infeasible in Python")
print(f"Phase filter: reduces to ~O(2^66.5)")

print("\n" + "=" * 72)
print("SUMMARY")
print("=" * 72)
print(f"""
r = {' * '.join(str(f) for f in rf)}
s = {' * '.join(str(f) for f in sf)}
Key: x2 = A-7 {'matches' if x2_mod_p == x_kG else 'does NOT match'} x_kG
     x2 {'IS' if leg % p == 1 else 'is NOT'} on curve secp256k1
     
The bridge: x2^3 connects s-domain and N-domain through cubic root structure.
Next practical step: identify which point x2 corresponds to on the curve,
which would directly reveal the bridge origin.
""")
