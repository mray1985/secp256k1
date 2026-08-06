#!/usr/bin/env python3
"""
Quantify whether the shared CF subsequences between G and the A-point
are statistically significant, or just expected by chance.
"""
import random
from collections import defaultdict
import math

cfG = [0, 139221578786736675480792904055773408246814158120981180980253974860784918464552, 4, 9, 1, 18, 3, 1, 235, 2, 1, 1, 2, 3, 1, 3, 8, 5, 9, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 17, 1, 2, 1, 4, 4, 6, 221, 3, 1, 2, 3, 1, 3, 1, 1, 1, 3, 7, 1, 32, 1, 2, 2, 4, 2, 1, 3, 1, 19, 1, 1, 6, 1, 1, 3, 24, 1, 14, 5, 1, 2, 2, 1, 1, 1, 22, 3, 1, 2, 41, 1, 28, 1, 1, 2, 5, 12, 1, 4, 4, 1, 1, 3, 1, 1, 1, 12, 1, 70, 3, 1, 3, 2, 7, 1, 3, 1, 17, 34, 2, 2, 1, 9, 1, 1, 2, 7, 2, 8, 1, 26, 1, 4, 1, 6, 7, 2, 1, 1, 2, 1, 3, 2, 1, 3, 12, 1, 1, 2, 5, 35, 1, 6, 3, 5, 21, 2, 3]

cfA = [0, 2745525926515359661109446723818622216143021757590666919792393338008076506413, 5, 7, 2, 2, 1, 4, 252, 6, 1, 5, 2, 1, 26, 5, 6, 2, 3, 1, 2, 7, 1, 3, 1, 2, 2, 3, 6, 1, 1, 7, 1, 1, 4, 1, 9, 1, 3, 2, 2, 5, 1, 8, 1, 1, 1, 1, 1, 5, 68, 2, 1, 39, 1, 18, 1, 1, 15, 8, 1, 1, 1, 1, 1, 1, 6, 48, 6, 2, 2, 3, 1, 1, 1, 5, 4, 8, 1, 9, 5, 1, 1, 1, 1, 6, 1, 6, 2047, 1, 1, 2, 1, 1, 2, 5, 2, 3, 1, 8, 8, 2, 2, 396, 2, 1, 1, 1, 2, 5, 1, 4, 2, 1, 2, 7, 43, 4, 6, 3, 2, 2, 3, 1, 12, 7, 1, 53, 5, 1, 6, 1, 2, 1, 81, 1, 1, 1, 1, 8]

cf1 = cfG[1:]
cf2 = cfA[1:]

print(f"CF-G length: {len(cf1)} terms (excluding leading 0)")
print(f"CF-A length: {len(cf2)} terms (excluding leading 0)")
print()

def find_longest_matches(arr1, arr2, min_len=3):
    matches = []
    for start1 in range(len(arr1)):
        for start2 in range(len(arr2)):
            length = 0
            while (start1 + length < len(arr1) and 
                   start2 + length < len(arr2) and
                   arr1[start1 + length] == arr2[start2 + length]):
                length += 1
            if length >= min_len:
                matches.append((start1, start2, length))
    deduped = []
    for s1, s2, l in matches:
        contained = False
        for s1b, s2b, lb in matches:
            if lb > l and s1 >= s1b and s1 + l <= s1b + lb and s2 >= s2b and s2 + l <= s2b + lb:
                contained = True
                break
        if not contained:
            deduped.append((s1, s2, l))
    return deduped

def euclidean_cf(a, b):
    terms = []
    while b != 0:
        q = a // b
        terms.append(q)
        a, b = b, a % b
    return terms

NUM_TRIALS = 1000
print(f"Running {NUM_TRIALS} Monte Carlo trials...")
print()

max_len_counts = defaultdict(int)
target_seq = [1, 1, 2, 1, 1, 2]
target_count = 0

all_max_lengths = []
all_match_counts = []

for trial in range(NUM_TRIALS):
    n1_bits = random.randint(254, 260)
    d1_bits = random.randint(508, 518)
    n2_bits = random.randint(250, 260)
    d2_bits = random.randint(508, 518)
    
    r1_num = random.getrandbits(n1_bits)
    r1_den = random.getrandbits(d1_bits)
    r2_num = random.getrandbits(n2_bits)
    r2_den = random.getrandbits(d2_bits)
    
    if r1_num > r1_den:
        r1_num, r1_den = r1_den, r1_num
    if r2_num > r2_den:
        r2_num, r2_den = r2_den, r2_num
    if r1_num == 0: r1_num = 1
    if r2_num == 0: r2_num = 1
    
    cf_r1 = euclidean_cf(r1_num, r1_den)
    cf_r2 = euclidean_cf(r2_num, r2_den)
    
    if len(cf_r1) >= 2:
        cf_r1 = cf_r1[1:]
    if len(cf_r2) >= 2:
        cf_r2 = cf_r2[1:]
    
    if len(cf_r1) < 10 or len(cf_r2) < 10:
        continue
    
    matches = find_longest_matches(cf_r1, cf_r2, min_len=3)
    
    max_len = max((l for _, _, l in matches), default=0)
    all_max_lengths.append(max_len)
    all_match_counts.append(len(matches))
    
    max_len_counts[max_len] += 1
    
    s1 = ",".join(str(t) for t in cf_r1)
    s2 = ",".join(str(t) for t in cf_r2)
    target_str = ",".join(str(t) for t in target_seq)
    if target_str in s1 and target_str in s2:
        target_count += 1

print("=== NULL DISTRIBUTION (from {0} trials) ===".format(NUM_TRIALS))
print()
print("Probability of at least one matching subsequence of length >= L:")
for L in [3, 4, 5, 6, 7]:
    trials_with_L = sum(v for k, v in max_len_counts.items() if k >= L)
    pct = 100 * trials_with_L / NUM_TRIALS
    print(f"  Length >= {L}: {trials_with_L}/{NUM_TRIALS} = {pct:.1f}%")
print()

print("Distribution of max match lengths:")
for L in sorted(set(all_max_lengths)):
    print(f"  max_len = {L}: {max_len_counts[L]} trials")
print()

# Actual comparison
actual_matches = find_longest_matches(cf1, cf2, min_len=3)
actual_max_len = max((l for _, _, l in actual_matches), default=0)
actual_total = len(actual_matches)
print("=== ACTUAL (G vs A-point) ===")
print(f"  Max match length: {actual_max_len}")
print(f"  Total subsequences (>=3): {actual_total}")
print(f"  All lengths: {sorted([l for _,_,l in actual_matches], reverse=True)}")
print()

for s1, s2, l in actual_matches:
    if l == actual_max_len:
        seq_str = ",".join(str(t) for t in cf1[s1:s1+l])
        print(f"  Longest: CF1[{s1+1}:{s1+1+l}] = CF2[{s2+1}:{s2+1+l}] = [{seq_str}]")
print()

# Percentile
pctile = 100 * sum(1 for m in all_max_lengths if m < actual_max_len) / len(all_max_lengths)
print(f"Percentile of actual max length ({actual_max_len}): {pctile:.1f}%")
print(f"  -> {100-pctile:.1f}% of random pairs match or exceed this length")
if 100-pctile > 5:
    print(f"  -> NOT statistically significant (p > 0.05)")
else:
    print(f"  -> STATISTICALLY SIGNIFICANT (p < 0.05)")
print()

# Target subsequence
pct_target = 100 * target_count / NUM_TRIALS
print(f"=== Target subsequence [1,1,2,1,1,2] ===")
print(f"  Both random CFs: {target_count}/{NUM_TRIALS} = {pct_target:.1f}%")
print()

# Theoretical Gauss-Kuzmin
print("=== GAUSS-KUZMIN THEORETICAL ===")
gk = lambda n: math.log2(1 + 1/(n*(n+2)))
p1 = gk(1)
p2 = gk(2)
p_seq = p1**4 * p2**2
print(f"P(1) = {p1:.4f}")
print(f"P(2) = {p2:.4f}")
print(f"P(1,1,2,1,1,2) = {p_seq:.6f} (1 in {1/p_seq:.0f})")
n1, n2 = len(cf1), len(cf2)
print(f"Expected length-6 matches: {n1} * {n2} * {p_seq:.6f} = {n1 * n2 * p_seq:.2f}")
print()

# Summary of match density
print(f"Average matches per trial: {sum(all_match_counts)/len(all_match_counts):.1f}")
print(f"Actual match count: {actual_total}")
