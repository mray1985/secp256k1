#!/usr/bin/env python3
"""Check if the cube-class relationship holds for ALL puzzle signatures."""
from __future__ import annotations
import csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "logs" / "SOLVED_NONCE_PANEL.csv"

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

omega_N = 37718080363155996902926221483475020450927657555482586988616620542887997980018
omega_p = 60197513588986302554485582024885075108884032450952339817679072026166228089408

def cube_class_N(val: int) -> str:
    check = pow(val, (N-1)//3, N)
    if check == 1: return "CUBE"
    if check == omega_N: return "omega"
    if check == pow(omega_N, 2, N): return "omega2"
    return f"OTHER({check})"

def cube_class_p(val: int) -> str:
    check = pow(val, (p-1)//3, p)
    if check == 1: return "CUBE"
    if check == omega_p: return "omega"
    if check == pow(omega_p, 2, p): return "omega2"
    return f"OTHER({check})"

# P135 data
r135 = 90653255469745952335985143920649543885181555095025199315947044135806663628368
s135 = 15509729875763924304053419655647994379903175655107184284998698212653288468986
z135 = 66278737796829840734606014530466656889790152192829793669891337810330530090951
x135 = 9210836494447108270027136741376870869791784014198948301625976867708124077590
x3_mod_p = (x135**3 + 7 - 7) % p    # x^3 mod p
x2_mod_N = x3_mod_p % N             # x^3 mod p reduced to N

Q135 = (s135 * z135) % N

print("P135 cube classes:")
print(f"  Q = s*z mod N -> {cube_class_N(Q135)}")
print(f"  x² mod p -> N  -> {cube_class_N(x2_mod_N)}")
print(f"  Same? {cube_class_N(Q135) == cube_class_N(x2_mod_N)}")
print(f"  Q/x² mod N is cube? {cube_class_N((Q135 * pow(x2_mod_N, -1, N)) % N)}")
print()

# Now test ALL puzzles from CSV
print("Testing cube class relationship for ALL puzzles 1-130...")
print(f"{'Puzzle':>6} {'Q class':>10} {'x³ class':>10} {'Same?':>6} {'Q/x³ cube?':>10}")
print("-" * 50)

matching = 0
total = 0
with open(CSV_PATH) as f:
    reader = csv.DictReader(f)
    for row in reader:
        n = int(row["puzzle"])
        # Skip if missing data
        if not row.get("r") or not row.get("s") or not row.get("z"):
            continue
        try:
            r = int(row["r"])
            s = int(row["s"])
            z = int(row["z"])
        except (ValueError, KeyError):
            continue
        
        # Get px from the row
        px = int(row["px"]) if row.get("px") else None
        if px is None:
            continue
        
        x3_p = (px ** 3) % p
        x3_N = x3_p % N
        Q = (s * z) % N
        
        q_class = cube_class_N(Q)
        x3_class = cube_class_N(x3_N)
        same = "Y" if q_class == x3_class else "N"
        
        # Q * x^(-3) mod N
        try:
            Qx3_inv = (Q * pow(x3_N, -1, N)) % N
            is_cube = "CUBE" if cube_class_N(Qx3_inv) == "CUBE" else "NOT"
        except:
            is_cube = "ERR"
        
        total += 1
        if same == "Y":
            matching += 1
        
        if n <= 20 or n % 5 == 0 or n >= 125:
            print(f"{n:6d} {q_class:>10} {x3_class:>10} {same:>6} {is_cube:>10}")

print(f"\nSummary: {matching}/{total} puzzles share cube class between Q and x³")
print()

# Also check mod p cube classes
print("Mod p check for P135 vs other puzzles:")
for n in [65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135]:
    if n == 135:
        r, s, z, x = r135, s135, z135, x135
    else:
        # Read from CSV
        pass  # skip for now, just check P135
    
print(f"P135 mod p: Q={cube_class_p(Q135)}, x_p={cube_class_p(x3_mod_p)}")

# Check what makes P135 special compared to others
# Read specific puzzles 130 and 135 to compare
print("\n--- Detailed comparison P130 vs P135 ---")
# P130 from CSV
with open(CSV_PATH) as f:
    reader = csv.DictReader(f)
    for row in reader:
        n = int(row["puzzle"])
        if n == 130:
            r130 = int(row["r"])
            s130 = int(row["s"])
            z130 = int(row["z"])
            px130 = int(row["px"])
            x3_130_p = (px130 ** 3) % p
            x3_130_N = x3_130_p % N
            Q130 = (s130 * z130) % N
            print(f"P130 Q class mod N: {cube_class_N(Q130)}")
            print(f"P130 x³ class mod N: {cube_class_N(x3_130_N)}")
            print(f"P130 Same? {cube_class_N(Q130) == cube_class_N(x3_130_N)}")
            print(f"P130 mod p Q: {cube_class_p(Q130)}, x³: {cube_class_p(x3_130_p)}")
            print(f"P130 Q/x³ mod p: {cube_class_p((Q130 * pow(x3_130_p, -1, p)) % p)}")
            break

print(f"\nP135 Q class mod N: {cube_class_N(Q135)}")
print(f"P135 x³ class mod N: {cube_class_N(x2_mod_N)}")
print(f"P135 Same? {cube_class_N(Q135) == cube_class_N(x2_mod_N)}")
Q135_p = (s135 * z135) % p
print(f"P135 mod p Q: {cube_class_p(Q135_p)}, x³: {cube_class_p(x3_mod_p)}")
try:
    ratio_p135 = (Q135_p * pow(x3_mod_p, -1, p)) % p
    print(f"P135 Q/x³ mod p: {cube_class_p(ratio_p135)}")
except:
    print("P135 Q/x³ mod p: error")
