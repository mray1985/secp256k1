# secp256k1 midpoint between 2^134 and 2^135 tri-fold echoes
# -----------------------------------------------------------
# Compute x_mid = sqrt(x134 * x135) mod p
# and verify y_mid from y^2 = x^3 + 7 mod p

# secp256k1 prime
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F

# your second tri-fold x-values (hex)
x134 = 0x57F7BB166C6D3C90673A24124199D85A95E73D41701440A0E3BD72B0218039DE
x135 = 0xf478056d9c102c1cd06d7b1e7557244c6d9cdac5874610e94d4786e106de12c0

# 1. multiply and reduce mod p
prod = (x134 * x135) % p

# 2. compute modular square root (since p ≡ 3 mod 4)
x_mid = pow(prod, (p + 1) // 4, p)

# 3. compute y from y^2 = x^3 + 7 mod p
y_sq = (pow(x_mid, 3, p) + 7) % p
y_mid = pow(y_sq, (p + 1) // 4, p)

# 4. verify on-curve
is_on_curve = (pow(y_mid, 2, p) - (pow(x_mid, 3, p) + 7)) % p == 0

# 5. display results
print("x_mid =", hex(x_mid))
print("y_mid =", hex(y_mid))
print("On curve:", is_on_curve)
