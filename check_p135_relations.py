#!/usr/bin/env python3
"""Check if P135's public key is a linear combination of known solved puzzle keys."""
from __future__ import annotations
import sys, math, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from puzzle_keys_53125 import parse_53125

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
px_135 = 0x145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16

INF = None

def modinv(x): return pow(x, -1, p)

def point_add(P, Q):
    if P is INF: return Q
    if Q is INF: return P
    x1, y1 = P; x2, y2 = Q
    if x1 == x2:
        if (y1 + y2) % p == 0: return INF
        lam = (3 * x1 * x1) * modinv(2 * y1) % p
    else:
        lam = (y2 - y1) * modinv(x2 - x1) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)

def point_mul(k, P):
    if k == 0 or P is INF: return INF
    if k < 0: return point_mul(-k, point_neg(P))
    result = INF; addend = P
    while k:
        if k & 1: result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result

def point_neg(P):
    if P is INF: return INF
    return (P[0], p - P[1])

start = time.time()

pkeys = parse_53125()
solved = {n: pkeys[n] for n in pkeys if 1 <= n <= 130}
print(f"Loaded {len(solved)} solved puzzles (1-130) from {len(pkeys)} total")

x3_7 = (px_135 ** 3 + 7) % p
y_135_pos = pow(x3_7, (p + 1) // 4, p)
y_135_neg = p - y_135_pos
y_135_file = 46351506704828816385393879789131775975171267756561783641521771795450741674800
print(f"P135 x: {px_135:#x}")
print(f"P135 y_pos: {y_135_pos:#x}")
print(f"P135 y_neg: {y_135_neg:#x}")
print(f"P135 y_file: {y_135_file:#x}")
print(f"y_pos matches file y? {y_135_pos == y_135_file}")
print(f"y_neg matches file y? {y_135_neg == y_135_file}")

Q_135 = (px_135, y_135_pos) if y_135_pos == y_135_file else (px_135, y_135_neg)
if y_135_pos != y_135_file and y_135_neg != y_135_file:
    print("WARNING: neither y matches file; using y_135_pos")
    Q_135 = (px_135, y_135_pos)

print(f"\n{'='*60}")
print(f"CHECK 1: Exact x-coordinate match with any known key")
print(f"{'='*60}")
for n, rec in solved.items():
    if rec.px == px_135:
        print(f"*** MATCH: P135 x = P{n} x ***")

print(f"\n{'='*60}")
print(f"CHECK 2: Exact y-coordinate match with any known key")
print(f"{'='*60}")
for n, rec in solved.items():
    if rec.py == Q_135[1]:
        print(f"*** MATCH: P135 y = P{n} y ***")
    if rec.py == p - Q_135[1]:
        print(f"*** MATCH: P135 y = -(P{n} y) ***")

print(f"\n{'='*60}")
print(f"CHECK 3: Q_135 = k * Q_i for small k (2 <= k <= 1000)")
print(f"{'='*60}")
found_k = []
for n in sorted(solved):
    rec = solved[n]
    Q_i = (rec.px, rec.py)
    Q_acc = Q_i
    for k in range(2, 1001):
        Q_acc = point_add(Q_acc, Q_i)
        if Q_acc[0] == Q_135[0] and Q_acc[1] == Q_135[1]:
            print(f"*** FOUND: Q_135 = {k} * Q_{n} (d_135 = {k} * {rec.d} mod n) ***")
            found_k.append((n, k))
            break
    # also check with negation of Q_135
    Q_acc2 = Q_i
    for k in range(2, 1001):
        Q_acc2 = point_add(Q_acc2, Q_i)
        if Q_acc2[0] == Q_135[0] and p - Q_acc2[1] == Q_135[1]:
            print(f"*** FOUND: Q_135 = -({k} * Q_{n}) ***")
            found_k.append((n, -k))
            break

if not found_k:
    print("  No exact scalar multiple found for k=2..1000")
else:
    print(f"\n  Found {len(found_k)} relations.")

# Extended check: k up to 10000 for puzzles with matching GCD pattern
print(f"\n  Extended: checking GCD-matched puzzles up to k=5000...")
gcd_matched = [n for n in solved if math.gcd(Gy, solved[n].py) == 8]
for n in sorted(gcd_matched):
    rec = solved[n]
    Q_i = (rec.px, rec.py)
    Q_acc = Q_i
    found = False
    for k in range(2, 5001):
        Q_acc = point_add(Q_acc, Q_i)
        if Q_acc[0] == Q_135[0] and Q_acc[1] == Q_135[1]:
            print(f"  *** FOUND (extended): Q_135 = {k} * Q_{n} ***")
            found = True
            break
    if found:
        break
else:
    print("  Still no match for GCD-matched puzzles up to k=5000")

print(f"\n{'='*60}")
print(f"CHECK 4: Q_135 = Q_i + Q_j (two-term sum, all pairs)")
print(f"{'='*60}")
points_by_x = {}
for n, rec in solved.items():
    points_by_x.setdefault(rec.px, []).append((n, rec.py))

pair_found = 0
for n, rec in solved.items():
    Q_i = (rec.px, rec.py)
    # Q_135 - Q_i = Q_j ?
    diff = point_add(Q_135, point_neg(Q_i))
    if diff is not INF and diff[0] in points_by_x:
        for n2, py2 in points_by_x[diff[0]]:
            if py2 == diff[1]:
                print(f"*** FOUND: Q_135 = Q_{n} + Q_{n2} (d_135 = d_{n} + d_{n2}) ***")
                pair_found += 1
    # Q_135 + Q_i = Q_j ?  
    sum_p = point_add(Q_135, Q_i)
    if sum_p is not INF and sum_p[0] in points_by_x:
        for n2, py2 in points_by_x[sum_p[0]]:
            if py2 == sum_p[1]:
                print(f"*** FOUND: Q_135 = Q_{n2} - Q_{n} (d_135 = d_{n2} - d_{n}) ***")
                pair_found += 1

if not pair_found:
    print("  No two-term sum/diff relation found")

print(f"\n{'='*60}")
print(f"CHECK 5: Q_135 = Q_i + G (adjacent keys)")
print(f"{'='*60}")
G_point = (Gx, Gy)
adj_found = 0
for n, rec in solved.items():
    Q_i = (rec.px, rec.py)
    # Q_135 = Q_i + G ?
    Q_i_plus_G = point_add(Q_i, G_point)
    if Q_i_plus_G[0] == Q_135[0] and Q_i_plus_G[1] == Q_135[1]:
        print(f"*** FOUND: Q_135 = Q_{n} + G ***")
        adj_found += 1
    # Q_135 + G = Q_i ?
    Q_135_plus_G = point_add(Q_135, G_point)
    if Q_135_plus_G[0] == rec.px and Q_135_plus_G[1] == rec.py:
        print(f"*** FOUND: Q_i = Q_135 + G => Q_135 = Q_{n} - G ***")
        adj_found += 1
if not adj_found:
    print("  No adjacent key relation found")

print(f"\n{'='*60}")
print(f"CHECK 6: P135 private key = k (direct scalar of G) for k=2..10000")
print(f"{'='*60}")
for k in range(2, 10001):
    Q_k = point_mul(k, G_point)
    if Q_k[0] == px_135:
        print(f"*** FOUND: P135 d = {k} ***")
        break
else:
    print("  P135 not a direct small multiple of G")

print(f"\n{'='*60}")
print(f"CHECK 7: GCD pattern analysis")
print(f"{'='*60}")
gcd_x_135 = math.gcd(Gx, px_135)
gcd_y_135 = math.gcd(Gy, Q_135[1])
print(f"GCD(Gx, x_135) = {gcd_x_135}")
print(f"GCD(Gy, y_135) = {gcd_y_135}")

print(f"\nPuzzles with matching GCD(Gx, x):")
for n in sorted(solved):
    rec = solved[n]
    if math.gcd(Gx, rec.px) == gcd_x_135:
        print(f"  P{n}: GCD(Gx, x) = {math.gcd(Gx, rec.px)}")

print(f"\nPuzzles with matching GCD(Gy, y):")
for n in sorted(solved):
    rec = solved[n]
    if math.gcd(Gy, rec.py) == gcd_y_135:
        print(f"  P{n}: GCD(Gy, y) = {math.gcd(Gy, rec.py)}")

print(f"\nAll GCD(Gx, x) values:")
for n in sorted(solved):
    rec = solved[n]
    print(f"  P{n}: GCD(Gx, x)={math.gcd(Gx, rec.px)}, GCD(Gy, y)={math.gcd(Gy, rec.py)}")

print(f"\n{'='*60}")
print(f"CHECK 8: x-coordinate proximity (|x_135 - x_i| < 2^64)")
print(f"{'='*60}")
prox = []
for n, rec in solved.items():
    d1 = abs(rec.px - px_135)
    d2 = p - d1
    md = min(d1, d2)
    if md < 2**64:
        prox.append((md, n, rec.d))
prox.sort()
for md, n, d in prox[:20]:
    print(f"  P{n}: |x_135 - x_{n}| = {md}, d_{n} = {d}")

print(f"\n{'='*60}")
print(f"CHECK 9: d_135 == d_i (mod small primes) via EC order check")
print(f"{'='*60}")
# If Q_135 = d_135 * G and Q_i = d_i * G,
# then (d_135 - d_i) * G = Q_135 - Q_i
# We can check if a point is a small multiple of G by computing k*G
# and seeing if it matches Q_135 - Q_i for small k
# This would mean d_135 - d_i = k (mod n) for small k
print("  Checking if Q_135 - Q_i = k*G for small |k| (d_135 - d_i mod n = k):")
for n, rec in solved.items():
    Q_i = (rec.px, rec.py)
    diff = point_add(Q_135, point_neg(Q_i))  # d_135 - d_i
    if diff is not INF:
        # Check if this equals k*G for small k
        for k in range(1, 101):
            Q_k = point_mul(k, G_point)
            if Q_k[0] == diff[0] and Q_k[1] == diff[1]:
                print(f"  *** FOUND: d_135 - d_{n} = {k} (mod n) ***")
            elif Q_k[0] == diff[0] and p - Q_k[1] == diff[1]:
                print(f"  *** FOUND: d_135 - d_{n} = -{k} (mod n) ***")
        # Also check diff = -k*G
        for k in range(1, 101):
            Q_k = point_mul(k, G_point)
            if Q_k[0] == diff[0] and Q_k[1] == diff[1]:
                break  # already checked above

print(f"\n{'='*60}")
print(f"CHECK 10: P135 relation with UNSOLVED puzzle pubkeys (140,145,150,155,160)")
print(f"{'='*60}")
unsolved = {n: pkeys[n] for n in pkeys if n > 130}
print(f"Unsolved puzzles parsed: {sorted(unsolved.keys())}")
for n, rec in unsolved.items():
    Q_u = (rec.px, rec.py)
    # Q_135 = Q_u ?
    if Q_u[0] == Q_135[0]:
        print(f"  P135 x = P{n} x!")
    if Q_u[1] == Q_135[1]:
        print(f"  P135 y = P{n} y!")
    # Q_135 = k * Q_u ?
    Q_acc = Q_u
    for k in range(2, 501):
        Q_acc = point_add(Q_acc, Q_u)
        if Q_acc[0] == Q_135[0] and Q_acc[1] == Q_135[1]:
            print(f"  *** FOUND: Q_135 = {k} * Q_{n} ***")
            break
    # Q_135 = Q_u + Q_i for solved Q_i ?
    for n2, rec2 in solved.items():
        Q_i = (rec2.px, rec2.py)
        Q_sum = point_add(Q_u, Q_i)
        if Q_sum[0] == Q_135[0] and Q_sum[1] == Q_135[1]:
            print(f"  *** FOUND: Q_135 = Q_{n} + Q_{n2} ***")
        Q_diff = point_add(Q_135, point_neg(Q_u))
        if Q_diff is not INF and Q_diff[0] == Q_i[0] and Q_diff[1] == Q_i[1]:
            print(f"  *** FOUND: Q_135 = Q_{n} + Q_{n2} (alt check) ***")

print(f"\n{'='*60}")
print(f"CHECK 11: y-coordinate ratio analysis")
print(f"{'='*60}")
# y_135 / y_i ratio pattern
for n in sorted(solved):
    rec = solved[n]
    if rec.py != 0:
        # y_135 / y_i mod p
        ratio_num = (Q_135[1] * modinv(rec.py)) % p
        # Check if ratio is a small integer
        if ratio_num < 1000 or ratio_num > p - 1000:
            r = ratio_num if ratio_num < 1000 else p - ratio_num
            print(f"  y_135 / y_{n} mod p = {r} {'(~={})'.format(-r) if ratio_num > p - 1000 else ''}")

print(f"\n{'='*60}")
print(f"CHECK 12: Extended two-term check with more pubkeys (all parsed)")
print(f"{'='*60}")
# Build comprehensive point list
all_points = {}
for n, rec in {**solved, **unsolved}.items():
    all_points.setdefault(rec.px, []).append((n, rec.py))

# Check Q_135 = P_i + P_j for ALL parsed keys
ext_found = 0
for n, rec in list({**solved, **unsolved}.items()):
    Q_i = (rec.px, rec.py)
    diff = point_add(Q_135, point_neg(Q_i))
    if diff is not INF and diff[0] in all_points:
        for n2, py2 in all_points[diff[0]]:
            if py2 == diff[1]:
                print(f"  *** FOUND: Q_135 = Q_{n} + Q_{n2} ***")
                ext_found += 1
    sum_p = point_add(Q_135, Q_i)
    if sum_p is not INF and sum_p[0] in all_points:
        for n2, py2 in all_points[sum_p[0]]:
            if py2 == sum_p[1]:
                print(f"  *** FOUND: Q_135 = Q_{n2} - Q_{n} ***")
                ext_found += 1
if not ext_found:
    print("  No two-term relation found across all parsed keys")

print(f"\n{'='*60}")
print(f"CHECK 13: P135 y^2 == (y^2 from file)")
print(f"{'='*60}")
y2_computed = (Q_135[1] ** 2) % p
y2_file = 80184233617433755134183875136831551618578922487806929476230322368028862899169
print(f"y^2 computed: {y2_computed:#x}")
print(f"y^2 from file: {y2_file:#x}")
print(f"Match: {y2_computed == y2_file}")
# Also verify y^2 == x^3 + 7
x3_7 = (px_135**3 + 7) % p
print(f"x^3+7: {x3_7:#x}")
print(f"y^2 == x^3+7? {y2_computed == x3_7}")

elapsed = time.time() - start
print(f"\nTotal time: {elapsed:.2f}s")
