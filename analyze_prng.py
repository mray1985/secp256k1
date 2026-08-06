#!/usr/bin/env python3
"""Check if puzzle private keys follow a deterministic PRNG pattern."""
from __future__ import annotations
import sys, hashlib, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from puzzle_keys_53125 import parse_53125

pkeys = parse_53125()

# Get sorted keys for puzzles 1-130
known: list[tuple[int, int]] = sorted(
    [(n, rec.d) for n, rec in pkeys.items() if rec.d > 0 and n <= 130]
)

print(f"Known keys: {len(known)} puzzles")

# Test 1: d_N = SHA256("puzzle_N_some_seed") mod 2^N
def test_hash_pattern(label: str, seed_fn):
    matches = 0
    for n, d in known:
        computed = seed_fn(n) % (1 << n)
        if computed == d:
            matches += 1
    print(f"{label}: {matches}/{len(known)} match")

# Various seed patterns
test_hash_pattern("SHA256('puzzle'||str(N))", 
    lambda n: int.from_bytes(hashlib.sha256(f"puzzle{n}".encode()).digest(), "big"))
test_hash_pattern("SHA256('B'||str(N))",
    lambda n: int.from_bytes(hashlib.sha256(f"B{n}".encode()).digest(), "big"))
test_hash_pattern("SHA256('Bitcoin'||str(N))",
    lambda n: int.from_bytes(hashlib.sha256(f"Bitcoin{n}".encode()).digest(), "big"))
test_hash_pattern("SHA256('Puzzle'||str(N))",
    lambda n: int.from_bytes(hashlib.sha256(f"Puzzle{n}".encode()).digest(), "big"))
test_hash_pattern("SHA256(N_bytes)",
    lambda n: int.from_bytes(hashlib.sha256(n.to_bytes(4, "big")).digest(), "big"))
test_hash_pattern("SHA256('1'*N)",
    lambda n: int.from_bytes(hashlib.sha256(("1" * n).encode()).digest(), "big"))

# Test 2: Direct PRNG pattern - check if next key is derived from previous
print("\n--- PRNG state continuity check ---")
for i in range(min(10, len(known)-1)):
    n1, d1 = known[i]
    n2, d2 = known[i+1]
    print(f"P{n1} -> P{n2}: d2 XOR d1 = {d2 ^ d1}")
    print(f"         d2 - d1 = {d2 - d1}")
    # If output is PRNG stream, check high bits
    if d2.bit_length() > d1.bit_length():
        print(f"         d2 top bits = {d2 >> d1.bit_length()}")

# Test 3: Check if high bits of consecutive keys form a PRNG sequence
print("\n--- High-bit pattern check (consecutive 32-bit chunks) ---")
for i in range(min(20, len(known))):
    n, d = known[i]
    high32 = d >> (d.bit_length() - 32) if d.bit_length() > 32 else d
    high32_alt = (d >> 32) & 0xFFFFFFFF if d.bit_length() > 32 else d
    print(f"P{n:3d}: key={d & 0xFFFFFFFF:010d}  high32={high32:010d}  bits={d.bit_length():3d}")

# Test 4: Check if keys are SHA256(prev_key) truncated
print("\n--- Hash chain check ---")
for i in range(len(known)-1):
    n1, d1 = known[i]
    n2, d2 = known[i+1]
    h = int.from_bytes(hashlib.sha256(str(d1).encode()).digest(), "big") % (1 << n2)
    if h == d2:
        print(f"  P{n2}: d = SHA256(d_{n1}) mod 2^{n2} MATCH!")

# Also check SHA256 of just the bytes
for i in range(len(known)-1):
    n1, d1 = known[i]
    n2, d2 = known[i+1]
    h = int.from_bytes(hashlib.sha256(d1.to_bytes((d1.bit_length()+7)//8, "big")).digest(), "big") % (1 << n2)
    if h == d2:
        print(f"  P{n2}: d = SHA256(d_{n1}_bytes) mod 2^{n2} MATCH!")

# Test 5: Check for LCG pattern in the nonce (k) values
# from hashkeys_rsz
sys.path.insert(0, str(ROOT))
from hashkeys_rsz import PUZZLE_RSZ

# Get k values
known_k = [(n, rsz.k) for n, rsz in sorted(PUZZLE_RSZ.items()) if rsz.k is not None]
print(f"\n--- Nonce (k) pattern check ---")
print(f"Known k values: {len(known_k)}")

# Check if k follows a pattern: k_{i+1} = (a * k_i + c) mod n
n_order = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
for i in range(len(known_k) - 2):
    n1, k1 = known_k[i]
    n2, k2 = known_k[i+1]
    n3, k3 = known_k[i+2]
    # Try to find LCG parameters
    # k2 = (a*k1 + c) mod n_order
    # k3 = (a*k2 + c) mod n_order
    # Subtract: k3 - k2 = a*(k2 - k1) mod n_order
    try:
        diff1 = (k2 - k1) % n_order
        diff2 = (k3 - k2) % n_order
        a_candidate = (diff2 * pow(diff1, -1, n_order)) % n_order
        c_candidate = (k2 - a_candidate * k1) % n_order
        # Verify with next values if available
        if i + 3 < len(known_k):
            n4, k4 = known_k[i+3]
            k4_pred = (a_candidate * k3 + c_candidate) % n_order
            if k4_pred == k4:
                print(f"  LCG FOUND! a={a_candidate}, c={c_candidate} (between P{n2} and P{n4})")
    except:
        pass

# Test 6: Check if nonces are deterministic (RFC6979 style)
print("\n--- RFC6979 nonce check ---")
for n, rsz in sorted(PUZZLE_RSZ.items()):
    if rsz.k is None or rsz.pvt_hex is None:
        continue
    # Try to verify: k should be derived from (d, z) 
    # We can't directly verify RFC6979, but we can check properties
    # RFC6979 generates k such that k*G has x-coordinate = r
    # This is already guaranteed by the signature equation
    # Check bit length of k vs d
    print(f"  P{n:3d}: k bits={rsz.k.bit_length():3d}  d bits={int(rsz.pvt_hex,16).bit_length():3d}  k>d? {rsz.k > int(rsz.pvt_hex,16)}")
