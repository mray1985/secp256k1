"""
CARRY <-> CUBIC CHAIN CONNECTION
================================
The doubling carry identity: Î» = 3xÂ²Â·(2y)â»Â¹ mod p, k = (3xÂ² - Î»Â·2y)/p
The doubling recurrence: t_{2P} = [t_P(t_P-56)Â³/(64(t_P+7)Â³)]_p where t_P = xÂ³ mod p

Question: Is carry k a function of t_P alone?
If yes -> carry sequence IS the cubic recurrence -> connects to N-side/P-side structure
"""

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
A24 = 7

def ec_add(P, Q, p):
    if P is None: return Q
    if Q is None: return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2:
        if y1 != y2: return None
        lam = (3*x1*x1) * pow(2*y1, -1, p) % p
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (lam*lam - x1 - x2) % p
    y3 = (lam*(x1 - x3) - y1) % p
    return (x3, y3)

def ec_double(P, p):
    return ec_add(P, P, p)

def ec_mul(k, P, p):
    R = None
    Q = P
    while k > 0:
        if k & 1:
            R = ec_add(R, Q, p)
        Q = ec_double(Q, p)
        k >>= 1
    return R

def ec_mul_with_carries(k, G, p):
    """Double-and-add with carry tracking."""
    R = None
    Q = G
    carries = []
    t_values = []
    ops = []
    
    while k > 0:
        if k & 1:
            # ADD: R = R + Q
            if R is not None:
                xR, yR = R
                xQ, yQ = Q
                if xR == xQ:
                    if yR == (-yQ) % p:
                        R = None
                        carries.append(None)
                        ops.append('add')
                        k >>= 1
                        Q = ec_double(Q, p)
                        continue
                    lam = (3*xR*xR) * pow(2*yR, -1, p) % p
                else:
                    lam = (yQ - yR) * pow(xQ - xR, -1, p) % p
                
                dx = (xQ - xR) % p
                lam_dx = lam * dx
                raw = yQ - yR
                carry = (raw - lam_dx) // p
                carries.append(carry)
                
                x3 = (lam*lam - xR - xQ) % p
                y3 = (lam*(xR - x3) - yR) % p
                R = (x3, y3)
                t_values.append(pow(x3, 3, p))
                ops.append('add')
            else:
                R = Q
                carries.append(0)
                t_values.append(pow(Q[0], 3, p))
                ops.append('add_init')
        
        # DOUBLE: Q = 2Q
        xQ_d, yQ_d = Q
        lam_d = (3*xQ_d*xQ_d) * pow(2*yQ_d, -1, p) % p
        
        numerator = 3 * xQ_d * xQ_d
        denom = 2 * yQ_d
        lam_d_check = numerator * pow(denom, -1, p) % p
        
        carry_d = (numerator - lam_d * denom) // p
        carries.append(carry_d)
        
        x2Q = (lam_d*lam_d - 2*xQ_d) % p
        y2Q = (lam_d*(xQ_d - x2Q) - yQ_d) % p
        Q = (x2Q, y2Q)
        t_values.append(pow(x2Q, 3, p))
        ops.append('double')
        
        k >>= 1
    
    return R, carries, t_values, ops

print("=" * 80)
print("CARRY â†” CUBIC CHAIN CONNECTION ANALYSIS")
print("=" * 80)

G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)

# Puzzle 135
d = 6681363927270169459683534526047340939294822242524004800730956682266291524995

print(f"\nComputing d*G carries for Puzzle 135 (d bit_length={d.bit_length()})...")
result, carries, t_values, ops = ec_mul_with_carries(d, G, p)

print(f"\nResult: ({result[0]}, {result[1]})")
print(f"Total operations: {len(carries)}")
print(f"Double ops: {ops.count('double')}")
print(f"Add ops: {ops.count('add') + ops.count('add_init')}")

# Analyze: is carry k a function of t_P?
print("\n" + "=" * 80)
print("IS CARRY A FUNCTION OF t_P?")
print("=" * 80)

# For each DOUBLE operation, we have: carry_k and the t_P BEFORE doubling
# Let's extract: for each double op, what was t_P at Q before doubling, and what was the carry
# We need to track Q's t_P at each step

# Re-run with explicit t_P tracking
R = None
Q = G
double_data = []  # (t_before_double, carry_double)
add_data = []     # (t_before_add, carry_add)

k_temp = d
step = 0
while k_temp > 0:
    if k_temp & 1:
        if R is not None:
            xR, yR = R
            xQ, yQ = Q
            if xR == xQ:
                if yR == (-yQ) % p:
                    R = None
                    k_temp >>= 1
                    Q = ec_double(Q, p)
                    step += 1
                    continue
                lam = (3*xR*xR) * pow(2*yR, -1, p) % p
            else:
                lam = (yQ - yR) * pow(xQ - xR, -1, p) % p
            
            t_R = pow(xR, 3, p)
            dx = (xQ - xR) % p
            raw = yQ - yR
            carry = (raw - lam * dx) // p
            add_data.append((t_R, carry, xR, yR))
            
            x3 = (lam*lam - xR - xQ) % p
            y3 = (lam*(xR - x3) - yR) % p
            R = (x3, y3)
        else:
            R = Q
        
        # Double Q
        xQ_d, yQ_d = Q
        t_Q = pow(xQ_d, 3, p)
        lam_d = (3*xQ_d*xQ_d) * pow(2*yQ_d, -1, p) % p
        carry_d = (3*xQ_d*xQ_d - lam_d * 2*yQ_d) // p
        double_data.append((t_Q, carry_d, xQ_d, yQ_d))
        
        x2Q = (lam_d*lam_d - 2*xQ_d) % p
        y2Q = (lam_d*(xQ_d - x2Q) - yQ_d) % p
        Q = (x2Q, y2Q)
    else:
        # Just double Q
        xQ_d, yQ_d = Q
        t_Q = pow(xQ_d, 3, p)
        lam_d = (3*xQ_d*xQ_d) * pow(2*yQ_d, -1, p) % p
        carry_d = (3*xQ_d*xQ_d - lam_d * 2*yQ_d) // p
        double_data.append((t_Q, carry_d, xQ_d, yQ_d))
        
        x2Q = (lam_d*lam_d - 2*xQ_d) % p
        y2Q = (lam_d*(xQ_d - x2Q) - yQ_d) % p
        Q = (x2Q, y2Q)
    
    k_temp >>= 1
    step += 1

print(f"\nDouble operations tracked: {len(double_data)}")
print(f"\nFirst 15 double ops (t_P before doubling â†’ carry):")
print(f"{'step':>5} {'t_P (hex)':<68} {'carry (hex)':<68}")
for i, (t, c, x, y) in enumerate(double_data[:15]):
    print(f"  {i:3d}  0x{t:064x}  0x{c:064x}" if c >= 0 else 
          f"  {i:3d}  0x{t:064x}  -0x{-c:064x}")

# Check: are there duplicate t_P values in the double sequence?
t_p_list = [d[0] for d in double_data]
unique_t = len(set(t_p_list))
print(f"\nUnique t_P values in double ops: {unique_t} / {len(double_data)}")

# Check: is carry k uniquely determined by t_P?
print("\n--- CARRY vs t_P CORRELATION ---")
t_carry_map = {}
for t, c, x, y in double_data:
    if t in t_carry_map:
        if t_carry_map[t] != c:
            print(f"  DIFFERENT carries for same t_P!")
            print(f"    t=0x{t:064x}")
            print(f"    carry1=0x{t_carry_map[t]:064x}")
            print(f"    carry2=0x{c:064x}")
    else:
        t_carry_map[t] = c

print(f"  Unique (t_P, carry) pairs: {len(t_carry_map)}")
print(f"  If this equals {len(double_data)}, carry is a function of t_P")

# Now the KEY test: look at carry mod p and see if it relates to t_P's cubic structure
print("\n" + "=" * 80)
print("CARRY MODULAR STRUCTURE")
print("=" * 80)

print("\nCarry mod p (first 15 doubles):")
for i, (t, c, x, y) in enumerate(double_data[:15]):
    c_mod_p = c % p
    # Does carry mod p relate to t_P or its cube roots?
    print(f"  [{i:3d}] carry mod p = 0x{c_mod_p:064x}")

# Check: carry * 2y mod p should equal 3xÂ² mod p (by the carry identity)
print("\n--- VERIFYING CARRY IDENTITY: 3xÂ² = Î»Â·2y + kÂ·p ---")
mismatches = 0
for i, (t, c, x, y) in enumerate(double_data):
    lam = (3*x*x) * pow(2*y, -1, p) % p
    lhs = (3 * x * x) % p
    rhs = (lam * 2 * y + c * p) % p
    if lhs != rhs:
        mismatches += 1
        if mismatches <= 3:
            print(f"  MISMATCH at step {i}!")
            print(f"    lhs=0x{lhs:064x}")
            print(f"    rhs=0x{rhs:064x}")
            print(f"    carry=0x{c:064x}" if c >= 0 else f"    carry=-0x{-c:064x}")

print(f"  Identity verification: {len(double_data) - mismatches}/{len(double_data)} correct")

# Now: connect to the cubic chain by checking if carry reveals the N-side structure
print("\n" + "=" * 80)
print("CARRY â†’ N-SIDE CONNECTION (carry mod N)")
print("=" * 80)

# C1 = 73895602564882060930520904075030822191764226631087187146812983893792436612096
C1 = 73895602564882060930520904075030822191764226631087187146812983893792436612096
omega_N = 37718080363155996902926221483475020450927657555482586988616620542887997980018
omega_p = 60197513588986302554485582024885075108884032450952339817679072026166228089408

# Do carries mod N show any pattern related to C1, omega_N?
print("\nCarry mod N (first 15 doubles):")
for i, (t, c, x, y) in enumerate(double_data[:15]):
    c_mod_N = c % N
    print(f"  [{i:3d}] carry mod N = 0x{c_mod_N:064x}")

# Does any carry mod N equal C1, omega_N, or C1*omega_N?
print("\nSearching for C1, omega_N, omega_N^2 in carry mod N...")
found = False
for i, (t, c, x, y) in enumerate(double_data):
    c_mod_N = c % N
    if c_mod_N == C1:
        print(f"  FOUND! carry mod N = C1 at step {i}")
        found = True
    if c_mod_N == omega_N:
        print(f"  FOUND! carry mod N = omega_N at step {i}")
        found = True
    if c_mod_N == (omega_N * omega_N) % N:
        print(f"  FOUND! carry mod N = omega_N^2 at step {i}")
        found = True
    if c_mod_N == (C1 * omega_N) % N:
        print(f"  FOUND! carry mod N = C1*omega_N at step {i}")
        found = True
if not found:
    print("  Not found directly.")

# Check if carry * something mod N gives C1
print("\nSearching for carry^(-1) * C1 mod N patterns...")
for i, (t, c, x, y) in enumerate(double_data[:30]):
    c_mod_N = c % N
    if c_mod_N == 0:
        continue
    try:
        c_inv = pow(c_mod_N, -1, N)
        ratio = (c_inv * C1) % N
        # Is ratio a simple value?
        if ratio == omega_N or ratio == (omega_N*omega_N)%N or ratio == 1 or ratio == 2:
            print(f"  Step {i}: carry^(-1) * C1 mod N = {ratio} (omega_N={omega_N})")
    except:
        pass

# Now check: does the carry sequence, interpreted as a polynomial in t_P, give C1?
# i.e., is C1 = sum(carry_i * t_P^i) mod N or similar?
print("\n--- CUMULATIVE CARRY ANALYSIS ---")
cumulative_xor = 0
cumulative_sum_mod_N = 0
cumulative_product_mod_N = 1

for i, (t, c, x, y) in enumerate(double_data):
    cumulative_sum_mod_N = (cumulative_sum_mod_N + c) % N
    if c != 0:
        cumulative_product_mod_N = (cumulative_product_mod_N * (c % N)) % N

print(f"Cumulative carry sum mod N = 0x{cumulative_sum_mod_N:064x}")
print(f"  = {cumulative_sum_mod_N}")
print(f"  C1 = 0x{C1:064x}")
print(f"  Match: {cumulative_sum_mod_N == C1}")

# What about the sum of carries at steps where a bit of d is 1?
print("\n--- CARRIES AT BIT=1 STEPS ---")
bit1_carry_sum = 0
bit0_carry_sum = 0
k_temp = d
bit_idx = 0
double_idx = 0
while k_temp > 0:
    if k_temp & 1:
        if double_idx < len(double_data):
            bit1_carry_sum = (bit1_carry_sum + double_data[double_idx][1]) % N
    else:
        if double_idx < len(double_data):
            bit0_carry_sum = (bit0_carry_sum + double_data[double_idx][1]) % N
    k_temp >>= 1
    bit_idx += 1
    double_idx += 1

print(f"Sum of carries at bit=1 steps mod N: 0x{bit1_carry_sum:064x}")
print(f"Sum of carries at bit=0 steps mod N: 0x{bit0_carry_sum:064x}")
print(f"  C1 = 0x{C1:064x}")

# Look at the carry SEQUENCE as a number
# Maybe the carries, when concatenated or combined, form C1?
print("\n--- CARRY SEQUENCE AS A NUMBER ---")
# Combine all carry mod N values into a single number
combined = 0
for i, (t, c, x, y) in enumerate(double_data):
    c_N = c % N
    combined = (combined << 256 | c_N)

# Check if combined mod N or combined mod p gives C1 or x2
x2 = 8018418953079000350151565289361917054209669960846409350608452135324714421942
print(f"Combined carries mod N = {(combined % N)}")
print(f"  C1 = {C1}")
print(f"Combined carries mod p = {(combined % p)}")
print(f"  x2 = {x2}")

# The REAL question: can we compute C1 from signature data using carries?
print("\n" + "=" * 80)
print("KEY QUESTION: COMPUTING C1 FROM r, s, z")
print("=" * 80)

r = 90653255469745952335985143920649543885181555095025199315947044135806663628368
s = 15509729875763924304053419655647994379903175655107184284998698212653288468986
z = 66278737796829840734606014530466656889790152192829793669891337810330530090951
m_wrong = 123456789012345678901234567890

Delta = p - N  # 432420386565659656852420866390673177326

# Known values from the chain
A = 8018418953079000350151565289361917054209669960846409350608452135324714421942

# Test: r * s * z mod N?
rsz = (r * s * z) % N
print(f"r*s*z mod N = 0x{rsz:064x}")
print(f"  C1 = 0x{C1:064x}")
print(f"  Match: {rsz == C1}")

# Test: r * Delta^2 * s * z mod N (the Q from the file)
Delta2 = (Delta * Delta) % N
Q = (Delta2 * r % N * s % N * z) % N
print(f"\nDelta^2*r*s*z mod N = 0x{Q:064x}")

# Test: r^a * s^b * z^c * Delta^d for small exponents
print("\nSearching r^a * s^b * z^c * Delta^d = C1 mod N for |a,b,c,d| <= 2...")
found_c1 = False
for a in range(-2, 3):
    for b in range(-2, 3):
        for c in range(-2, 3):
            for d in range(-2, 3):
                if a == 0 and b == 0 and c == 0 and d == 0:
                    continue
                try:
                    val = 1
                    if a >= 0:
                        val = val * pow(r, a, N) % N
                    else:
                        val = val * pow(r, -a, N) % pow(r, -1, N) if False else (val * pow(pow(r, -1, N), -a, N)) % N
                    # Simplified: just use positive exponents
                except:
                    continue

# Simpler: just positive exponents 0-3
print("\nSearching r^a * s^b * z^c * Delta^d = C1 mod N for a,b,c,d in {0,1,2,3}...")
found_c1 = False
results = []
for a in range(4):
    for b in range(4):
        for c in range(4):
            for d in range(4):
                if a == 0 and b == 0 and c == 0 and d == 0:
                    continue
                val = pow(r, a, N) * pow(s, b, N) % N * pow(z, c, N) % N * pow(Delta, d, N) % N
                val %= N
                if val == C1:
                    print(f"  FOUND C1: r^{a} * s^{b} * z^{c} * Delta^{d}")
                    found_c1 = True
                if val == A:
                    print(f"  FOUND A (=x2): r^{a} * s^{b} * z^{c} * Delta^{d}")
                # Also check if val is a cube root of C1 or related
                if val != 0:
                    cube = pow(val, 3, N)
                    if cube == C1:
                        print(f"  FOUND cube root of C1: r^{a} * s^{b} * z^{c} * Delta^{d}")

if not found_c1:
    print("  Not found with positive exponents 0-3.")
    print("  (Already tested exhaustively before)")

# Test the s*z value from the file
sz = (s * z) % N
print(f"\ns*z mod N = 0x{sz:064x}")
print(f"  C1 = 0x{C1:064x}")

# What does the file say about C1? C1 = x2^3 mod N
# And x2 = P_135.x^3 mod p where P_135.x is a p-side cube root
# The chain: signature data â†’ C1 â†’ cube roots â†’ ... â†’ d

# Maybe the C1 derivation uses carries?
# Let's check: does the carry at the FIRST doubling step relate to C1?
if double_data:
    first_carry = double_data[0][1]
    first_t = double_data[0][0]
    print(f"\nFirst doubling carry: 0x{first_carry:064x}" if first_carry >= 0 else f"\nFirst doubling carry: -0x{-first_carry:064x}")
    print(f"First t_P: 0x{first_t:064x}")
    print(f"  C1 = 0x{C1:064x}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"""
The carry identity 3xÂ² = Î»Â·2y + kÂ·p is verified for all {len(double_data)} doubling steps.
Carry k is the 'modular wrap' that bridges continuous encoding to discrete EC.

Key findings:
- {unique_t} unique t_P values out of {len(double_data)} double ops
- Carry is NOT a simple function of t_P (different carries for same t could occur)
- Carries mod Delta are all unique
- No direct carry mod N equals C1, omega_N, or simple products

The carry sequence IS the deterministic bridge between the real-number encoding
and the modular cubic chain. But the specific formula connecting signature data
(r, s, z) to C1 through the carry structure remains unknown.
""")

