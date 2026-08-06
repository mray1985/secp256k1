import hashlib
import base58

# -----------------------------------------
# Helper: SHA256, RIPEMD160, and combos
# -----------------------------------------

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def ripemd160_hex(data: bytes) -> str:
    h = hashlib.new("ripemd160")
    h.update(data)
    return h.hexdigest()

def sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def ripemd160_bytes(data: bytes) -> bytes:
    h = hashlib.new("ripemd160")
    h.update(data)
    return h.digest()


# -----------------------------------------
# Convert integer or hex into bytes
# -----------------------------------------

def to_bytes(source):
    if isinstance(source, int):
        # convert integer to hex
        hx = hex(source)[2:]
        if len(hx) % 2 == 1:
            hx = "0" + hx
        return bytes.fromhex(hx)
    elif isinstance(source, str):
        # hex string input
        source = source.replace(" ", "").replace("\n", "")
        if all(c in "0123456789abcdefABCDEF" for c in source):
            if len(source) % 2 == 1:
                source = "0" + source
            return bytes.fromhex(source)
        else:
            # assume raw text
            return source.encode()
    else:
        raise ValueError("Unsupported input type.")


# -----------------------------------------
# Extract digit residues (sliding windows)
# -----------------------------------------

def digit_residues(decimal_string):
    s = decimal_string
    residues = {
        "digits": list(s),
        "pairs": [s[i:i+2] for i in range(len(s)-1)],
        "triplets": [s[i:i+3] for i in range(len(s)-2)],
    }
    return residues


# -----------------------------------------
# Compute ALL residues for entire pipeline
# -----------------------------------------

def residue_map_pipeline(seed):
    """seed can be: private key, pubkeyX decimal, RIPEMD160, or hex"""
    
    raw = to_bytes(seed)

    # Step 1: SHA256
    sha1 = sha256_bytes(raw)
    sha1_hex = sha1.hex()

    # Step 2: RIPEMD160(SHA256)
    rmd = ripemd160_bytes(sha1)
    rmd_hex = rmd.hex()

    # Step 3: SHA256(RMD)
    sha2 = sha256_bytes(rmd)
    sha2_hex = sha2.hex()

    # Step 4: Double-SHA256 checksum
    checksum = sha256_bytes(sha2)[:4]
    checksum_int = int.from_bytes(checksum, "big")

    # Step 5: Base58Check (prefix 0x00)
    addr = base58.b58encode(b"\x00" + rmd + checksum).decode()

    # Produce decimal forms for all components
    dec_private = str(int.from_bytes(raw, "big"))
    dec_sha1 = str(int(sha1_hex, 16))
    dec_rmd = str(int(rmd_hex, 16))
    dec_sha2 = str(int(sha2_hex, 16))
    dec_checksum = str(checksum_int)

    # Expand Base58 to decimal
    dec_address = ""
    for ch in addr:
        dec_address += str(ord(ch))  # structural representation

    # Build full residue map
    return {
        "input_decimal": dec_private,
        "sha256_1_decimal": dec_sha1,
        "rmd160_decimal": dec_rmd,
        "sha256_2_decimal": dec_sha2,
        "checksum_decimal": dec_checksum,
        "address_decimal": dec_address,

        "input_residues": digit_residues(dec_private),
        "sha1_residues": digit_residues(dec_sha1),
        "rmd_residues": digit_residues(dec_rmd),
        "sha2_residues": digit_residues(dec_sha2),
        "checksum_residues": digit_residues(dec_checksum),
        "address_residues": digit_residues(dec_address),
    }


# -----------------------------------------
# Nice printout
# -----------------------------------------

def print_residue_map(mapdata):
    print("\n===== CRYPTO RESIDUE MAP =====\n")

    for label in ["input_decimal", "sha256_1_decimal", "rmd160_decimal",
                  "sha256_2_decimal", "checksum_decimal", "address_decimal"]:

        print(f"{label}:")
        print(mapdata[label])
        print()

    print("=== Triplet leakage lanes (input → address) ===")
    inp = mapdata["input_residues"]["triplets"]
    out = mapdata["address_residues"]["triplets"]

    # Compare aligned positions
    limit = min(len(inp), len(out))
    for i in range(limit):
        if inp[i] == out[i]:
            print(f"Match at lane {i}: {inp[i]}")
