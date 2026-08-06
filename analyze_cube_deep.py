#!/usr/bin/env python3
"""Deep dive: cube root relationships for matching puzzles."""
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
omega_N = 37718080363155996902926221483475020450927657555482586988616620542887997980018
m = (N - 1) // 3

def cube_root_mod_N(a: int) -> int:
    return pow(a, pow(3, -1, m), N)

def cube_class(val, mod, omega):
    c = pow(val, (mod - 1) // 3, mod)
    if c == 1: return "CUBE"
    if c == omega: return "omega"
    return "omega2"

CSV_PATH = ROOT / "logs" / "SOLVED_NONCE_PANEL.csv"

# Collect all matching puzzles with full data
matches = []
with open(CSV_PATH) as f:
    reader = csv.DictReader(f)
    for row in reader:
        n = int(row["puzzle"])
        try:
            r = int(row["r"]); s = int(row["s"]); z = int(row["z"])
            px = int(row["px"]); py = int(row["py"])
            k = int(row["k"]); d = int(row["d"])
        except (ValueError, KeyError):
            continue
        
        x3_p = (px ** 3) % p
        x3_N = x3_p % N
        Q = (s * z) % N
        
        if cube_class(Q, N, omega_N) != cube_class(x3_N, N, omega_N):
            continue
        
        Qx3 = (Q * pow(x3_N, -1, N)) % N
        c = cube_root_mod_N(Qx3)
        
        matches.append((n, d, k, px, py, c, r, s, z))

print(f"Found {len(matches)} matching puzzles")
print()

# Check various relationships for each matching puzzle
print(f"{'Puz':>4} {'c/k mod N (short)':>20} {'c/d mod N (short)':>20} {'c/kx mod N':>20} {'c/k/x mod N':>20}")
for n, d, k, px, py, c, r, s, z in matches:
    ck = (c * pow(k, -1, N)) % N
    cd = (c * pow(d, -1, N)) % N
    ckx = (c * pow(k * px % N, -1, N)) % N
    ck_div_x = (c * pow(k, -1, N) * px) % N
    
    # Also check c/k relationship: is it constant? Random? Related to something?
    print(f"{n:4d} {ck % 1000000:20d} {cd % 1000000:20d} {ckx % 1000000:20d} {ck_div_x % 1000000:20d}")

print()

# Key question: is c related to k by a known function pattern?
# Let's check if c/k correlates with puzzle number, d bits, etc.
print("--- Is c/k correlated with anything? ---")
print(f"{'Puz':>4} {'ck mod N (class)':>14} {'c class':>8} {'k class':>8} {'d class':>8} {'c*d class':>10}")
for n, d, k, px, py, c, r, s, z in matches:
    ck = (c * pow(k, -1, N)) % N
    print(f"{n:4d} {cube_class(ck, N, omega_N):>14} {cube_class(c, N, omega_N):>8} {cube_class(k, N, omega_N):>8} {cube_class(d, N, omega_N):>8} {cube_class(c*d % N, N, omega_N):>10}")

print()

# Critical check: does c = k^(-1) * (something) for any matching puzzle?
# From ECDSA: k = s^(-1)*(z+r*d) => k^(-1) = s/(z+r*d)
# And c^3 = Q/x^3 = s*z/x^3
# So c^3 = k^(-1)*z*(z+r*d)/x^3 = s*z/x^3

# If c = k * x * something, then c/kx = constant
# Let's check c/kx across matching puzzles
print("--- Is c/(k*x) constant? ---")
ckx_values = []
for n, d, k, px, py, c, r, s, z in matches:
    ckx = (c * pow(k * px % N, -1, N)) % N
    ckx_values.append(ckx)
    if len(ckx_values) >= 2:
        ratio = (ckx_values[-1] * pow(ckx_values[-2], -1, N)) % N
        print(f"P{n:3d}: c/kx = {ckx % 1000000:06d} (ratio to prev: {ratio % 1000000:06d})")
    else:
        print(f"P{n:3d}: c/kx = {ckx % 1000000:06d}")

print()

# Check if c*d/k is interesting
print("--- Is c*d/k constant? ---")
for n, d, k, px, py, c, r, s, z in matches:
    cdk = (c * d % N * pow(k, -1, N)) % N
    print(f"P{n:3d}: c*d/k mod N = {cdk % 1000000:06d} | class={cube_class(cdk, N, omega_N)}")

print()

# Check: what if v = cube_root(c) (nested cube root)?
# c is a CUBE, so we can take its cube root too!
print("--- Nested cube root ---")
for n, d, k, px, py, c, r, s, z in matches:
    c2 = cube_root_mod_N(c)
    c3 = cube_root_mod_N(c2)
    print(f"P{n:3d}: sqrt3(c) = {c2 % 1000000:06d}, sqrt3(sqrt3(c)) = {c3 % 1000000:06d}")
    # Check if nested root relates to k or d
    r_k = (c2 * pow(k, -1, N)) % N
    r_d = (c2 * pow(d, -1, N)) % N
    print(f"       c2/k = {r_k % 1000000:06d}, c2/d = {r_d % 1000000:06d}")
