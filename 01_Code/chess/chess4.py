import numpy as np

def build_board():
    return np.zeros((160, 160), dtype=np.int8)

def build_stack():
    return np.zeros((5, 160, 160), dtype=np.int8)

def delta_hamming(h1, h2):
    b1 = bin(int(h1, 16))[2:].zfill(160)
    b2 = bin(int(h2, 16))[2:].zfill(160)
    return sum(c1 != c2 for c1, c2 in zip(b1, b2))

def project_delta_to_board(board, deltaH):
    cx, cy = 20, 20   # <<< MOVED CENTER SO YOU CAN SEE IT
    radius = deltaH / 2

    for x in range(160):
        for y in range(160):
            if np.sqrt((x - cx)**2 + (y - cy)**2) <= radius:
                board[x, y] = 1
    return board

def project_to_stack(stack, deltaH):
    cx, cy = 20, 20   # <<< MOVED CENTER
    max_radius = deltaH / 2

    for layer in range(5):
        shrink = 1.0 - (layer * 0.12)
        radius = max_radius * shrink

        for x in range(160):
            for y in range(160):
                if np.sqrt((x - cx)**2 + (y - cy)**2) <= radius:
                    stack[layer, x, y] = 1
    return stack

def print_board(board):
    # print full 160×160 region
    for row in board:
        print("".join("█" if c else " " for c in row))

if __name__ == "__main__":
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

    board = build_board()
    stack = build_stack()

    ΔH = delta_hamming(h1, h2)
    print("ΔH =", ΔH)

    board = project_delta_to_board(board, ΔH)
    stack = project_to_stack(stack, ΔH)

    print_board(board)

    np.save("RM160_stack.npy", stack)
