#!/usr/bin/env python3
"""Analyze hex extraction pattern for P130"""
x130 = "633CBE3EC02B9401C5EFFA144C5B4D22F87940259634858FC7E59B1C09937852"
y130 = "B078A17CC1558A9A4FA0B406F194C9A2B71D9A61424B533CEEFE27408B3191E3"
d130 = "33e7665705359f04f28b88cf897c603c9"

print("Index mapping of d130 hex digits to x/y hex positions:")
print("d_idx d_char x_pos y_pos")
for i, ch in enumerate(d130.upper()):
    x_pos = [j for j, c in enumerate(x130) if c == ch]
    y_pos = [j for j, c in enumerate(y130) if c == ch]
    print(f"{i:2d}    {ch}     x:{x_pos} y:{y_pos}")

# Show x and y in a 4x16 grid
print("\nx130 positions (0-63):")
for i in range(0, 64, 16):
    row = " ".join(x130[i+j] for j in range(16))
    print(f"  {i:2d}-{i+15:2d}: {row}")

print("\ny130 positions (0-63):")
for i in range(0, 64, 16):
    row = " ".join(y130[i+j] for j in range(16))
    print(f"  {i:2d}-{i+15:2d}: {row}")
