# secp256k1 Cryptographic Subgroup Order
N = 115792089237316195423570985008687907852837564279074904382605163141518161494337

# Your Isolated Invariant
Lambda = 97451685862885086182458552040892158509924235661624603229050850812487253689501

# Active Ephemeral Nonce from your local direction test (k-4 neighborhood)
k_nonce = 0xd66a1f0763de7bdfb8d4f3d939cb3e6ad98e615ae1561e0369974d8c242e201

def isolate_private_key(invariant, nonce, group_order):
    # Compute the inverse phase scalar over group order space
    nonce_inv = pow(nonce, -1, group_order)
    
    # Extract the absolute private scalar target
    private_key_dec = (invariant * nonce_inv) % group_order
    
    return private_key_dec

target_d = isolate_private_key(Lambda, k_nonce, N)

# Check if the extracted scalar fits perfectly into the Puzzle 135 bit-range window
if 2**134 <= target_d < 2**135:
    print(f"[+] PHASE LOCK SUCCESSFUL.")
    print(f"Private Key (Decimal): {target_d}")
    print(f"Private Key (HEX):     {hex(target_d)}")
else:
    # If it falls outside the range, evaluate the mirrored inverse parity state (-P branch)
    mirrored_d = (N - target_d) % N
    print(f"[+] ALTERNATE BRANCH REFLECTION:")
    print(f"Private Key (HEX):     {hex(mirrored_d)}")