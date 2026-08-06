#!/usr/bin/env python3
"""
Analyze the SECOND CF in cl989.txt - different numbers, different point.
"""
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424

# Second CF values
num2_num = 2 * 46351506704828816385393879789131775975171267756561783641521771795450741674800
den2_base = 9210836494447108270027136741376870869791784014198948301625976867708124077590
den2 = 3 * den2_base * den2_base

print("=== SECOND CF IN CL989.TXT ===")
print(f"Numerator 2*Y = {num2_num}")
print(f"Denominator 3*X^2 = {den2}")
print()

# The value
from decimal import Decimal, getcontext
getcontext().prec = 200
val2 = Decimal(num2_num) / Decimal(den2)
print(f"Value = {val2}")
print(f"       = {float(val2):.15e}")
print()

# Identify the point
Y_val = 46351506704828816385393879789131775975171267756561783641521771795450741674800
X_val = den2_base  # 9210836494447108270027136741376870869791784014198948301625976867708124077590

print(f"Y-coordinate candidate: {Y_val}")
print(f"X-coordinate candidate: {X_val}")
print(f"  bit length: {X_val.bit_length()}")
print(f"  byte length: {X_val.bit_length() // 8}")
print()

# Check if (X_val, Y_val) is on the curve
lhs = (Y_val * Y_val) % p
rhs = (pow(X_val, 3, p) + 7) % p
on_curve = (lhs == rhs)
print(f"Is (X, Y) on secp256k1? {on_curve}")
if on_curve:
    print(f"  LHS = {lhs}")
    print(f"  RHS = {rhs}")

# Check if it could be a puzzle public key
# Known puzzle pubkeys
known_pub = {
    65: "02746b76f3d633cafdde3c676c1416e868362c03d1126b16bce6a96a5e6d68a40b",
    90: "02e2b8b6cda2bd76e4e78e5b29482a13a6d6405dbf504594d5544a503b8976c04c",
    100: "0376b1fce76c07f4bacc9df8dbe57278b8489b1e595c69ca6e26d87d0874b75531",
    115: "0372bf2e9c2afc92029539bbeb4bb1a78c1fddb1862b224098c6889a3f05a41323",
    120: "029f8666abe2e93e0c93b5cdf1ae52af32d49b3b4a52e9c5a4fba536c5a6ceb6b4",
    125: "0283e63c9de1bcf155b9249d1d636a3167ece1606aa8e47888f12b179e42808b89",
    130: "02ecc8097fd386b15cc167ad293a79f327bdd779dd9e5b7ba8f5bb837a0548af7b",
    160: "02e0a8b039282faf6fe0fd769cfbc4b6b4cf8758ba68220eac420e32b91ddfa673",
}

def decompress(comp_hex):
    prefix = int(comp_hex[:2], 16)
    x = int(comp_hex[2:], 16)
    y_sq = (pow(x, 3, p) + 7) % p
    y = pow(y_sq, (p + 1) // 4, p)
    if prefix == 0x02 and y % 2 != 0:
        y = p - y
    elif prefix == 0x03 and y % 2 != 1:
        y = p - y
    return (x, y)

print()
print("Checking if X_val matches any known puzzle x-coordinate:")
for pnum, comp in known_pub.items():
    x_pub, y_pub = decompress(comp)
    if X_val == x_pub:
        print(f"  *** MATCH! X = Puzzle {pnum} public key x-coordinate!")
    if Y_val == y_pub:
        print(f"  *** MATCH! Y = Puzzle {pnum} public key y-coordinate!")

# Check if X_val is the negative of G or something
print()
print(f"Compare to G: Gx = {Gx}")
print(f"  X_val - Gx = {X_val - Gx}")
print(f"  p - X_val = {p - X_val}")
if p - X_val == Gx:
    print("  *** X_val = p - Gx (negated x-coordinate)")

# Second CF terms
print()
print("=== SECOND CF TERMS ===")
terms2 = [0, 2745525926515359661109446723818622216143021757590666919792393338008076506413, 5, 7, 2, 2, 1, 4, 252, 6, 1, 5, 2, 1, 26, 5, 6, 2, 3, 1, 2, 7, 1, 3, 1, 2, 2, 3, 6, 1, 1, 7, 1, 1, 4, 1, 9, 1, 3, 2, 2, 5, 1, 8, 1, 1, 1, 1, 1, 5, 68, 2, 1, 39, 1, 18, 1, 1, 15, 8, 1, 1, 1, 1, 1, 1, 6, 48, 6, 2, 2, 3, 1, 1, 1, 5, 4, 8, 1, 9, 5, 1, 1, 1, 1, 6, 1, 6]
print(f"First non-zero: {terms2[1]}")
print(f"  bits: {terms2[1].bit_length()}")
print()

# Compare a1 to p and N
a1 = terms2[1]
print(f"  a1 - p = {a1 - p}")
print(f"  a1 - N = {a1 - N}")
print(f"  a1 - N = {(a1 - N) % N if a1 > N else 'N/A'}")
