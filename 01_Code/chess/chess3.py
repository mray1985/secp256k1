import numpy as np

# ======================================================
# 1. BUILD EMPTY 160×160 CHESSBOARD
# ======================================================

def build_board():
    """
    Creates a 160×160 empty board initialized with zeros.
    """
    return np.zeros((160, 160), dtype=np.int8)


# ======================================================
# 3. BUILD 5-LAYER RIPEMD-160 STATE STACK
# ======================================================

def build_stack():
    """
    Creates a 5-layer RM160 curvature stack (5 lanes × 160×160 grid).
    Each lane corresponds to one of RIPEMD-160's 32-bit lanes mapped across the board.
    """
    return np.zeros((5, 160, 160), dtype=np.int8)


# ======================================================
# Hamming weight calculator for hex strings
# ======================================================

def hamming_weight_hex(h):
    """
    Returns the Hamming weight (number of 1 bits)
    in a hex string.
    """
    return bin(int(h, 16)).count("1")


def delta_hamming(h1, h2):
    """
    Computes ΔH between two hex values.
    """
    b1 = bin(int(h1, 16))[2:].zfill(160)
    b2 = bin(int(h2, 16))[2:].zfill(160)
    return sum(c1 != c2 for c1, c2 in zip(b1, b2))


# ======================================================
# Map ΔH curvature field onto a 160×160 grid
# ======================================================

def project_delta_to_board(board, deltaH):
    """
    Projects a ΔH value into the center of the board
    as a radial "curvature bubble".
    """
    cx, cy = 80, 80  # center
    radius = deltaH / 2

    for x in range(160):
        for y in range(160):
            dist = np.sqrt((x - cx)**2 + (y - cy)**2)
            if dist <= radius:
                board[x, y] = 1

    return board


# ======================================================
# Project ΔH onto the full 5-lane stack
# ======================================================

def project_to_stack(stack, deltaH):
    """
    Places ΔH curvature onto all 5 layers with increasing
    intensity per layer (0 → weak, 4 → strongest).
    """
    cx, cy = 80, 80
    max_radius = deltaH / 2

    for layer in range(5):
        shrink = 1.0 - (layer * 0.12)     # slightly smaller radius each lane
        radius = max_radius * shrink

        for x in range(160):
            for y in range(160):
                dist = np.sqrt((x - cx)**2 + (y - cy)**2)
                if dist <= radius:
                    stack[layer, x, y] = 1

    return stack


# ======================================================
# Optional: ASCII visualization for quick viewing
# ======================================================

def print_board(board):
    """
    Renders the 160×160 board in ASCII (cropped for readability).
    """
    for row in board[:32]:  # print just top-left 32 rows for preview
        print("".join("█" if c else " " for c in row[:80]))


# ======================================================
# Example usage
# ======================================================

if __name__ == "__main__":

    # Your hashes here — example from earlier runs
    h1 = "8000000000000000000000000000000000000000"
    h2 = "BFD5F95500056885C53E4F884189C0A5399B4885"
    h3 = "8000000000000000000000000000000000000050"
    h4 = "DCF8629B82766F04F316EEE0530C4E253667DE8E"
    h5 = "916D0BD2B03556DF16C8413AB9466111627CD1E3"
    h6 = "10000000000000000000000000000000000000000"
    h7 = "8C9CCF5C6114A36801952B4B232B3FF8DB3320EA"
    h8 = "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAF"
    h9 = "ED9948D508CFD2FE663275EA50431082BC1520EA"
    h10 = "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F"
    h11 = "3B23BFD1F5AF9A57D93E9A7DCE1B463E3829134F"
    h12 = "B504F333F9DE6484597D89B3754ABE9F1D6F60BA"
    h13 = "85652E928DA6C4B5747E3FB1D0FCD7DBDFC1F3A0"

    # Build base structures
    board = build_board()
    stack = build_stack()

    # Compute ΔH
    ΔH = delta_hamming(h1, h2)
    print(f"ΔH = {ΔH}")

    # Project onto board and stack
    board = project_delta_to_board(board, ΔH)
    stack = project_to_stack(stack, ΔH)

    # Preview top-left region
    print_board(board)

    # Save stack for later visualization
    np.save("RM160_stack.npy", stack)
