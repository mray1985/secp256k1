import hashlib
import numpy as np
from sklearn.manifold import MDS

# ---------------------------------------------------------
# Hamming distance
# ---------------------------------------------------------
def delta_hamming(h1, h2):
    b1 = bin(int(h1, 16))[2:].zfill(160)
    b2 = bin(int(h2, 16))[2:].zfill(160)
    return sum(c1 != c2 for c1, c2 in zip(b1, b2))

# ---------------------------------------------------------
# Fake "public key" generator (safe)
# ---------------------------------------------------------
def synthetic_pub(seed_hex):
    """
    Creates a deterministic but SAFE vector from the hash,
    without acting as an ECC private scalar.
    """
    seed_bytes = bytes.fromhex(seed_hex)
    out = b""

    # propagate using SHA256 → SHA256 → RIPEMD160 emulation
    for _ in range(3):
        seed_bytes = hashlib.sha256(seed_bytes).digest()
        out += seed_bytes

    # return first 20 bytes as a fake 160-bit point
    return out[:20].hex()

# ---------------------------------------------------------
# MC node list (your 15 RM160 values)
# ---------------------------------------------------------
MC = [
    "8000000000000000000000000000000000000000",
    "8000000000000000000000000000000000000050",
    "BFD5F95500056885C53E4F884189C0A5399B4885",
    "DCF8629B82766F04F316EEE0530C4E253667DE8E",
    "1B5274C8B6EEC8306C567D4107B4A6AE27B5FF48",
    "8000000000000000000000000000000000000000",
    "916D0BD2B03556DF16C8413AB9466111627CD1E3",
    "8C9CCF5C6114A36801952B4B232B3FF8DB3320EA",
    "0CD39C1380041B9762381DF1E160D64E548BA3B1",
    "6E556D13F7F48464DFDF9A23669A7A2026B9B43C",
    "AEF5255D6DEAECBEB43AA1D442B01BBD63955AF8",
    "597AB98D12E175C09641B17453FABFFB399112EC",
    "D89F6300869B8B992B3F9B40B29E976D9D9FE131",
    "A286F33638E585AF105FEA5E954442D3F952CD29",
    "46FD7132D6346D490045E49643AEA85DA485236F"
]

N = len(MC)

# ---------------------------------------------------------
# 1. Compute propagation RM160s
# ---------------------------------------------------------
prop = [synthetic_pub(h) for h in MC]

# ---------------------------------------------------------
# 2. Compute ΔH between propagated hashes and original MC hashes
# ---------------------------------------------------------
DH = np.zeros((N, N), dtype=int)
for i in range(N):
    for j in range(N):
        DH[i, j] = delta_hamming(prop[i], MC[j])

print("Propagation ΔH Matrix:")
print(DH)

# Save raw matrix
np.save("RM160_propagation_matrix.npy", DH)

# ---------------------------------------------------------
# 3. Mod-81 propagation classes
# ---------------------------------------------------------
DH_mod81 = DH % 81
print("\nΔH mod 81:")
print(DH_mod81)

# ---------------------------------------------------------
# 4. FIX — MDS REQUIRES A SYMMETRIC MATRIX
# ---------------------------------------------------------

# Average the matrix with its transpose
DH_sym = (DH_mod81 + DH_mod81.T) / 2
DH_sym = DH_sym.astype(float)

# Save symmetric matrix
np.save("RM160_propagation_sym.npy", DH_sym)

# ---------------------------------------------------------
# 5. 3D Atlas Embedding using the symmetric ΔH matrix
# ---------------------------------------------------------
mds = MDS(n_components=3, dissimilarity="precomputed", random_state=42)
coords = mds.fit_transform(DH_sym)

# Save the coordinates
np.save("RM160_propagation_atlas.npy", coords)

print("\n3D Propagation Atlas Coordinates:")
print(coords)
print("\nRM160 Propagation Atlas built successfully.")
