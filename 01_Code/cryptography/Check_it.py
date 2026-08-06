import hashlib
from datetime import datetime, timezone

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ALPHABET_IDX = {c: i for i, c in enumerate(ALPHABET)}

def b58decode(s: str) -> bytes:
    n = 0
    for c in s:
        n = n * 58 + ALPHABET_IDX[c]

    hex_str = hex(n)[2:]
    if len(hex_str) % 2:
        hex_str = "0" + hex_str
    raw = bytes.fromhex(hex_str) if hex_str else b""

    # Restore leading zero bytes for each leading '1'
    leading_ones = len(s) - len(s.lstrip("1"))
    return b"\x00" * leading_ones + raw

def decode_legacy_address(address: str) -> dict:
    raw25 = b58decode(address)
    if len(raw25) != 25:
        raise ValueError(f"Expected 25 decoded bytes for legacy Base58 address, got {len(raw25)}")

    payload = raw25[:-4]
    checksum = raw25[-4:]
    calc = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]

    version = payload[:1]
    h160 = payload[1:]

    return {
        "address": address,
        "raw25_hex": raw25.hex(),
        "version_hex": version.hex(),
        "hash160_hex": h160.hex(),
        "checksum_hex": checksum.hex().upper(),
        "checksum_int_be": int.from_bytes(checksum, "big"),
        "checksum_valid": checksum == calc,
        "checksum_calc_hex": calc.hex().upper(),
    }

# Example: SecretScan puzzle 135 address
info = decode_legacy_address("16RGFo6hjq9ym6Pj7N5H7L1NR1rVPJyw2v")
for k, v in info.items():
    print(f"{k}: {v}")

# If you want a Unix timestamp hypothesis:
ts = info["checksum_int_be"]
print("timestamp_utc:", datetime.fromtimestamp(ts, tz=timezone.utc))
