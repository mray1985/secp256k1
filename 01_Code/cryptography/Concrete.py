# secp256k1 Order
N = 115792089237316195423570985008687907852837564279074904382605163141518161494337

# Input your exact coefficients
A = 1511449323671149686157664069932893842231045217247889530853657103754363559557007154889890079127984322836076383551274007804476632740009544005665888112315986
B = 6458974735165190013751084106282797157118382637896713181633992134535458536053764609225379724115843651775505787114130783298493396930138585541328975843805451
C = 51866120889717641461810659005716431188799022756838843706514074509901265629059

# Step 1: Modular Reduction
a = A % N
b = B % N
c = C % N

# Step 2: Modular Inversion to isolate k
u = pow(a, -1, N)
alpha = (u * b) % N
beta = (u * c) % N

# Step 3: Construct the LLL Lattice
# We scale the lattice by a factor to balance the bounds of d (2^135) and k (2^256)
X = 2**135  # Bounding range of Puzzle 135
L = Matrix(ZZ, [N, 0],
    [beta, 1])

# Perform LLL reduction
L_reduced = L.LLL()

# Extract the shortest vector components
for row in L_reduced:
    # Check if the vector coordinates correspond to a valid key d
    potential_d = abs(row[1])
    if 2**134 <= potential_d < 2**135:
        potential_k = (alpha + beta * potential_d) % N
        print(f"[+] Private Key Found (Dec): {potential_d}")
        print(f"[+] Private Key Found (Hex): {hex(potential_d)}")
        print(f"[+] Corresponding Nonce k: {potential_k}")
        break