# GIVEN SEQUENCE (1–70)
SEQ = [
    1, 3, 7, 8, 21, 49, 76, 224, 467, 514,
    1155, 2683, 5216, 10544, 26867, 51510, 95823,
    198669, 357535, 863317, 1811764, 3007503, 5598802,
    14428676, 33185509, 54538862, 111949941, 227634408,
    400708894, 1033162084, 2102388551, 3093472814,
    7137437912, 14133072157, 20112871792, 42387769980,
    100251560595, 146971536592, 323724968937, 1003651412950,
    1458252205147, 2895374552463, 7409811047825,
    15404761757071, 19996463086597, 51408670348612,
    119666659114170, 191206974700443, 409118905032525,
    611140496167764, 2058769515153876, 4216495639600700,
    6763683971478124, 9974455244496707, 30045390491869460,
    44218742292676575, 138245758910846492, 199976667976342049,
    525070384258266191, 1135041350219496382,
    1425787542618654982, 3908372542507822062,
    8993229949524469768, 17799667357578236628,
    30568377312064202855, 46346217550346335726,
    132656943602386256302, 219898266213316039825,
    297274491920375905804, 970436974005023690481
]


def oscillatory_decompose(target, basis):
    remaining = target
    terms = []

    gens = sorted(basis, reverse=True)

    for g in gens:
        while True:
            if remaining >= g:
                terms.append(g)
                remaining -= g
            else:
                break

            if remaining >= 2 * g:
                terms.append(2 * g)
                remaining -= 2 * g
            else:
                break

        if remaining == 0:
            break

    return terms


def generate_next(seq):
    basis = seq.copy()
    last = seq[-1]

    # empirical growth factor from your data (~1.7–2.3)
    estimate = int(last * 1.85)

    terms = oscillatory_decompose(estimate, basis)
    return sum(terms), terms


# CONTINUE SEQUENCE
N_EXTEND = 5
seq = SEQ.copy()

for i in range(N_EXTEND):
    next_val, terms = generate_next(seq)
    seq.append(next_val)

    print(f"{len(seq)} = {next_val}")
