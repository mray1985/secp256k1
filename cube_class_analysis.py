"""
BREAKTHROUGH HYPOTHESIS: Q mod N and x2 are in the SAME cube residue class.
Therefore Q * x2^(-1) mod N is a perfect cube.
If the cube root relates to k, we solve ECDLP.
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

omega_N = 37718080363155996902926221483475020450927657555482586988616620542887997980018
omega_N2 = pow(omega_N, 2, N)
omega_p = 60197513588986302554485582024885075108884032450952339817679072026166228089408

d = 6681363927270169459683534526047340939294822242524004800730956682266291524995
k_known = 3565365438013091479694526138621187818738232691050383493655197611165138308430

Q = s * z
Q_mod_N = Q % N
Q_mod_p = Q % p

print("=" * 70)
print("KEY FINDING: Q mod N and x2 are in same cube class")
print("=" * 70)

# Verify: both yield omega_N
QN_check = pow(Q_mod_N, (N-1)//3, N)
x2_check = pow(x2, (N-1)//3, N)
print(f"(Q mod N)^((N-1)/3) mod N = {QN_check} (omega_N = {omega_N})")
print(f"x2^((N-1)/3) mod N = {x2_check}")
print(f"Both yield omega_N: {QN_check == omega_N and x2_check == omega_N}")

# Therefore Q * x2^(-1) mod N IS a perfect cube
Qx2_inv = (Q_mod_N * pow(x2, -1, N)) % N
Qx2_check = pow(Qx2_inv, (N-1)//3, N)
print(f"\nQ * x2^(-1) mod N = {Qx2_inv}")
print(f"(Q * x2^(-1))^((N-1)/3) mod N = {Qx2_check}")
print(f"Is perfect cube: {Qx2_check == 1}")

# Compute cube root(s) of Q * x2^(-1) mod N
# Since (N-1)/3 is integer and Q*x2^(-1) is a cube, there are 3 cube roots
# One root: (Q*x2^(-1))^(1/3) mod N
# But we need pow(Qx2_inv, e, N) where 3e = 1 mod (N-1)
# gcd(3, N-1) = 3, so inverse doesn't exist
# Instead: since Qx2_inv is a cube, (Qx2_inv)^(1/3) = (Qx2_inv)^((2*(N-1)/3 + 1)/3)... 
# Actually: if a = b^3, then a^((2N-1)/3) is NOT b in general when 3 | (N-1)

# The standard approach: find any cube root
# a^((2*(N-1)/3 + 1)/3) ... no, that's not right either

# When 3 | (N-1) and a is a cube, the cube roots are:
# a^((2*(N-1)/3 + 1)/3) ... hmm
# Actually: if a = b^3 and we want b:
# b = a^(e) where 3e = 1 mod (N-1)
# But gcd(3, N-1) = 3, so no inverse exists
# However, if a IS a cube (a^((N-1)/3) = 1), then:
# a^((2*(N-1)+3)/9) if 9 | (2*(N-1)+3)... this is getting complicated

# Simpler: try to find cube root by checking if a = b^3 for specific b
# Or use: b = a^((2*k*(N-1)+1)/3) for some k
# We need (2*k*(N-1)+1) to be divisible by 3
# 2*k*(N-1)+1 = 2*k*3*m + 1 = 6km + 1 where (N-1) = 3m
# We need 3 | (6km+1), but 6km+1 â‰¡ 1 mod 3. So this doesn't work.

# Alternative: since a is a cube, a = g^(3j) for some generator g and exponent j
# Then a^(1/3) = g^j, but we don't know g or j

# Practical approach: just try a^(e) for various e
# If a = b^3, then b = a^e where 3e = 1 mod ord(a)
# ord(a) divides (N-1)/gcd(exponent stuff)

# Actually the simplest: since we know a is a cube,
# let's try b = a^((2*(N-1)/3 + 1) // 3)
e_candidate = (2 * (N-1) // 3 + 1) // 3
print(f"\nTrying exponent e = (2*(N-1)/3 + 1)/3 = {e_candidate}")
print(f"  3*e mod (N-1) = {(3 * e_candidate) % (N-1)}")

# Check: does (N-1)/3 divide evenly?
m = (N-1) // 3
print(f"  (N-1)/3 = {m}")
print(f"  (N-1) = 3 * {m}")

# Try: a^(m) should give... hmm
# If a = g^(3j), then a^m = g^(3jm) = g^(j*(N-1)) = 1. Not useful.

# Better approach: enumerate
# We know a is a cube. a = b^3 for some b.
# Try b = a^e for e in range
# We need: (a^e)^3 = a^(3e) = a mod (N... ) No, a^(3e) = a only if 3e = 1 mod ord(a)

# Since ord(a) | (N-1) and 3 | (N-1), ord(a) might not be coprime to 3
# But since a IS a cube, ord(a) | (N-1)/3 is possible

# Let's just try the Tonelli-Shanks analog for cube roots
# Or: try b = a^((2*m+1)/3) if this is integer
numerator = 2 * m + 1
if numerator % 3 == 0:
    e = numerator // 3
    print(f"  Cube root exponent: e = (2*(N-1)/3 + 1)/3 = {e}")
    b = pow(Qx2_inv, e, N)
    print(f"  Cube root candidate: {b}")
    print(f"  Verify: b^3 mod N = {pow(b, 3, N)}")
    print(f"  Expected: Q*x2^(-1) mod N = {Qx2_inv}")
    print(f"  Match: {pow(b, 3, N) == Qx2_inv}")
else:
    print(f"  (2*(N-1)/3 + 1) = {numerator}, not divisible by 3")

# Another approach: just try e = (N+2)/3 or similar
# For p prime with p â‰¡ 2 mod 3: cube root of a = a^((2p-1)/3)
# N is prime. N mod 3 = ?
print(f"\n  N mod 3 = {N % 3}")
print(f"  N mod 9 = {N % 9}")

# If N â‰¡ 2 mod 3, cube root = a^((2N-1)/3)
if N % 3 == 2:
    e = (2*N - 1) // 3
    print(f"  N â‰¡ 2 mod 3, trying e = (2N-1)/3 = {e}")
    b = pow(Qx2_inv, e, N)
    print(f"  Cube root: {b}")
    print(f"  Verify: {pow(b, 3, N) == Qx2_inv}")
else:
    print(f"  N â‰¡ {N%3} mod 3, standard formula doesn't apply")

# Since N-1 = 3m and N % 3 = 1 (because N-1 divisible by 3), we need a different approach
# When 3 | (p-1), cube roots are not unique and require Cipolla-like or Tonelli-Shanks-like

# Actually: N = 115792089237316195423570985008687907852837564279074904382605163141518161494337
# N mod 3: sum of digits of N... let's compute
N_digits_sum = sum(int(c) for c in str(N))
print(f"\n  N digit sum = {N_digits_sum}")
print(f"  N digit sum mod 3 = {N_digits_sum % 3}")
print(f"  N mod 3 = {N % 3}")

# OK so N â‰¡ 1 mod 3 (since N-1 divisible by 3 means N â‰¡ 1 mod 3)
# For cube roots when p â‰¡ 1 mod 3:
# We need to find a primitive cube root of unity omega
# Then find one cube root b0, and the three roots are b0, b0*omega, b0*omega^2

# For the specific case where a is known to be a cube:
# Try: b = a^((2*(N-1)/3 + 1)/3) -- but this needs 3 | (2*(N-1)/3 + 1)
# 2*(N-1)/3 + 1 = 2m + 1. We need 3 | (2m+1).
# m = (N-1)/3. 
m = (N-1)//3
print(f"  m = (N-1)/3 = {m}")
print(f"  2m+1 = {2*m+1}")
print(f"  (2m+1) mod 3 = {(2*m+1) % 3}")

if (2*m + 1) % 3 == 0:
    e = (2*m + 1) // 3
    b = pow(Qx2_inv, e, N)
    print(f"  Cube root exponent e = {e}")
    print(f"  b = a^e mod N = {b}")
    print(f"  Verify: b^3 mod N = {pow(b, 3, N)}")
    print(f"  Expected: {Qx2_inv}")
    print(f"  Match: {pow(b, 3, N) == Qx2_inv}")
    
    # Check if b = k_known or related
    print(f"\n  b = {b}")
    print(f"  k_known = {k_known}")
    print(f"  b == k_known? {b == k_known}")
    print(f"  b mod N = {b}")
    print(f"  b * omega_N mod N = {(b * omega_N) % N}")
    print(f"  b * omega_N^2 mod N = {(b * omega_N2) % N}")
    print(f"  Any == k_known? {(b * omega_N) % N == k_known or (b * omega_N2) % N == k_known}")
    
    # Also check if b == d or related
    print(f"  b == d? {b == d}")
    print(f"  b * omega_N mod N == d? {(b * omega_N) % N == d}")
    print(f"  b * omega_N^2 mod N == d? {(b * omega_N2) % N == d}")

# Also: since Q mod N is in the same cube class as x2,
# Q = x2 * c^3 mod N for some c.
# What is c?
c_cubed = (Q_mod_N * pow(x2, -1, N)) % N
print(f"\n--- Q = x2 * c^3 mod N ---")
print(f"c^3 = Q * x2^(-1) mod N = {c_cubed}")

# Check all values in the file against cube classes
print("\n" + "=" * 70)
print("CUBE RESIDUE CLASS CHECK (yields what when raised to (N-1)/3?)")
print("=" * 70)

vals_to_check = {
    "Q mod N": Q_mod_N,
    "x2": x2,
    "C1": C1,
    "r": r % N,
    "s": s % N,
    "z": z % N,
    "A": A,
    "Delta": Delta,
    "omega_N": omega_N,
}

for name, val in vals_to_check.items():
    check = pow(val, (N-1)//3, N)
    if check == 1:
        label = "CUBE"
    elif check == omega_N:
        label = "omega_N (non-cube class 1)"
    elif check == omega_N2:
        label = "omega_N^2 (non-cube class 2)"
    else:
        label = f"OTHER: {check}"
    print(f"  {name:15s} -> {label}")

# Same for mod p
print("\n--- mod p ---")
vals_p = {
    "Q mod p": Q_mod_p,
    "x2": x2 % p,
    "r": r % p,
    "s": s % p,
    "z": z % p,
    "A": A % p,
    "Delta mod p": Delta % p,
}

for name, val in vals_p.items():
    check = pow(val, (p-1)//3, p)
    if check == 1:
        label = "CUBE"
    elif check == omega_p:
        label = "omega_p"
    elif check == (omega_p * omega_p) % p:
        label = "omega_p^2"
    else:
        label = f"OTHER: {check}"
    print(f"  {name:15s} -> {label}")

