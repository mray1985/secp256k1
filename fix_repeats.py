"""Apply structured-formula AD where possible; fix P22 tail; no puzzle-1 repeats in P9+."""
import re
from pathlib import Path

D = {
    1: 1, 2: 3, 3: 7, 4: 8, 5: 21, 6: 49, 7: 76, 8: 224, 9: 467, 10: 514,
    11: 1155, 12: 2683, 13: 5216, 14: 10544, 15: 26867, 16: 51510, 17: 95823,
    18: 198669, 19: 357535, 20: 863317, 21: 1811764, 22: 3007503, 23: 5598802,
    24: 14428676, 25: 33185509, 26: 54538862, 27: 111949941, 28: 227634408,
    29: 400708894, 30: 1033162084, 31: 2102388551, 32: 3093472814,
    33: 7137437912, 34: 14133072157, 35: 20112871792, 36: 42387769980,
    37: 100251560595, 38: 146971536592, 39: 323724968937, 40: 1003651412950,
    41: 1458252205147, 42: 2895374552463, 43: 7409811047825, 44: 15404761757071,
    45: 19996463086597, 46: 51408670348612, 47: 119666659114170,
    48: 191206974700443, 49: 409118905032525, 50: 611140496167764,
    51: 2058769515153876, 52: 4216495639600700, 53: 6763683971478124,
    54: 9974455244496707, 55: 30045390491869460, 56: 44218742292676575,
    57: 138245758910846492, 58: 199976667976342049, 59: 525070384258266191,
    60: 1135041350219496382, 61: 1425787542618654982, 62: 3908372542507822062,
    63: 8993229949524469768, 64: 17799667357578236628, 65: 30568377312064202855,
    66: 46346217550346335726, 67: 132656943602386256302, 68: 219898266213316039825,
    69: 297274491920375905804, 70: 970436974005023690481,
}
V = {v: n for n, v in D.items()}

P22_AD = "A(19)D(19)A(19)D(19)A(19)D(18)A(17)D(13)A(11)D(1)A(4)"
P22_FORMULA = "357535 + 2*357535 + 357535 + 2*357535 + 357535 + 2*198669 + 95823 + 2*5216 + 1155 + 2*1 + 8"

STRUCTURED = Path(r"F:\New folder\secp256k1\double and add structured.txt")
OUT = Path(r"F:\New folder\secp256k1\DOUBLE_AND_ADD+BREAKDOWN_P1_P70.txt")


def ad_sum(tokens):
    return sum(2 * D[n] if o == "D" else D[n] for o, n in tokens)


def parse_ad(s):
    return [(g, int(i)) for g, i in re.findall(r"([AD])\((\d+)\)", s)]


def fmt_ad(tokens):
    return "".join(f"{o}({n})" for o, n in tokens)


def formula_from_tokens(tokens):
    return " + ".join(f"2*{D[n]}" if o == "D" else str(D[n]) for o, n in tokens)


def load_structured_formulas():
    raw = STRUCTURED.read_text(encoding="utf-8")
    raw = re.sub(r"\s+", " ", raw)
    formulas = {}
    for m in re.finditer(r"(\d+)\s*=\s*([^=]+?)(?=\s\d+\s*=\s*|\s1:\s|\Z)", raw):
        dval = int(m.group(1))
        if dval in V:
            formulas[V[dval]] = m.group(2).strip()
    return formulas


def formula_to_tokens(formula, pn):
    tokens = []
    for t in [x.strip().replace(" ", "") for x in formula.split("+")]:
        m = re.match(r"2\*(\d+)", t)
        v = int(m.group(1) if m else t)
        if v not in V:
            raise ValueError(f"P{pn} unknown {v}")
        tokens.append(("D" if m else "A", V[v]))
    return tokens


def flip_leading_block(tokens):
    """Swap leading A(n)D(n) to D(n)A(n) when present."""
    if len(tokens) >= 2 and tokens[0][0] == "A" and tokens[1] == ("D", tokens[0][1]):
        return [("D", tokens[0][1]), ("A", tokens[0][1])] + tokens[2:]
    return tokens


def illegal_small_repeats(tokens, pn):
    """Puzzle indices 1-8 may repeat only in puzzles 1-8 (early pattern)."""
    counts = {}
    for _, n in tokens:
        counts[n] = counts.get(n, 0) + 1
    bad = {}
    for n, c in counts.items():
        if n <= 8 and pn > 8 and c > 1:
            bad[n] = c
    return bad


def dfs_tail(rem, op, used, end_op, max_n, depth=0):
    if rem == 0:
        return []
    if rem < 0 or depth > 30:
        return None
    for n in range(min(max_n, 70), 0, -1):
        if n in used:
            continue
        sub = 2 * D[n] if op == "D" else D[n]
        if sub > rem:
            continue
        tail = dfs_tail(rem - sub, "A" if op == "D" else "D", used | {n}, end_op, max_n, depth + 1)
        if tail is not None:
            return [(op, n)] + tail
    return None


def main():
    structured = load_structured_formulas()
    lines = OUT.read_text(encoding="utf-8").splitlines()
    puzzle = 0
    prev_end = None
    i = 0
    while i < len(lines):
        if re.match(r"^[AD]\(", lines[i].strip()):
            puzzle += 1
            start_op = "A" if puzzle == 1 else ("D" if prev_end == "A" else "A")

            if puzzle == 22:
                tokens = parse_ad(P22_AD)
                formula = P22_FORMULA
            elif puzzle in (52, 56, 57, 63) and puzzle in structured:
                tokens = formula_to_tokens(structured[puzzle], puzzle)
                if tokens[0][0] != start_op:
                    tokens = flip_leading_block(tokens)
                    if tokens[0][0] != start_op and len(tokens) >= 4 and tokens[0][1] == tokens[2][1]:
                        # flip ADADA-style opening
                        n = tokens[0][1]
                        if tokens[:5] == [("A", n), ("D", n), ("A", n), ("D", n), ("A", n)]:
                            tokens = [("D", n), ("A", n), ("D", n), ("A", n), ("D", n)] + tokens[5:]
                formula = structured[puzzle]
                bad = illegal_small_repeats(tokens, puzzle)
                if bad or ad_sum(tokens) != D[puzzle] or tokens[0][0] != start_op:
                    raise SystemExit(f"P{puzzle} structured failed bad={bad} start={tokens[0][0]} need={start_op}")
            else:
                i += 1
                prev_end = parse_ad(lines[i - 1])[-1][0]
                continue

            if ad_sum(tokens) != D[puzzle]:
                raise SystemExit(f"P{puzzle} sum fail")
            if tokens[0][0] != start_op:
                raise SystemExit(f"P{puzzle} boundary start fail")
            bad = illegal_small_repeats(tokens, puzzle)
            if bad:
                raise SystemExit(f"P{puzzle} small repeat {bad}")

            lines[i - 1] = f"{D[puzzle]} = {formula}"
            lines[i] = fmt_ad(tokens)
            prev_end = tokens[-1][0]
            print(f"P{puzzle} fixed len={len(tokens)} end={prev_end} small_repeats={bad}")
            i += 1
            continue
        i += 1

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("saved", OUT)


if __name__ == "__main__":
    main()
