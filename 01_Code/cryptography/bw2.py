# Constants
N = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16)

def rotate_and_bucket(binary_str):
    """
    Rotates the binary string, calculates the scalar, 
    and buckets by the starting digit (2, 3, or 4).
    """
    n = len(binary_str)
    
    # Initialize buckets
    buckets = {'2': [], '3': [], '4': []}
    
    print(f"{'Phase':<6} | {'Scalar (Start Digit)':<25} | {'Bucketed?'}")
    print("-" * 70)
    
    for phase in range(256):
        shift = phase % n
        rotated_bin = binary_str[shift:] + binary_str[:shift]
        
        # Scalar Calculation
        scalar = int(rotated_bin, 2)
        scalar_str = str(scalar)
        start_digit = scalar_str[0]
        
        # Check if start digit is 2, 3, or 4
        is_bucketed = False
        if start_digit in buckets:
            buckets[start_digit].append({'phase': phase, 'scalar': scalar})
            is_bucketed = True
        
        # Print summary
        status = f"Bucket: {start_digit}" if is_bucketed else "---"
        print(f"{phase:<6} | {scalar_str[:20]}... ({start_digit}) | {status}")
        
    return buckets

# Your 135-bit binary segment
base_binary = "100000110101001111000110000010000110100000001110111000101110101001100111000101110101000100010100110101111011010101010101100001011001001"

if __name__ == "__main__":
    results = rotate_and_bucket(base_binary)
    
    print("\n--- Final Bucket Summary ---")
    for digit in ['2', '3', '4']:
        print(f"Bucket {digit}: {len(results[digit])} candidates found.")