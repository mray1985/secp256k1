N = 115792089237316195423570985008687907852837564279074904382605163141518161494337

# The cleared cubic residue
M = 3820628127091453859030266576898546114566560342084415068589713593856641559477

# The omega^2 defect you discovered
w2 = 37718080363155996902926221483475020450927657555482586988616620542887997980018

# 1. The Deterministic Exponent for N = 7 (mod 9)
exp = (N + 2) // 9

# 2. Extract Root 1 (Lambda 1)
Lambda_1 = pow(M, exp, N)

# 3. Use the omega defect to jump to Root 2 (Lambda 2)
Lambda_2 = (Lambda_1 * w2) % N

# 4. Use the omega defect to jump to Root 3 (Lambda 3)
Lambda_3 = (Lambda_2 * w2) % N

print(f"[+] Lambda 1: {Lambda_1}")
print(f"[+] Lambda 2: {Lambda_2}")
print(f"[+] Lambda 3: {Lambda_3}")

# Mathematical Verification
print("\n[!] Verifying cubes:")
print(f"L1^3 == M ? {pow(Lambda_1, 3, N) == M}")
print(f"L2^3 == M ? {pow(Lambda_2, 3, N) == M}")
print(f"L3^3 == M ? {pow(Lambda_3, 3, N) == M}")