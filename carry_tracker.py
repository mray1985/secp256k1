"""
EC Carry Tracker for secp256k1
Tracks the modular carry k at every doubling and addition step.

The carry identity:
  Doubling: 3x^2 = lambda * 2y + k * p   =>  k = (3x^2 - lambda*2y) / p
  Addition: (y_Q - y_P) = lambda * (x_Q - x_P) + k * p  => k = (y_Q - y_P - lambda*(x_Q - x_P)) / p

where lambda is the standard EC slope mod p.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G = (Gx, Gy)
INFINITY = None

def ec_add(P, Q):
    if P is None: return Q
    if Q is None: return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and y1 == y2:
        lam = (3 * x1 * x1 * pow(2 * y1, -1, p)) % p
    elif x1 == x2:
        return None
    else:
        lam = ((y2 - y1) * pow((x2 - x1) % p, -1, p)) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)


def ec_add_carry(P, Q):
    """EC addition returning (result, carry_double, carry_add).
    For doubling: carry is from 3x^2 = lam*2y + k*p
    For addition: carry is from (y_Q-y_P) = lam*(x_Q-x_P) + k*p
    Returns (R, k_double_or_None, k_add_or_None)
    """
    if P is None: return (Q, None, None)
    if Q is None: return (P, None, None)
    x1, y1 = P
    x2, y2 = Q

    if x1 == x2 and y1 == y2:
        # DOUBLING
        two_y = (2 * y1) % p
        three_x2 = (3 * x1 * x1) % p
        two_y_inv = pow(two_y, -1, p)
        lam = (three_x2 * two_y_inv) % p

        # Carry: 3*x1^2 = lam * 2*y1 + k * p  (as integers)
        # But 3*x1^2 and lam*2*y1 are huge. Compute k = (3*x1^2 - lam*2*y1) / p
        lhs = 3 * x1 * x1
        rhs = lam * 2 * y1
        k = (lhs - rhs) // p
        assert lhs - rhs == k * p, "Carry identity broken for doubling!"

        x3 = (lam * lam - 2 * x1) % p
        y3 = (lam * (x1 - x3) - y1) % p
        return ((x3, y3), k, None)

    elif x1 == x2:
        return (None, None, None)

    else:
        # ADDITION
        dx = (x2 - x1) % p
        dy = (y2 - y1) % p
        dx_inv = pow(dx, -1, p)
        lam = (dy * dx_inv) % p

        # Carry: (y2 - y1) = lam * (x2 - x1) + k * p  (using actual integer differences)
        actual_dy = y2 - y1  # can be negative
        actual_dx = x2 - x1  # can be negative
        k = (actual_dy - lam * actual_dx) // p
        assert actual_dy - lam * actual_dx == k * p, f"Carry identity broken for addition! diff={actual_dy - lam * actual_dx}, k*p={k*p}"

        x3 = (lam * lam - x1 - x2) % p
        y3 = (lam * (x1 - x3) - y1) % p
        return ((x3, y3), None, k)


def ec_mul_carry(scalar, point):
    """Double-and-add with full carry tracking.
    Returns (result_point, carry_log) where carry_log is a list of
    (operation, carry_value, t_value, current_point) tuples.
    """
    result = None
    addend = point
    carry_log = []
    bits = bin(scalar)[2:]

    for i, bit in enumerate(bits):
        if bit == '1':
            # Double then Add: first double result, then add addend
            # But actually in standard double-and-add (left-to-right):
            # result = 2*result (if i > 0), then result = result + addend

            if result is not None:
                # Double
                result, k_dbl, _ = ec_add_carry(result, result)
                t_val = pow(result[0], 3, p) if result else None
                carry_log.append(('double', k_dbl, t_val, result))

            # Add
            result, _, k_add = ec_add_carry(result, addend)
            t_val = pow(result[0], 3, p) if result else None
            carry_log.append(('add', k_add, t_val, result))
        else:
            # Just double
            if result is not None:
                result, k_dbl, _ = ec_add_carry(result, result)
                t_val = pow(result[0], 3, p) if result else None
                carry_log.append(('double', k_dbl, t_val, result))

    return result, carry_log


def ec_mul_carry_window(scalar, point, window_bits=4):
    """Double-and-add with window method and carry tracking."""
    # Precompute multiples
    precomp = {1: point}
    for i in range(2, 2**window_bits):
        precomp[i] = ec_add(precomp[i-1], point)

    result = None
    carry_log = []
    bits = bin(scalar)[2:]

    # Process in chunks
    i = 0
    while i < len(bits):
        # Find window
        chunk = bits[i:i+window_bits]
        w = int(chunk, 2)

        # Double window_bits times
        for _ in range(len(chunk)):
            if result is not None:
                result, k_dbl, _ = ec_add_carry(result, result)
                t_val = pow(result[0], 3, p) if result else None
                carry_log.append(('double', k_dbl, t_val, result))

        # Add window value
        if w > 0 and result is not None:
            result, _, k_add = ec_add_carry(result, precomp[w])
            t_val = pow(result[0], 3, p) if result else None
            carry_log.append(('add', k_add, t_val, result))
        elif w > 0:
            result = precomp[w]

        i += window_bits

    return result, carry_log


# ============================================================
# Run for Puzzle 135
# ============================================================
print("=" * 80)
print("CARRY TRACKER: Puzzle 135 (d * G)")
print("=" * 80)

d = 6681363927270169459683534526047340939294822242524004800730956682266291524995
print(f"d = {d}")
print(f"d bit_length = {d.bit_length()}")
print(f"d bits = {bin(d)[2:]}")
print()

P, carry_log = ec_mul_carry(d, G)

print(f"d*G = ({P[0]}, {P[1]})")
print(f"Verify on curve: {pow(P[1], 2, p) == (pow(P[0], 3, p) + 7) % p}")
print(f"Total operations: {len(carry_log)}")
print()

# Summary statistics
dbl_carries = [c[1] for c in carry_log if c[0] == 'double']
add_carries = [c[1] for c in carry_log if c[0] == 'add' and c[1] is not None]
print(f"Double operations: {len(dbl_carries)}")
print(f"Add operations: {len(add_carries)}")
print()

if dbl_carries:
    print(f"Double carry range: [{min(dbl_carries)}, {max(dbl_carries)}]")
    print(f"Double carry mean: {sum(dbl_carries) / len(dbl_carries):.2f}")
    print(f"Double carry sum: {sum(dbl_carries)}")
if add_carries:
    print(f"Add carry range: [{min(add_carries)}, {max(add_carries)}]")
    print(f"Add carry mean: {sum(add_carries) / len(add_carries):.2f}")
    print(f"Add carry sum: {sum(add_carries)}")
print()

# Print first 20 and last 20 operations
print("--- First 30 operations ---")
for i, (op, carry, t_val, pt) in enumerate(carry_log[:30]):
    t_hex = hex(t_val) if t_val else "None"
    c_str = str(carry) if carry is not None else "N/A"
    print(f"  [{i:3d}] {op:6s}  carry={c_str:>10s}  t={t_hex}")

print(f"  ... ({len(carry_log) - 60} more) ...")

print("--- Last 30 operations ---")
for i, (op, carry, t_val, pt) in enumerate(carry_log[-30:], len(carry_log)-30):
    t_hex = hex(t_val) if t_val else "None"
    c_str = str(carry) if carry is not None else "N/A"
    print(f"  [{i:3d}] {op:6s}  carry={c_str:>10s}  t={t_hex}")
print()

# ============================================================
# Analyze carry patterns
# ============================================================
print("=" * 80)
print("CARRY PATTERN ANALYSIS")
print("=" * 80)

# Check: do carries relate to t_P = x^3 mod p?
print("\n--- Carry vs t_P correlation ---")
all_ops = [(i, op, carry, t_val) for i, (op, carry, t_val, pt) in enumerate(carry_log)]

# For doubling carries, check if carry relates to t_P
dbl_ops = [(i, carry, t_val) for i, op, carry, t_val in all_ops if op == 'double' and carry is not None]
if dbl_ops:
    carries_d = [c for _, c, _ in dbl_ops]
    t_vals_d = [t for _, _, t in dbl_ops]

    # Check: is carry = (t^2 + something) / (something)?
    # From the doubling recurrence: t_{2P} = [t(t-56)^3 / (64(t+7)^3)]_p
    # The carry should relate to how much t*... overflows p

    print(f"Number of double carries: {len(carries_d)}")
    print(f"Carry values (first 20): {carries_d[:20]}")
    print()

    # Check if carry is related to t_P / p (the fractional part)
    # carry_k = (3x^2 - lambda*2y) / p
    # And t = x^3 mod p, so x^3 = t + alpha*p for some alpha
    # 3x^2 relates to dt/dx which relates to the curve slope

    # Just check: unique carry values
    unique_carries = sorted(set(carries_d))
    print(f"Unique double carry values: {len(unique_carries)}")
    if len(unique_carries) <= 20:
        for c in unique_carries:
            count = carries_d.count(c)
            print(f"  carry={c:>4d}: appears {count} times")
    print()

# For addition carries
add_ops = [(i, carry, t_val) for i, op, carry, t_val in all_ops if op == 'add' and carry is not None]
if add_ops:
    carries_a = [c for _, c, _ in add_ops]
    print(f"Number of add carries: {len(carries_a)}")
    print(f"Carry values (first 20): {carries_a[:20]}")
    unique_add = sorted(set(carries_a))
    print(f"Unique add carry values: {len(unique_add)}")
    if len(unique_add) <= 30:
        for c in unique_add:
            count = carries_a.count(c)
            print(f"  carry={c:>4d}: appears {count} times")
    print()

# ============================================================
# Connect to cubic chain: check t_P = x^3 mod p at each step
# ============================================================
print("=" * 80)
print("T_P = x^3 mod p AT EACH STEP (connection to cubic chain)")
print("=" * 80)

# The doubling recurrence: t_{2P} = [t_P(t_P - 56)^3 / (64(t_P + 7)^3)]_p
# Check if this matches our computed t values

def t_doubling_formula(t):
    """Compute t_{2P} from t_P using the closed-form doubling formula."""
    num = t * pow(t - 56, 3, p) % p
    den = pow(64 * pow(t + 7, 3, p), -1, p) % p
    return (num * den) % p

# Verify: does the doubling formula match our EC computation?
print("\nVerifying doubling formula against EC computation...")
mismatches = 0
for i, (op, carry, t_val, pt) in enumerate(carry_log):
    if op == 'double' and t_val is not None:
        # Get previous t value
        if i > 0:
            prev_t = carry_log[i-1][2]
            if prev_t is not None:
                expected_t = t_doubling_formula(prev_t)
                if expected_t != t_val:
                    mismatches += 1
                    if mismatches <= 3:
                        print(f"  MISMATCH at step {i}: expected {hex(expected_t)}, got {hex(t_val)}")

print(f"  Total mismatches: {mismatches} / {len([c for c in carry_log if c[0]=='double'])}")
print()

# Now: the cubic chain from claude.txt
# x2 = P_135.x^3 mod p
# C1 = x2^3 mod N
# The chain: C1 -> cube root mod N -> x2 -> cube root mod p -> P.x

# Check: does the carry at each step relate to the cube root structure?
# Specifically: does carry mod 3, carry mod Delta, etc. show patterns?

print("--- Carry modulo analysis ---")
Delta = p - N
print(f"Delta = p - N = {Delta}")
print(f"Delta bit_length = {Delta.bit_length()}")
print()

# Check carries mod Delta
if dbl_carries:
    dbl_mod_delta = [c % Delta for c in dbl_carries]
    print(f"Double carries mod Delta: first 20 = {dbl_mod_delta[:20]}")
    print(f"  Unique values mod Delta: {len(set(dbl_mod_delta))}")
print()

# Check carries mod 3
if dbl_carries:
    dbl_mod3 = [c % 3 for c in dbl_carries]
    from collections import Counter
    c3 = Counter(dbl_mod3)
    print(f"Double carries mod 3: {dict(c3)}")
if add_carries:
    add_mod3 = [c % 3 for c in add_carries]
    c3a = Counter(add_mod3)
    print(f"Add carries mod 3: {dict(c3a)}")
print()

# Check carries mod s (the ECDSA s value)
s_val = 0x224a322e81c044d341521f65fabdfa86d84673fb55ed7533862e37f7724931fa
if dbl_carries:
    dbl_mod_s = [c % s_val for c in dbl_carries]
    print(f"Double carries mod s: first 10 = {[hex(x) for x in dbl_mod_s[:10]]}")
    print(f"  Unique values mod s: {len(set(dbl_mod_s))}")
print()

# ============================================================
# Key insight: track t_P and carry together through the chain
# ============================================================
print("=" * 80)
print("FULL CHAIN: t_P and carry at each doubling step")
print("=" * 80)

# Show the first 50 steps with t_P and carry
for i, (op, carry, t_val, pt) in enumerate(carry_log[:50]):
    if t_val:
        t_hex = hex(t_val)
        c_str = str(carry) if carry is not None else "N/A"
        print(f"  [{i:3d}] {op:6s}  carry={c_str:>6s}  t_P={t_hex}")
print(f"  ... ({len(carry_log) - 50} more) ...")
