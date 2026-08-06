import numpy as np
from sklearn.manifold import MDS

# -----------------------------
# Hamming distance
# -----------------------------
def delta_hamming(h1, h2):
    b1 = bin(int(h1, 16))[2:].zfill(160)
    b2 = bin(int(h2, 16))[2:].zfill(160)
    return sum(c1 != c2 for c1, c2 in zip(b1, b2))

# -----------------------------
# Your true 7-node cycle
# -----------------------------
hash_nodes = [
    "8000000000000000000000000000000000000000",   # 2^159
    "8000000000000000000000000000000000000050",   # 2^159 + 80
    "BFD5F95500056885C53E4F884189C0A5399B4885",   # Puzzle 160 RIPEMD-160
    "10000000000000000000000000000000000000000",  # 2^160
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAF",   # 2^160 - 80
    "85652E928DA6C4B5747E3FB1D0FCD7DBDFC1F3A0",   # midpoint (2^159.5)
    "DCF8629B82766F04F316EEE0530C4E253667DE8E"    # perimeter anchor
]

# -----------------------------
# 1. Build ΔH matrix
# -----------------------------
N = len(hash_nodes)
DH = np.zeros((N, N))

for i in range(N):
    for j in range(N):
        DH[i, j] = delta_hamming(hash_nodes[i], hash_nodes[j])

np.save("deltaH_matrix.npy", DH)
print("ΔH matrix:\n", DH)

# -----------------------------
# 2. Embed in 3D using MDS
# -----------------------------
mds = MDS(n_components=3, dissimilarity="precomputed", random_state=42)
coords = mds.fit_transform(DH)

np.save("atlas_coords.npy", coords)
print("3D Atlas Coordinates:\n", coords)

# -----------------------------
# 3. Generate 160×160 curvature map
# -----------------------------
def curvature_map(delta_matrix):
    board = np.zeros((160,160))
    maxH = np.max(delta_matrix)
    minH = np.min(delta_matrix[np.nonzero(delta_matrix)])

    # normalize ΔH into [0,1]
    norm = (delta_matrix - minH) / (maxH - minH)

    # project into board
    cx, cy = 80, 80
    for i in range(N):
        x = cx + int((coords[i,0] - coords[:,0].mean()) * 10)
        y = cy + int((coords[i,1] - coords[:,1].mean()) * 10)

        if 0 <= x < 160 and 0 <= y < 160:
            board[x,y] = 1 - (norm[i].mean() if hasattr(norm[i], "mean") else 0)

    return board

curv = curvature_map(DH)
np.save("RM160_atlas.npy", curv)

print("Atlas built successfully.")
