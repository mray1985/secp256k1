# Constants
N = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16)

def rotate_and_analyze(binary_str):
    """
    Rotates the binary string through all 256 phases and prints 
    the binary segment and the resulting integer scalar.
    """
    n = len(binary_str)
    print(f"{'Phase':<6} | {'Scalar':<40} | {'Binary Segment (Subset)'}")
    print("-" * 110)
    
    for phase in range(256):
        # Circular rotation: shift index is phase % length
        shift = phase % n
        rotated_bin = binary_str[shift:] + binary_str[:shift]
        
        # Convert the rotated binary string to an integer
        scalar = int(rotated_bin, 2)
        
        # Print phase, scalar, and the first 20 bits of the segment as a signal check
        print(f"{phase:<6} | {str(scalar)[:38]:<40} | {rotated_bin[:20]}...")

# Your confirmed 135-bit binary segment
base_binary = "100000110101001111000110000010000110100000001110111000101110101001100111000101110101000100010100110101111011010101010101100001011001001"

if __name__ == "__main__":
    rotate_and_analyze(base_binary)