# secp256k1 Subgroup Order N
N = 115792089237316195423570985008687907852837564279074904382605163141518161494337

# Input your exact coefficients from the signature equation
A = 1511449323671149686157664069932893842231045217247889530853657103754363559557007154889890079127984322836076383551274007804476632740009544005665888112315986
B = 6458974735165190013751084106282797157118382637896713181633992134535458536053764609225379724115843651775505787114130783298493396930138585541328975843805451
C = 51866120889717641461810659005716431188799022756838843706514074509901265629059

# Extended Euclidean Algorithm for modular inverse (Python 3 native fallback)
def ext_gcd(a, b):
    if a == 0:
        return b, 0, 1
    g, y, x = ext_gcd(b % a, a)
    return g, x - (b // a) * y, y

def modinv(a, m):
    g, x, y = ext_gcd(a, m)
    if g!= 1:
        raise ValueError('Modular inverse does not exist')
    return x % m

# Helper for exact nearest-integer division (preserves 100% precision with no float limits)
def div_nearest(num, den):
    q, r = divmod(num, den)
    if 2 * r >= den:
        return q + 1
    return q

# Step 1: Modular Reduction of inputs
a = A % N
b = B % N
c = C % N

# Step 2: Modular Inversion to isolate k
try:
    u = modinv(a, N)
except ValueError:
    print("[-] Error: 'a' is not invertible modulo N. Check coefficients.")
    exit()

alpha = (u * b) % N
beta = (u * c) % N

# Step 3: Pure Python 2D Gauss-Lagrange Lattice Reduction
# We want to find the shortest vector in the 2D lattice spanned by:
# v1 = (N, 0)
# v2 = (beta, 1)
v1 = [N, 0]
v2 = [beta, 1]

def dot(u, v):
    return u * v + u[2] * v[2]

# 2D Lattice Reduction Loop
while True:
    # Ensure v1 is the shorter vector
    if dot(v1, v1) > dot(v2, v2):
        v1, v2 = v2, v1
    
    # Calculate orthogonal projection multiplier
    m = div_nearest(dot(v1, v2), dot(v1, v1))
    
    if m == 0:
        break
        
    # Subtract the projection from v2
    v2 = [v2 - m * v1, v2[2] - m * v1[2]]

# The shortest vectors are now v1 and v2
candidates = [v1, v2]

# Step 4: Range-Checking against Puzzle 135 Target Space [2^134, 2^135)
found = False
for vec in candidates:
    potential_d = abs(vec[2])
    if 2**134 <= potential_d < 2**135:
        potential_k = (alpha + beta * potential_d) % N
        print(f"[+] Private Key Found (Dec): {potential_d}")
        print(f"[+] Private Key Found (Hex): {hex(potential_d)}")
        print(f"[+] Corresponding Nonce k: {potential_k}")
        found = True
        break

if not found:
    print("[-] Shortest lattice vectors resolved but they fell outside the exact Puzzle 135 range:")
    print(f"    Vector 1: d = {abs(v1[2])} (Bit length: {abs(v1[2]).bit_length()}), k_offset = {v1}")
    print(f"    Vector 2: d = {abs(v2[2])} (Bit length: {abs(v2[2]).bit_length()}), k_offset = {v2}")