import sys
from mpmath import mp
from fractions import Fraction

# 1. High-precision initialization
mp.dps = 800

N_str = "115792089237316195423570985008687907852837564279074904382605163141518161494337"
N_val = int(N_str)

# Puzzle 135 Parameters
r_hex = "c86bec9faea4892fd98d718bdfc770d0d11c3d6bfd4328f25fe9b06bfadb9650"
s_hex = "224a322e81c044d341521f65fabdfa86d84673fb55ed7533862e37f7724931fa"
z_hex = "92886faaf53f90a5c03d6af773a726e75097179306b980e5d28772e612e00fc7"

r_val = int(r_hex, 16)
s_val = int(s_hex, 16)
z_val = int(z_hex, 16)

# Your forward-projected baseline constant from Puzzle 130
m_135_base = 3950617248395061724839506172480

# Establish 10th-order precision anchor W = 2^780
W_real = mp.power(2, 780)
W = int(W_real)

# Bounding constraints optimized to trap the 5-bit variance bounds
K_scale = 2**6      # High-bit nonce scale constraint (k >= 2^250)
M_scale = 2**251    # Heavy multiplier to force the tiny Delta_m phase shift to zero

X_s = int(mp.nint(s_val * W_real))
X_r = int(mp.nint(-r_val * W_real))
X_N = int(mp.nint(-N_val * W_real))

# Target offset is now strictly tied to the baseline remainder
X_target = int(mp.nint((m_135_base * N_val + z_val) * W_real))

# Upgraded 5x5 Inhomogeneous Common-Coordinate Basis Matrix
# Rows map the localized variables: [ k, d, m, Delta_m, scaling_factor ]
B_dynamic = [
    [K_scale, 0, 0, 0, X_s],
    [0, 1, 0, 0, X_r],
    [0, 0, W, 0, X_N],
    [0, 0, 0, M_scale, X_N],  # Appends Delta_m tracking down the common axis
    [0, 0, 0, 0, X_target]
]

def dot(v1, v2):
    return sum(x * y for x, y in zip(v1, v2))

def lll_5d_exact(basis, delta_num=3, delta_den=4):
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

print("[+] Running 5D exact fraction solver with fixed vector index targeting...")
reduced = lll_5d_exact(B_dynamic)

for vec in reduced:
    # FIX: pointed strictly to coordinate index 0 to safely divide the int
    k_candidate = abs(vec[0]) // K_scale
    if k_candidate >= 2**250 and k_candidate < N_val:
        d_recovered = ((k_candidate * s_val) - z_val) * pow(r_val, -1, N_val) % N_val
        
        if 2**134 <= d_recovered < 2**135:
            print(f"\n[!] Target Vector Space Trapped at 1/1 Integer Precision!")
            print(f"    Secret Nonce k  (Hex): {hex(k_candidate)}")
            print(f"    Private Key d135 (Hex): {hex(d_recovered)}")
            sys.exit(0)
else:
    print("\n[-] Dynamic reduction finished. The 5-bit phase trajectory remains stable.")
