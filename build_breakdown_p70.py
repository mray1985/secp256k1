"""P1-P70 breakdown: keep user P1-31, shortest subtract paths for the rest."""
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
D_TO_N = {v: n for n, v in D.items()}

P22_FORMULA = "357535 + 2*357535 + 357535 + 2*357535 + 357535 + 2*198669 + 95823 + 2*5216 + 1155 + 2*3 + 1 + 2*1 + 1"
P22_AD = "A(19)D(19)A(19)D(19)A(19)D(18)A(17)D(13)A(11)D(2)A(1)D(1)A(1)"


def ad_sum(tokens):
    return sum(2 * D[n] if o == "D" else D[n] for o, n in tokens)


def parse_ad(s):
    return [(g, int(i)) for g, i in re.findall(r"([AD])\((\d+)\)", s)]


def fmt_ad(tokens):
    return "".join(f"{o}({n})" for o, n in tokens)


def formula_from_tokens(tokens):
    return " + ".join(f"2*{D[n]}" if o == "D" else str(D[n]) for o, n in tokens)


def valid_tokens(tokens, target, start_op):
    if not tokens or tokens[0][0] != start_op:
        return False
    if any(tokens[i][0] == tokens[i + 1][0] for i in range(len(tokens) - 1)):
        return False
    return ad_sum(tokens) == target


def subtract_path(target, start_op, max_n, max_steps=400):
    """Fast calculator method: largest fitting subtract each step."""

    def go(rem, op, path):
        if rem == 0:
            return path
        if rem < 0 or len(path) > max_steps:
            return None
        for n in range(min(max_n, 70), 0, -1):
            sub = 2 * D[n] if op == "D" else D[n]
            if sub <= rem:
                r = go(rem - sub, "A" if op == "D" else "D", path + [(op, n)])
                if r:
                    return r
        return None

    return go(target, start_op, [])


def read_copy_by_dvalue(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    out = {}
    i = 0
    while i < len(lines):
        m = re.match(r"^(\d+)\s*=\s*(.+)$", lines[i].strip())
        if m and int(m.group(1)) in D_TO_N:
            n = D_TO_N[int(m.group(1))]
            formula = m.group(2).strip()
            ad = lines[i + 1].strip() if i + 1 < len(lines) and re.match(r"^[AD]\(", lines[i + 1]) else None
            out[n] = {"formula": formula, "ad": ad}
            i += 2 if ad else 1
            continue
        i += 1
    return out


def main():
    copy = read_copy_by_dvalue(r"F:\New folder\secp256k1\DOUBLE_AND_ADD+BREAKDOWN_P22fix.txt")
    out_path = Path(r"F:\New folder\secp256k1\DOUBLE_AND_ADD+BREAKDOWN_P1_P70.txt")

    results = {}
    formulas_out = {}
    prev_end = None
    notes = []

    for n in range(1, 71):
        target = D[n]
        start_op = "A" if n == 1 else ("D" if prev_end == "A" else "A")
        tokens = None

        if n == 22:
            tokens = parse_ad(P22_AD)
        elif n <= 31 and n in copy and copy[n]["ad"]:
            t = parse_ad(copy[n]["ad"])
            if valid_tokens(t, target, start_op):
                tokens = t

        if tokens is None:
            tokens = subtract_path(target, start_op, n - 1)
            notes.append(f"P{n} generated ({len(tokens)} tok)")

        if not tokens or not valid_tokens(tokens, target, start_op):
            raise SystemExit(f"FAILED P{n}")

        results[n] = tokens
        formulas_out[n] = formula_from_tokens(tokens)
        prev_end = tokens[-1][0]

    lines = []
    for n in range(1, 71):
        lines.append(f"{D[n]} = {formulas_out[n]}")
        lines.append(fmt_ad(results[n]))
        lines.append("")

    lines.extend([
        "1: 1, 2: 3, 3: 7, 4: 8, 5: 21, 6: 49, 7: 76, 8: 224, 9: 467, 10: 514,",
        "    11: 1155, 12: 2683, 13: 5216, 14: 10544, 15: 26867, 16: 51510, 17: 95823,",
        "    18: 198669, 19: 357535, 20: 863317, 21: 1811764, 22: 3007503, 23: 5598802,",
        "    24: 14428676, 25: 33185509, 26: 54538862, 27: 111949941, 28: 227634408,",
        "    29: 400708894, 30: 1033162084, 31: 2102388551, 32: 3093472814,",
        "    33: 7137437912, 34: 14133072157, 35: 20112871792, 36: 42387769980,",
        "    37: 100251560595, 38: 146971536592, 39: 323724968937, 40: 1003651412950,",
        "    41: 1458252205147, 42: 2895374552463, 43: 7409811047825, 44: 15404761757071, 45: 19996463086597, 46: 51408670348612, 47: 119666659114170,",
        "    48: 191206974700443, 49: 409118905032525, 50: 611140496167764,",
        "    51: 2058769515153876, 52: 4216495639600700, 53: 6763683971478124,",
        "    54: 9974455244496707, 55: 30045390491869460, 56: 44218742292676575,",
        "    57: 138245758910846492, 58: 199976667976342049, 59: 525070384258266191,",
        "    60: 1135041350219496382, 61: 1425787542618654982, 62: 3908372542507822062,",
        "    63: 8993229949524469768, 64: 17799667357578236628, 65: 30568377312064202855,",
        "    66: 46346217550346335726, 67: 132656943602386256302, 68: 219898266213316039825,",
        "    69: 297274491920375905804, 70: 970436974005023690481,",
    ])
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote", out_path)
    for note in notes:
        print(note)
    lens = [len(results[n]) for n in range(32, 71)]
    print(f"P32-P70 token range: {min(lens)}-{max(lens)}, total {sum(lens)}")


if __name__ == "__main__":
    main()
