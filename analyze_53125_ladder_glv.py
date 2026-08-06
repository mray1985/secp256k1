#!/usr/bin/env python3
"""53125 halving-ladder analysis — full implementation.

Computes v^(k/log2(v)) in high-precision real arithmetic.
For each k, remainder = floor(result) - 2^k gives a 'digit' in the ladder.
"""
from __future__ import annotations
import sys, math
from pathlib import Path
from dataclasses import dataclass

import mpmath as mp
mp.mp.dps = 120

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
DELTA = p - N
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE
LAMBDA = 0x5363AD4CC05C30E0A5261C028812645A122E22EA20816678DF02967C1B23BD72
LAMBDA2 = pow(LAMBDA, 2, N)

Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from puzzle_keys_53125 import parse_53125
from hashkeys_rsz import PUZZLE_RSZ

puzzle_d: dict[int, int] = {}
puzzle_px: dict[int, int] = {}
puzzle_py: dict[int, int] = {}
puzzle_k: dict[int, int] = {}
puzzle_r: dict[int, int] = {}

def load_all():
    pkeys = parse_53125()
    for n, rec in pkeys.items():
        puzzle_d[n] = rec.d
        puzzle_px[n] = rec.px
        puzzle_py[n] = rec.py
    for n, rsz in PUZZLE_RSZ.items():
        if rsz.k is not None:
            puzzle_k[n] = rsz.k
        if n not in puzzle_d and rsz.pvt_hex is not None:
            puzzle_d[n] = int(rsz.pvt_hex, 16)
        if n not in puzzle_px:
            raw = bytes.fromhex(rsz.pub_compressed)
            puzzle_px[n] = int.from_bytes(raw[1:], "big")
        puzzle_r[n] = rsz.r

load_all()

def ladder_53125(v: int, num_bits: int = 256, min_bit: int = 1) -> list[tuple[int, int]]:
    """Compute 53125 ladder for value v.
    Returns list of (k, digit) for k from num_bits-1 down to min_bit.
    digit = floor(v^(k/log2(v))) - 2^k
    """
    if v == 0:
        return []
    mv = mp.mpf(v)
    log2v = mp.log(mv, 2)  # high precision internal
    ladder = []
    for k in range(num_bits - 1, min_bit - 1, -1):
        exp = mp.mpf(k) / log2v
        r = mv ** exp
        approx = int(r)
        digit = approx - (1 << k)
        ladder.append((k, digit))
    return ladder

def get_digits(ladder: list[tuple[int, int]]) -> list[int]:
    return [d for _, d in ladder]

def format_ladder(ladder: list[tuple[int, int]], n_digits: int = 15) -> str:
    return ", ".join(str(d) for _, d in ladder[:n_digits])

def compute_ladder_for_puzzles(puzzle_range: list[int] | None = None):
    """Compute 53125 ladders for Gx, Gy² and all puzzle coordinates."""
    print("=" * 80)
    print("53125 HALVING-LADDER: Coordinate Analysis")
    print("=" * 80)
    
    # Reference ladders
    gx_lad = ladder_53125(Gx)
    gy2 = (pow(Gx, 3, p) + 7) % p
    gy2_lad = ladder_53125(gy2)
    print(f"\nGx   first 20 digits: {get_digits(gx_lad)[:20]}")
    print(f"Gy²  first 20 digits: {get_digits(gy2_lad)[:20]}")
    print(f"Gx   last 15 digits: {get_digits(gx_lad)[-15:]}")
    print(f"Gy²  last 15 digits: {get_digits(gy2_lad)[-15:]}")
    
    puzzles = puzzle_range or sorted(p for p in puzzle_d if p <= 130)
    
    for n in puzzles:
        if n not in puzzle_px:
            continue
        px = puzzle_px[n]
        py2 = (pow(px, 3, p) + 7) % p
        px_lad = ladder_53125(px)
        py2_lad = ladder_53125(py2)
        d = puzzle_d.get(n, 0)
        dx = (d * Gx) % p  # d * Gx mod p (NOT d*G, just scalar*Gx)
        
        print(f"\nP{n:3d} d={d} bits={d.bit_length()}")
        print(f"  Px  first 20: {get_digits(px_lad)[:20]}")
        print(f"  Py² first 20: {get_digits(py2_lad)[:20]}")
        print(f"  Px  last 15:  {get_digits(px_lad)[-15:]}")
        print(f"  Py² last 15:  {get_digits(py2_lad)[-15:]}")

def cross_puzzle_ladder_comparison():
    """Compare 53125 ladders across Px, Rx, Gx for all puzzles."""
    print("\n" + "=" * 80)
    print("CROSS-PUZZLE LADDER COMPARISON (digits at bit positions 256, 255, 254)")
    print("=" * 80)
    
    header = f"{'Puzzle':>6} | {'Px_d256':>8} {'Px_d255':>8} {'Px_d254':>8} | {'Rx_d256':>8} {'Rx_d255':>8} {'Rx_d254':>8} | {'Gx_ratio':>10}"
    print(header)
    print("-" * len(header))
    
    gx_lad = dict(ladder_53125(Gx, 256, 230))
    
    for n in sorted(puzzle_px.keys()):
        if n > 135:
            continue
        px = puzzle_px[n]
        px_lad = dict(ladder_53125(px, 256, 230))
        
        r_val = puzzle_r.get(n, 0)
        rx_lad = dict(ladder_53125(r_val, 256, 230)) if r_val else {}
        
        d256_px = px_lad.get(256, -1)
        d255_px = px_lad.get(255, -1)
        d254_px = px_lad.get(254, -1)
        d256_rx = rx_lad.get(256, -1)
        d255_rx = rx_lad.get(255, -1)
        d254_rx = rx_lad.get(254, -1)
        
        # Compare Px digits to Gx digits
        gx_d256 = gx_lad.get(256, -1)
        ratio_256 = (d256_px * pow(gx_d256, -1, p)) % p if gx_d256 and d256_px else -1
        
        print(f"P{n:>4} | {d256_px:>8} {d255_px:>8} {d254_px:>8} | {d256_rx:>8} {d255_rx:>8} {d254_rx:>8} | {ratio_256:>10}")

def glv_decomposition_check():
    """Compute GLV decomposition of all known private keys."""
    print("\n" + "=" * 80)
    print("GLV ENDOMORPHISM DECOMPOSITION")
    print("=" * 80)
    
    b1 = 0xE4437ED6010E88286F547FA90ABFE4C3
    b2 = 0x3086D221A7D46BCDE86C90E49284EB15
    G1 = 0x00000000000000000000003086D221A7D46BCDE86C90E49284EB153DAB
    G2 = 0x0000000000000000000000E4437ED6010E88286F547FA90ABFE4C42212
    
    header = f"{'Puzzle':>6} | {'bits':>5} | {'k1_bits':>7} | {'k2_bits':>7} | {'expected':>8} | {'flag':>10}"
    print(header)
    print("-" * len(header))
    
    for n in sorted(puzzle_d.keys()):
        d = puzzle_d[n]
        bits = d.bit_length()
        
        # GLV split
        c1 = (d * G1) >> 272
        c2 = (d * G2) >> 272
        k2 = (c1 * b1 + c2 * (N - b2)) % N
        k1 = (d - k2 * LAMBDA) % N
        if k1 > N // 2: k1 -= N
        if k2 > N // 2: k2 -= N
        
        k1_bits = abs(k1).bit_length() - (1 if k1 < 0 else 0)
        k2_bits = abs(k2).bit_length() - (1 if k2 < 0 else 0)
        expected = max(1, (bits + 1) // 2)
        flag = "***SMALL***" if k1_bits <= expected - 8 or k2_bits <= expected - 8 else ""
        
        print(f"P{n:>4} | {bits:>5} | {k1_bits:>7} | {k2_bits:>7} | {expected:>8} | {flag:>10}")

def nonce_pattern_analysis():
    """Analyze known nonces for PRNG patterns."""
    print("\n" + "=" * 80)
    print("NONCE PATTERN ANALYSIS")
    print("=" * 80)
    
    nonces = sorted([(n, k) for n, k in puzzle_k.items()])
    print(f"\nKnown nonces ({len(nonces)}):")
    for n, k in nonces:
        rsz = PUZZLE_RSZ.get(n)
        z = rsz.z if rsz else 0
        print(f"  P{n:3d}: k={k:x}")
        # Check simple patterns
        if k == z:
            print(f"         *** k == z!")
        if k == (N - z) % N:
            print(f"         *** k == -z!")
        if k == puzzle_d.get(n, 0):
            print(f"         *** k == d!")
    
    # LCG detection
    print("\n--- LCG detection on consecutive nonces ---")
    ns = [k for _, k in nonces]
    for i in range(len(ns) - 2):
        k0, k1, k2 = ns[i], ns[i+1], ns[i+2]
        diff1 = (k1 - k0) % N
        diff2 = (k2 - k1) % N
        if diff1 != 0:
            a = (diff2 * pow(diff1, -1, N)) % N
            c = (k1 - a * k0) % N
            print(f"  P{nonces[i][0]:3d}-P{nonces[i+2][0]:3d}: a={a:x} c={c:x}")
            # verify on next
            if i + 3 < len(ns):
                k3 = ns[i+3]
                pred = (a * k2 + c) % N
                match = "OK" if pred == k3 else "MISMATCH"
                print(f"         next triple: {match}")
    
    # Check for k = s^(-1) * z (simplified ECDSA when d=0)
    print("\n--- k = s^(-1)*z mod N (would imply d=0)? ---")
    for n, k in nonces:
        rsz = PUZZLE_RSZ.get(n)
        if rsz:
            s_inv_z = (pow(rsz.s, -1, N) * rsz.z) % N
            if k == s_inv_z:
                print(f"  P{n:3d}: k == s^(-1)*z  ***")

if __name__ == "__main__":
    compute_ladder_for_puzzles([65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135])
    cross_puzzle_ladder_comparison()
    glv_decomposition_check()
    nonce_pattern_analysis()
