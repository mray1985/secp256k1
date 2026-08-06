import hashlib
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "ECDLP")
from ecdlp_full_pipeline import puzzle_band
from hashkeys_rsz import PUZZLE_RSZ
from puzzle_keys_53125 import parse_53125

PUZZLE_KEYS = {n: k.d for n, k in parse_53125().items() if k.d}

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F


def h160_int(pub_hex: str) -> int:
    raw = bytes.fromhex(pub_hex)
    x = int(pub_hex[2:], 16)
    ysq = (pow(x, 3, P) + 7) % P
    y = pow(ysq, (P + 1) // 4, P)
    if (raw[0] == 2) != (y % 2 == 0):
        y = (-y) % P
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    digest = hashlib.new(
        "ripemd160",
        hashlib.sha256(pref + x.to_bytes(32, "big")).digest(),
    ).digest()
    return int.from_bytes(digest, "big")


in_band = 0
rows = []
for n in sorted(PUZZLE_KEYS.keys()):
    if n < 20:
        continue
    d_true = PUZZLE_KEYS[n]
    lo, hi, _ = puzzle_band(n)
    pub = PUZZLE_RSZ[n].pub_compressed
    h = h160_int(pub)
    inside = lo <= h < hi
    if inside:
        in_band += 1
    bf_d = (d_true - lo) / (hi - lo)
    bf_h = (h - lo) / (hi - lo) if inside else None
    diff = abs(bf_d - bf_h) if inside else None
    rows.append((n, inside, bf_d, bf_h, diff, h.bit_length(), d_true.bit_length()))

print("hash160 in puzzle band:", in_band, "/", len(rows))
print()
print("n   in?  bf_d    bf_h    |diff|  h_bits d_bits")
for n, inside, bf_d, bf_h, diff, hb, db in rows[-30:]:
    mark = "Y" if inside else "N"
    bf_h_s = f"{bf_h:.4f}" if bf_h is not None else "---"
    diff_s = f"{diff:.4f}" if diff is not None else "---"
    print(f"{n:3d} {mark}  {bf_d:.4f}  {bf_h_s:>7}  {diff_s:>7}  {hb} {db}")

n = 160
lo, hi, _ = puzzle_band(160)
h = h160_int(PUZZLE_RSZ[160].pub_compressed)
print()
print("P160 h160", hex(h))
print("P160 band_frac(h)", (h - lo) / (hi - lo))
