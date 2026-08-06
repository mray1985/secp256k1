#!/usr/bin/env python3
"""Generate puzzle D/A depletion chains P1..P70 — each row sums exactly to P(n)."""

from __future__ import annotations

import re
from dataclasses import dataclass

PUZZLE: dict[int, int] = {
    1: 1,
    2: 3,
    3: 7,
    4: 8,
    5: 21,
    6: 49,
    7: 76,
    8: 224,
    9: 467,
    10: 514,
    11: 1155,
    12: 2683,
    13: 5216,
    14: 10544,
    15: 26867,
    16: 51510,
    17: 95823,
    18: 198669,
    19: 357535,
    20: 863317,
    21: 1811764,
    22: 3007503,
    23: 5598802,
    24: 14428676,
    25: 33185509,
    26: 54538862,
    27: 111949941,
    28: 227634408,
    29: 400708894,
    30: 1033162084,
    31: 2102388551,
    32: 3093472814,
    33: 7137437912,
    34: 14133072157,
    35: 20112871792,
    36: 42387769980,
    37: 100251560595,
    38: 146971536592,
    39: 323724968937,
    40: 1003651412950,
    41: 1458252205147,
    42: 2895374552463,
    43: 7409811047825,
    44: 15404761757071,
    45: 19996463086597,
    46: 51408670348612,
    47: 119666659114170,
    48: 191206974700443,
    49: 409118905032525,
    50: 611140496167764,
    51: 2058769515153876,
    52: 4216495639600700,
    53: 6763683971478124,
    54: 9974455244496707,
    55: 30045390491869460,
    56: 44218742292676575,
    57: 138245758910846492,
    58: 199976667976342049,
    59: 525070384258266191,
    60: 1135041350219496382,
    61: 1425787542618654982,
    62: 3908372542507822062,
    63: 8993229949524469768,
    64: 17799667357578236628,
    65: 30568377312064202855,
    66: 46346217550346335726,
    67: 132656943602386256302,
    68: 219898266213316039825,
    69: 297274491920375905804,
    70: 970436974005023690481,
}

# User-trusted reference chains (P1-P37 from intake; P29 anchor for extension)
USER_DA: dict[int, str] = {
    1: "A(1)",
    2: "D(1)A(1)",
    3: "D(2)A(1)",
    4: "D(1)A(1)D(1)A(1)D(1)",
    5: "A(2)D(2)A(2)D(2)A(1)D(1)",
    6: "A(3)D(3)A(3)D(3)A(3)",
    7: "D(4)A(4)D(4)A(4)D(4)A(2)D(2)A(1)D(1)",
    8: "A(5)D(5)A(5)D(5)A(5)D(5)A(5)D(3)",
    9: "A(6)D(6)A(6)D(6)A(6)D(5)A(5)D(5)A(4)D(2)A(2)D(1)",
    10: "A(7)D(7)A(7)D(7)A(6)D(2)A(2)",
    11: "D(8)A(8)D(8)A(5)D(3)",
    12: "A(9)D(9)A(9)D(8)A(8)D(6)A(5)D(4)A(4)",
    13: "D(10)A(10)D(10)A(10)D(10)A(10)D(8)A(7)D(5)A(5)D(1)A(1)",
    14: "D(11)A(11)D(11)A(11)D(11)A(11)D(6)A(6)D(1)",
    15: "A(12)D(12)A(12)D(12)A(12)D(12)A(12)D(4)A(3)D(3)",
    16: "A(13)D(13)A(13)D(13)A(13)D(13)A(12)D(10)A(8)D(8)A(7)D(6)A(2)D(2)",
    17: "A(14)D(14)A(14)D(14)A(14)D(14)A(9)D(8)A(2)D(2)A(1)D(1)",
    18: "A(15)D(15)A(15)D(15)A(14)D(14)A(11)D(11)A(10)D(10)A(8)D(8)A(6)D(6)A(2)D(2)",
    19: "A(16)D(16)A(16)D(16)A(14)D(14)A(13)D(13)A(10)D(8)A(8)D(2)A(2)",
    20: "D(17)A(17)D(17)A(17)D(17)A(17)D(8)A(8)D(6)A(6)D(5)A(5)D(3)A(3)D(2)A(1)",
    21: "A(18)D(18)A(18)D(18)A(18)D(18)A(14)D(13)A(12)D(5)A(5)D(3)A(3)",
    22: "D(19)A(19)D(19)A(19)D(19)A(16)D(15)A(15)D(13)A(12)D(10)A(10)D(8)A(3)",
    23: "D(20)A(20)D(20)A(20)D(18)A(14)D(13)A(9)D(6)A(5)",
    24: "D(21)A(21)D(21)A(21)D(20)A(20)D(19)A(18)D(15)A(10)D(6)A(6)D(2)A(1)",
    25: "D(22)A(22)D(22)A(22)D(22)A(22)D(22)A(17)D(12)A(11)D(8)A(7)D(6)A(4)D(1)",
    26: "A(23)D(23)A(23)D(23)A(23)D(23)A(22)D(19)A(19)D(15)A(13)D(13)A(6)D(6)A(3)",
    27: "D(24)A(24)D(24)A(24)D(23)A(23)D(22)A(21)D(19)A(15)D(13)A(11)D(10)A(6)D(6)A(3)D(1)A(1)",
    28: "D(25)A(25)D(25)A(25)D(23)A(23)D(22)A(22)D(20)A(20)D(16)A(12)D(12)A(9)D(9)A(3)D(2)A(2)D(1)",
    29: "A(26)D(26)A(26)D(26)A(26)D(23)A(23)D(19)A(19)D(18)A(18)D(17)A(17)D(16)A(16)D(13)A(13)D(12)A(12)D(11)A(11)D(10)A(10)D(8)A(8)D(7)A(7)D(6)A(6)D(5)A(5)D(4)A(3)D(2)",
}


@dataclass(frozen=True)
class Tok:
    op: str  # 'A' or 'D'
    k: int


def parse_da(s: str) -> list[Tok]:
    return [Tok(t, int(k)) for t, k in re.findall(r"([DA])\((\d+)\)", s)]


def format_da(tokens: list[Tok]) -> str:
    return "".join(f"{t.op}({t.k})" for t in tokens)


def eval_tokens(tokens: list[Tok]) -> int:
    return sum((2 if t.op == "D" else 1) * PUZZLE[t.k] for t in tokens)


def oppose(op: str) -> str:
    return "A" if op == "D" else "D"


def block_at_k(q: int, start_op: str, k: int) -> list[Tok]:
    seq: list[Tok] = []
    rem = q
    op = start_op
    while rem > 0:
        if op == "D" and rem >= 2:
            seq.append(Tok("D", k))
            rem -= 2
            op = "A"
        elif op == "A" and rem >= 1:
            seq.append(Tok("A", k))
            rem -= 1
            op = "D"
        else:
            break
    return seq


def decompose_tail(
    rem: int,
    max_k: int,
    start_op: str,
    cache: dict[tuple[int, int, str], list[Tok] | None],
) -> list[Tok] | None:
    if rem == 0:
        return []
    key = (rem, max_k, start_op)
    if key in cache:
        return cache[key]

    best: list[Tok] | None = None
    # Prefer larger puzzle indices first (matches user tails)
    for k in range(max_k, 0, -1):
        pk = PUZZLE[k]
        if start_op == "D" and rem >= 2 * pk:
            sub = decompose_tail(rem - 2 * pk, k, oppose("D"), cache)
            if sub is not None:
                cand = [Tok("D", k)] + sub
                best = cand
                break
        if start_op == "A" and rem >= pk:
            sub = decompose_tail(rem - pk, k, oppose("A"), cache)
            if sub is not None:
                cand = [Tok("A", k)] + sub
                best = cand
                break

    cache[key] = best
    return best


def build_chain(n: int, prev_end: str) -> list[Tok] | None:
    if n < 4:
        return parse_da(USER_DA[n])
    start_k = n - 3
    q = PUZZLE[n] // PUZZLE[start_k]
    head = block_at_k(q, oppose(prev_end), start_k)
    head_val = eval_tokens(head)
    rem = PUZZLE[n] - head_val
    if rem < 0:
        return None
    tail_start = oppose(head[-1].op) if head else oppose(prev_end)
    tail = decompose_tail(rem, start_k - 1, tail_start, {})
    if tail is None:
        return None
    return head + tail


def verify_row(n: int, s: str) -> tuple[bool, int]:
    v = eval_tokens(parse_da(s))
    return v == PUZZLE[n], v - PUZZLE[n]


def alt_breaks(chains: dict[int, str], lo: int, hi: int) -> list[tuple[int, str, str]]:
    out: list[tuple[int, str, str]] = []
    for n in range(lo, hi):
        end = parse_da(chains[n])[-1].op
        start = parse_da(chains[n + 1])[0].op
        if end == start:
            out.append((n, end, start))
    return out


def main() -> None:
    # Anchor P1-P20 (last good row before P20->P21 A/A glitch in hand-built chain)
    chains: dict[int, str] = {n: USER_DA[n] for n in range(1, 21)}

    print("=== Anchor P1-P20 ===")
    bad_ref = [n for n in range(1, 21) if not verify_row(n, chains[n])[0]]
    print("bad sums:", bad_ref if bad_ref else "none")
    br = alt_breaks(chains, 1, 20)
    print("alt breaks in anchor:", br if br else "none")

    # Regenerate P21-P70 from P20 end (A -> P21 must start D)
    prev_end = parse_da(chains[20])[-1].op
    failed: list[int] = []
    for n in range(21, 71):
        toks = build_chain(n, prev_end)
        if toks is None:
            failed.append(n)
            continue
        s = format_da(toks)
        ok, delta = verify_row(n, s)
        if not ok:
            failed.append(n)
            print(f"P{n} FAIL delta={delta}")
        chains[n] = s
        prev_end = toks[-1].op

    print("failed:", failed if failed else "none")
    br_all = alt_breaks(chains, 1, 70)
    print("alt breaks P1-P70:", br_all if br_all else "NONE")
    print()

    out_txt = __file__.replace(".py", "_P1_P70.txt")
    out_md = __file__.replace(".py", "_P1_P70.md")
    lines = []
    for n in range(1, 71):
        s = chains[n]
        ok, delta = verify_row(n, s)
        first = parse_da(s)[0]
        last = parse_da(s)[-1]
        floor_q = (2 ** (n - 1)) // PUZZLE[n - 3] if n >= 4 else 0
        height_q = (2**n - 1) // PUZZLE[n - 3] if n >= 4 else 0
        q = PUZZLE[n] // PUZZLE[n - 3] if n >= 4 else 0
        lines.append(
            f"P{n:02d} = {PUZZLE[n]}\n"
            f"  q={q}  floor={floor_q}  height={height_q}  start={first.op}({first.k})  end={last.op}({last.k})  rem={delta}\n"
            f"  {s}\n"
        )

    text = "\n".join(lines)
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(text)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Puzzle D/A depletion P1–P70\n\n```\n" + text + "\n```\n")

    print(f"Wrote {out_txt}")
    print()
    print("=== P20-P25 (regen from P21) ===")
    for n in range(20, 26):
        block = "".join(lines[(n - 1) * 3 : n * 3])
        print(block)


if __name__ == "__main__":
    main()
