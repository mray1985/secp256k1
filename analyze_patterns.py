#!/usr/bin/env python3
"""Brute-force extraction pattern discovery."""
import csv, itertools, math
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Load puzzle data
puzzles = {}
with open(ROOT / "logs" / "SOLVED_NONCE_PANEL.csv") as f:
    for row in csv.DictReader(f):
        n = int(row["puzzle"])
        try:
            px = int(row["px"]); py = int(row["py"]); d = int(row["d"])
            x_hex = format(px, "x").zfill(64).upper()
            y_hex = format(py, "x").zfill(64).upper()
            d_hex = format(d, "x").upper()
            puzzles[n] = {"x": x_hex, "y": y_hex, "d": d_hex, "d_int": d}
        except:
            pass

# Test: typical grid scan patterns on combined x+y grid
# Grid = 4 rows x 16 cols for EACH of x and y, or combined 8x16?
x = puzzles[130]["x"]
y = puzzles[130]["y"]
d = puzzles[130]["d"]

# Create a combined grid of x overlaid with y
# Or separately: scan each grid in a pattern

def test_pattern(name, get_chars_fn):
    """Test if a pattern extracts d correctly from x or y.
    get_chars_fn(x_hex, y_hex) -> list of (char, source) tuples.
    """
    for n in [130, 125, 120, 115, 110]:
        p = puzzles.get(n)
        if not p:
            continue
        extracted = get_chars_fn(p["x"], p["y"])
        extracted_str = "".join(c for c, s in extracted)
        if extracted_str == p["d"]:
            print(f"  P{n}: MATCH!")
            return True, extracted
    return False, []

# Pattern 1: Interleaved rows (take specific rows from x and y)
# Pattern 2: Column-major scan
# Pattern 3: Diagonal scan
# Pattern 4: Spiral from center
# Pattern 5: Hilbert curve pattern

# Let me try: the combined 8x16 grid where rows 0-3 are x, rows 4-7 are y
# Then scan a specific pattern

# First, let me check: does d appear as a subsequence of x+y?
combined = x + y
print("Checking if d is a subsequence of x+y...")
it = iter(combined)
pos = 0
match_positions = []
for ch in d:
    while pos < len(combined):
        if combined[pos] == ch:
            match_positions.append(pos)
            pos += 1
            break
        pos += 1

if len(match_positions) == len(d):
    print(f"  YES! d is a subsequence of x+y at positions {match_positions}")
    sources = ["x" if p < 64 else "y" for p in match_positions]
    print(f"  Sources: {sources}")
else:
    print(f"  NO. Only matched {len(match_positions)}/{len(d)} digits")

# Pattern: scanning rows of 8x16 grid (x then y) from right to left?
print()
print("Testing reversed scan...")
combined_rev = combined[::-1]
it = iter(combined_rev)
pos = 0
match_positions = []
for ch in d:
    while pos < len(combined_rev):
        if combined_rev[pos] == ch:
            orig_pos = len(combined_rev) - 1 - pos
            match_positions.append(orig_pos)
            pos += 1
            break
        pos += 1
if len(match_positions) == len(d):
    print(f"  YES! In reversed order at positions {match_positions}")

# Pattern: column-major (read down each column)
print()
print("Testing column-major scan of 8x16 grid...")
# 8 rows: 0-3=x, 4-7=y, 16 columns
grid = []
for r in range(4):
    grid.append(list(x[r*16:(r+1)*16]))
for r in range(4):
    grid.append(list(y[r*16:(r+1)*16]))

# Scan column-major
col_major = []
for col in range(16):
    for row in range(8):
        col_major.append(grid[row][col])
col_str = "".join(col_major)
it = iter(col_str)
pos = 0
match_positions = []
for ch in d:
    while pos < len(col_str):
        if col_str[pos] == ch:
            match_positions.append(pos)
            pos += 1
            break
        pos += 1
if len(match_positions) == len(d):
    print(f"  YES! Column-major, positions {match_positions}")

# Pattern: diagonal (top-left to bottom-right)
print()
print("Testing diagonal scan...")
diag = []
for d_idx in range(8+16-1):
    for row in range(max(0, d_idx-15), min(8, d_idx+1)):
        col = d_idx - row
        if col < 16:
            diag.append(grid[row][col])
diag_str = "".join(diag)
it = iter(diag_str)
pos = 0
match_positions = []
for ch in d:
    while pos < len(diag_str):
        if diag_str[pos] == ch:
            match_positions.append(pos)
            pos += 1
            break
        pos += 1
if len(match_positions) == len(d):
    print(f"  YES! Diagonal scan, positions {match_positions}")

# Let me look at the Y extraction from the file more carefully
print()
print("Y-extraction positions from file interpretation...")
# The y extraction shows specific characters at specific grid positions
# Let me try to figure out the reading order from the extracted values

# From the file, the y-extracted sequence is:
# 33E7 + 665 + 70 + 53 + 59F04F28B + 88C + F97C03 + C9
y_extracted = "33E7665705359F04F28B88CF97C03C9"

# Let me find these in the y grid by matching subsequences
# First, check if y_extracted is a subsequence of y
print(f"  Y-extracted: {y_extracted}")
print(f"  Y hex:       {y}")
it = iter(y)
pos = 0
y_match_positions = []
for ch in y_extracted:
    while pos < 64:
        if y[pos] == ch:
            y_match_positions.append(pos)
            pos += 1
            break
        pos += 1
if len(y_match_positions) == len(y_extracted):
    print(f"  Y-extracted IS in y at positions: {y_match_positions}")
else:
    print(f"  Y-extracted NOT a subsequence of y")
    
# Also try x
it = iter(x)
pos = 0
x_match_positions = []
for ch in y_extracted:
    while pos < 64:
        if x[pos] == ch:
            x_match_positions.append(pos)
            pos += 1
            break
        pos += 1
if len(x_match_positions) == len(y_extracted):
    print(f"  Y-extracted IS in x at positions: {x_match_positions}")
else:
    print(f"  Y-extracted NOT a subsequence of x")

# Now let me extract which 2 x-digits are needed to replace the mismatches
# From d: pos 24=8, pos 25=9, pos 26=7, pos 27=C, pos 28=6, pos 29=0, pos 30=3
# From y_extracted: pos 24=9, pos 25=7, pos 26=C, pos 27=0, pos 28=3, pos 29=C, pos 30=9
# So we need: 8,9,7,C,6,0,3 from x at positions where y_extracted has wrong chars
# And y_extracted has: 9,7,C,0,3,C,9 which should go later

# Actually, looking at the last 7 chars:
# d: 897C603C9  (9 chars)
# y: 97C03C9    (7 chars)
# So d has 8 where y has nothing, and the rest are shifted
# The 8 at position 24 comes from x grid
