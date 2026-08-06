#!/usr/bin/env python3
"""Analyze exact Y extraction pattern to determine grid positions."""
import re

# Raw Y extraction lines from the file (with leading whitespace)
y_lines_raw = [
    (248, ' 33  E                            7      6                        '),
    (249, '6                5                               7      0     5'),
    (250, ' 3                        5        9           F              '),
    (251, '          0   4     F           2 8                   B       8 '),
    (252, '                                             8 8 C   '),
    (253, '                     F                   x9                   7 '),
    (254, '    C     x0                               3             C 9                                        '),
]

# Wait, these are actually the X extraction lines (237-243)
# The Y extraction lines are 248-255
y_lines = [
    (248, '                                             33  E    7            '),
    (249, '                        6              6     5                     '),
    (250, '   7                0                                              '),
    (251, '           5                                               3       '),
    (252, '            5  9  F 0          4                    F 2   8B       '),
    (253, '    8        8                C                                    '),
    (254, '                          Fx9      7             C      x0  3      '),
    (255, '         C                     9                                   '),
]

y130 = "B078A17CC1558A9A4FA0B406F194C9A2B71D9A61424B533CEEFE27408B3191E3"

# Let me try laying out y in a 4x16 grid and see if the extraction positions align
print("y130 grid (4 rows x 16 cols):")
for row in range(4):
    start = row * 16
    row_chars = y130[start:start+16]
    print(f"  Row {row}: {' '.join(row_chars)}")

print()
print("Let me check if extraction follows a column-based pattern...")
# For each column position in the grid, what digits appear in the extraction?
extracted_str = "33E76657055F04F28B88CF_97C_03C9"  # from combining y-line extractions

# Let me check what the combined extraction string should be
d130 = "33e7665705359f04f28b88cf897c603c9"
print(f"d130 hex: {d130}")

# From lines 248-255, the extracted digit groups are:
# Line 248: 33E7
# Line 249: 665
# Line 250: 70
# Line 251: 53
# Line 252: 59F04F28B
# Line 253: 88C
# Line 254: F_97C_03 (F, 9, 7, C from y, 0 from x, 3)
# Line 255: C9
# Concatenated: 33E7 + 665 + 70 + 53 + 59F04F28B + 88C + F97C03 + C9 = 33E7665705359F04F28B88CF97C03C9

combined = "33E7" + "665" + "70" + "53" + "59F04F28B" + "88C" + "F97C03" + "C9"
print(f"Combined from y-extraction: {combined}")
print(f"d130:                      {d130.upper()}")
print()

# Compare character by character
for i, (a, b) in enumerate(zip(combined, d130.upper())):
    match = "OK" if a == b else f"DIFF (got {a}, expected {b})"
    print(f"  Pos {i:2d}: {a} vs {b} - {match}")
