from coincurve import PublicKey

# SECP256K1 Group Order N
N = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16)

# Puzzle 135 Target Public Key
TARGET_PUB_HEX = "04145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16667A05E9A1BDD6F70142B66558BD12CE2C0F9CBC7001B20C8A6A109C80DC5330"

def get_public_key_hex(scalar):
    try:
        # Keep everything constrained inside the valid group order bounds
        priv_bytes = (scalar % N).to_bytes(32, 'big')
        pub = PublicKey.from_secret(priv_bytes)
        return pub.format(compressed=False).hex().upper()
    except:
        return None

def run_landmark_sweep(base_binary, radius):
    n = len(base_binary)
    buckets = {'2': [], '3': [], '4': []}
    
    print("--- Phase 1: Processing Cyclic 135-bit Frames ---")
    # Wrap loop across the full 256 operational depth
    for phase in range(256):
        shift = phase % n
        rotated_bin = base_binary[shift:] + base_binary[:shift]
        
        scalar = int(rotated_bin, 2)
        scalar_str = str(scalar)
        start_digit = scalar_str[0]
        
        if start_digit in buckets:
            buckets[start_digit].append({
                'phase': phase,
                'scalar': scalar,
                'bin_subset': rotated_bin[:20]
            })
            
    print(f"Landmarks Found -> Bucket 2: {len(buckets['2'])}, Bucket 3: {len(buckets['3'])}, Bucket 4: {len(buckets['4'])}")
    print(f"Sweep Vector: +/- {radius:,} from targeted landmarks\n")
    
    print("--- Phase 2: Targeted Proximity Verification ---")
    for digit in ['4', '3', '2']:
        for item in buckets[digit]:
            base_scalar = item['scalar']
            phase_num = item['phase']
            
            print(f"Scanning Phase {phase_num:3d} | Base Scalar: {str(base_scalar)[:40]}...")
            
            # Direct sweep loop at current focus point
            for step in range(1, radius + 1):
                candidates = [base_scalar + step, base_scalar - step]
                for cand in candidates:
                    if get_public_key_hex(cand) == TARGET_PUB_HEX:
                        print(f"\n[!!!] TARGET PRIVATE KEY IDENTIFIED: {cand}")
                        return cand
                        
    print("\nSweep complete. Proximity bounds exhausted.")

# 135-bit Base Projection Map
base_binary = "1010001011101001001100001000111001000001000111010001110010110111011110110011100010010110011100000111101110001001011110000100110111001101101001111001100010011010111100011111000001010101000110010001100001111101110011011011011010000100011010001111000010110"

if __name__ == "__main__":
    # Adjust this range variable depending on how close you expect the bit-alignment shift to be
    test_radius = 100000000000000 
    run_landmark_sweep(base_binary, test_radius)