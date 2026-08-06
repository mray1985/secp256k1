"""
FOLLOW-UP: Identify what point (x2, y) represents on secp256k1
x2 = A - 7 where A = IP (Intermediate Point from TRUE71)
"""
from math import gcd

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

r_val = 90653255469745952335985143920649543885181555095025199315947044135806663628368
s_val = 15509729875763924304053419655647994379903175655107184284998698212653288468986
z_val = 66278737796829840734606014530466656889790152192829793669891337810330530090951

A = 80184233617433755134183875136831551618578922487806929476230322368028862899169
x2 = A - 7

X135 = 0x145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16
y_target = pow((pow(X135, 3, p) + 7) % p, (p+1)//4, p)
if y_target % 2 != 0: y_target = p - y_target

delta = p - N
x_kG = (r_val - delta) % p
y_kG = pow((pow(x_kG, 3, p) + 7) % p, (p+1)//4, p)
if pow(y_kG, 2, p) != (pow(x_kG, 3, p) + 7) % p:
    # Need to handle the other sqrt
    y_kG = p - y_kG

# x2 point
y2_at_x2 = (pow(x2, 3, p) + 7) % p
y_x2 = pow(y2_at_x2, (p+1)//4, p)
if pow(y_x2, 2, p) != y2_at_x2:
    y_x2 = (p - y_x2) if pow(p - y_x2, 2, p) == y2_at_x2 else None
    if y_x2 is None:
        print("ERROR: x2 not on curve!")
        exit()

print("=== POINT IDENTIFICATION ===")
print(f"Point P_x2 = ({x2}, {y_x2})")
print(f"  y even? {y_x2 % 2 == 0}")
print()

# Known points
points = {
    "P_kG (nonce pt)": (x_kG, y_kG),
    "P_dG (pubkey)": (X135, y_target),
}

def point_add(P, Q):
    x1, y1 = P; x2p, y2 = Q
    if x1 is None: return Q
    if x2p is None: return P
    if x1 == x2p and (y1 == y2 or y1 == 0):
        if y1 == 0: return (None, None)
        return point_double(P)
    if x1 == x2p:
        return (None, None)
    s = ((y2 - y1) * pow(x2p - x1, -1, p)) % p
    x3 = (s*s - x1 - x2p) % p
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
    if k == 0: return (None, None)
    if k < 0: return point_mul(-k, (P[0], (-P[1]) % p))
    R = (None, None); Q = P
    while k:
        if k & 1: R = point_add(R, Q)
        Q = point_double(Q); k >>= 1
    return R

Px2 = (x2, y_x2)
P_kG = (x_kG, y_kG)
P_dG = (X135, y_target)
G = (Gx, Gy)

# Check if Px2 equals any known point
for name, pt in points.items():
    match = (pt[0] == x2 and pt[1] == y_x2)
    print(f"P_x2 == {name}? {match}")

# Check if Px2 equals -P (negation of known points)
for name, pt in points.items():
    neg = (pt[0], (-pt[1]) % p)
    match = (neg[0] == x2 and neg[1] == y_x2)
    if match: print(f"P_x2 == -({name})? YES")

# Check if x2 equals A
print(f"\nx2 == A? {x2 == A}")
print(f"x2 == A-7? {x2 == A - 7}")

# Check if A itself is on the curve
y2_A = (pow(A, 3, p) + 7) % p
leg_A = pow(y2_A, (p-1)//2, p)
print(f"\nA on curve? {leg_A % p == 1}")
print(f"A mod p = {A % p}")

# Check if A = x2 + 7 (trivially true, but check mod p)
print(f"A mod p == x2 + 7 mod p? {(x2 + 7) % p == A % p}")

# Check GLV conjugates (cube roots of unity)
# lambda is the GLV endomorphism scalar
lam = 0x5363ad4cc05c30e0a5261c028812645a122e22ea20816678df02967c1b23bd72

# The cube roots of unity mod N: 1, lam, lam^2
# The cube roots of unity mod p (different beta)
# Primitive cube root of unity mod p
for g in range(2, 100):
    beta = pow(g, (p-1)//3, p)
    if beta != 1 and pow(beta, 3, p) == 1:
        break

print(f"\nGLV lambda = {lam}")
print(f"GLV beta (cube root mod p) = {beta}")

# Check if Px2 = P_dG multiplied by lambda
# P_dG * lam has x-coordinate = beta * X135 mod p (GLV property)
x_dG_lam = (beta * X135) % p
print(f"\nlambda * P_dG.x = {x_dG_lam}")
print(f"Px2.x = {x2}")
print(f"Match? {x_dG_lam == x2}")

# Check if Px2 = P_kG * lam
x_kG_lam = (beta * x_kG) % p
print(f"lambda * P_kG.x = {x_kG_lam}")
print(f"Match? {x_kG_lam == x2}")

# Check if Px2 = lam^2 * P_dG
x_dG_lam2 = (pow(beta, 2, p) * X135) % p
print(f"\nlambda^2 * P_dG.x = {x_dG_lam2}")
print(f"Match? {x_dG_lam2 == x2}")

# Check point sums
print("\n=== Point relationships ===")
# Try Px2 + P_dG
sum1 = point_add(Px2, P_dG)
print(f"Px2 + P_dG = ({sum1[0] if sum1[0] else None}, ...)")

# Try Px2 + P_kG
sum2 = point_add(Px2, P_kG)
print(f"Px2 + P_kG = ({sum2[0] if sum2[0] else None}, ...)")

# Try Px2 - P_dG = Px2 + (-P_dG)
neg_dG = (X135, (-y_target) % p)
diff1 = point_add(Px2, neg_dG)
print(f"Px2 - P_dG = ({diff1[0] if diff1[0] else None}, ...)")

# Try Px2 - P_kG
neg_kG = (x_kG, (-y_kG) % p)
diff2 = point_add(Px2, neg_kG)
print(f"Px2 - P_kG = ({diff2[0] if diff2[0] else None}, ...)")

# Check if sums equal G
match_G = sum1[0] == Gx if sum1[0] else False
print(f"Px2 + P_dG == G? {match_G}")
match_G2 = sum2[0] == Gx if sum2[0] else False
print(f"Px2 + P_kG == G? {match_G2}")

# Check if Px2 = G + something
for pt_name, pt in [("P_dG", P_dG), ("P_kG", P_kG)]:
    pt_neg = (pt[0], (-pt[1]) % p)
    # G - pt = G + (-pt)
    val = point_add(G, pt_neg)
    if val[0] == x2 and val[1] == y_x2:
        print(f"P_x2 = G - {pt_name}: MATCH!")

# Check if Px2 = 2*P_dG (doubling)
dbl_dG = point_double(P_dG)
print(f"\n2*P_dG.x = {dbl_dG[0]}")
print(f"Match Px2? {dbl_dG[0] == x2}")

# Check if Px2 = 2*P_kG
dbl_kG = point_double(P_kG)
print(f"2*P_kG.x = {dbl_kG[0]}")
print(f"Match Px2? {dbl_kG[0] == x2}")

# ECDLP question: what k such that k*G = Px2?
# This is the discrete log problem, same difficulty
# But we can check if k is a simple value

# Check if Px2 = G * scalar for small scalars
print("\n=== Small scalar check ===")
for k in range(1, 17):
    pt = point_mul(k, G)
    if pt[0] == x2:
        print(f"P_x2 = {k}*G *** FOUND ***")
        
# Check if Px2 = G * (r mod N) or similar
for scalar_name, scalar in [("r", r_val), ("s", s_val), ("z", z_val), ("delta", delta)]:
    pt = point_mul(scalar, G)
    if pt[0] == x2:
        print(f"P_x2 = {scalar_name}*G *** FOUND ***")
        break
else:
    print("No simple scalar found")

# Final: check if x-coordinate relationship with n1 or n3
# n1 and n3 are the N-side cube roots (along with x2)
n1 = 40220395037450137658562871366385094182673796545182808438190875548898232062868
n3 = 111179549819748498054395223514159169904422409525160070850789128366109228026644

# Check x_kG relationship with n1, n3
x_kG_mod_N = x_kG % N
print(f"\nx_kG mod N = {x_kG_mod_N}")
print(f"n1 = {n1}")
print(f"n3 = {n3}")
print(f"x_kG == n1? {x_kG_mod_N == n1}")
print(f"x_kG == n3? {x_kG_mod_N == n3}")
# Check X135 too
X135_mod_N = X135 % N
print(f"X135 mod N = {X135_mod_N}")
print(f"X135 == n1? {X135_mod_N == n1}")
print(f"X135 == n3? {X135_mod_N == n3}")
