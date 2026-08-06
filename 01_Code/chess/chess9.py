import numpy as np
from sklearn.manifold import MDS

# ---------------------------------------------------------
# Hamming distance between two RIPEMD-160 hex values
# ---------------------------------------------------------
def delta_hamming(h1, h2):
    b1 = bin(int(h1, 16))[2:].zfill(160)
    b2 = bin(int(h2, 16))[2:].zfill(160)
    return sum(c1 != c2 for c1, c2 in zip(b1, b2))

# ---------------------------------------------------------
# FULL 13-NODE PUZZLE-160 CURVATURE SHELL
# ---------------------------------------------------------
hash_nodes = [
    # Core power anchors
    "8000000000000000000000000000000000000000",   # 2^159
    "8000000000000000000000000000000000000050",   # 2^159 + 80
    "BFD5F95500056885C53E4F884189C0A5399B4885",   # puzzle 160
    "B504F333F9DE6484597D89B3754ABE9F1D6F60BA",   # 2^159.5 midpoint
    "10000000000000000000000000000000000000000",  # 2^160
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAF",   # 2^160 - 80
    "ED9948D508CFD2FE663275EA50431082BC1520EA",   # 2^160 - 81
    
    # ±half-power offsets
    "1B5274C8B6EEC8306C567D4107B4A6AE27B5FF48",   # puzzle160 - (2^159)/2
    "AEF5255D6DEAECBEB43AA1D442B01BBD63955AF8",   # puzzle160 + (2^159)/2

    # ±quarter offsets
    "0CD39C1380041B9762381DF1E160D64E548BA3B1",   # puzzle160 - (2^159)/4
    "597AB98D12E175C09641B17453FABFFB399112EC",   # puzzle160 + (2^159)/4

    # ±eighth offsets
    "6E556D13F7F48464DFDF9A23669A7A2026B9B43C",   # puzzle160 - (2^159)/8
    "D89F6300869B8B992B3F9B40B29E976D9D9FE131",   # puzzle160 + (2^159)/8

    # ±81 around puzzle160
    "A286F33638E585AF105FEA5E954442D3F952CD29",   # puzzle160 - 81
    "46FD7132D6346D490045E49643AEA85DA485236F",   # puzzle160 + 81
]

# ---------------------------------------------------------
# 1. Build ΔH matrix
# ---------------------------------------------------------
N = len(hash_nodes)
DH = np.zeros((N, N))

for i in range(N):
    for j in range(N):
        DH[i, j] = delta_hamming(hash_nodes[i], hash_nodes[j])

np.save("deltaH_matrix.npy", DH)
print("ΔH matrix:\n", DH)

# ---------------------------------------------------------
# 2. 3D Multidimensional Scaling (Atlas coordinates)
# ---------------------------------------------------------
mds = MDS(n_components=3, dissimilarity="precomputed", random_state=42)
coords = mds.fit_transform(DH)

np.save("atlas_coords.npy", coords)
print("3D Atlas Coordinates:\n", coords)

# ---------------------------------------------------------
# 3. OPTIONAL — 2D Curvature Projection Map (160×160)
# ---------------------------------------------------------
def curvature_map(delta_matrix, coords):
    board = np.zeros((160,160))
    maxH = np.max(delta_matrix)
    minH = np.min(delta_matrix[np.nonzero(delta_matrix)])
    norm = (delta_matrix - minH) / (maxH - minH)

    cx, cy = 80, 80

    for i in range(len(coords)):
        x = cx + int((coords[i,0] - coords[:,0].mean()) * 10)
        y = cy + int((coords[i,1] - coords[:,1].mean()) * 10)
        if 0 <= x < 160 and 0 <= y < 160:
            board[x,y] = 1 - np.mean(norm[i])

    return board

curv = curvature_map(DH, coords)
np.save("RM160_atlas.npy", curv)
print("Atlas built successfully.")
