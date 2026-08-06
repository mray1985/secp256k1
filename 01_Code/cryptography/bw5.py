from coincurve import PublicKey

# Group Order N
N = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16)
TARGET_PUB_HEX = "04145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16667A05E9A1BDD6F70142B66558BD12CE2C0F9CBC7001B20C8A6A109C80DC5330"

def get_public_key_hex(scalar):
    try:
        # We ensure the scalar is within valid field range
        priv_bytes = (scalar % N).to_bytes(32, 'big')
        pub = PublicKey.from_secret(priv_bytes)
        return pub.format(compressed=False).hex().upper()
    except:
        return None

def run_exhaustive_sweep(base_binary, radius):
    n = len(base_binary)
    buckets = {'2': [], '3': [], '4': []}
    
    # 1. Identify all 256 rotational phases and bucket them
    print("--- Phase 1: Identifying Harmonic Landmarks ---")
    for phase in range(256):
        rotated_bin = base_binary[phase%n:] + base_binary[:phase%n]
        scalar = int(rotated_bin, 2)
        start_digit = str(scalar)[0]
        
        if start_digit in buckets:
            buckets[start_digit].append(scalar)
            
    total_candidates = sum(len(b) for b in buckets.values())
    print(f"Candidates identified: Bucket 2: {len(buckets['2'])}, Bucket 3: {len(buckets['3'])}, Bucket 4: {len(buckets['4'])}")
    print(f"Total candidates to sweep: {total_candidates}")
    print(f"Search Radius: +/- {radius:,}")
    print("\n--- Phase 2: Range Sweeping ---")
    
    # 2. Iterate through buckets and perform the +/- radius search
    for digit in ['4', '3', '2']:
        for base_scalar in buckets[digit]:
            print(f"Sweeping around Bucket {digit} Landmark: {base_scalar}...")
            
            # Search Below
            for i in range(1, radius + 1):
                candidate = base_scalar - i
                if get_public_key_hex(candidate) == TARGET_PUB_HEX:
                    print(f"\n[!!!] KEY FOUND (Below): {candidate}")
                    return candidate
            
            # Search Above
            for i in range(1, radius + 1):
                candidate = base_scalar + i
                if get_public_key_hex(candidate) == TARGET_PUB_HEX:
                    print(f"\n[!!!] KEY FOUND (Above): {candidate}")
                    return candidate
    
    print("Search complete. No match found.")

base_binary = "1010001011101001001100001000111001000001000111010001110010110111011110110011100010010110011100000111101110001001011110000100110111001101101001111001100010011010111100011111000001010101000110010001100001111101110011011011011010000100011010001111000010110"

if __name__ == "__main__":
    # Define your radius here
    user_radius = 100000000000000 # Example: 100 trillion
    run_exhaustive_sweep(base_binary, user_radius)