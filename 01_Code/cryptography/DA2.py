SEQ = {
    1: 1, 2: 3, 3: 7, 4: 8, 5: 21, 6: 49, 7: 76, 8: 224,
    9: 467, 10: 514, 11: 1155, 12: 2683, 13: 5216,
    14: 10544, 15: 26867, 16: 51510, 17: 95823
}

def term_state(term, basis):
    return "D" if term % 2 == 0 and (term // 2) in basis else "A"


def decompose_forward(index, start_state):
    target = SEQ[index]
    basis = [SEQ[i] for i in range(1, index)]
    doubles = [2*x for x in basis]
    remaining = target
    terms = []

    # enforce start
    starters = doubles if start_state == "D" else basis
    for t in sorted(starters, reverse=True):
        if t <= remaining:
            terms.append(t)
            remaining -= t
            break
    else:
        raise RuntimeError(f"No valid start for puzzle {index}")

    # continue additively
    all_terms = sorted(basis + doubles, reverse=True)
    while remaining > 0:
        for t in all_terms:
            if t <= remaining:
                terms.append(t)
                remaining -= t
                break
        else:
            raise RuntimeError(f"Stuck at puzzle {index}")

    end_state = term_state(terms[-1], basis)
    return terms, end_state


def pretty(terms, basis):
    out = []
    for t in terms:
        if t % 2 == 0 and (t//2) in basis:
            out.append(f"2({t//2})")
        else:
            out.append(str(t))
    return " + ".join(out)


# RUN FROM PUZZLE 1
state = "A"  # Puzzle 1 starts as ADD
print("Puzzle 1 = 1")
print("state A\n")

for i in range(2, 18):
    basis = [SEQ[j] for j in range(1, i)]
    terms, end_state = decompose_forward(i, state)
    print(f"Puzzle {i}: {SEQ[i]} = {pretty(terms, basis)}")
    print(f"start {state} → end {end_state}\n")
    state = "A" if end_state == "D" else "D"
