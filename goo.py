import sys
from mpmath import mp
from fractions import Fraction

# 1. Initialize precision buffer to capture the deep tenth-tier floors
mp.dps = 800

# secp256k1 Scalar Group Order N
N_str = "115792089237316195423570985008687907852837564279074904382605163141518161494337"
N_val = int(N_str)
N = mp.mpf(N_val)

# INPUT 1: Puzzle 135 Parameters from Hashkeys Space
r1_hex = "c86bec9faea4892fd98d718bdfc770d0d11c3d6bfd4328f25fe9b06bfadb9650"
s1_hex = "224a322e81c044d341521f65fabdfa86d84673fb55ed7533862e37f7724931fa"

r1_val = int(r1_hex, 16)
s1_val = int(s1_hex, 16)

r1 = mp.mpf(r1_val)
s1 = mp.mpf(s1_val)

# INPUT 2: Secondary Puzzle Input within the Same Transaction 
# !!! REPLACE THESE PLACEHOLDERS WITH THE COMPANION SIGNATURE VALUES !!!
r2_hex = "9fca00d29192007648f7e4b525f15a00a5180833617a604ec6701833eb26e580" 
s2_hex = "03633cbe3ec02b9401c5effa144c5b4d22f87940259634858fc7e59b1c09937852"

r2_val = int(r2_hex, 16)
s2_val = int(s2_hex, 16)

r2 = mp.mpf(r2_val)
s2 = mp.mpf(s2_val)

# 2. Establish tenth-tier scaling factor W = 2^780
W_real = mp.power(2, 780)
W = int(W_real)

# 3. Define the bounding constraint weights
# High-bit nonce scale constraint for target window k >= 2^250 (Headroom = 6 bits)
K_scale = 2**6   

# Private key constraint scaling to balance the 135-bit search window against N
D_scale = 2**121  

# 4. Map the multi-signature parameters into a common coordinate axis scaled by W
X_s1 = int(mp.nint(s1 * W_real))
X_s2 = int(mp.nint(-s2 * W_real))
X_r1 = int(mp.nint(-r1 * W_real))
X_r2 = int(mp.nint(r2 * W_real))
X_N  = int(mp.nint(-N * W_real))

# Rigorous 5x5 Joint-Transaction Coordinate Aligned Matrix Basis
# Rows map the unknown vector elements: [ k1, k2, d1, d2, m_joint ]
B_joint = [
    [K_scale, 0, 0, 0, X_s1],
    [0, K_scale, 0, 0, X_s2],
    [0, 0, D_scale, 0, X_r1],
    [0, 0, 0, D_scale, X_r2],
    [0, 0, 0, 0, X_N]
]

def dot(v1, v2):
    return sum(x * y for x, y in zip(v1, v2))

def lll_exact_5d(basis, delta_num=3, delta_den=4):
    """Infinite-precision 5D LLL solver using exact fractions to prevent float overflow"""
    n = len(basis)
    f_basis = [[Fraction(x) for x in row] for row in basis]
    ortho = [[Fraction(0) for _ in range(n)] for _ in range(n)]
    mu = [[Fraction(0) for _ in range(n)] for _ in range(n)]
    
    def update_gps():
        for i in range(n):
            ortho[i] = list(f_basis[i])
            for j in range(i):
                ortho_j_sq = dot(ortho[j], ortho[j])
                if ortho_j_sq != 0:
                    mu[i][j] = dot(f_basis[i], ortho[j]) / ortho_j_sq
                else:
                    mu[i][j] = Fraction(0)
                ortho[i] = [ortho[i][k] - mu[i][j] * ortho[j][k] for k in range(n)]

    update_gps()
    k = 1
    while k < n:
        for j in reversed(range(k)):
            if abs(mu[k][j]) > Fraction(1, 2):
                q = round(mu[k][j])
                f_basis[k] = [f_basis[k][i] - q * f_basis[j][i] for i in range(n)]
                update_gps()
        
        lhs = dot(ortho[k], ortho[k])
        rhs = (Fraction(delta_num, delta_den) - mu[k][k-1]**2) * dot(ortho[k-1], ortho[k-1])
        if lhs >= rhs:
            k += 1
        else:
            f_basis[k], f_basis[k-1] = f_basis[k-1], f_basis[k]
            update_gps()
            k = max(k - 1, 1)
    return [[int(x) for x in row] for row in f_basis]

print("[+] Running 5D exact fraction solver with joint-transaction coordinate alignment...")
reduced_basis = lll_exact_5d(B_joint)

# Evaluate short vectors to find target parameters
for vec in reduced_basis:
    k1_candidate = abs(vec[0]) // K_scale
    k2_candidate = abs(vec[1]) // K_scale
    d1_candidate = abs(vec[2]) // D_scale
    d2_candidate = abs(vec[3]) // D_scale
    
    # Validate candidates against the joint 135-bit Puzzle target constraints
    if (2**134 <= d1_candidate < 2**135) and (k1_candidate >= 2**250 and k1_candidate < N_val):
        print(f"\n[!] Target Vector Space Captured via Simultaneous 5D Intersection!")
        print(f"    Private Key d1 (Hex): {hex(d1_candidate)}")
        print(f"    Private Key d2 (Hex): {hex(d2_candidate)}")
        print(f"    Nonce k1       (Hex): {hex(k1_candidate)}")
        print(f"    Nonce k2       (Hex): {hex(k2_candidate)}")
        sys.exit(0)
else:
    print("\n[-] 5D basis reduction complete. Load actual companion signature values to break the underdetermined state.")
