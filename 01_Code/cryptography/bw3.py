from coincurve import PublicKey
import binascii

# Constants for secp256k1
# Target Public Key (Hex)
TARGET_PUB_HEX = "0414644AA35DFFA448923D487E3D4BD8A176B156D8CFBCA87932646217B0081060C4FEABAC26FE2942DCEB083AAEA96A5FB3146757CF359D76E5E53E84460F1C4D"
# Base binary segment (135-bit)
base_binary = "100000110101001111000110000010000110100000001110111000101110101001100111000101110101000100010100110101111011010101010101100001011001001"

def get_public_key_hex(scalar):
    """
    Derives the public key from a scalar (private key).
    """
    try:
        # Convert scalar to 32-byte format
        priv_bytes = scalar.to_bytes(32, 'big')
        pub = PublicKey.from_secret(priv_bytes)
        return pub.format(compressed=False).hex().upper()
    except Exception:
        return None

def run_full_analysis(binary_str):
    n = len(binary_str)
    buckets = {'2': [], '3': [], '4': []}
    
    print(f"{'Phase':<6} | {'Scalar (Start Digit)':<25} | {'Bucket'}")
    print("-" * 75)
    
    for phase in range(256):
        # Rotate bits
        shift = phase % n
        rotated_bin = binary_str[shift:] + binary_str[:shift]
        
        # Calculate scalar
        scalar = int(rotated_bin, 2)
        scalar_str = str(scalar)
        start_digit = scalar_str[0]
        
        # Verify if it lands in the bucket
        is_bucketed = start_digit in buckets
        if is_bucketed:
            buckets[start_digit].append({'phase': phase, 'scalar': scalar, 'bin': rotated_bin})
            
        print(f"{phase:<6} | {scalar_str[:20]}... ({start_digit}) | {'Bucket: ' + start_digit if is_bucketed else '---'}")

    # Process Buckets and Perform Truth Test
    print("\n--- Verifying Bucketed Candidates ---")
    for digit in ['4', '3', '2']: # Priority order
        for entry in buckets[digit]:
            pub_hex = get_public_key_hex(entry['scalar'])
            if pub_hex == TARGET_PUB_HEX:
                print(f"\n[!!!] FOUND MATCH AT PHASE {entry['phase']}")
                print(f"Private Key (Scalar): {entry['scalar']}")
                return entry['scalar']
            
    print("No match found in current segment phase analysis.")

if __name__ == "__main__":
    run_full_analysis(base_binary)