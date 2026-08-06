from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# ----------------------------
# Input: your known puzzle values
# ----------------------------
PUZZLES: Dict[int, int] = {
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

# TDAD repeating multipliers: Triple, Double, Add, Double
TDAD = [3, 2, 1, 2]

@dataclass
class Term:
    coeff: int
    idx: int
    val: int

def tdad_decompose(
    target_idx: int,
    puzzles: Dict[int, int],
    pattern: List[int] = TDAD,
    start_from: Optional[int] = None,
) -> List[Term]:
    """
    Greedy TDAD decomposition:
    - Remaining starts as puzzles[target_idx]
    - Walk coeff pattern (3,2,1,2,...) cyclically
    - Each step: choose the largest puzzle index < current_cursor such that coeff*value <= remaining
    - Subtract and continue
    """
    if target_idx not in puzzles:
        raise KeyError(f"Target puzzle {target_idx} not in puzzles dict.")
    remaining = puzzles[target_idx]

    # Only allow using indices strictly less than target_idx by default.
    cursor = (start_from if start_from is not None else target_idx - 1)
    if cursor >= target_idx:
        cursor = target_idx - 1

    terms: List[Term] = []
    k = 0

    while remaining > 0:
        coeff = pattern[k % len(pattern)]
        found = False

        # search downward from cursor
        for j in range(cursor, 0, -1):
            if j not in puzzles:
                continue
            v = puzzles[j]
            if coeff * v <= remaining:
                terms.append(Term(coeff=coeff, idx=j, val=v))
                remaining -= coeff * v
                cursor = j - 1
                found = True
                break

        if not found:
            # If no term fits with this coeff, advance the coeff (next phase in TDAD cycle)
            # BUT keep the same cursor so we still try big pieces first.
            k += 1

            # Hard stop protection (shouldn't trigger unless target can't be represented under your rules)
            if k > 100000:
                raise RuntimeError("Decomposition stalled (too many steps).")
            continue

        k += 1

    return terms

def pretty_terms(terms: List[Term]) -> str:
    return " + ".join([f"{t.coeff}({t.idx})" for t in terms])

def check_sum(target_idx: int, terms: List[Term], puzzles: Dict[int, int]) -> bool:
    total = sum(t.coeff * puzzles[t.idx] for t in terms)
    return total == puzzles[target_idx]

# ----------------------------
# Demo: run on a list of targets
# ----------------------------
if __name__ == "__main__":
    targets = [14, 15, 16, 68, 69, 70, 130]  # change this to whatever you want

    for t in targets:
        terms = tdad_decompose(t, PUZZLES)
        ok = check_sum(t, terms, PUZZLES)
        print(f"Puzzle {t} = {PUZZLES[t]}")
        print("TDAD terms:", pretty_terms(terms))
        print("Verified:", ok)
        print("-" * 80)
