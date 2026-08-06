#!/usr/bin/env python3
"""Puzzle 71 multiplier area: floor = 2^(n-1)//P(n-3), height = (2^n-1)//P(n-3)."""

PUZZLE = {
    67: 132656943602386256302,
    68: 219898266213316039825,
    69: 297274491920375905804,
    70: 970436974005023690481,
}


def max_block(q: int, start_op: str) -> tuple[list[str], int]:
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
    return seq, w


def to_da(seq: list[str], k: int) -> str:
    return "".join(f"{t}({k})" for t in seq)


def block_value(seq: list[str], k: int) -> int:
    return sum((2 if t == "D" else 1) * PUZZLE[k] for t in seq)


def multiplier_area(n: int) -> tuple[int, int, int]:
    start = n - 3
    p_start = PUZZLE[start]
    floor_q = (2 ** (n - 1)) // p_start
    height_q = (2**n - 1) // p_start
    return start, floor_q, height_q


def main() -> None:
    n = 71
    start, floor_q, height_q = multiplier_area(n)
    p_start = PUZZLE[start]

    print(f"Puzzle {n}: start puzzle {start}, P{start} = {p_start}")
    print()
    print("Multiplier area (weight budget bracket for opening block):")
    print(f"  floor  = 2^{n-1} // P{start} = {floor_q}")
    print(f"  height = (2^{n} - 1) // P{start} = {height_q}")
    print(f"  span   = {height_q - floor_q} (q can be floor..height inclusive)")
    print()
    print("Value bracket for q * P{0} bulk:".format(start))
    print(f"  floor bulk  = {floor_q * p_start}  (>= 2^{n-1}? {floor_q * p_start >= 2**(n-1)})")
    print(f"  height bulk = {height_q * p_start}  (<= 2^{n}-1? {height_q * p_start <= 2**n - 1})")
    print()

    # Calibrate on solved P70
    s70, f70, h70 = multiplier_area(70)
    q70_actual = PUZZLE[70] // PUZZLE[s70]
    print("=== Calibration P70 (solved) ===")
    print(f"  floor={f70}  height={h70}  actual P70//P67={q70_actual}")
    print(f"  actual in [floor,height]? {f70 <= q70_actual <= h70}")
    print()

    # P71 opens D(68) because P70 ends A (user)
    print("=== P71 opening blocks (start D(68), P70 ended A) ===")
    for label, q in [("floor", floor_q), ("height", height_q)]:
        seq, w = max_block(q, "D")
        print(f"  {label} q={q}: {to_da(seq, start)}  weight={w}  value={block_value(seq, start)}")

    print()
    print("=== P71 opening if started A(68) (wrong if P70 ends A) ===")
    for label, q in [("floor", floor_q), ("height", height_q)]:
        seq, w = max_block(q, "A")
        print(f"  {label} q={q}: {to_da(seq, start)}  weight={w}")


if __name__ == "__main__":
    main()
