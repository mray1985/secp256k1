import numpy as np
from sklearn.manifold import MDS

# ============================================================
# 1. Hamming Distance
# ============================================================
def delta_hamming(h1, h2):
    """Compute ΔH between two 160-bit hex strings."""
    b1 = bin(int(h1, 16))[2:].zfill(160)
    b2 = bin(int(h2, 16))[2:].zfill(160)
    return sum(c1 != c2 for c1, c2 in zip(b1, b2))


# ============================================================
# 2. Mod-81 Propagation Class
# ============================================================
def propagation_class(dh):
    """
    Map ΔH → ΔH mod 81.
    This is the MC propagation signature.
    """
    return dh % 81


# ============================================================
# 3. Build ΔH Matrix and ΔH mod 81 Matrix
# ============================================================
def build_deltaH_matrices(hash_list):
    n = len(hash_list)
    deltaH = np.zeros((n, n))
    mod81 = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            dh = delta_hamming(hash_list[i], hash_list[j])
            deltaH[i, j] = dh
            mod81[i, j] = propagation_class(dh)

    return deltaH, mod81


# ============================================================
# 4. Build the 3-D Atlas using MDS
# ============================================================
def build_atlas(deltaH_matrix):
    """
    Multi-Dimensional Scaling projection into ℝ³
    using ΔH as the metric.
    """

    mds = MDS(
        n_components=3,
        dissimilarity="precomputed",
        normalized_stress="auto",
        random_state=42,
    )

    coords = mds.fit_transform(deltaH_matrix)
    return coords


# ============================================================
# 5. Pretty Printing
# ============================================================
def print_matrix(mat, name="Matrix"):
    print(f"\n{name}:")
    for row in mat:
        print(" ".join(f"{int(v):3d}" for v in row))


# ============================================================
# 6. MAIN
# ============================================================
if __name__ == "__main__":

    # =======================================================
    # MC HASH LIST (the one YOU derived)
    # =======================================================
    hash_list = [
        "8000000000000000000000000000000000000000",  # 2^159
        "8000000000000000000000000000000000000050",  # 2^159 + 80
        "BFD5F95500056885C53E4F884189C0A5399B4885",  # rmd160 anchor
        "DCF8629B82766F04F316EEE0530C4E253667DE8E",
        "916D0BD2B03556DF16C8413AB9466111627CD1E3",
        "10000000000000000000000000000000000000000",  # 2^160
        "8C9CCF5C6114A36801952B4B232B3FF8DB3320EA",
        "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAF",  # 2^160 − 81
        "ED9948D508CFD2FE663275EA50431082BC1520EA",
        "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F",  # p reduced form
        "3B23BFD1F5AF9A57D93E9A7DCE1B463E3829134F",
        "B504F333F9DE6484597D89B3754ABE9F1D6F60BA",
        "85652E928DA6C4B5747E3FB1D0FCD7DBDFC1F3A0",
        "1B5274C8B6EEC8306C567D4107B4A6AE27B5FF48",
        "0CD39C1380041B9762381DF1E160D64E548BA3B1",
    ]

    # =======================================================
    # 1. Build ΔH and ΔH mod 81 matrices
    # =======================================================
    deltaH, mod81 = build_deltaH_matrices(hash_list)

    print_matrix(deltaH, "ΔH Matrix")
    print_matrix(mod81, "ΔH mod 81 (Propagation Classes)")

    # =======================================================
    # 2. Build 3-D Propagation Atlas
    # =======================================================
    atlas = build_atlas(deltaH)
    print("\n3D Atlas Coordinates (Propagation-Based):")
    print(atlas)

    # Save results
    np.save("MC_deltaH.npy", deltaH)
    np.save("MC_mod81.npy", mod81)
    np.save("MC_atlas_coords.npy", atlas)

    print("\nMod-81 Propagation Atlas built successfully.\n")
