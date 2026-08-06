import ecdsa
import hashlib
import ripemd160

# secp256k1 curve
curve = ecdsa.SECP256k1
G = curve.generator
n = curve.order  # Prime order of the curve

# Range: 2^70 to 2^70 + 999
start = 2**70
end = start + 1000

def ripemd160(data):
    h = hashlib.new('ripemd160')
    h.update(data)
    return h.digest()

for d in range(start, end):
    # Private key (d) * Generator (G) = Public key (Q)
    Q = d * G
    # Compress public key (0x02 + x if y is even, 0x03 + x if y is odd)
    x_bytes = Q.x().to_bytes(32, 'big')
    y_bytes = Q.y().to_bytes(32, 'big')
    prefix = bytes([0x02 if y_bytes[-1] % 2 == 0 else 0x03])
    compressed_pubkey = prefix + x_bytes
    # Hash: SHA-256 → RIPEMD-160
    sha256 = hashlib.sha256(compressed_pubkey).digest()
    rmd160 = ripemd160(sha256)
    print(f"{d}: {rmd160.hex()}")