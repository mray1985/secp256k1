# Your exact sequence (index → value)
SEQ = {
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
    69: 297274491920375905804, 70: 970436974005023690481
}

BASIS = sorted(SEQ.values())
DOUBLES = {2 * x for x in BASIS}


def term_type(x):
    return "D" if x in DOUBLES else "A"


def decompose(target, start_state):
    remaining = target
    terms = []

    # enforce start rule
    allowed = BASIS if start_state == "A" else sorted(DOUBLES)

    for t in sorted(allowed, reverse=True):
        if t <= remaining:
            terms.append(t)
            remaining -= t
            break
    else:
        raise RuntimeError("No valid starting term")

    # after first term, free selection
    all_terms = sorted(BASIS + list(DOUBLES), reverse=True)

    while remaining > 0:
        for t in all_terms:
            if t <= remaining:
                terms.append(t)
                remaining -= t
                break
        else:
            raise RuntimeError("Stuck during decomposition")

    end_state = term_type(terms[-1])
    return terms, end_state


def pretty(terms):
    out = []
    for t in terms:
        if t in DOUBLES:
            out.append(f"2({t//2})")
        else:
            out.append(str(t))
    return " + ".join(out)


def run_sequence(start_index=14, end_index=18, initial_state="D"):
    state = initial_state
    for i in range(start_index, end_index + 1):
        value = SEQ[i]
        terms, end_state = decompose(value, state)
        print(f"{value} = {pretty(terms)}")
        print(f"start {state} → end {end_state}\n")
        state = "A" if end_state == "D" else "D"


# Example: reproduce your region
run_sequence(14, 17, initial_state="D")
