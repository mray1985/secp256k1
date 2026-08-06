import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# 1. RM160 CHESS MOVE CLASSIFIER
# ---------------------------------------------------------

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
    if 21 <= deltaH <= 80: return deltaH, "DOUBLE-QUEEN / BOARD SWEEP"
    return deltaH, "BOARD FLIP (CHECKMATE BOUNDARY)"


# ---------------------------------------------------------
# 2. BUILD 160×160 BOARD
# ---------------------------------------------------------

def curvature_board(deltaH):
    board = np.zeros((160, 160))

    cx, cy = 80, 80
    radius = deltaH / 2

    for x in range(160):
        for y in range(160):
            dist = np.sqrt((x - cx)**2 + (y - cy)**2)
            if dist <= radius:
                board[x, y] = 1

    return board


# ---------------------------------------------------------
# 3. PLOT ATLAS TILE WITH MATPLOTLIB
# ---------------------------------------------------------

def render_tile(board, title):
    plt.imshow(board, cmap="inferno")
    plt.title(title)
    plt.colorbar()
    plt.show()


# ---------------------------------------------------------
# 4. MAIN
# ---------------------------------------------------------

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

for i in range(len(hash_list) - 1):
    h1, h2 = hash_list[i], hash_list[i+1]
    delta, move = rm160_chess_move(h1, h2)

    print(f"{h1} → {h2} : ΔH = {delta} → {move}")

    board = curvature_board(delta)
    render_tile(board, f"ΔH = {delta}  ({move})")
