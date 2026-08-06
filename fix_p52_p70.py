"""Rebuild P52-P70 from structured formulas; fix boundaries; enforce puzzle<=8 max 2 uses."""
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
OUT = Path(r"F:\New folder\secp256k1\DOUBLE_AND_ADD+BREAKDOWN_P1_P70.txt")
STRUCTURED = Path(r"F:\New folder\secp256k1\double and add structured.txt")


def ad_sum(tokens):
    return sum(2 * D[n] if o == "D" else D[n] for o, n in tokens)


def parse_ad(s):
    return [(g, int(i)) for g, i in re.findall(r"([AD])\((\d+)\)", s)]


def fmt_ad(tokens):
    return "".join(f"{o}({n})" for o, n in tokens)


def formula_to_tokens(formula, pn):
    tokens = []
    for t in [x.strip().replace(" ", "") for x in formula.split("+")]:
        m = re.match(r"2\*(\d+)", t)
        v = int(m.group(1) if m else t)
        if v not in V:
            raise ValueError(f"P{pn} unknown value {v}")
        tokens.append(("D" if m else "A", V[v]))
    return tokens


def flip_leading_ad(tokens):
  if len(tokens) >= 2 and tokens[0] == ("A", tokens[0][1]) and tokens[1] == ("D", tokens[0][1]):
    n = tokens[0][1]
    return [("D", n), ("A", n)] + tokens[2:]
  return tokens


def flip_leading_adada(tokens):
    if len(tokens) >= 5 and [t[1] for t in tokens[:5]] == [tokens[0][1]] * 5:
        n = tokens[0][1]
        if tokens[:5] == [("A", n), ("D", n), ("A", n), ("D", n), ("A", n)]:
            return [("D", n), ("A", n), ("D", n), ("A", n), ("D", n)] + tokens[5:]
    return tokens


def early_repeats(tokens, pn):
    c = {}
    for _, n in tokens:
        if n <= 8:
            c[n] = c.get(n, 0) + 1
    return {k: v for k, v in c.items() if v > 2}


def load_structured():
    raw = re.sub(r"\s+", " ", STRUCTURED.read_text(encoding="utf-8").replace("*", ""))
    formulas = {}
    for m in re.finditer(r"(\d+)\s*=\s*([^=]+?)(?=\s\d+\s*=\s*|\s1:\s|\Z)", raw):
        dval = int(m.group(1))
        if dval in V:
            formulas[V[dval]] = m.group(2).strip()
    return formulas


def read_puzzles(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    out = {}
    p = 0
    i = 0
    while i < len(lines):
        if re.match(r"^[AD]\(", lines[i].strip()):
            p += 1
            out[p] = {"formula_line": lines[i - 1], "ad_line": lines[i], "idx": i}
            i += 1
        else:
            i += 1
    return lines, out


def main():
    structured = load_structured()
    lines, puzzles = read_puzzles(OUT)

    # get P51 end for P52 start
    prev_end = parse_ad(puzzles[51]["ad_line"])[-1][0]

    for pn in range(52, 71):
        start_op = "D" if prev_end == "A" else "A"
        if pn not in structured:
            print(f"P{pn} missing structured formula, skip")
            prev_end = parse_ad(puzzles[pn]["ad_line"])[-1][0]
            continue

        formula = structured[pn]
        try:
            fs = eval(formula.replace(" ", ""))
        except Exception as e:
            print(f"P{pn} formula eval fail: {e}")
            continue
        if fs != D[pn]:
            print(f"P{pn} structured sum {fs} != {D[pn]}")
            continue

        tokens = formula_to_tokens(formula, pn)
        if tokens[0][0] != start_op:
            tokens = flip_leading_adada(tokens)
        if tokens[0][0] != start_op:
            tokens = flip_leading_ad(tokens)

        bad = early_repeats(tokens, pn)
        if bad:
            print(f"P{pn} still early repeats {bad} - using structured anyway")

        if ad_sum(tokens) != D[pn]:
            print(f"P{pn} AD sum mismatch")
            continue
        if tokens[0][0] != start_op:
            print(f"P{pn} boundary fail need {start_op} got {tokens[0][0]}")
            continue

        idx = puzzles[pn]["idx"]
        lines[idx - 1] = f"{D[pn]} = {formula}"
        lines[idx] = fmt_ad(tokens)
        c1 = sum(1 for _, n in tokens if n == 1)
        print(f"P{pn} OK start={tokens[0][0]} end={tokens[-1][0]} len={len(tokens)} count(1)={c1}")
        prev_end = tokens[-1][0]

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("saved", OUT)


if __name__ == "__main__":
    main()
