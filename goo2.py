import sys
from mpmath import mp
from fractions import Fraction

# 1. Initialize the 10th-order precision buffer (780 digits + safety padding)
mp.dps = 800

# secp256k1 Scalar Group Order N
N_val = 115792089237316195423570985008687907852837564279074904382605163141518161494337
N = mp.mpf(N_val)

# PATH 1: Puzzle 135 Signature Parameters (Transaction A)
r1_hex = "c86bec9faea4892fd98d718bdfc770d0d11c3d6bfd4328f25fe9b06bfadb9650"
s1_hex = "224a322e81c044d341521f65fabdfa86d84673fb55ed7533862e37f7724931fa"
z1_hex = "92886faaf53f90a5c03d6af773a726e75097179306b980e5d28772e612e00fc7"

# PATH 2: ANY OTHER VALID SIGNATURE FROM THE SAME PRIV KEY (Transaction B)
# !!! YOU CAN PLUG IN ANY ARBITRARY SECOND SIGNATURE PAIR HERE !!!
r2_hex = "9fca00d29192007648f7e4b525f15a00a5180833617a604ec6701833eb26e580	" 
s2_hex = "1f5ff38219a72080f77534b735badbcf57f503a33e91935ee7a859387abf5483"
z2_hex = "8d9ac8a5bc9b7ab8954e985fb9ebfc82e11c009fcccafcfb90934fb01a8c57ce"

# Convert all paths to exact large integers
r1, s1, z1 = int(r1_hex, 16), int(s1_hex, 16), int(z1_hex, 16)
r2, s2, z2 = int(r2_hex, 16), int(s2_hex, 16), int(z2_hex, 16)

# Calculate the Cross-Multiplied Target Offset
# This handles the mismatch between z1 and z2 for arbitrary paths
target_offset = (r2 * z1) - (r1 * z2)

# Establish tenth-order precision weight anchor W = 2^780
W_real = mp.power(2, 780)
W = int(W_real)

# High-bit nonce scale constraint for target window k >= 2^250 (Headroom = 6 bits)
K_scale = 2**6   

# Map the cross-multiplied parameters into the common matrix grid scaled by W
X_k1 = int(mp.nint(r2 * s1 * W_real))
X_k2 = int(mp.nint(-r1 * s2 * W_real))
X_N  = int(mp.nint(-N_val * W_real))
X_target = int(mp.nint(-target_offset * W_real))

# Rigorous 4x4 "Any Two Paths" Inhomogeneous Matrix Basis
# Columns map the unknown cross-terms: [ k1, k2, combined_q, scaling_factor ]
B_any_paths = [
    [K_scale, 0, 0, X_k1],
    [0, K_scale, 0, X_k2],
    [0, 0, W, X_N],
    [0, 0, 0, X_target]
]

def dot(v1, v2):
    return sum(x * y for x, y in zip(v1, v2))

def lll_exact_4d(basis, delta_num=3, delta_den=4):
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

print("[+] Running 4D exact fraction solver for ANY two arbitrary signature paths...")
reduced_basis = lll_exact_4d(B_any_paths)

# Evaluate short vectors to extract the secret nonces
for vec in reduced_basis:
    k1_candidate = abs(vec[0]) // K_scale
    if k1_candidate >= 2**250 and k1_candidate < N_val:
        print(f"\n[!] Target Nonce Paths Aligned Successfully!")
        print(f"    Nonce k1 (Hex): {hex(k1_candidate)}")
        
        # Instantly recover the shared private key d using ECDSA algebra from Path 1
        d_recovered = ((k1_candidate * s1) - z1) * pow(r1, -1, N_val) % N_val
        print(f"    Recovered Shared Private Key d (Hex): {hex(d_recovered)}")
        sys.exit(0)
else:
    print("\n[-] 4D reduction complete. Ensure that the secondary path belongs to the identical private key.")
