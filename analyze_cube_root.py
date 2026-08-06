#!/usr/bin/env python3
"""Find cube root of Q/x mod N and check patterns across puzzles."""
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

omega_N = 37718080363155996902926221483475020450927657555482586988616620542887997980018
m = (N - 1) // 3  # N = 3*m + 1, gcd(3, m) = 1

def cube_root_mod_N(a: int) -> int:
    e = pow(3, -1, m)
    return pow(a, e, N)

def cube_class(val: int, mod: int, omega) -> str:
    check = pow(val, (mod - 1) // 3, mod)
    if check == 1: return "CUBE"
    if check == omega: return "omega"
    return "omega2"

# P135 cube root
r135 = 90653255469745952335985143920649543885181555095025199315947044135806663628368
s135 = 15509729875763924304053419655647994379903175655107184284998698212653288468986
z135 = 66278737796829840734606014530466656889790152192829793669891337810330530090951
x135 = 9210836494447108270027136741376870869791784014198948301625976867708124077590

x3_p = (x135 ** 3) % p
x3_N = x3_p % N
Q = (s135 * z135) % N
Qx3_inv = (Q * pow(x3_N, -1, N)) % N

c = cube_root_mod_N(Qx3_inv)
check = pow(c, 3, N)
print(f"P135 cube root: c = {c}")
print(f"  verify c^3 = Q/x^3? {check == Qx3_inv}")
print(f"  c class = {cube_class(c, N, omega_N)}")
print()

# Check k candidates from cube root
for i, k_candidate in enumerate([c, (c * x135) % N, (c * pow(x135, -1, N)) % N]):
    d_candidate = ((s135 * k_candidate - z135) * pow(r135, -1, N)) % N
    print(f"  k-cand {i}: d bits={d_candidate.bit_length()}, in range={2**134 <= d_candidate < 2**135}")
print()

# Now analyze ALL matching puzzles
print("=== Matching puzzles: cube root vs k vs d ===")
CSV_PATH = ROOT / "logs" / "SOLVED_NONCE_PANEL.csv"
with open(CSV_PATH) as f:
    reader = csv.DictReader(f)
    for row in reader:
        n = int(row["puzzle"])
        try:
            r = int(row["r"]); s = int(row["s"]); z = int(row["z"])
            px = int(row["px"]); k = int(row["k"]); d = int(row["d"])
        except (ValueError, KeyError):
            continue
        
        x3_p = (px ** 3) % p
        x3_N = x3_p % N
        Q = (s * z) % N
        
        if cube_class(Q, N, omega_N) != cube_class(x3_N, N, omega_N):
            continue
        
        Qx3 = (Q * pow(x3_N, -1, N)) % N
        c = cube_root_mod_N(Qx3)
        
        if pow(c, 3, N) != Qx3:
            continue
        
        # Check relationships: c = k * x * something?
        # c^3 = Q/x^3 = s*z * x^{-3} mod N
        # From ECDSA: s = k^{-1}(z+r*d), so s*z = k^{-1}*z*(z+r*d)
        # c^3 = k^{-1}*z*(z+r*d) * x^{-3}
        # c^3 * k = z*(z+r*d) * x^{-3}
        
        # What if c = k? Then c^3 = k^3 = Q/x^3
        # => k^3 = s*z / x^3 mod N
        # => from ECDSA: k^3 = k^{-1}*z*(z+r*d) / x^3
        # => k^4 = z*(z+r*d)/x^3
        # Let's check if c = k approximately (compare values)
        
        # Check: if c = k * x^j for some j, then Q/x^3 = c^3 = k^3 * x^{3j}
        # And Q = x^3 * k^3 * x^{3j} = k^3 * x^{3+3j}
        # From ECDSA: Q = s*z = k^{-1}*z*(z+r*d)
        # So k^{-1}*z*(z+r*d) = k^3 * x^{3+3j}
        # k^4 * x^{3+3j} = z*(z+r*d)
        
        # Maybe c = k * something simple?
        ratio_c_k = (c * pow(k, -1, N)) % N
        ratio_class = cube_class(ratio_c_k, N, omega_N)
        
        # Check c = d?
        ratio_c_d = (c * pow(d, -1, N)) % N
        
        # Check c = k * x?
        ratio_c_kx = (c * pow(k * px % N, -1, N)) % N
        
        print(f"P{n:3d}: c/k class={ratio_class:6s} | c = k * {ratio_c_k % 1000000}")
