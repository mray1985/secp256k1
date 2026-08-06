#!/usr/bin/env python3
"""
Puzzle 160 Deep Factoradic Stacking
====================================
Stack factoradic digits a1..a10 to accumulate modular constraints.

Key insight:
  d = a1*1! + a2*2! + a3*3! + ... + a10*10!
  
  For mod m, only factorials < m contribute meaningfully.
  Each digit adds a new modular filter.

Constraints so far:
  - a1..a5 -> mod 9 constraint (80 prefixes from 720)
  - a6 adds mod 7 constraint (7! = 5040 = 7*720)
  - a7 adds mod constraint from 8!
  - etc.

Goal: find how many independent modular constraints we can stack,
and whether they narrow the search space enough.
"""

import sys
import os

# Factorials
FACT = [1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880, 3628800, 39916800]

# secp256k1 constants (only N needed for mod calculations)
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

def main():
    print("=" * 80)
    print("DEEP FACTORADIC STACKING FOR PUZZLE 160")
    print("=" * 80)
    print()
    
    # Part 1: Analyze what each factoradic digit contributes to each mod
    print("PART 1: Factorial contributions modulo small primes/powers")
    print("=" * 80)
    print()
    
    mods = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 25, 27]
    
    print(f"{'n!':<6}", end="")
    for m in mods:
        print(f"mod{m:<4}", end="")
    print()
    print("-" * (6 + 5 * len(mods)))
    
    for n in range(1, 11):
        print(f"{FACT[n]:<6}", end="")
        for m in mods:
            val = FACT[n] % m
            print(f"{val:<5}", end="")
        print()
    
    print()
    print("Key: n! = 0 (mod m) means digit a_n no longer affects mod m")
    print()
    
    # Part 2: For each mod, which digits matter?
    print("PART 2: Which factoradic digits matter for each modulus?")
    print("=" * 80)
    print()
    
    for m in mods:
        # Find first n where n! = 0 (mod m)
        cutoff = 11  # beyond a10
        for n in range(1, 11):
            if FACT[n] % m == 0:
                cutoff = n
                break
        digits = list(range(1, cutoff))
        print(f"  mod {m:>3}: digits a{'..a'.join(str(d) for d in digits)} matter (cutoff at {cutoff}!)")
    
    print()
    
    # Part 3: Build the stacking attack
    print("PART 3: Stacking constraints step by step")
    print("=" * 80)
    print()
    
    BAND_LO = 2**159
    BAND_HI = 2**160 - 1
    
    # We know d = 7 (mod 9) from the Origin Rule
    TARGET_MOD9 = 7
    
    # Step 1: a1..a5 for mod 9 (already done)
    print("Step 1: a1..a5 for mod 9 constraint")
    prefixes_80 = []
    for a1 in range(0, 2):
        for a2 in range(0, 3):
            for a3 in range(0, 4):
                for a4 in range(0, 5):
                    for a5 in range(0, 6):
                        val = a1*FACT[1] + a2*FACT[2] + a3*FACT[3] + a4*FACT[4] + a5*FACT[5]
                        if val % 9 == TARGET_MOD9:
                            prefixes_80.append((a1, a2, a3, a4, a5, val))
    print(f"  80 valid prefixes (from 720)")
    print()
    
    # Step 2: Extend each to a6 (mod 7 constraint)
    print("Step 2: Extend to a6 (adds mod 7 constraint)")
    print("  7! = 5040 = 7 * 720, so a6*7! mod 7 = a6 * 0 = 0")
    print("  Wait - 7! = 5040, 5040/7 = 720 exactly. So 7! = 0 (mod 7)")
    print("  Therefore a6 does NOT add a mod-7 constraint!")
    print()
    
    # Actually let me recalculate more carefully
    # For mod 7:
    # 1! = 1, 2! = 2, 3! = 6, 4! = 24 = 3*7+3 -> 3, 5! = 120 = 17*7+1 -> 1
    # 6! = 720 = 102*7+6 -> 6, 7! = 5040 = 720*7 -> 0
    # So mod 7, a1..a6 matter
    
    print("Correction: Let me compute which digits matter for mod 7:")
    for n in range(1, 8):
        print(f"  {n}! mod 7 = {FACT[n] % 7}")
    print("  7! = 0 (mod 7), so a1..a6 matter for mod 7")
    print()
    
    # Step 3: For each of the 80 prefixes, what does a6 add?
    print("Step 3: Extending to a6 (mod 7 filter on top of mod 9)")
    a6_prefixes = []
    for (a1, a2, a3, a4, a5, base_val) in prefixes_80:
        for a6 in range(0, 7):  # a6 in [0,6]
            val = base_val + a6 * FACT[6]
            # Check: does this value satisfy some mod-7 constraint?
            # We don't know the target mod-7 value yet, so just track all
            a6_prefixes.append((a1, a2, a3, a4, a5, a6, val))
    
    print(f"  80 * 7 = {len(a6_prefixes)} combinations")
    print()
    
    # For mod 7, we can compute what the actual d mod 7 should be
    # for each known solved puzzle, and see if there's a pattern
    
    # But we don't know d for P160. What we CAN do is:
    # For each possible mod-7 value, how many prefixes survive?
    
    print("  Distribution of (val mod 7) across all 560 a1..a6 combos:")
    mod7_dist = {}
    for (a1, a2, a3, a4, a5, a6, val) in a6_prefixes:
        r = val % 7
        mod7_dist[r] = mod7_dist.get(r, 0) + 1
    for r in range(7):
        print(f"    val mod 7 = {r}: {mod7_dist.get(r, 0)} prefixes")
    print()
    
    # Step 4: Check what mod 7 value known puzzles give
    print("Step 4: Known puzzle d mod 7 values")
    known = [
        (65,  30568377312064202855),
        (90,  868012190417726402719548863),
        (100, 868221233689326498340379183142),
        (115, 31464123230573852164273674364426950),
        (120, 919343500840980333540511050618764323),
        (125, 37650549717742544505774009877315221420),
        (130, 1103873984953507439627945351144005829577),
    ]
    print(f"  {'Puzzle':<10} {'d mod 9':<10} {'d mod 7':<10} {'d mod 8':<10} {'d mod 5':<10}")
    print("  " + "-" * 50)
    for pnum, d in known:
        print(f"  P{pnum:<9} {d % 9:<10} {d % 7:<10} {d % 8:<10} {d % 5:<10}")
    print()
    
    # Step 5: Stack all constraints we can
    print("=" * 80)
    print("PART 4: FULL STACKING - a1..a10 with all available mod constraints")
    print("=" * 80)
    print()
    
    # Build deeper: a1..a10
    # a1: 0-1, a2: 0-2, a3: 0-3, a4: 0-4, a5: 0-5, a6: 0-6, a7: 0-7, a8: 0-8, a9: 0-9, a10: 0-10
    
    # We need to know target mod values for each modulus.
    # We only know mod 9 = 7 for P160.
    # For other mods, we'd need to figure out targets.
    
    # But we CAN do this: for each modulus m, the constraint from
    # the factoradic digits gives us partial info about d mod m.
    # The number of possible d mod m values narrows as we add digits.
    
    # Let's compute: for each modulus m, how many possible d mod m
    # values exist after considering a1..a_k?
    
    mods_to_check = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 25, 27]
    
    print(f"{'mod m':<8} {'digits':<20} {'possible':<12} {'total':<8} {'reduction'}")
    print("-" * 65)
    
    for m in mods_to_check:
        # Find which digits matter
        cutoff = 11
        for n in range(1, 11):
            if FACT[n] % m == 0:
                cutoff = n
                break
        
        # Compute all possible values of (a1*1! + a2*2! + ... + a_{cutoff-1}*(cutoff-1)!) mod m
        possible = set()
        
        # For efficiency, enumerate
        def enumerate_mod(depth, current_val, max_digit):
            if depth == cutoff:
                possible.add(current_val % m)
                return
            n = depth + 1  # factoradic index (1-based)
            for a in range(0, n + 1):
                enumerate_mod(depth + 1, current_val + a * FACT[n], n)
        
        if cutoff <= 10:
            enumerate_mod(1, 0, 1)
        
        num_digits = cutoff - 1
        reduction = m / len(possible) if len(possible) > 0 else float('inf')
        print(f"{m:<8} a1..a{num_digits:<16} {len(possible):<12} {m:<8} {reduction:.2f}x")
    
    print()
    
    # Part 5: Combined constraint strength
    print("=" * 80)
    print("PART 5: COMBINED CONSTRAINT ANALYSIS")
    print("=" * 80)
    print()
    
    # The question: if we know d mod m for several m values,
    # what is the total search space reduction?
    
    # From mod 9: 9x reduction (d = 7 mod 9)
    # From mod 7: depends on target value
    # From mod 8: depends on target value
    # etc.
    
    # Let's compute: what's the LCM of all achievable moduli?
    # If we can determine d mod 9, d mod 7, d mod 8, d mod 5, d mod 11, etc.
    # the combined period is lcm(9, 7, 8, 5, 11, ...) 
    
    # Known moduli we can extract:
    # mod 9 from a1..a5 (factoradic structure)
    # mod 7 from a1..a6 (factoradic structure)  
    # mod 8 from a1..a3 (24 = 0 mod 8)
    # mod 5 from a1..a5 (120 = 0 mod 5, so a1..a4: 1,2,6,24 mod 5 = 1,2,1,4)
    
    # Wait - 5! = 120 = 0 mod 5, so for mod 5, a1..a4 matter
    # For mod 8: 4! = 24 = 0 mod 8, so a1..a3 matter
    
    # Actually 4! = 24 = 3*8, so yes 0 mod 8
    # 3! = 6, 2! = 2, 1! = 1
    
    # For mod 5: 4! = 24 = 4 mod 5, 3! = 6 = 1 mod 5, 2! = 2, 1! = 1
    # 5! = 120 = 0 mod 5
    
    # Let's just compute the product of achievable mod reductions
    
    print("Known constraint: d = 7 (mod 9) from Origin Rule")
    print()
    print("Additional constraints from factoradic structure:")
    print("  If we could determine the TARGET value for each mod,")
    print("  we could stack them via CRT.")
    print()
    print("The key question: what determines the target mod values?")
    print("Answer: the actual private key d itself.")
    print()
    print("We can't know the targets without knowing d.")
    print("BUT: we can use the factoradic structure to narrow")
    print("which targets are POSSIBLE.")
    print()
    
    # Part 6: The real attack - enumerate all factoradic combos
    # and see if the intersection of mod constraints is tight enough
    
    print("=" * 80)
    print("PART 6: FACTORADIC ENUMERATION a1..a10")
    print("=" * 80)
    print()
    
    # Full enumeration of a1..a10 with mod 9 = 7 filter
    # a1: 0-1 (2), a2: 0-2 (3), a3: 0-3 (4), a4: 0-4 (5), a5: 0-5 (6)
    # = 720 combos, filtered to 80 by mod 9
    # Then a6: 0-6 (7), a7: 0-7 (8), a8: 0-8 (9), a9: 0-9 (10), a10: 0-10 (11)
    
    # For each full combo, compute d mod m for various m
    # Then group by (d mod 9, d mod 7, d mod 8, d mod 5, d mod 11)
    # and see how many unique combinations exist
    
    print("Enumerating a1..a10 (filtered by mod 9 = 7)...")
    print()
    
    # Track: for each combo of mod values, how many factoradic combos map to it
    mod_profiles = {}  # (mod9, mod7, mod8, mod5, mod11) -> count
    
    count = 0
    for a1 in range(0, 2):
        for a2 in range(0, 3):
            for a3 in range(0, 4):
                for a4 in range(0, 5):
                    for a5 in range(0, 6):
                        base5 = a1*1 + a2*2 + a3*6 + a4*24 + a5*120
                        if base5 % 9 != 7:
                            continue
                        for a6 in range(0, 7):
                            base6 = base5 + a6 * 720
                            for a7 in range(0, 8):
                                base7 = base6 + a7 * 5040
                                for a8 in range(0, 9):
                                    base8 = base7 + a8 * 40320
                                    for a9 in range(0, 10):
                                        base9 = base8 + a9 * 362880
                                        for a10 in range(0, 11):
                                            d_partial = base9 + a10 * 3628800
                                            profile = (
                                                d_partial % 9,
                                                d_partial % 7,
                                                d_partial % 8,
                                                d_partial % 5,
                                                d_partial % 11,
                                            )
                                            mod_profiles[profile] = mod_profiles.get(profile, 0) + 1
                                            count += 1
    
    print(f"Total a1..a10 combos (with mod9=7 filter): {count}")
    print(f"Unique (mod9, mod7, mod8, mod5, mod11) profiles: {len(mod_profiles)}")
    print()
    
    # Show distribution
    print("Profile distribution (top 20):")
    sorted_profiles = sorted(mod_profiles.items(), key=lambda x: -x[1])
    print(f"  {'mod9':<6} {'mod7':<6} {'mod8':<6} {'mod5':<6} {'mod11':<6} {'count':<10}")
    print("  " + "-" * 45)
    for profile, cnt in sorted_profiles[:20]:
        m9, m7, m8, m5, m11 = profile
        print(f"  {m9:<6} {m7:<6} {m8:<6} {m5:<6} {m11:<6} {cnt:<10}")
    
    print(f"  ... ({len(sorted_profiles)} total profiles)")
    print()
    
    # How many profiles have only 1 combo? (fully determined)
    singletons = sum(1 for cnt in mod_profiles.values() if cnt == 1)
    print(f"Profiles with exactly 1 combo (fully determined): {singletons}")
    print(f"Profiles with >1 combo: {len(mod_profiles) - singletons}")
    print()
    
    # The CRITICAL question: what is the period of the full factoradic system?
    # d = sum(a_i * i!) for i=1..10
    # The maximum value is sum(i * i!) for i=1..10 = ?
    max_d = sum(FACT[i] * i for i in range(1, 11))
    print(f"Maximum d from a1..a10: {max_d} = {max_d.bit_length()} bits")
    print(f"  = 0x{max_d:010x}")
    print(f"  Puzzle 160 band: [{BAND_LO.bit_length()-1} bits, {BAND_HI.bit_length()} bits]")
    print()
    
    # The factoradic digits a1..a10 can represent up to about 10! * 10 = 36M
    # The band is 2^159 ~ 10^47
    # So factoradic a1..a10 only covers a tiny fraction of the band!
    
    # This means: d = (some value from a1..a10) + k * 11! for some large k
    # Wait, that's not how factoradic works for large numbers.
    
    # Actually, for a 160-bit number, the full factoradic representation
    # would need about 160 digits (since n! grows roughly as (n/e)^n).
    
    # The first ~10 digits only constrain the LOW bits of d.
    # The high bits are determined by later digits.
    
    print()
    print("=" * 80)
    print("PART 7: CRITICAL INSIGHT - WHAT DO a1..a10 ACTUALLY CONSTRAIN?")
    print("=" * 80)
    print()
    
    # For a number d in [2^159, 2^160), the factoradic representation
    # has many digits. The first 10 digits only constrain the value
    # modulo 11! = 39916800.
    
    period = FACT[11]  # = 11! = 39916800
    print(f"a1..a10 constrain d mod {period}")
    print(f"  11! = {period} = {period.bit_length()} bits")
    print(f"  Puzzle 160 band: 2^159 to 2^160")
    print(f"  Number of 11! blocks in the band: ~2^159 / {period} = 2^{159 - period.bit_length() + 1:.1f}")
    print()
    
    # So a1..a10 narrow d to one residue class mod 11!
    # That's a reduction of 11! = 40M, which is about 2^25
    
    reduction_bits = period.bit_length() - 1
    remaining = 159 - reduction_bits
    print(f"Reduction from a1..a10: {period}x = ~{reduction_bits} bits")
    print(f"Remaining search space: ~2^{remaining}")
    print()
    
    # For mod 9 = 7 specifically:
    # From a1..a5: 80 out of 720 combos, factor of 9 = 2^3.17
    # From a6..a10: additional constraints on d mod 11!
    
    # The total number of valid a1..a10 combos with mod9=7 is:
    valid_total = sum(mod_profiles.values())
    print(f"Valid a1..a10 combos (mod9=7): {valid_total}")
    print(f"  out of total a1..a10 combos: {count}")
    print(f"  Reduction from mod9=7: {count/valid_total:.1f}x")
    print()
    
    # The actual reduction is mod 9 = 7 gives 1/9 of all values
    # So valid_total should be count / 9
    print(f"  Expected: {count} / 9 = {count/9:.0f}")
    print()
    
    # The real question: can we get MORE constraints?
    # Answer: only if we know additional target mod values.
    
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    print("1. Factoradic a1..a10 constrains d mod 11! (period = 39,916,800)")
    print("   This is a ~2^25 reduction, leaving ~2^134 candidates.")
    print()
    print("2. The mod 9 = 7 constraint from Origin Rule is ALREADY included")
    print("   in the factoradic structure (it's the a1..a5 filter).")
    print()
    print("3. To narrow further, we need either:")
    print("   a) More modular constraints from the Origin Rule / bridge")
    print("   b) A way to determine the target mod values for mod 7, mod 8, etc.")
    print("   c) A structural property that links the factoradic to the EC point")
    print()
    print("4. The gap remains: factoradic gives us d mod 11!, but we need")
    print("   to SEARCH the remaining 2^134 space, which is still infeasible")
    print("   without a fast EC scalar multiplication test.")
    print()
    print("RECOMMENDATION: The factoradic approach alone cannot solve P160.")
    print("It reduces 2^159 -> 2^134, but the real bottleneck is the EC")
    print("computation. Need a different angle from the frozen findings.")

if __name__ == "__main__":
    main()
