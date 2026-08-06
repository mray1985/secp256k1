# goo4.py — m and fractional-residual calculation for every puzzle in the PDF archive
import json, sys, os
from mpmath import mp

PAGE = 25

def page_out(lines):
    for i in range(0, len(lines), PAGE):
        chunk = lines[i:i + PAGE]
        for ln in chunk:
            print(ln)
        if i + PAGE < len(lines):
            try:
                input("-- more (Enter to continue, Ctrl+C to stop) --")
            except (EOFError, KeyboardInterrupt):
                print()
                sys.exit(0)

mp.dps = 800
N_val = 115792089237316195423570985008687907852837564279074904382605163141518161494337

data = json.load(open(r"C:\Users\mitch\Desktop\secp256k1\ARCHIVE\puzzle_1_160_full_data.json"))
full = sorted(data["full"], key=lambda e: int(e["n"]))
partial = sorted(data["partial"], key=lambda e: int(e["n"]))

W_real = mp.power(2, 780)

answers = 0
out = []
for e in full:
    answers += 1
    n = int(e["n"])
    s = int(e["s"], 16)
    k = int(e["k"], 16)
    r = int(e["r"], 16)
    d = int(e["d"], 16)
    z = int(e["z"], 16)
    m = (s * k - r * d - z) // N_val
    fractional_residual = (m * (2**256 - N_val)) / (2**256)
    out.append(f"[Answer {answers}] Puzzle {n}: m = {m}, fractional residual = {float(fractional_residual)}")

for e in partial:
    answers += 1
    n = int(e["n"])
    out.append(f"[Answer {answers}] Puzzle {n}: cannot compute m (d and k unknown, unsolved)")

save = r"C:\Users\mitch\Desktop\secp256k1\goo4_output.txt"
if "--save" in sys.argv:
    open(save, "w").write("\n".join(out) + "\n")
    print(f"Saved all {answers} answers to {save}")
else:
    page_out(out)
