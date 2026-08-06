#!/usr/bin/env python3
"""
Identify the second point in cl989.txt and its tangent slope.
"""
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424

X = 9210836494447108270027136741376870869791784014198948301625976867708124077590
Y = 46351506704828816385393879789131775975171267756561783641521771795450741674800

print(f"Point (X, Y):")
print(f"  X = {X}")
print(f"  Y = {Y}")
print()

# Is it a multiple of G? Check 2G, 3G, etc.
print("Checking if it's a small multiple of G...")

def ec_add(P1, P2):
    if P1 is None: return P2
    if P2 is None: return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2:
        if y1 == y2:
            lam = (3 * x1 * x1) * pow(2 * y1, -1, p) % p
        else:
            return None
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)

def ec_mul(k, P):
    result = None
    addend = P
    while k > 0:
        if k & 1:
            result = ec_add(result, addend)
        addend = ec_add(addend, addend)
        k >>= 1
    return result

G = (Gx, Gy)
for k in range(2, 20):
    Q = ec_mul(k, G)
    if Q and Q[0] == X and Q[1] == Y:
        print(f"  *** POINT = {k}*G !!!")
    if Q and Q[0] == X and Q[1] == (p - Y):
        print(f"  *** POINT = -{k}*G (negated y)")

# Check if it's negated G
if X == Gx and Y == p - Gy:
    print(f"  POINT = -G (negated generator)")
if X == p - Gx and Y == Gy:
    print(f"  POINT = vertically mirrored G")

# Check if it relates to the projection defect D
delta = p - N
print()
print(f"Delta (p-N) = {delta}")
print(f"X mod delta = {X % delta}")
print(f"Y mod delta = {Y % delta}")

# Check if X or Y relate to R-point from true69
# In TRUE69: x_kG = r - delta mod p
# Let's check some common R-values
print()
print("Checking if X matches known reconstructed R-values...")

# Puzzle 160's r and z from the known files
# r for P160
known_r = {
    65: 78851156821939598930719225276335666564424400002456474814517642714684883061408,
    90: 69673304720876160075229624583547409885636207434161816957474172319527500474415,
    100: 100182957009067260676129163398412919222496578752554197866304926759487636509729,
    115: 62641386159082452201681958645023150433102249854530986013739112343764069317711,
    120: 100480591869089994315869534883181916927590910231092411991845900661570178084117,
    125: 63833400142572548270929737909115586706553550972272560806111166328807706465903,
    130: 6276493284178792263728042533158666787380597239988507667129682066325892829262,
}

for puzzle, r in known_r.items():
    R_x_reconstructed = (r - delta) % p
    if R_x_reconstructed == X:
        print(f"  *** X = R_x for Puzzle {puzzle}! (r - delta mod p)")

# Check if (X,Y) is 2*G
Q2 = ec_mul(2, G)
print(f"\n2*G = ({Q2[0]}, {Q2[1]})")
if Q2[0] == X:
    print("  *** X matches 2G x-coord!")
print()

# Compute slope at (X,Y)
lam_X = (3 * X * X) * pow(2 * Y, -1, p) % p
print(f"Slope lambda at (X,Y)  mod p = {lam_X}")
print(f"  lambda mod 9 = {lam_X % 9}")

# Check if this relates to any puzzle d
known_d = {
    65: 30568377312064202855,
    90: 868012190417726402719548863,
    100: 868221233689326498340379183142,
    115: 31464123230573852164273674364426950,
    120: 919343500840980333540511050618764323,
    125: 37650549717742544505774009877315221420,
    130: 1103873984953507439627945351144005829577,
}
print()
for pnum, d in known_d.items():
    if lam_X == d:
        print(f"  *** lam_X = Puzzle {pnum} d!")
    if (lam_X - d) % p < 100 or (d - lam_X) % p < 100:
        print(f"  lam_X and Puzzle {pnum} d differ by {min((lam_X-d)%p, (d-lam_X)%p)}")

# Check: what is lam_X mod N?
lam_X_mod_N = lam_X % N
print(f"\nlam_X mod N = {lam_X_mod_N}")
print(f"N - lam_X_mod_N = {N - lam_X_mod_N}")
