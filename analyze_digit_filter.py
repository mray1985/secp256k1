#!/usr/bin/env python3
"""Check digit filtering pattern: private key digits within x decimal digits."""
from __future__ import annotations
from pathlib import Path
ROOT = Path(__file__).resolve().parent
import sys; sys.path.insert(0, str(ROOT))
from puzzle_keys_53125 import parse_53125

def hex_filter(v):
    h = format(v, "x").zfill(64)
    dec_digits = "".join(c for c in h if c.isdigit())
    hex_letters = "".join(c for c in h if c.isalpha())
    return dec_digits, hex_letters

pkeys = parse_53125()
print("Puzzle d bits | d in x dec digits? | dec_len | hex_len | hex_val/60 | d in x dec start pos")
for n in [95, 100, 105, 110, 115, 120, 125, 130, 135]:
    rec = pkeys.get(n)
    x = rec.px
    dec, hex_l = hex_filter(x)
    hex_val = int(hex_l if hex_l else "0", 16) if hex_l else 0
    
    if n == 135:
        print(f"P{n:3d} | N/A | {len(dec):3d} decimal digits | {len(hex_l):3d} hex letters | {hex_val/60:>20.1f}")
    else:
        d = rec.d
        d_str = str(d)
        idx = dec.find(d_str)
        if idx >= 0:
            print(f"P{n:3d} | {d.bit_length():3d} bits | d IN dec digits at pos {idx} | len={len(dec)} | hex_letters={len(hex_l)} | hex/60={hex_val/60:>20.1f}")
        else:
            # Check if d hex appears in x dec digits somehow
            d_hex = format(d, "x")
            in_dec_hex = d_hex in dec
            print(f"P{n:3d} | {d.bit_length():3d} bits | NOT in dec | d-hex in dec={in_dec_hex} | len={len(dec)} | hex_letters={len(hex_l)} | hex/60={hex_val/60:>20.1f}")

print()
print("=== Full digit position mapping for P130 ===")
x130 = 0x633CBE3EC02B9401C5EFFA144C5B4D22F87940259634858FC7E59B1C09937852
d130 = 37650549717742544505774009877315221420
h130 = format(x130, "x").zfill(64)
dec130, hex130 = hex_filter(x130)

# Show positions of d130's hex digits within x130
d130_hex = format(d130, "x")
print(f"x130 hex: {h130}")
print(f"d130 hex: {d130_hex}")
print(f"x130 decimal digits: {dec130}")
print(f"x130 hex letters: {hex130}")

# For each digit of d130, find its position in x130
print(f"\nd130 hex digit positions in x130:")
for i, ch in enumerate(d130_hex):
    pos = h130.find(ch, i * 4)  # rough position
    if pos >= 0:
        pass
print(f"  Note: x130 has {len(dec130)} decimal digits and {len(hex130)} hex letters")
print(f"  d130_hex has {len(d130_hex)} chars")

# For P135, show ALL numbers from 53125.txt
print()
print("=== P135 digit analysis ===")
x135 = 0x145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16
h135 = format(x135, "x").zfill(64)
dec135, hex135 = hex_filter(x135)
hex_val_135 = int(hex135, 16) if hex135 else 0

print(f"x135 hex: {h135}")
print(f"decimal digits from x: {dec135}")
print(f"hex letters from x: {hex135} = {hex_val_135}")
print(f"hex letters dec: {hex_val_135}")
print(f"hex/60: {hex_val_135 / 60}")
print()

# Check: does d lie near these values?
# d should be in [2^134, 2^135)
min_d = 2**134
max_d = 2**135
print(f"Expected d range: [{min_d}, {max_d})")
print(f"dec135 as int: {int(dec135) if dec135 else 'N/A'} (bits={(int(dec135).bit_length() if dec135 else 0)})")
print(f"hex_val_135 in range? {min_d <= hex_val_135 < max_d}")
print(f"hex_val_135 * 60 = {hex_val_135 * 60} in range? {min_d <= hex_val_135 * 60 < max_d}")
print(f"dec135 in range? {min_d <= int(dec135) < max_d if dec135 else False}")
print(f"dec135 as int * something?")
