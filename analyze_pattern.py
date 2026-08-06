#!/usr/bin/env python3
"""Deep analysis of 53125 patterns with ASCII-safe output."""
from pathlib import Path
import re, csv

ROOT = Path(__file__).resolve().parent
TEXT_PATH = ROOT / "00_Projects" / "patent" / "53125.txt"
text = TEXT_PATH.read_text(encoding="utf-8", errors="replace")

# Load known private keys from CSV
puzzles = {}
with open(ROOT / "logs" / "SOLVED_NONCE_PANEL.csv") as f:
    for row in csv.DictReader(f):
        n = int(row["puzzle"])
        try:
            puzzles[n] = {"d": int(row["d"]), "px": int(row["px"])}
        except:
            pass

# Parse pages: find each puzzle section, then find page within it
lines = text.split("\n")
page_puzzles = {}
current_puzzle = None
for i, line in enumerate(lines):
    pm = re.search(r"puzzle\s+(\d+)", line.strip().lower())
    if pm:
        current_puzzle = int(pm.group(1))
    if current_puzzle and ("page" in line.lower()):
        pm2 = re.search(r"page[:\s]+(\d+)", line)
        if pm2 and current_puzzle:
            page_puzzles[current_puzzle] = int(pm2.group(1))
            current_puzzle = None  # prevent re-matching in same section

print("=" * 70)
print("1. PAGE ANALYSIS: d = 60*page + offset")
print("=" * 70)
for n in sorted(page_puzzles):
    page = page_puzzles[n]
    if n in puzzles:
        d = puzzles[n]["d"]
        pred = 60 * page
        offset = d - pred
        print(f"P{n:3d}: page={page}")
        print(f"      60*page={pred}, d={d}, offset={offset:4d}")
    else:
        print(f"P{n:3d}: page={page} (UNSOLVED)")

# Page growth rates (skip P130 which only has page for solved)
print("\n--- Page growth (consecutive pairs) ---")
sorted_ns = sorted([n for n in page_puzzles if n in puzzles])
for i in range(len(sorted_ns)-1):
    n1, n2 = sorted_ns[i], sorted_ns[i+1]
    p1, p2 = page_puzzles[n1], page_puzzles[n2]
    ratio = p2 / p1
    print(f"  P{n1}->P{n2}: {p1} -> {p2}, ratio={ratio:.6f}, bits={p2.bit_length()}")

# === ECHO PAGE (from result^(n/256)) ===
print("\n--- Echo page = result^n/256 // 60 ---")
for m in re.finditer(r"result\^(\d+)/256\s*=\s*(\d+)", text, re.IGNORECASE):
    n = int(m.group(1))
    result_int = int(m.group(2))
    echo_page = result_int // 60
    print(f"  P{n:3d}: result_int={result_int}, echo_page={echo_page}")

# === PIECES EXTRACTION ===
print("\n" + "=" * 70)
print("2. RESULT/REMAINDER SEQUENCES (halving-ladder pieces)")
print("=" * 70)
for m in re.finditer(r"(?:x|y|\(y\^2\s*=\s*x\^3\s*\+\s*7\)\s*mod\s*p)?(?:135)?:?\s*RESULTS?:?\s*\(?([\d,\s]+)\)?", text, re.IGNORECASE):
    pieces_str = m.group(1)
    pieces = [int(x) for x in re.findall(r"\d+", pieces_str)]
    if len(pieces) >= 3:
        # Find which puzzle this belongs to by looking backwards
        pre = text[:m.start()]
        pz = re.findall(r"puzzle\s+(\d+)", pre)
        puzzle_n = pz[-1] if pz else "??"
        print(f"  P{puzzle_n}: {pieces}")

# === PRODUCT + PRIME FACTOR LINES ===
print("\n" + "=" * 70)
print("3. PRODUCT FORMULAS (pieces product = prime factors)")
print("=" * 70)
for m in re.finditer(r"(\d[\d\s\*]+)\s*=\s*([^=]+?)(?:\d+<|\n)", text):
    prod = m.group(1).strip()
    factors = m.group(2).strip()
    if len(prod) > 5 and len(factors) > 5:
        print(f"  {prod[:60]} = {factors[:60]}")

# === PRIVATE KEY DECOMPOSITION (536870912 = 2^29 decomposition) ===
print("\n" + "=" * 70)
print("4. BINARY DECOMPOSITION (2^29 basis)")
print("=" * 70)
for m in re.finditer(r"1\((\d+)\)\s*=\s*(\d+)\s*\n1\(\1\)\s*=\s*([^\n]+)", text):
    n = int(m.group(1))
    d = int(m.group(2))
    decomp = m.group(3)
    print(f"  P{n:3d}: d={d}")
    print(f"        {decomp[:100]}")
