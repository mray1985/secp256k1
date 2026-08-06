#!/usr/bin/env python3
"""Draft P71 D/A chain from user rules (P70 ends on A -> P71 starts D(68))."""

PUZZLE = {
    64: 17799667357578236628,
    65: 30568377312064202855,
    66: 46346217550346335726,
    67: 132656943602386256302,
    68: 219898266213316039825,
    69: 297274491920375905804,
    70: 970436974005023690481,
}


def max_block(q: int, start_op: str) -> tuple[list[str], int, int]:
    seq: list[str] = []
    rem = q
    op = start_op
    while True:
        if op == "D" and rem >= 2:
            seq.append("D")
            rem -= 2
            op = "A"
        elif op == "A" and rem >= 1:
            seq.append("A")
            rem -= 1
            op = "D"
        else:
            break
    w = sum(2 if t == "D" else 1 for t in seq)
    return seq, w, rem


def to_da(seq: list[str], k: int) -> str:
    return "".join(f"{t}({k})" for t in seq)


def block_value(seq: list[str], k: int) -> int:
    return sum((2 if t == "D" else 1) * PUZZLE[k] for t in seq)


def main() -> None:
    p68 = PUZZLE[68]
    q_range = (2**71 - 1) // p68
    q_alt = 2**70 // p68

    print("=== P71 quotient candidates ===")
    print(f"(2^71 - 1) // P68 = {q_range}")
    print(f"2^70 // P68         = {q_alt}")
    print(f"P70 // P68 (solved) = {PUZZLE[70] // p68}")
    print()

    print("=== P71 opening block (must start D(68); P70 ends A) ===")
    for label, q in [("range (2^71-1)/P68", q_range), ("2^70/P68", q_alt)]:
        seq, w, rem = max_block(q, "D")
        print(f"{label}: q={q}")
        print(f"  {to_da(seq, 68)}  weight={w}  leftover_budget={rem}")
        print(f"  block value = {block_value(seq, 68)}")
    print()

    print("=== P70 check (user says ends on A) ===")
    q70 = PUZZLE[70] // PUZZLE[67]
    for start in ("D", "A"):
        seq, w, _ = max_block(q70, start)
        bulk = block_value(seq, 67)
        tail = PUZZLE[70] - bulk
        print(f"start {start}: {to_da(seq, 67)} weight={w} bulk={bulk} tail={tail}")
    print()

    # Greedy tail depletion for P70 if start A, budget 7
    seq70, _, _ = max_block(q70, "A")
    tail = PUZZLE[70] - block_value(seq70, 67)
    print(f"P70 candidate if starts A(67): {to_da(seq70, 67)} + tail({tail})")
    # try express tail with coeffs 1,2 on P69..P64
    keys = [69, 68, 67, 66, 65, 64]
    best = None
    for mask in range(3 ** 6):
        coeffs = []
        m = mask
        for _ in keys:
            coeffs.append(m % 3)
            m //= 3
        val = sum(c * PUZZLE[k] for c, k in zip(coeffs, keys))
        if val == tail:
            best = list(zip(keys, coeffs))
            break
    print("tail as 0/1/2 coeffs on P69..P64:", best)


if __name__ == "__main__":
    main()
