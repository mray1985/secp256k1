#!/usr/bin/env python3
# TDAD5.py
#
# TDAD decomposition with:
# - coefficient cycle: [3, 2, 1, 2]
# - no self-use (cannot use Ptarget as a term)
# - atomic closure for remainder == 1 using P1
# - optional mod-preference (e.g., prefer indices congruent to target mod 5)
# - per-index reuse cap (default 8)

import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# ---- PUZZLE VALUES (as provided) ----
PUZZLES: Dict[int, int] = {
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

    # Expanded ones you referenced
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
    130: 1103873984953507439627945351144005829577,
}

# ---- CONFIG ----
TDAD_CYCLE = [3, 2, 1, 2]

@dataclass
class TDADConfig:
    prefer_mod: Optional[int] = 5     # prefer i % 5 == target % 5 (set None to disable)
    max_uses_per_index: int = 8       # cap per index usage count
    allow_atomic_one: bool = True     # allow remainder==1 -> 1(P1)
    max_steps: int = 200000           # safety


def verify_terms(terms: List[Tuple[int, int]], puzzles: Dict[int, int], target_value: int) -> bool:
    total = 0
    for coeff, idx in terms:
        total += coeff * puzzles[idx]
    return total == target_value


def tdad_decompose(target_idx: int, puzzles: Dict[int, int], cfg: TDADConfig) -> List[Tuple[int, int]]:
    if target_idx not in puzzles:
        raise KeyError(f"Puzzle {target_idx} not in PUZZLES dict.")
    target_value = puzzles[target_idx]

    # Candidate indices: all indices except the target itself (no self term)
    candidates = sorted([i for i in puzzles.keys() if i != target_idx], reverse=True)

    remainder = target_value
    terms: List[Tuple[int, int]] = []
    uses = defaultdict(int)

    cycle_pos = 0
    steps = 0

    # quick access
    p1_exists = (1 in puzzles and puzzles[1] == 1)

    while remainder > 0:
        steps += 1
        if steps > cfg.max_steps:
            raise RuntimeError(f"TDAD stalled (too many steps). Remainder={remainder}")

        # Atomic closure
        if cfg.allow_atomic_one and remainder == 1:
            if not p1_exists:
                raise RuntimeError("Remainder=1 but P1=1 is not available in PUZZLES.")
            # Enforce cap
            if uses[1] >= cfg.max_uses_per_index:
                raise RuntimeError("Remainder=1 but P1 usage cap reached.")
            terms.append((1, 1))
            uses[1] += 1
            remainder -= 1
            break

        coeff = TDAD_CYCLE[cycle_pos]
        cycle_pos = (cycle_pos + 1) % len(TDAD_CYCLE)

        # pick best candidate for this coeff
        chosen = None

        # optional mod preference: try preferred class first, then fall back
        preferred = []
        fallback = []
        if cfg.prefer_mod is not None:
            m = cfg.prefer_mod
            for i in candidates:
                if i == 1 and not cfg.allow_atomic_one:
                    continue
                if i % m == target_idx % m:
                    preferred.append(i)
                else:
                    fallback.append(i)
            search_lists = [preferred, fallback]
        else:
            search_lists = [candidates]

        for lst in search_lists:
            for i in lst:
                if uses[i] >= cfg.max_uses_per_index:
                    continue
                v = puzzles[i]
                if coeff * v <= remainder:
                    chosen = i
                    break
            if chosen is not None:
                break

        # if nothing fits this coeff, try "relax": attempt any smaller coeff (3->2->1)
        if chosen is None:
            relaxed_found = False
            for relaxed_coeff in (2, 1):
                # search again with relaxed coeff
                for lst in search_lists:
                    for i in lst:
                        if uses[i] >= cfg.max_uses_per_index:
                            continue
                        v = puzzles[i]
                        if relaxed_coeff * v <= remainder:
                            terms.append((relaxed_coeff, i))
                            uses[i] += 1
                            remainder -= relaxed_coeff * v
                            relaxed_found = True
                            break
                    if relaxed_found:
                        break
                if relaxed_found:
                    break

            if not relaxed_found:
                # last chance: if remainder itself is a puzzle value (other than target), allow coeff=1
                for i in candidates:
                    if uses[i] >= cfg.max_uses_per_index:
                        continue
                    if puzzles[i] == remainder:
                        terms.append((1, i))
                        uses[i] += 1
                        remainder = 0
                        relaxed_found = True
                        break

            if not relaxed_found:
                raise RuntimeError(f"TDAD stalled — remainder {remainder} cannot be decomposed.")

            continue

        # apply chosen
        terms.append((coeff, chosen))
        uses[chosen] += 1
        remainder -= coeff * puzzles[chosen]

    # Final sanity
    if remainder != 0:
        raise RuntimeError(f"TDAD ended with nonzero remainder {remainder}.")

    # Verify against target
    if not verify_terms(terms, puzzles, target_value):
        raise RuntimeError("Internal error: terms do not sum to target.")

    return terms


def format_terms(terms: List[Tuple[int, int]]) -> str:
    return " + ".join([f"{c}({i})" for c, i in terms]) + " +"


def run_one(idx: int, cfg: TDADConfig):
    print("=" * 80)
    print(f"Puzzle {idx} = {PUZZLES[idx]}")
    terms = tdad_decompose(idx, PUZZLES, cfg)
    print("TDAD terms:")
    print(format_terms(terms))
    print(f"Verified: {verify_terms(terms, PUZZLES, PUZZLES[idx])}")


def main():
    cfg = TDADConfig()

    args = sys.argv[1:]
    if not args:
        print("Usage:")
        print("  python3 TDAD5.py 70")
        print("  python3 TDAD5.py 70 65 60 55 50 45 40 35 30 25 20 15 10 5")
        print("  python3 TDAD5.py --all")
        sys.exit(0)

    if "--all" in args:
        # run all known puzzles in PUZZLES
        for idx in sorted(PUZZLES.keys()):
            run_one(idx, cfg)
        return

    # Otherwise, treat args as puzzle indices
    indices = []
    for a in args:
        if a.startswith("--"):
            continue
        indices.append(int(a))

    for idx in indices:
        if idx not in PUZZLES:
            print(f"Puzzle {idx} not found in PUZZLES dict, skipping.")
            continue
        run_one(idx, cfg)


if __name__ == "__main__":
    main()
