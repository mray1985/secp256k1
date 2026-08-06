"""
TEST: Is k^3 = Q * x2^(-1) mod N?
If yes, then knowing Q (=s*z) and x2 gives us k via cube root.
And x2 can be found from the cubic chain structure.
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
omega_p = 60197513588986302554485582024885075108884032450952339817679072026166228089408

d = 6681363927270169459683534526047340939294822242524004800730956682266291524995
k_known = 3565365438013091479694526138621187818738232691050383493655197611165138308430

Q = s * z
Q_mod_N = Q % N

# c^3 = Q * x2^(-1) mod N
c_cubed = (Q_mod_N * pow(x2, -1, N)) % N

print("=" * 70)
print("IS k^3 = Q * x2^(-1) mod N?")
print("=" * 70)

k3 = pow(k_known, 3, N)
print(f"k^3 mod N    = {k3}")
print(f"c^3 (=Q*x2^-1) = {c_cubed}")
print(f"Match: {k3 == c_cubed}")

# Also check the 3 omega-shifted versions
for j in range(3):
    kj_cubed = pow(k_known * pow(omega_N, j, N) % N, 3, N)
    print(f"(k*omega_N^{j})^3 mod N = {kj_cubed}")
    print(f"  Match c^3? {kj_cubed == c_cubed}")

# Check: is k^3 = Q mod N directly?
print(f"\nk^3 mod N = {k3}")
print(f"Q mod N   = {Q_mod_N}")
print(f"Match: {k3 == Q_mod_N}")

# What about: k^3 mod N = something else in the chain?
print(f"\n--- k^3 relationships ---")
print(f"k^3 mod N = {k3}")
print(f"k^3 mod p = {pow(k_known, 3, p)}")

# What about: k^3 * x2 mod N?
k3_x2 = pow(k_known, 3, N) * x2 % N
print(f"k^3 * x2 mod N = {k3_x2}")
print(f"Q mod N = {Q_mod_N}")
print(f"Match: {k3_x2 == Q_mod_N}")

# What about: s * k^3 mod N?
sk3 = s * pow(k_known, 3, N) % N
print(f"\ns * k^3 mod N = {sk3}")

# ECDSA: k*s = m + r*d mod N
# So k^3 * s = k^2 * (m + r*d) mod N
ks = k_known * s % N
print(f"\nk*s mod N = {ks}")
print(f"m + r*d mod N = (m + r*d) mod N")

# With m = 123456789012345678901234567890
m_wrong = 123456789012345678901234567890
val_wrong = (m_wrong + r * d) % N
print(f"m_wrong + r*d mod N = {val_wrong}")
print(f"k*s mod N = {ks}")
print(f"Match: {val_wrong == ks}")

# What m would make it work?
m_correct = (ks - r * d) % N
print(f"Correct m = (k*s - r*d) mod N = {m_correct}")

# Now test: does m_correct relate to z?
print(f"\nm_correct = {m_correct}")
print(f"z = {z}")
print(f"m_correct == z? {m_correct == z}")
print(f"m_correct mod N = {m_correct}")

# THE KEY QUESTION: can we derive x2 from s, z, k?
# If k^3 = Q * x2^(-1) mod N, then x2 = Q * k^(-3) mod N
x2_from_k = Q_mod_N * pow(k_known, 3, N) % N * pow(k_known, 3, N) % N
# Wait: x2 = Q * (k^3)^(-1) mod N = Q * k^(-3) mod N
x2_from_k = Q_mod_N * pow(pow(k_known, 3, N), -1, N) % N
print(f"\nx2 derived from k: {x2_from_k}")
print(f"Actual x2:         {x2}")
print(f"Match: {x2_from_k == x2}")

# If that doesn't match, try the other possibility:
# Maybe Q * x2^(-1) = (k*s)^3 or (k*r)^3 or similar
print("\n--- Testing Q = x2 * (k*something)^3 mod N ---")
for name, val in [("k", k_known), ("k*s", k_known*s%N), ("k*r", k_known*r%N), 
                   ("k*z", k_known*z%N), ("s", s), ("r", r), ("z", z),
                   ("k^2", pow(k_known,2,N)), ("s^2", pow(s,2,N))]:
    cube = pow(val, 3, N)
    test = x2 * cube % N
    if test == Q_mod_N:
        print(f"  MATCH: Q = x2 * {name}^3 mod N!")

# Check: Q = x2 * s^3 * z^3 / (something)?
# Or Q = s*z = x2 * (s*z/x2) ... trivially
# The real question is what c is in Q = x2 * c^3

# Let's check: c = s * z^? or c = something simple
print(f"\n--- What is c in Q = x2 * c^3 mod N? ---")
print(f"c^3 = {c_cubed}")

# Is c^3 = s^3 * z^3 * x2^(-1) ... nah, that would give Q^3/x2
s3z3 = pow(s, 3, N) * pow(z, 3, N) % N
print(f"s^3 * z^3 mod N = {s3z3}")
print(f"Q^3 mod N = {pow(Q_mod_N, 3, N)}")

# Is c = s * z * x2^(-1) mod N?
c_candidate = s * z % N * pow(x2, -1, N) % N
print(f"\ns * z * x2^(-1) mod N = {c_candidate}")
c_cubed_check = pow(c_candidate, 3, N)
print(f"(s*z*x2^-1)^3 mod N = {c_cubed_check}")
print(f"c^3 = {c_cubed}")
print(f"Match: {c_cubed_check == c_cubed}")

# Is c = s * z^(-1) * x2^(-1) mod N?
c2 = s * pow(z, -1, N) % N * pow(x2, -1, N) % N
print(f"\ns * z^(-1) * x2^(-1) mod N = {c2}")
print(f"(c2)^3 mod N = {pow(c2, 3, N)}")

# Is c = (s*z)^(1/3) * x2^(-1/3) mod N? That's just c itself...

# Let me check: does k^3 * x2 = Q mod N? (i.e., Q = x2 * k^3)
print(f"\n--- Direct: Q = x2 * k^3 mod N? ---")
test = x2 * pow(k_known, 3, N) % N
print(f"x2 * k^3 mod N = {test}")
print(f"Q mod N = {Q_mod_N}")
print(f"Match: {test == Q_mod_N}")

# What about Q = x2 * k^3 * omega_N^j for some j?
for j in range(3):
    test = x2 * pow(k_known, 3, N) % N * pow(omega_N, j, N) % N
    print(f"x2 * k^3 * omega_N^{j} mod N = {test}")
    print(f"  Match Q? {test == Q_mod_N}")

# MOD p check
print("\n--- MOD P ANALYSIS ---")
Q_mod_p = Q % p
# Q mod p is a cube, x2 mod p is a cube
# So Q * x2^(-1) mod p is also a cube
Qx2_inv_p = Q_mod_p * pow(x2, -1, p) % p
print(f"Q * x2^(-1) mod p = {Qx2_inv_p}")
print(f"(Q * x2^(-1))^((p-1)/3) mod p = {pow(Qx2_inv_p, (p-1)//3, p)}")

# Is k^3 = Q * x2^(-1) mod p?
k3_p = pow(k_known, 3, p)
print(f"\nk^3 mod p = {k3_p}")
print(f"Q * x2^(-1) mod p = {Qx2_inv_p}")
print(f"Match: {k3_p == Qx2_inv_p}")

# What about: does k^3 mod p = Q mod p?
print(f"k^3 mod p = {k3_p}")
print(f"Q mod p = {Q_mod_p}")
print(f"Match: {k3_p == Q_mod_p}")

# Since Q mod p is a cube and k^3 mod p is a cube, check if they're the same cube
# Q * x2^(-1) mod p = k^3 mod p?
print(f"\nQ * x2^(-1) mod p = {Qx2_inv_p}")
print(f"k^3 mod p = {k3_p}")
print(f"Match: {Qx2_inv_p == k3_p}")

# Try all omega shifts
for j in range(3):
    test = k3_p * pow(omega_p, j, p) % p
    print(f"k^3 * omega_p^{j} mod p = {test}")
    print(f"  Match Q*x2^-1? {test == Qx2_inv_p}")
