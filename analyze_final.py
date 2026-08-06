#!/usr/bin/env python3
"""Comprehensive final analysis: x-truncation, nonce PRNG, factorization pattern."""
from __future__ import annotations
import csv, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "logs" / "SOLVED_NONCE_PANEL.csv"

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# === 1. X-COORDINATE TRUNCATION CHECK ===
print("=" * 70)
print("1. X-COORDINATE TRUNCATION CHECK")
print("=" * 70)
checks = []
with open(CSV_PATH) as f:
    reader = csv.DictReader(f)
    for row in reader:
        n = int(row["puzzle"])
        try:
            px = int(row["px"]); d = int(row["d"])
        except:
            continue
        
        # Test: d = px mod 2^N (truncate x to N bits)
        if d == px % (1 << n):
            checks.append((n, f"x mod 2^{n}"))
        
        # Test: d = px mod 2^(n+1)
        if n > 0 and d == px % (1 << (n+1)):
            checks.append((n, f"x mod 2^{n+1}"))
        
        # Test: d = (px >> (256 - n)) (top N bits of x)
        if d == (px >> (256 - n)):
            checks.append((n, "x >> (256-n)"))
        
        # Test: d = px mod (2^N) for known constant range
        for offset in [-2, -1, 0, 1, 2]:
            test_n = n + offset
            if test_n > 0 and test_n <= 256:
                if d == px % (1 << test_n):
                    checks.append((n, f"x mod 2^{test_n}"))
                if d == (px >> (256 - test_n)):
                    checks.append((n, f"x>>{256-test_n}"))

if checks:
    for n, desc in checks:
        print(f"P{n:3d}: MATCH! d = {desc}")
else:
    print("  No x-truncation match found for any puzzle")
print()

# Also check: d = hash of x truncated
def open_csv_rows(path):
    with open(path) as f:
        yield from csv.DictReader(f)

print("--- d = SHA256(x) mod 2^N ---")
for row in open_csv_rows(CSV_PATH):
    n = int(row["puzzle"])
    try:
        px = int(row["px"]); d = int(row["d"])
    except:
        continue
    h = hashlib.sha256(str(px).encode()).digest()
    if d == int.from_bytes(h, "big") % (1 << n):
        print(f"  P{n:3d}: d = SHA256(x_dec) mod 2^{n}")

# Check d = SHA256(x_hex) mod 2^N
for row in open_csv_rows(CSV_PATH):
    n = int(row["puzzle"])
    try:
        px = int(row["px"]); d = int(row["d"])
    except:
        continue
    h = hashlib.sha256(format(px, "x").encode()).digest()
    if d == int.from_bytes(h, "big") % (1 << n):
        print(f"  P{n:3d}: d = SHA256(x_hex) mod 2^{n}")

# Check d = SHA256(x_bytes) mod 2^N  
for row in open_csv_rows(CSV_PATH):
    n = int(row["puzzle"])
    try:
        px = int(row["px"]); d = int(row["d"])
    except:
        continue
    h = hashlib.sha256(px.to_bytes(32, "big")).digest()
    if d == int.from_bytes(h, "big") % (1 << n):
        print(f"  P{n:3d}: d = SHA256(x_bytes) mod 2^{n}")

print()

# === 2. NONCE PRNG ANALYSIS ===
print("=" * 70)
print("2. NONCE PRNG ANALYSIS (full CSV data)")
print("=" * 70)

# Load all nonces in order
nonces = []
with open(CSV_PATH) as f:
    reader = csv.DictReader(f)
    for row in reader:
        n = int(row["puzzle"])
        k = int(row["k"])
        d = int(row["d"])
        nonces.append((n, k, d))

# Check: k_{i+1} = (a * k_i + c) mod N (LCG)
print("--- LCG pattern check across all 130 puzzles ---")
for i in range(len(nonces) - 2):
    n1, k1, d1 = nonces[i]
    n2, k2, d2 = nonces[i+1]
    n3, k3, d3 = nonces[i+2]
    
    diff1 = (k2 - k1) % N
    diff2 = (k3 - k2) % N
    
    if diff1 == 0:
        continue
    
    try:
        a = (diff2 * pow(diff1, -1, N)) % N
        c = (k2 - a * k1) % N
        
        # Verify with next value
        if i + 3 < len(nonces):
            n4, k4, d4 = nonces[i+3]
            pred = (a * k3 + c) % N
            if pred == k4:
                print(f"  LCG FOUND at P{n1}-P{n4}: a={a}, c={c}")
    except:
        pass

# Check: k = SHA256(d) (or similar)
print("\n--- Nonce derived from private key? ---")
for n, k, d in nonces:
    h = hashlib.sha256(str(d).encode()).digest()
    k_from_d = int.from_bytes(h, "big") % (1 << 256)
    if k == k_from_d:
        print(f"  P{n}: k = SHA256(d_str)")
    h = hashlib.sha256(d.to_bytes(32, "big")).digest()
    k_from_d_bytes = int.from_bytes(h, "big")
    if k == k_from_d_bytes:
        print(f"  P{n}: k = SHA256(d_bytes)")

# Check: k = k_prev XOR d (XOR chain)?
print("\n--- XOR chain check ---")
for i in range(len(nonces) - 1):
    n1, k1, d1 = nonces[i]
    n2, k2, d2 = nonces[i+1]
    if k2 == (k1 ^ d2) or k2 == (k1 ^ d1):
        print(f"  P{n1}-P{n2}: XOR chain found!")
    if k2 == (k1 + d1) % N or k2 == (k1 - d1) % N:
        print(f"  P{n1}-P{n2}: Add chain found!")

# === 3. FACTORIZATION PATTERN ===
print("\n" + "=" * 70)
print("3. 53125 FACTORIZATION PATTERN ANALYSIS")
print("=" * 70)

# Read 53125.txt and extract page/pieces/primes for each puzzle
import re
TEXT_PATH = ROOT / "00_Projects" / "patent" / "53125.txt"
text = TEXT_PATH.read_text(encoding="utf-8", errors="replace")

# Find puzzle sections with page/pieces/primes
puzzle_pattern = re.compile(r"puzzle (\d+)\s*\n.*?priv hex (.+?)\s*priv dec (\d+)\s*\n.*?page: (\d+).*?pieces: (.+?)\s*primes: (.+?)(?:\n|$)", re.DOTALL)

print("PAGE/PIECES/PRIMES data from 53125.txt:")
for puzzle_num in range(65, 131):
    # Look for this puzzle in text
    start = text.find(f"\npuzzle {puzzle_num}\n")
    if start < 0:
        continue
    section = text[start:start+2000]
    
    # Extract page
    page_match = re.search(r"page[ :]+(\d+)", section)
    pieces_match = re.search(r"pieces: (.+)", section)
    primes_match = re.search(r"primes: (.+)", section)
    
    page = page_match.group(1) if page_match else "?"
    pieces = pieces_match.group(1).strip() if pieces_match else "?"
    primes = primes_match.group(1).strip() if primes_match else "?"
    
    if page != "?" or pieces != "?":
        print(f"P{puzzle_num:3d}: page={page[:30] if len(page) > 30 else page}")
