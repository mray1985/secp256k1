from coincurve import PublicKey

# SECP256K1 Group Order N
N = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16)
TARGET_PUB_HEX = "04145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16667A05E9A1BDD6F70142B66558BD12CE2C0F9CBC7001B20C8A6A109C80DC5330"

def get_public_key_hex(scalar):
    try:
        # Normalize scalar to valid range before deriving key
        priv_bytes = (scalar % N).to_bytes(32, 'big')
        pub = PublicKey.from_secret(priv_bytes)
        return pub.format(compressed=False).hex().upper()
    except:
        return None

def run_exhaustive_sweep(base_binary, radius):
    n = len(base_binary)
    buckets = {'2': [], '3': [], '4': []}
    
    print("--- Phase 1: Identifying Harmonic Landmarks ---")
    for phase in range(256):
        rotated_bin = base_binary[phase%n:] + base_binary[:phase%n]
        scalar = int(rotated_bin, 2)
        scalar_str = str(scalar)
        start_digit = scalar_str[0]
        
        if start_digit in buckets:
            buckets[start_digit].append(scalar)
            
    print(f"Candidates identified: Bucket 2: {len(buckets['2'])}, Bucket 3: {len(buckets['3'])}, Bucket 4: {len(buckets['4'])}")
    total = sum(len(b) for b in buckets.values())
    print(f"Total bucketed landmarks to sweep: {total}")
    print(f"Search Radius: +/- {radius:,}")
    print("\n--- Phase 2: Range Sweeping ---")
    
    # Priority order for search
    for digit in ['4', '3', '2']:
        for base_scalar in buckets[digit]:
            print(f"Sweeping +/- {radius:,} around Bucket {digit} Landmark: {base_scalar}...")
            
            # Sweeping
            for i in range(1, radius + 1):
                # Search Above and Below
                candidates = [base_scalar + i, base_scalar - i]
                for cand in candidates:
                    if get_public_key_hex(cand) == TARGET_PUB_HEX:
                        print(f"\n[!!!] KEY FOUND: {cand}")
                        return cand
    print("Search complete. No match found.")

# The binary string representing your Puzzle 135 scalar projection
base_binary = "1010001011101001001100001000111001000001000111010001110010110111011110110011100010010110011100000111101110001001011110000100110111001101101001111001100010011010111100011111000001010101000110010001100001111101110011011011011010000100011010001111000010110"

if __name__ == "__main__":
    # WARNING: A radius of 10^14 is computationally massive for a local script.
    run_exhaustive_sweep(base_binary, radius=100000000000000)