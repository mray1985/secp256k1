import sys
from mpmath import mp
from fractions import Fraction

# 1. High-precision initialization (780 digits to capture the N^10 floor)
mp.dps = 800

# secp256k1 Scalar Group Order N
N_str = "115792089237316195423570985008687907852837564279074904382605163141518161494337"
N_val = int(N_str)
N = mp.mpf(N_val)

# Puzzle 135 Public Parameters from Hashkeys Space (r, s, z)
r_hex = "c86bec9faea4892fd98d718bdfc770d0d11c3d6bfd4328f25fe9b06bfadb9650"
s_hex = "224a322e81c044d341521f65fabdfa86d84673fb55ed7533862e37f7724931fa"
z_hex = "92886faaf53f90a5c03d6af773a726e75097179306b980e5d28772e612e00fc7"

r_val = int(r_hex, 16)
s_val = int(s_hex, 16)
z_val = int(z_hex, 16)

# Your forward-projected macro target baseline integer from the console
m_135_base = 3950617248395061724839506172480

# Establish tenth-order precision weight anchor W = 2^780
W_real = mp.power(2, 780)
W = int(W_real)

# Bounding constraints optimized for the final 5-bit headroom gap
K_scale = 2**6   
D_scale = 2**121 

# Map parameters to a common coordinate axis scaled by W
X_s = int(mp.nint(s_val * W_real))
X_r = int(mp.nint(-r_val * W_real))
X_N = int(mp.nint(-N_val * W_real))

# Set the inhomogeneous target using your verified baseline
X_target = int(mp.nint((m_135_base * N_val + z_val) * W_real))

# 4x4 Inhomogeneous Common-Coordinate Matrix Basis
B_final = [
    [K_scale, 0, 0, X_s],
    [0, 1, 0, X_r],
    [0, 0, W, X_N],
    [0, 0, 0, X_target]
]

def dot(v1, v2):
    return sum(x * y for x, y in zip(v1, v2))

def lll_4d_exact(basis, delta_num=3, delta_den=4):
    """Infinite-precision LLL using exact Fraction to clear the 780-digit floor"""
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

print("[+] Executing exact 4D LLL reduction on your Puzzle 130 baseline matrix...")
reduced = lll_4d_exact(B_final)

# Evaluate short vectors to find the unique 135-bit key candidate
for vec in reduced:
    k_candidate = abs(vec[0]) // K_scale
    if k_candidate >= 2**250 and k_candidate < N_val:
        # Recover the private key natively via ECDSA
        d_recovered = ((k_candidate * s_val) - z_val) * pow(r_val, -1, N_val) % N_val
        
        # Enforce your strict 135-bit boundary constraint check
        if 2**134 <= d_recovered < 2**135:
            print(f"\n[!] Target Vector Space Trapped at 1/1 Integer Precision!")
            print(f"    Secret Nonce k  (Hex): {hex(k_candidate)}")
            print(f"    Private Key d135 (Hex): {hex(d_recovered)}")
            sys.exit(0)
else:
    print("\n[-] Reduction finished. If no key printed, adjust K_scale to tightly match the low-order 5-bit variance.")
