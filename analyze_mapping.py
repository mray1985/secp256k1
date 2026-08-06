#!/usr/bin/env python3
"""Systematically find the hex extraction pattern by analyzing multiple solved puzzles."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Load all solved puzzle data
puzzles = {}
with open(ROOT / "logs" / "SOLVED_NONCE_PANEL.csv") as f:
    for row in csv.DictReader(f):
        n = int(row["puzzle"])
        try:
            px = int(row["px"])
            py = int(row["py"])
            d = int(row["d"])
            x_hex = format(px, "x").zfill(64).upper()
            y_hex = format(py, "x").zfill(64).upper()
            d_hex = format(d, "x").upper()
            puzzles[n] = {"x_hex": x_hex, "y_hex": y_hex, "d_hex": d_hex, "d": d}
        except:
            pass

# For each puzzle, find for each d-hex digit, which position(s) in x or y it could come from
# Try the most constrained mapping: use UNIQUE positions first, then resolve ambiguities

def find_positions(ch, grid, exclude=set()):
    """Find all positions of ch in grid, excluding already-used positions."""
    return [i for i, c in enumerate(grid) if c == ch and i not in exclude]

# For P130, try to determine exact positions
p130 = puzzles[130]
x = p130["x_hex"]
y = p130["y_hex"]
d = p130["d_hex"]
d_full = format(p130["d"], "x").zfill(33).upper()

print(f"P130 d_hex (full, 33 chars): {d_full}")
print(f"P130 d_hex (compact, {len(d)} chars): {d}")
print(f"P130 x_hex (64): {x}")
print(f"P130 y_hex (64): {y}")
print()

# Let's count which positions in x+y have unique values
combined = x + y  # positions 0-63 = x, 64-127 = y
print("Finding exact position for each d-hex digit using uniqueness:")
used_positions = set()
mapping = []

for i, ch in enumerate(d):
    # Check if ch appears only ONCE in combined (excluding used positions)
    unmatched = [p for p, c in enumerate(combined) if c == ch and p not in used_positions]
    if len(unmatched) == 1:
        pos = unmatched[0]
        source = "x" if pos < 64 else "y"
        grid_pos = pos if pos < 64 else pos - 64
        used_positions.add(pos)
        mapping.append((ch, source, grid_pos))
        status = "UNIQUE"
    else:
        mapping.append((ch, "?", -1))
        status = f"AMBIGUOUS ({len(unmatched)} choices: {unmatched[:5]}...)"
    print(f"  d[{i:2d}]={ch}: {status}")

print(f"\nMapping ({len(mapping)} digits):")
for ch, source, pos in mapping:
    if source != "?":
        grid = x if source == "x" else y
        print(f"  {ch} -> {source}[{pos}] = {grid[pos]}")
    else:
        print(f"  {ch} -> UNKNOWN")

# Now let me try to use the Y-only extraction lines to narrow down
# From lines 248-255, the extraction from Y grid gives:
y_extract = [
    (248, ["33E7"]),
    (249, ["665"]),
    (250, ["70"]),
    (251, ["53"]),
    (252, ["59F04F28B"]),
    (253, ["88C"]),
    (254, ["F97C03"]),  # F,9(from x),7,C,0(from x),3
    (255, ["C9"]),
]

# All y-extracted digits
y_extracted_digits = "33E7665705359F04F28B88CF97C03C9"
print(f"\nAll y-extracted digits: {y_extracted_digits}")
print(f"Actual d digits:         {d}")

# Find where the y-extracted differs from d
for i, (a, b) in enumerate(zip(y_extracted_digits, d)):
    if a != b:
        print(f"  Diff at pos {i}: y-extract={a}, d={b}")

# Also check positions beyond 32 chars
if len(y_extracted_digits) != len(d):
    print(f"  Length mismatch: y-extract={len(y_extracted_digits)}, d={len(d)}")
