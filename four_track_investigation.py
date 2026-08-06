"""
FOUR-TRACK INVESTIGATION:
1. Trace what A (IP) encodes
2. Exhaustive x2 = f(r,s,z) algebraic search
3. GLV + Phase Filter narrowed d range
4. Map 10 cube-roots to d candidates
"""
import sys
from math import gcd

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

r = 90653255469745952335985143920649543885181555095025199315947044135806663628368
s = 15509729875763924304053419655647994379903175655107184284998698212653288468986
z = 66278737796829840734606014530466656889790152192829793669891337810330530090951
A = 80184233617433755134183875136831551618578922487806929476230322368028862899169
x2 = A - 7
delta = p - N

omega_N = pow(2, (N-1)//3, N)  # primitive cube root mod N
omega_p = pow(2, (p-1)//3, p)  # primitive cube root mod p

# Ensure they're actually primitive cube roots
if omega_N == 1:
    for g in range(3, 50):
        w = pow(g, (N-1)//3, N)
        if w != 1 and pow(w, 3, N) == 1:
            omega_N = w; break
if omega_p == 1:
    for g in range(3, 50):
        w = pow(g, (p-1)//3, p)
        if w != 1 and pow(w, 3, p) == 1:
            omega_p = w; break

omega_N2 = pow(omega_N, 2, N)
omega_p2 = pow(omega_p, 2, p)

print("=" * 72)
print("TRACK 1: TRACE WHAT A (IP) ENCODES")
print("=" * 72)

# Check: what is A's relationship to r, s, z?
# First, cube class analysis
def cube_class(val, mod, omega):
    """Return 'CUBE', 'OMEGA', 'OMEGA2', or 'OTHER' based on (val^((mod-1)/3) mod mod)."""
    c = pow(val, (mod-1)//3, mod)
    if c == 1: return "CUBE"
    if c == omega: return "OMEGA"
    if c == pow(omega, 2, mod): return "OMEGA2"
    return f"OTHER({c})"

print("Cube residue classes:")
for name, val in [("r", r), ("s", s), ("z", z), ("x2", x2), ("A", A),
                   ("delta", delta), ("s*z", (s*z) % N), ("r*s", (r*s) % N),
                   ("r*z", (r*z) % N), ("r*s*z", (r*s*z) % N)]:
    cn = cube_class(val, N, omega_N)
    cp = cube_class(val % p, p, omega_p)
    print(f"  {name:10s}  N:{cn:10s}  p:{cp}")

# Q = s*z and x2 share cube class omega_N mod N
Q = (s * z) % N
print(f"\nQ = s*z mod N = {Q}")
print(f"Q/x2 mod N = {(Q * pow(x2, -1, N)) % N}")
ratio_mod_N = (Q * pow(x2, -1, N)) % N
print(f"(Q/x2)^((N-1)/3) mod N = {pow(ratio_mod_N, (N-1)//3, N)} (should be 1)")
print(f"Q/x2 IS a perfect cube mod N: {pow(ratio_mod_N, (N-1)//3, N) == 1}")

# What is c such that Q = x2 * c^3 mod N?
# Since Q/x2 is a cube: c = (Q/x2)^((2*(N-1)/3 + 1)/3) ... but we need the right exponent
# When N = 1 mod 3, we need a Cipolla-style cube root
# Let's just compute the cube class ratio analysis differently

print("\n" + "=" * 72)
print("TRACK 2: x2 = f(r,s,z) ALGEBRAIC SEARCH")
print("=" * 72)

# Exhaustive search: does x2 = a*r + b*s + c*z + d*delta + e mod N for small coefficients?
print("Linear combinations (a*r + b*s + c*z + d*delta + e mod N):")
found = False
for a in range(-5, 6):
    for b in range(-5, 6):
        for c_ in range(-5, 6):
            for d in range(-5, 6):
                for e in range(-5, 6):
                    val = (a*r + b*s + c_*z + d*delta + e) % N
                    if val == x2:
                        print(f"  FOUND: x2 = {a}*r + {b}*s + {c_}*z + {d}*delta + {e} mod N")
                        found = True
if not found: print("  No small linear combination found mod N")

# Multiplicative: x2 = r^a * s^b * z^c * delta^d mod N
print("\nMultiplicative combinations (r^a * s^b * z^c * delta^d mod N):")
found = False
for a in range(-3, 4):
    for b in range(-3, 4):
        for c_ in range(-3, 4):
            for d in range(-3, 4):
                if a == 0 and b == 0 and c_ == 0 and d == 0: continue
                val = (pow(r, a, N) * pow(s, b, N) * pow(z, c_, N) * pow(delta, d, N)) % N
                if val == x2:
                    print(f"  FOUND: x2 = r^{a} * s^{b} * z^{c_} * delta^{d} mod N")
                    found = True
if not found: print("  No small multiplicative combo mod N")

# Check: x2 = r*s*z * delta^k mod N for some k?
for k in range(-10, 11):
    val = (r * s * z * pow(delta, k, N)) % N
    if val == x2:
        print(f"  x2 = r*s*z * delta^{k} mod N ***")
    val2 = (pow(r, k, N) * s * z) % N
    if val2 == x2:
        print(f"  x2 = r^{k} * s * z mod N ***")
    val3 = (r * pow(s, k, N) * z) % N
    if val3 == x2:
        print(f"  x2 = r * s^{k} * z mod N ***")
    val4 = (r * s * pow(z, k, N)) % N
    if val4 == x2:
        print(f"  x2 = r * s * z^{k} mod N ***")

# The KEY insight: Q = s*z and x2 share cube class
# So c exists such that Q = x2 * c^3 mod N
# What is c? For each candidate c, c^3 = Q/x2 mod N
# We can compute 3 cube roots of Q/x2 mod N
# These cube roots are: c, c*omega_N, c*omega_N^2

# Let's compute the cube root using the exponent
# Since N mod 9 = 7 (from earlier), the cube root formula when N = 2 mod 3 is (2N-1)/3
# But N mod 3 = 1, so we need a different approach

# Since (N-1)/3 is divisible by 3, we can compute:
# Let s3 = (Q/x2)^((N-1)/9) if (N-1)/9 is integer and Q/x2 is a cube
# Then s3^3 = (Q/x2)^((N-1)/3) = 1, so s3 is a cube root of unity
# This doesn't give us the cube root directly

# Better approach: Find the cube root via Tonelli-Shanks adaptation for cubes
# Or simply: since we know Q/x2 is a cube, and the ratio of two cubes is a cube:
# (s*z)/x2 is a cube => s*z = x2 * cube
# So cube = (s*z)/x2 mod N

cube_val = (Q * pow(x2, -1, N)) % N
print(f"\nCube value: c^3 = Q/x2 = {cube_val}")

# Check if cube_val is related to any known value
# If c = k (the ECDSA nonce), then k^3 = Q/x2, and we can compute k
# But extracting cube roots when N = 1 mod 3 requires the Adleman-Manders-Miller algorithm

# For now, let's check the multiplicative relations more systematically
# x2 could equal r*s*z * something for various "something" values
print("\nExtended multiplicative search:")
# Check if x2 / (r^a * s^b * z^c) is a cube mod N for small a,b,c
for a in range(-2, 3):
    for b in range(-2, 3):
        for c_ in range(-2, 3):
            denom = (pow(r, a, N) * pow(s, b, N) * pow(z, c_, N)) % N
            ratio = (x2 * pow(denom, -1, N)) % N
            cc = pow(ratio, (N-1)//3, N)
            if cc == 1:  # ratio is a cube
                print(f"  x2 / (r^{a} * s^{b} * z^{c_}) is a CUBE mod N")

# Direct check: does x2 equal r*s*z * c^3 for small c?
for c_candidate in range(-100, 101):
    cubed = pow(c_candidate, 3, N)
    val = (r * s * z * cubed) % N
    if val == x2:
        print(f"\n  *** x2 = r*s*z * ({c_candidate})^3 mod N ***")

# Check x2 mod p relationships
print("\n" + "=" * 72)
print("TRACK 3: GLV + PHASE FILTER NARROWED d RANGE")
print("=" * 72)

# Phase Filter
# q = floor((r*d - z) / N), q mod 9 in {2,5,8} for Omega = +1
d_lo = 2**134
d_hi = 2**135 - 1

# For Omega = +1: (r*d - z) mod N mod 9 in {1,4,7}
# Since r mod 9 = 0, Phase Filter via q mod 9 is the only discriminant
# q mod 9 in {2,5,8}

# GLV constraint: if we know that d (the private key) has a specific GLV property
# The GLV endomorphism gives: phi(P) = lam * P where lam^3 = 1 mod N
# So d*G's GLV conjugates are: d*G, lam*d*G, lam^2*d*G
# These correspond to private keys: d, lam*d mod N, lam^2*d mod N

# Check: what are the GLV conjugates of possible d values?
lam = omega_N  # GLV lambda = primitive cube root of unity mod N
print(f"GLV lambda = {lam}")
print(f"lambda^3 mod N = {pow(lam, 3, N)}")
print(f"d_lo * lam mod N (bits) = {(d_lo * lam) % N}")
print(f"d_hi * lam mod N (bits) = {(d_hi * lam) % N}")
print(f"d_lo * lam^2 mod N (bits) = {(d_lo * pow(lam, 2, N)) % N}")

# If d in [2^134, 2^135), then GLV conjugates are in different ranges
# lam*d and lam^2*d could be outside the puzzle range
# This further constrains possible d values

# Check: does x2 relate to d? If x2 = some function of d, then...
# x2^3 mod N = C1N has roots n1 = x2*lam^2, n2 = x2, n3 = x2*lam
# These are GLV conjugates of x2

# If d (the private key) has a known GLV structure, and x2 shares that structure,
# then x2 and d could be related by the GLV endomorphism

# Check if d in [2^134, 2^135) maps to x2 through GLV
# d * lam^? mod N should be within range
for j in range(3):
    conj = d_lo * pow(lam, j, N) % N
    print(f"  d_lo * lam^{j} mod N = {conj} (in [2^134,2^135)? {d_lo <= conj <= d_hi})")
    conj = d_hi * pow(lam, j, N) % N
    print(f"  d_hi * lam^{j} mod N = {conj} (in [2^134,2^135)? {d_lo <= conj <= d_hi})")

# GLV + Phase: combine q mod 9 filter with GLV constraint
# For each d candidate, check:
# 1. q = floor((r*d - z)/N), q mod 9 in {2,5,8}
# 2. d in [2^134, 2^135)
# 3. Optionally: x2 relates to d^3 mod N

print("\n" + "=" * 72)
print("TRACK 4: MAP 10 CUBE-ROOTS TO d CANDIDATES")
print("=" * 72)

# The 9 s-side roots (cube roots of C1 = x2^3 mod s)
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

C1_s = pow(x2, 3, s)

print("9 s-side roots all satisfy root^3 = x2^3 mod s:")
for i, root in enumerate(file_roots):
    ok = pow(root, 3, s) == C1_s
    print(f"  root[{i}]: {'OK' if ok else 'FAIL'}")

# Map each root to potential d via the ECDSA equation
# If root = k (the nonce) or root = d (the private key):
# ECDSA: s = k^-1 * (z + r*d) mod N
# So: d = r^-1 * (s*k - z) mod N
# If root = k, then d = r^-1 * (s*root - z) mod N
# Check if d is in [2^134, 2^135)

rinv_N = pow(r, -1, N)

print("\nMapping s-side roots to d candidates:")
for i, root in enumerate(file_roots):
    # If root = k (the nonce)
    d_from_k = (rinv_N * ((s * root) % N - z)) % N
    in_range = d_lo <= d_from_k <= d_hi
    print(f"  root[{i}] -> d = r^-1 * (s*root - z) mod N = {d_from_k}")
    print(f"           in [{d_lo}, {d_hi})? {'YES ***' if in_range else 'no'} ({d_from_k.bit_length()} bits)")

# Also check if root = d directly
for i, root in enumerate(file_roots):
    in_range = d_lo <= root <= d_hi
    if in_range:
        k_from_d = (z + r * root) * pow(s, -1, N) % N
        print(f"  root[{i}] is d in range! k = {k_from_d}")

# Check the relation: root = x2 * w mod s for some cube root of unity w mod s
# Since gcd(x2, s) = 2, we work mod s_odd
s_odd = s // 2
x2_odd = x2 % s_odd
# For each root, compute root * x2^(-1) mod s_odd
# This should give a cube root of unity mod s_odd
for i, root in enumerate(file_roots):
    root_odd = root % s_odd
    w = (root_odd * pow(x2_odd, -1, s_odd)) % s_odd
    cube_check = pow(w, 3, s_odd)
    print(f"  root[{i}] = x2 * w where w^3 mod s_odd = {cube_check} (=1? {cube_check == 1})")

# The 10 cube roots of unity mod s
# From the file: x^3 = 1 mod s has 10 solutions
# These form a group isomorphic to C_3 × C_3 × C_... 
# The exact structure depends on the factorization:
# s = 2 * 827 * 655346491 * large_prime_221bit
# 655346491 mod 3 = 1 (since 655346490 is divisible by 3)
# The remaining factor 14308620010927899874559133748058166637028466906242409479479782149 mod 3:
# Let me check 14308620010927899874559133748058166637028466906242409479479782149 mod 3

print(f"\ns factor 655346491 mod 3 = {655346491 % 3}")
large_factor_s = 14308620010927899874559133748058166637028466906242409479479782149
print(f"large factor mod 3 = {large_factor_s % 3}")
print(f"large factor mod 9 = {large_factor_s % 9}")

# Since 827 mod 3 = 2 (1 cube root) and large_factor mod 3 = 2 (1 cube root)
# and 655346491 mod 3 = 1 (3 cube roots),
# Total odd cube roots of unity = 1*1*3 = 3
# Combined with mod 2: 1*3 = 3 total cube roots of unity
# But the file says 10!

# Wait, this is wrong. Let me check large_factor more carefully
# Actually, 14308620010927899874559133748058166637028466906242409479479782149
# We need to check if this is prime or composite
# If it factors further into more primes where some are 1 mod 3...
# Let me check the proper factorization
print(f"\nProper s factor check:")
temp = s
for p_ in [2, 827, 655346491]:
    if temp % p_ == 0: temp //= p_
print(f"Remaining cofactor of s: {temp}")
# Check if this is prime or composite
if temp > 1:
    from math import isqrt
    # Check if it's likely prime by trial division to 10^7
    is_prime = True
    for i in range(2, min(10000000, int(isqrt(temp)) + 1)):
        if temp % i == 0:
            print(f"  Found factor: {i}")
            print(f"  Other factor: {temp // i}")
            is_prime = False
            break
    if is_prime:
        print(f"  Cofactor appears prime after trial division to 10^7")

# Actually the cube root count 10 = 1 * 2 * 5...
# Let me check: mod 2: 1 cupric root
# mod each odd prime: if p = 1 mod 3: 3 cube roots; if p = 2 mod 3: 1 cube root
# So total = 1 * product over odd primes of (1 or 3)
# We have: 1 (mod 2) * 1 (827) * 3 (655346491) * 1 (large_factor if 2 mod 3)
# = 3 total cube roots
# But file says 10. 

# Wait - does 655346491 have a SQUARE factor? 
# Or does the large factor also have a prime = 1 mod 3?
# Let me check more carefully
if large_factor_s % 3 == 1:
    print("\nLarge factor mod 3 = 1 => could have 3 cube roots")
    # If large_factor = 1 mod 3 and is prime:
    # Total = 1 * 1 * 3 * 3 = 9 cube roots
    # That would give 9 + 1 = 10 cube roots of unity mod s
    print("If prime and =1 mod 3: 9 odd cube roots => 10 total (matches file!)")
elif large_factor_s % 3 == 2:
    print("\nLarge factor mod 3 = 2 => only 1 cube root")
    print("  Total = 1*1*3*1 = 3 cube roots. MISMATCH with file's 10!")
    print("  => Large factor must be composite with a =1 mod 3 factor inside")

# Check: 10 = 1 * 2 * 5...
# Or maybe s-1 factors differently
# Actually, for the number of cube roots of unity mod m = product over prime powers:
# For m = 2^k where k=1: 1 solution
# For odd prime p^e: number of solutions to x^3 = 1 mod p^e
# If p = 2 mod 3: 1 solution
# If p = 1 mod 3: 3 solutions (for all e)

# So total = 3^k where k = number of =1 mod 3 primes
# For 10: 3^0 * x = 10, 3^1 * x = 10, 3^2 * x = 10...
# Not possible! 10 is not a multiple of 3^0=1, 3^1=3, or 3^2=9
# Unless there's a 2-power factor contributing

# Actually for mod 2^e:
# e=1: 1 solution (x=1 mod 2)
# e=2: 2 solutions (x=1,3 mod 4)
# e>=3: 4 solutions (x=1, 2^{e-1}-1, 2^{e-1}+1, 2^{e}-1 mod 2^e)
# s has exactly 2^1 factor, so 1 solution from 2

# For odd primes:
# Each p=1 mod 3 contributes factor of 3
# Each p=2 mod 3 contributes factor of 1
# So total odd = 3^k
# Total = odd * (2-power factor)
# = 3^k * 1 (for s which has 2^1)

# 10 = 1 * 10. But 10 is not a power of 3.
# This means either:
# 1. The file lists only SOME cube roots (not all)
# 2. Our factorization is incomplete
# 3. There's a special case

# Let me count the actual solutions from the file again
# Lines 2-11 = 10 solutions
# x = 1 is one
# The other 9 are nontrivial
# BUT: 9 = 3^2, meaning there are 2 distinct odd primes where p=1 mod 3
# AND: the file may include solutions from BOTH mod s and mod 2 context

# Actually, from the basic theory:
# x^3 = 1 mod s has solutions given by CRT
# s = 2 * 827 * 655346491 * large_factor
# 655346491 mod 3 = 1: contributes 3 cube roots
# If large_factor has a factor that's 1 mod 3: contributes 3 cube roots
# Total: 1*1*3*3 = 9
# Plus x=1: 10 total!

# So large_factor MUST have a 1 mod 3 factor
# Let me verify by checking if large_factor - 1 is divisible by 3
print(f"\nlarge_factor - 1 mod 3 = {(large_factor_s - 1) % 3}")
# If it's divisible by 3, the factor IS 1 mod 3
print(f"large_factor - 1 mod 9 = {(large_factor_s - 1) % 9}")

# This means large_factor is either:
# a) Prime with p = 1 mod 3 => 3 cube roots
# b) Composite with a 1 mod 3 factor inside => 3 cube roots from that factor
