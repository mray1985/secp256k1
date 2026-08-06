import numpy as np
import matplotlib.pyplot as plt
import os

# ------------------------------
# RM160 Chess Move Classifier
# ------------------------------


def rm160_chess_move(a, b):
    a_bits = bin(int(a, 16))[2:].zfill(160)
    b_bits = bin(int(b, 16))[2:].zfill(160)
    deltaH = sum(x != y for x, y in zip(a_bits, b_bits))

    if deltaH == 0: return deltaH, "NO MOVE"
    if deltaH == 1: return deltaH, "KING MOVE"
    if deltaH == 2: return deltaH, "KNIGHT MOVE"
    if 3 <= deltaH <= 4: return deltaH, "BISHOP MOVE"
    if 5 <= deltaH <= 8: return deltaH, "ROOK MOVE"
    if 9 <= deltaH <= 20: return deltaH, "QUEEN MOVE"
    if 21 <= deltaH <= 80: return deltaH, "DOUBLE-QUEEN"
    return deltaH, "BOARD FLIP"

# ------------------------------
# Build Curvature Tile
# ------------------------------

def curvature_board(deltaH):
    board = np.zeros((160, 160))
    cx, cy = 80, 80
    radius = deltaH / 2

    for x in range(160):
        for y in range(160):
            if np.sqrt((x - cx)**2 + (y - cy)**2) <= radius:
                board[x, y] = 1
    return board

# ------------------------------
# Render & Save Tile
# ------------------------------

def save_tile(board, title, filename):
    plt.figure(figsize=(5,5))
    plt.imshow(board, cmap="inferno")
    plt.title(title)
    plt.axis("off")
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

# ------------------------------
# MAIN ATLAS GENERATOR
# ------------------------------

hash_list = [
    "8000000000000000000000000000000000000000",
    "BFD5F95500056885C53E4F884189C0A5399B4885",
    "8000000000000000000000000000000000000050",
    "DCF8629B82766F04F316EEE0530C4E253667DE8E",
    "916D0BD2B03556DF16C8413AB9466111627CD1E3",
    "10000000000000000000000000000000000000000",
    "8C9CCF5C6114A36801952B4B232B3FF8DB3320EA",
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAF",
    "ED9948D508CFD2FE663275EA50431082BC1520EA",
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F",
    "3B23BFD1F5AF9A57D93E9A7DCE1B463E3829134F",
    "B504F333F9DE6484597D89B3754ABE9F1D6F60BA",
    "85652E928DA6C4B5747E3FB1D0FCD7DBDFC1F3A0"
]

os.makedirs("atlas_tiles", exist_ok=True)

atlas_maps = []
movement_labels = []

for i in range(len(hash_list) - 1):
    h1 = hash_list[i]
    h2 = hash_list[i+1]

    delta, move = rm160_chess_move(h1, h2)

    title = f"ΔH={delta}  {move}"
    print(f"{h1} → {h2} : {title}")

    tile = curvature_board(delta)
    atlas_maps.append(tile)
    movement_labels.append(title)

    save_tile(tile, title, f"atlas_tiles/tile_{i+1}.png")

print("\nAll 13 tiles generated in folder: atlas_tiles/")
