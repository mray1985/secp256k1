import hashlib
from mpmath import mp
from fractions import Fraction

# 1. Initialize precision buffer to capture the deep tenth-tier floors
mp.dps = 800

# secp256k1 Scalar Group Order N
N_str = "115792089237316195423570985008687907852837564279074904382605163141518161494337"
N_val = int(N_str)

# Puzzle 135 Parameters from Hashkeys Space
r1 = 0xc86bec9faea4892fd98d718bdfc770d0d11c3d6bfd4328f25fe9b06bfadb9650
s1 = 0x224a322e81c044d341521f65fabdfa86d84673fb55ed7533862e37f7724931fa
z1 = 0x92886faaf53f90a5c03d6af773a726e75097179306b980e5d28772e612e00fc7

# Twin-key simulation vectors
r2, s2, z2 = r1, s1, z1

# Exact 10th-order precision scaling weights
W = int(mp.power(2, 780))
K_scale = 2**6

# Process coordinate parameters along the common axis
X_k1 = int(mp.nint(r2 * s1 * mp.power(2, 780)))
X_k2 = int(mp.nint(-r1 * s2 * mp.power(2, 780)))
X_N  = int(mp.nint(-N_val * mp.power(2, 780)))

# FIX: Calculated Lattice Determinant Bounds using infinite-precision mpmath
det_volume = (K_scale ** 2) * W * W
minkowski_first_vector_bound = mp.mpf('1.414') * mp.power(mp.mpf(det_volume), mp.mpf('0.25'))
max_reduction_steps = int(4**2 * (det_volume.bit_length()))

print("\n[+] --- LATTICE DETERMINANT BOUNDARY METRICS ---")
print(f"    Lattice Determinant Volume: ~2^{det_volume.bit_length()}")
print(f"    Minkowski Short Vector Ceiling: ~2^{int(mp.log(minkowski_first_vector_bound, 2))}")
print(f"    Maximum LLL Iterations Cap: {max_reduction_steps} steps\n")

# Construct the 4x4 Inhomogeneous Basis Matrix
B_cross = [
    [K_scale, 0, 0, X_k1],
    [0, K_scale, 0, X_k2],
    [0, 0, W, X_N],
    [0, 0, 0, W]
]

def dot(v1, v2):
    return sum(x * y for x, y in zip(v1, v2))

def lll_4d_exact(basis, delta_num=3, delta_den=4):
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

print("[+] Executing exact 4D LLL reduction sequence...")
reduced_basis = lll_4d_exact(B_cross)
print("[+] Reduction loop complete. System limits successfully mapped.")
