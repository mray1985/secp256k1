#!/usr/bin/env python3
"""
Try to determine the hex extraction pattern systematically.

Key insight from file: y grid positions contribute 31 out of 33 d-hex chars.
The pattern groups are: 33E7 | 665 | 70 | 53 | 59F04F28B | 88C | F97C03 | C9
These groups likely correspond to specific columns or diagonal scans of the 4x16 grid.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent

puzzles = {}
with open(ROOT / "logs" / "SOLVED_NONCE_PANEL.csv") as f:
    for row in csv.DictReader(f):
        n = int(row["puzzle"])
        try:
            px = int(row["px"]); py = int(row["py"]); d = int(row["d"])
            x_hex = format(px, "x").zfill(64).upper()
            y_hex = format(py, "x").zfill(64).upper()
            d_hex = format(d, "x").upper()
            puzzles[n] = {"x": x_hex, "y": y_hex, "d": d_hex}
        except:
            pass

y130 = puzzles[130]["y"]
x130 = puzzles[130]["x"]
d130 = puzzles[130]["d"]

# The y extracted groups from the file:
# Groups: [33E7, 665, 70, 53, 59F04F28B, 88C, F97C03, C9]
# Total: 4+3+2+2+9+3+6+2 = 31 chars

# Let me try: reading specific columns of the 4x16 y-grid
# If the group sizes correspond to columns, some pattern like:
# Columns [some set] contribute {4,3,2,2,9,3,6,2} chars each
# But 16 columns, and sum of group sizes is 31... so not 1-to-1

# Alternative: maybe the pattern reads DIAGONALS of the 4x16 y-grid
# Each diagonal of a 4x16 grid has at most 4 cells
# Unless we consider 8x16 combined grid (x+y)

# Let me try: scan the combined 8x16 grid (x rows 0-3, y rows 4-7) in diagonals
# Groups {4,3,2,2,9,3,6,2} could be the number of cells from each diagonal
# that are included in the extraction

# Actually - what if the extraction is about COLUMN PAIRS?
# Group 33E7 = 4 chars = 2 columns' worth of selected cells
# Group 665 = 3 chars = not a full column
# ...

# Let me try a different idea: what if the grid is read in a specific order
# determined by the PIECES (halving-ladder remainders)?

# For P130, the pieces are: 39508, 19676, 9799, 4880, 2430, 1210, 602, 300, 149, 74, 37, 18, 9, 4, 2, 1
# These are 16 numbers. 16 columns!

# Let me check: pieces[0] = 39508. 39508 / 64 = 617.3... not a position
# 39508 % 64 = 39508 - 617*64 = 39508 - 39488 = 20
# So 39508 mod 64 = 20.
# 19676 mod 64 = 19676 - 307*64 = 19676 - 19648 = 28
# 9799 mod 64 = 9799 - 153*64 = 9799 - 9792 = 7
# ...

pieces130 = [39508, 19676, 9799, 4880, 2430, 1210, 602, 300, 149, 74, 37, 18, 9, 4, 2, 1]
mod_positions = [p % 64 for p in pieces130]
print(f"P130 pieces mod 64: {mod_positions}")

# Hmm, the remainders mod 64 don't look like they encode positions.

# Let me check P135 pieces
pieces135 = [23643, 11775, 5864, 2920, 1454, 724, 360, 179, 89, 44, 22, 11, 5, 2, 1]
mod_pos_135 = [p % 64 for p in pieces135]
print(f"P135 pieces mod 64: {mod_pos_135}")

# What about using pieces to determine COLUMNS?
# 16 pieces → one per column
# Check: descending? Ascending?

# Another idea: maybe the private key is encoded in the public key 
# using a fixed permutation. Let me check if the SAME position set works
# for ALL puzzles.

# For each puzzle, test whether d is a function of y at fixed positions
def extract_positions(y_hex, positions):
    """Extract hex chars at specific positions."""
    return "".join(y_hex[p] for p in positions if p < len(y_hex))

# Try: positions = the y-extracted sequence positions for P130
# Since I don't know the positions yet, let me try BRUTE FORCE
# by checking if the same subset of column positions works across puzzles

# Each column in 4x16 grid has 4 cells (one per row)
# If the extraction takes specific rows for each column:
# Pattern row_mask[col] = which rows (0-3) are selected for column col
# Sum(row_masks) = 31

# Let me generate common row_mask patterns
# Pattern 1: all rows for first 7 columns (28), 3 rows for one more (31)
# Pattern 2: first 8 columns, 4 rows each = 32, skip 1 cell somewhere

# The y-extraction group sizes: 4,3,2,2,9,3,6,2
# These DON'T match a per-column count (max 4 per column)

# Unless each GROUP in the extraction spans MULTIPLE columns
# Groups: 4(33E7), 3(665), 2(70), 2(53), 9(59F04F28B), 3(88C), 6(F97C03), 2(C9)
# Sum by column spans: 4+3+2+2+9+3+6+2 = 31 chars

# Let me try: groups = diagonal stripes of the 4x16 grid
# In a 4x16 grid, diagonals (top-left to bottom-right) have lengths:
# 1,2,3,4,4,4,4,4,4,4,4,4,4,4,4,3,2,1 = 64 total

# But our groups don't match this: 4,3,2,2,9,3,6,2
# Totally different.

# Let me try: anti-diagonals (top-right to bottom-left)
# Same lengths as diagonals

# What about reading the grid in specific directions?
# Maybe the 4x16 grid is read: 
# Row 0 left-to-right (16), Row 3 right-to-left (16) = 32, skip one = 31?

# Row 0: y[0:16] = B078A17CC1558A9A → chars: "33E7" found?
# y[0:16] = B 0 7 8 A 1 7 C C 1 5 5 8 A 9 A
# "33E7" not in this row

# Let me try something. The extraction annotations show specific positions.
# Let me trace the VISUAL path through the grid.

# The Y extraction lines (248-255) show positioned characters:
# Line 248: 33 E    7  (at specific columns)
# Line 249: 6     6     5
# Line 250: 7       0
# Line 251: 5                3
# Line 252: 5  9 F 0    4        F 2   8B
# Line 253: 8    8       C
# Line 254: F 9   7     C      0  3   (Fx9 = F from y, 9 from x; x0 = 0 from x)
# Line 255: C           9

# This looks like scanning specific positions in a KNIGHT'S TOUR or similar path!

# Let me visualize the y grid with annotations:
print()
print("=== Y Grid with extraction positions ===")
print("Row 0: B 0 7 8 A 1 7 C C 1 5 5 8 A 9 A")
# Line 248: 33 E    7 at columns... (need to determine exact columns)

# Let me figure out column positions from the extraction
# Line 248 starts with "33  E" - the two 3's are at specific columns, E is later
# Given the y grid:
# Col:  0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
# Row 0: B 0 7 8 A 1 7 C C 1 5  5  8  A  9  A

# If line 248 notes: 3, 3, E, 7 at different (row, col) positions
# Row 0 has: B 0 7 8 A 1 7 C C 1 5 5 8 A 9 A — NO 3, NO E
# Row 1: 4 F A 0 B 4 0 6 F 1 9 4 C 9 A 2 — NO 3, NO E
# Row 2: B 7 1 D 9 A 6 1 4 2 4 B 5 3 3 C — Has 3 at col 13,14; NO E
# Row 3: E E F E 2 7 4 0 8 B 3 1 9 1 E 3 — Has E at 0,1,3,14; 3 at 10,15

# So for "33E7": 
# 3 could be from row 2 col 13 or row 3 col 10 or row 3 col 15
# 3 could be from row 2 col 14 or row 3 col 10 or row 3 col 15
# E could be from row 3 col 0 or 1 or 3 or 14
# 7 could be from row 0 col 2 or 6, row 1=none, row 2 col 1, row 3 col 5

# Too many possibilities! Let me look at the extracted value ORDER to narrow down.
# The sequence 33E7 appears as a VISUAL group in line 248.
# This means the four cells (with chars 3,3,E,7) are read in a specific visual order.

# In the ASCII art, "33 E    7" shows:
# cols: 0112 3456 7890
#       33  E    7
# So: 3, 3, (gap), E, (5 spaces), 7
# The positions in a 16-col grid where these would appear...

# Actually, looking at the file more carefully, spaces represent column gaps.
# "33  E    7" with double space before E suggests the E is at column 4 or 5 of the grid.

# OK I'm going to try a completely practical approach instead.

print()
print("=" * 60)
print("TESTING: Known extraction patterns from the file")
print("=" * 60)

# Let me extract the exact positions used in the Y extraction
# by examining the relationship between y_hex and y-extracted for MULTIPLE puzzles
# Using a STABLE MARRIAGE or similar algorithm

# For each puzzle n, y-extracted is mostly a subset of d (minus x-contributed digits)
# The y-extracted for P130: 33E7665705359F04F28B88CF97C03C9
# Actual d:                  33E7665705359F04F28B88CF897C603C9
# Differences at positions 24-30

# Key: y_extracted[24:31] = "97C03C9" but d[24:31] = "897C603"
# This is a SHIFT — two x-digits (8 and 6?) inserted at different positions
# Actually it looks like: y = "97C03C9" and d has "897C603" = "8"+"97C603"
# Wait no: d = "897C603C9" (9 chars from 24 to 32)
# y =  "97C03C9"  (7 chars)
# So: d[24]='8' from x, d[25]='9' from y[24], d[26]='7' from y[25], d[27]='C' from y[26], 
# d[28]='6' from x? No, y[27]='0' but d[28]='6'
# d[29]='0' from y[28]... hmm this is getting confusing
# 
# Actually the pattern might be: the SAME grid positions are read for ALL puzzles.
# For some puzzles, certain positions come from x, for others from y.
# The positions are FIXED, but the source (x/y) depends on which grid has the correct digit.

# Let me try a fourth approach: test specific GRID SHAPES

# Shape 1: "X" pattern overlaid on 4x16 grid (two diagonals)
# Shape 2: Checkerboard
# Shape 3: Border cells
# Shape 4: Specific rows/columns

for name, positions_fn in [
    ("diag1", lambda g: [g[r][c] for d in range(4+16-1) for r in range(max(0,d-15), min(4,d+1)) for c in [d-r] if c < 16]),
    ("diag2", lambda g: [g[r][c] for d in range(4+16-1) for r in range(max(0,d-15), min(4,d+1)) for c in [d-r] if c < 16]),
    ("col_major", lambda g: [g[r][c] for c in range(16) for r in range(4)]),
    ("row_major", lambda g: [g[r][c] for r in range(4) for c in range(16)]),
    ("rev_row_major", lambda g: [g[r][c] for r in range(4) for c in range(15,-1,-1)]),
    ("rev_col_major", lambda g: [g[r][c] for c in range(15,-1,-1) for r in range(4)]),
]:
    y_grid = [list(y130[i*16:(i+1)*16]) for i in range(4)]
    result = positions_fn(y_grid)
    result_str = "".join(result)
    # Check if d is a subsequence of result
    it = iter(result_str)
    match_len = 0
    for ch in d130:
        for c in it:
            if c == ch:
                match_len += 1
                break
            break
    print(f"  Pattern '{name}': matched {match_len}/{len(d130)}")

# Most important: let me look at the actual file to understand the visual grid
# The extraction annotations show that specific cells are selected
# These cells form a PATH through the 4x16 grid

# Let me read the P130 section and manually extract cell coordinates
print()
print("=== Manual coordinate analysis ===")
print("Y grid (P130):")
for row in range(4):
    print(f"  Row {row}: {' '.join(y130[row*16:(row+1)*16])}")

# Based on the file's annotations, the extraction follows these rows:
# Line 248: Row 3 has positions 2 characters, 3 chars somehow producing "33E7" 
# Actually, the columns are 0-15. Let me look at where 3,3,E,7 appear in each row.

# Finding FIRST occurrence of each needed char in each row:
for row in range(4):
    rchars = y130[row*16:(row+1)*16]
    for needed in ["3", "E", "7"]:
        if needed in rchars:
            pos = rchars.index(needed)
            print(f"  {needed} in row {row}, col {pos} {'(global pos ' + str(row*16+pos) + ')'}")
