N = 115792089237316195423570985008687907852837564279074904382605163141518161494337

IP = 80184233617433755134183875136831551618578922487806929476230322368028862899162

EXP = (N - 1) // 3

classes = {}

for k in range(-100, 101):

    value = (IP + k) % N

    c = pow(value, EXP, N)

    if c not in classes:
        classes[c] = []

    classes[c].append(k)

for idx, (key, vals) in enumerate(classes.items(), start=1):
    print("\n")
    print("=" * 80)
    print(f"CLASS {idx}")
    print(f"Representative = {key}")
    print(f"Offsets = {vals}")