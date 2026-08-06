#!/usr/bin/env python3
# ------------------------------------------------
# TDAD with:
# - stride-5 bridges
# - max reuse = 8
# - NO self reference allowed
# ------------------------------------------------

from collections import defaultdict

# -------------------------------
# Puzzle values
# -------------------------------
PUZZLES = {
    1: 1, 2: 3, 3: 7, 4: 8, 5: 21, 6: 49, 7: 76, 8: 224, 9: 467, 10: 514,
    11: 1155, 12: 2683, 13: 5216, 14: 10544, 15: 26867, 16: 51510,
    17: 95823, 18: 198669, 19: 357535, 20: 863317, 21: 1811764,
    22: 3007503, 23: 5598802, 24: 14428676, 25: 33185509,
    26: 54538862, 27: 111949941, 28: 227634408, 29: 400708894,
    30: 1033162084, 31: 2102388551, 32: 3093472814,
    33: 7137437912, 34: 14133072157, 35: 20112871792,
    36: 42387769980, 37: 100251560595, 38: 146971536592,
    39: 323724968937, 40: 1003651412950,
    41: 1458252205147, 42: 2895374552463,
    43: 7409811047825, 44: 15404761757071,
    45: 19996463086597, 46: 51408670348612,
    47: 119666659114170, 48: 191206974700443,
    49: 409118905032525, 50: 611140496167764,
    51: 2058769515153876, 52: 4216495639600700,
    53: 6763683971478124, 54: 9974455244496707,
    55: 30045390491869460, 56: 44218742292676575,
    57: 138245758910846492, 58: 199976667976342049,
    59: 525070384258266191, 60: 1135041350219496382,
    61: 1425787542618654982, 62: 3908372542507822062,
    63: 8993229949524469768, 64: 17799667357578236628,
    65: 30568377312064202855, 66: 46346217550346335726,
    67: 132656943602386256302, 68: 219898266213316039825,
    69: 297274491920375905804, 70: 970436974005023690481,
    75: 22538323240989823823367,
    80: 1105520030589234487939456,
    85: 21090315766411506144426920,
    90: 868012190417726402719548863,
    95: 25525831956644113617013748212,
    100: 868221233689326498340379183142,
    105: 29083230144918045706788529192435,
    110: 1090246098153987172547740458951748,
    115: 31464123230573852164273674364426950,
    120: 919343500840980333540511050618764323,
    125: 37650549717742544505774009877315221420,
    130: 1103873984953507439627945351144005829577
}

MAX_REUSE = 8
MAX_STEPS = 20000

# -------------------------------
# Build basis EXCLUDING self
# -------------------------------
def build_basis(target_index):
    basis = {}

    # Other puzzles
    for k, v in PUZZLES.items():
        if k != target_index:
            basis[f"P{k}"] = v

    # Stride-5 bridges (excluding self)
    for k in PUZZLES:
        if k - 5 in PUZZLES and k != target_index:
            bridge = PUZZLES[k] - PUZZLES[k - 5]
            if bridge > 0:
                basis[f"B{k}"] = bridge

    return basis

# -------------------------------
# TDAD decomposition
# -------------------------------
def tdad_decompose(target_index):
    target = PUZZLES[target_index]
    basis = build_basis(target_index)
    sorted_basis = sorted(basis.items(), key=lambda x: x[1], reverse=True)

    remainder = target
    terms = defaultdict(int)
    steps = 0

    while remainder > 0 and steps < MAX_STEPS:
        progressed = False

        for key, val in sorted_basis:
            if val <= remainder and terms[key] < MAX_REUSE:
                remainder -= val
                terms[key] += 1
                progressed = True
                break

        if not progressed:
            raise RuntimeError(
                f"TDAD stalled — remainder {remainder} cannot be decomposed."
            )

        steps += 1

    if remainder != 0:
        raise RuntimeError("TDAD failed to converge")

    return dict(terms)

# -------------------------------
# Verify
# -------------------------------
def verify(target_index, terms):
    basis = build_basis(target_index)
    total = sum(basis[k] * c for k, c in terms.items())
    return total == PUZZLES[target_index]

# -------------------------------
# Pretty print
# -------------------------------
def pretty_print(terms):
    return " + ".join(f"{c}({k})" for k, c in sorted(terms.items()))

# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    TESTS = [50, 70, 75, 65, 55, 60]

    for idx in TESTS:
        print("=" * 80)
        print(f"Puzzle {idx} = {PUZZLES[idx]}")

        terms = tdad_decompose(idx)
        print("TDAD terms:")
        print(pretty_print(terms))

        print("Verified:", verify(idx, terms))
