"""
HYPOTHESIS: Q = s*z feeds into the cubic chain.
The file computes Q = s*z and SZ^2 = s*z^2.
Maybe Q mod p or Q mod N is a cube root of something in the chain?
Maybe Q is the P-side bridge value (replacing x2)?
"""

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Delta = p - N

r = 90653255469745952335985143920649543885181555095025199315947044135806663628368
s = 15509729875763924304053419655647994379903175655107184284998698212653288468986
z = 66278737796829840734606014530466656889790152192829793669891337810330530090951
A = 80184233617433755134183875136831551618578922487806929476230322368028862899169
x2 = A - 7
C1 = 73895602564882060930520904075030822191764226631087187146812983893792436612096

G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)

d = 6681363927270169459683534526047340939294822242524004800730956682266291524995

omega_N = 37718080363155996902926221483475020450927657555482586988616620542887997980018
omega_p = 60197513588986302554485582024885075108884032450952339817679072026166228089408

Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240

# Known d*G
dG = (10272283993622899808044784651867258771963562076122194765880555341454942560481,
       78031030852379254403296293287605662244648002152767059923811274280009202247303)

# Known k for Puzzle 135
k_known = 3565365438013091479694526138621187818738232691050383493655197611165138308430

# The Q values from the file
Q = s * z  # plain integer
Q_mod_N = Q % N
Q_mod_p = Q % p

SZ2 = s * z * z  # s*z^2
SZ2_mod_N = SZ2 % N
SZ2_mod_p = SZ2 % p

print("=" * 70)
print("CUBIC CHAIN ANALYSIS FOR Q = s*z")
print("=" * 70)

print(f"\nQ = s*z = {Q}")
print(f"Q bit_length = {Q.bit_length()}")
print(f"Q mod N = {Q_mod_N}")
print(f"Q mod p = {Q_mod_p}")
print(f"\nSZ^2 = s*z^2 = {SZ2}")
print(f"SZ^2 mod N = {SZ2_mod_N}")
print(f"SZ^2 mod p = {SZ2_mod_p}")

# Check cubic residuosity
print("\n--- CUBIC RESIDUOSITY ---")

# Q mod N
QN_third = pow(Q_mod_N, (N-1)//3, N) if (N-1) % 3 == 0 else None
print(f"Q mod N = {Q_mod_N}")
if QN_third is not None:
    print(f"  (Q mod N)^((N-1)/3) mod N = {QN_third}")
    if QN_third == 1:
        print(f"  -> Q mod N IS a perfect cube mod N")
    elif QN_third == omega_N:
        print(f"  -> Q mod N is NOT a cube mod N (yields omega_N)")
    elif QN_third == (omega_N * omega_N) % N:
        print(f"  -> Q mod N is NOT a cube mod N (yields omega_N^2)")
    else:
        print(f"  -> Unknown residue class")

# Check (N-1) mod 3
print(f"  (N-1) mod 3 = {(N-1) % 3}")

# Q mod p
print(f"\nQ mod p = {Q_mod_p}")
# Check if p-1 divisible by 3
print(f"  (p-1) mod 3 = {(p-1) % 3}")
# p-1 = FFFFFF...FC2E, p-1 mod 3 = ?
# p = FFFFFF...FC2F, p-1 = FFFFFF...FC2E
# Sum of hex digits of p-1... let's just compute
Qp_third = pow(Q_mod_p, (p-1)//3, p) if (p-1) % 3 == 0 else None
if Qp_third is not None:
    print(f"  (Q mod p)^((p-1)/3) mod p = {Qp_third}")
    if Qp_third == 1:
        print(f"  -> Q mod p IS a perfect cube mod p")
    elif Qp_third == omega_p:
        print(f"  -> Q mod p is NOT a cube mod p (yields omega_p)")
    elif Qp_third == (omega_p * omega_p) % p:
        print(f"  -> Q mod p is NOT a cube mod p (yields omega_p^2)")
    else:
        print(f"  -> Unknown residue class: {Qp_third}")
else:
    print(f"  (p-1) not divisible by 3, so unique cube root exists")

# Compare Q values with known chain values
print("\n--- COMPARISON WITH KNOWN CHAIN VALUES ---")
known_vals = {
    "A": A,
    "x2 = A-7": x2,
    "C1": C1,
    "r": r,
    "s": s,
    "z": z,
    "Gx": Gx,
    "dGx": dG[0],
    "dGy": dG[1],
    "k_known": k_known,
    "omega_N": omega_N,
    "omega_p": omega_p,
}

for name, val in known_vals.items():
    if Q_mod_N == val:
        print(f"  Q mod N == {name} = {val}")
    if Q_mod_p == val:
        print(f"  Q mod p == {name} = {val}")

# Now the KEY test: compute cubic chain for Q
print("\n" + "=" * 70)
print("CUBIC CHAIN FOR Q mod p (iterating x -> x^3 mod p)")
print("=" * 70)

val = Q_mod_p
for step in range(10):
    print(f"  step {step}: {val}")
    # Check if this value equals anything in the known chain
    for name, kv in known_vals.items():
        if val == kv:
            print(f"    *** MATCH: equals {name} ***")
    val = pow(val, 3, p)

print("\n" + "=" * 70)
print("CUBIC CHAIN FOR Q mod N (iterating x -> x^3 mod N)")
print("=" * 70)

val = Q_mod_N
for step in range(10):
    print(f"  step {step}: {val}")
    for name, kv in known_vals.items():
        if val == kv:
            print(f"    *** MATCH: equals {name} ***")
    val = pow(val, 3, N)

# Now check: what about r?
print("\n" + "=" * 70)
print("CUBIC CHAIN FOR r mod p (r = R.x = k*G.x)")
print("=" * 70)

r_mod_p = r % p
val = r_mod_p
for step in range(10):
    print(f"  step {step}: {val}")
    for name, kv in known_vals.items():
        if val == kv:
            print(f"    *** MATCH: equals {name} ***")
    val = pow(val, 3, p)

print("\n" + "=" * 70)
print("CUBIC CHAIN FOR r mod N")
print("=" * 70)

r_mod_N = r % N
val = r_mod_N
for step in range(10):
    print(f"  step {step}: {val}")
    for name, kv in known_vals.items():
        if val == kv:
            print(f"    *** MATCH: equals {name} ***")
    val = pow(val, 3, N)

# Check the chain for d*G.x
print("\n" + "=" * 70)
print("CUBIC CHAIN FOR dG.x mod p (should match file's chain)")
print("=" * 70)

dGx = dG[0]
val = dGx % p
for step in range(10):
    print(f"  step {step}: {val}")
    for name, kv in known_vals.items():
        if val == kv:
            print(f"    *** MATCH: equals {name} ***")
    val = pow(val, 3, p)

print("\n" + "=" * 70)
print("CUBIC CHAIN FOR dG.x mod N")
print("=" * 70)

val = dGx % N
for step in range(10):
    print(f"  step {step}: {val}")
    for name, kv in known_vals.items():
        if val == kv:
            print(f"    *** MATCH: equals {name} ***")
    val = pow(val, 3, N)

# THE CRUCIAL CHECK: does the r-chain and dG-chain CONVERGE?
print("\n" + "=" * 70)
print("DO r AND dG.x CHAINS CONVERGE? (mod p)")
print("=" * 70)

r_chain = [r % p]
dg_chain = [dGx % p]
for step in range(20):
    r_chain.append(pow(r_chain[-1], 3, p))
    dg_chain.append(pow(dg_chain[-1], 3, p))
    if r_chain[-1] == dg_chain[-1]:
        print(f"  CONVERGENCE at step {step+1}!")
        print(f"  Common value = {r_chain[-1]}")
        break
else:
    print(f"  No convergence in 20 steps")
    # Check if they share any value
    for i, rv in enumerate(r_chain):
        for j, dv in enumerate(dg_chain):
            if rv == dv:
                print(f"  Shared value at r_step={i}, dg_step={j}: {rv}")

# And for Q
print("\n--- Q-chain vs r-chain vs dG-chain (mod p) ---")
q_chain = [Q_mod_p]
for step in range(20):
    q_chain.append(pow(q_chain[-1], 3, p))
    for i, rv in enumerate(r_chain):
        if q_chain[-1] == rv:
            print(f"  Q-chain step {step+1} == r-chain step {i}: {q_chain[-1]}")
    for j, dv in enumerate(dg_chain):
        if q_chain[-1] == dv:
            print(f"  Q-chain step {step+1} == dG-chain step {j}: {q_chain[-1]}")

# NEW IDEA: what if we need to cube root Q to get into the chain?
print("\n" + "=" * 70)
print("CUBE ROOT OF Q mod p -> CHAIN")
print("=" * 70)

# Try to find cube root of Q mod p
# If (p-1) % 3 != 0, cubing is a bijection and inverse exists
if (p - 1) % 3 != 0:
    # gcd(3, p-1) = 1, so cubing is bijection
    # cube root = Q^((2p-1)/3) mod p ? No, we need the inverse of x^3
    # If x^3 = a mod p, then x = a^e where 3e = 1 mod (p-1)
    # 3e = 1 mod (p-1) => e = (2*(p-1)+1)/3 if (p-1) = 3k+1 => e = (2*3k+3)/3 = 2k+1 = (2*(p-1)+1)/3
    e = (2*(p-1) + 1) // 3
    print(f"  (p-1) = 3*{(p-1)//3} + {(p-1)%3}")
    print(f"  Inverse exponent e = (2*(p-1)+1)/3 = {e}")
    # Wait, we need 3*e = 1 mod (p-1)
    # Since gcd(3, p-1) = gcd(3, (p-1)%3) = gcd(3,1) = 1 (if (p-1)%3=1)
    # Then e = pow(3, -1, p-1)
    e = pow(3, -1, p-1)
    print(f"  e = pow(3, -1, p-1) = {e}")
    Q_cuberoot_mod_p = pow(Q_mod_p, e, p)
    print(f"  Q^(1/3) mod p = {Q_cuberoot_mod_p}")
    
    # Verify
    print(f"  Verify: (Q^(1/3))^3 mod p = {pow(Q_cuberoot_mod_p, 3, p)}")
    print(f"  Q mod p = {Q_mod_p}")
    print(f"  Match: {pow(Q_cuberoot_mod_p, 3, p) == Q_mod_p}")
    
    # Now chain from Q^(1/3) mod p
    print(f"\n  Chain from Q^(1/3) mod p:")
    val = Q_cuberoot_mod_p
    for step in range(10):
        print(f"    step {step}: {val}")
        for name, kv in known_vals.items():
            if val == kv:
                print(f"      *** MATCH: equals {name} ***")
        val = pow(val, 3, p)
else:
    print(f"  (p-1) divisible by 3, multiple cube roots exist")

# Same for mod N
print("\n" + "=" * 70)
print("CUBE ROOT OF Q mod N -> CHAIN")
print("=" * 70)
if (N - 1) % 3 != 0:
    e = pow(3, -1, N-1)
    print(f"  e = pow(3, -1, N-1) = {e}")
    Q_cuberoot_mod_N = pow(Q_mod_N, e, N)
    print(f"  Q^(1/3) mod N = {Q_cuberoot_mod_N}")
    print(f"  Verify: {pow(Q_cuberoot_mod_N, 3, N) == Q_mod_N}")
    
    val = Q_cuberoot_mod_N
    for step in range(10):
        print(f"  step {step}: {val}")
        for name, kv in known_vals.items():
            if val == kv:
                print(f"    *** MATCH: equals {name} ***")
        val = pow(val, 3, N)
else:
    print(f"  (N-1) divisible by 3 = {(N-1)%3}")

# FINAL CHECK: what if Q = s*z = k * something?
print("\n" + "=" * 70)
print("DOES Q = k * (known value)?")
print("=" * 70)

# k_known = 3565365438013091479694526138621187818738232691050383493655197611165138308430
print(f"  k_known = {k_known}")
print(f"  Q / k_known = {Q / k_known}")
print(f"  Q mod k_known = {Q % k_known}")
print(f"  Q / (k_known * N) = {Q / (k_known * N)}")

# Is Q = k * s * z / k = s * z? Yes, trivially.
# But is Q = k * something_useful?
# k * r = ?
kr = k_known * r
print(f"  k*r = {kr}")
print(f"  k*r mod N = {kr % N}")
print(f"  k*r mod p = {kr % p}")
print(f"  Q mod N = {Q_mod_N}")
print(f"  Match k*r mod N? {kr % N == Q_mod_N}")

# What about: does Q/k give us something?
Q_over_k = Q // k_known
Q_mod_k = Q % k_known
print(f"  Q // k = {Q_over_k}")
print(f"  Q % k = {Q_mod_k}")
print(f"  Is Q divisible by k? {Q % k_known == 0}")

# What about: does Q = k * r * something?
print(f"\n  Q / (k*r) = {Q / (k_known * r)}")
print(f"  Q / (k*s) = {Q / (k_known * s)}")
print(f"  Q / (k*z) = {Q / (k_known * z)}")
