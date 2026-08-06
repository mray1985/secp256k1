#!/usr/bin/env python3
"""
TRUE71 continued: Two investigations.

Part A: Does (Px - x_kG) mod p encode the private key d?
  For solved puzzles: check if (Px - x_kG) mapsto d via a known function
  For Puzzle 135: can we constrain d from this?

Part B: Check Puzzle 150 for Omega-blindness.
  Puzzle 150's public key x-coordinate and r value (if known).
"""
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
delta = p - N

# =====================================================================
# PART A: (Px - x_kG) vs d
# =====================================================================
print("=" * 80)
print("PART A: Does (Px - x_kG) mod p encode the private key d?")
print("=" * 80)

# Omega_p for orbit computations
omega_p = 55594575648329892869085402983802832744385952214688224221778511981742606582254
omega2_p = pow(omega_p, 2, p)

PUZZLES = {
    65:  { "d": 30568377312064202855, "r": 78851156821939598930719225276335666564424400002456474814517642714684883061408, "Omega": None, "Px": None },
    90:  { "d": 868012190417726402719548863, "r": 69673304720876160075229624583547409885636207434161816957474172319527500474415, "Omega": 0, "Px": 73943783080778544644073884909700639244535035648913344726967543677669522231490 },
    100: { "d": 868221233689326498340379183142, "r": 100182957009067260676129163398412919222496578752554197866304926759487636509729, "Omega": -1, "Px": 105107843095134683032230224202731497462680734257039598193514443284282804011944 },
    115: { "d": 31464123230573852164273674364426950, "r": 62641386159082452201681958645023150433102249854530986013739112343764069317711, "Omega": -1, "Px": 85799604727846561812244241365231437466950600594787996655912655443161772323420 },
    120: { "d": 919343500840980333540511050618764323, "r": 100480591869089994315869534883181916927590910231092411991845900661570178084117, "Omega": 1, "Px": 50990964210960446035476088109883183111472112728381819682361255294726240249067 },
    125: { "d": 37650549717742544505774009877315221420, "r": 63833400142572548270929737909115586706553550972272560806111166328807706465903, "Omega": -1, "Px": 82401241076497321097773355916846363684918813910079306023559651114443564616840 },
    130: { "d": 1103873984953507439627945351144005829577, "r": 6276493284178792263728042533158666787380597239988507667129682066325892829262, "Omega": -1, "Px": 105115992598952352481870529596996922472741646760946249511237288164845045142827 },
    135: { "d": None, "r": 0x86bec9faea4892fd98d718bdfc770d0d11c3d6bfd4328f25fe9b06bfadb9650, "Omega": 1, "Px": 0x145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16 },
    160: { "d": 0xE0A8B039282FAF6FE0FD769CFBC4B6B4CF8758BA68220EAC420E32B91DDFA673, "r": None, "Omega": -1, "Px": int("E0A8B039282FAF6FE0FD769CFBC4B6B4CF8758BA68220EAC420E32B91DDFA673", 16) },
}

print(f"{'Puzzle':<8} {'Px - x_kG mod p':<12} {'d':<20} {'ratio':<10} {'mod9':<6}")
print("-" * 60)

for height in sorted(PUZZLES.keys()):
    pd = PUZZLES[height]
    Px = pd["Px"]
    r = pd["r"]
    d = pd["d"]
    
    if Px is None or r is None:
        print(f"{height:<8} {'N/A':<12} {str(d) if d else 'N/A':<20}")
        continue
    
    x_kG = (r - delta) % p
    diff_mod_p = (Px - x_kG) % p
    diff_mod_N = (Px - x_kG) % N
    
    if d:
        ratio = diff_mod_p / d
        print(f"{height:<8} {diff_mod_p:<12} {d:<20} {ratio:<10.2f} {diff_mod_p % 9}")
        # Check various relationships
        # Is diff ≡ d mod something?
        print(f"         diff - d mod p = {(diff_mod_p - d) % p}")
        print(f"         diff - d mod N = {(diff_mod_N - d) % N}")
        print(f"         diff mod N / d mod N = {(diff_mod_N * pow(d % N, -1, N)) % N if d % N != 0 else 'N/A'}")
    else:
        print(f"{height:<8} {diff_mod_p:<12} {'UNKNOWN':<20} {'':<10} {diff_mod_p % 9}")
    print()

# Part A2: check if (Px - x_kG) relates to dG (= Px)
print("Check: does (Px - x_kG)^-1 mod p relate to Lambda?")
Lambda = 97451685862885086182458552040892158509924235661624603229050850812487253689501
for height in sorted(PUZZLES.keys()):
    pd = PUZZLES[height]
    Px = pd["Px"]
    r = pd["r"]
    if Px is None or r is None: continue
    x_kG = (r - delta) % p
    diff = (Px - x_kG) % p
    diff_inv_mod_p = pow(diff, -1, p)
    print(f"Puzzle {height}: diff_inv mod p = {diff_inv_mod_p}")
    ratio_L = (diff_inv_mod_p * pow(Lambda, -1, p)) % p
    print(f"  diff_inv / Lambda = {ratio_L}")
    ratio_K = (diff_inv_mod_p * pow(Lambda, 1, p)) % p
    print(f"  diff_inv * Lambda = {ratio_K}")

# =====================================================================
# PART B: Puzzle 150 check
# =====================================================================
print()
print("=" * 80)
print("PART B: Puzzle 150 - Omega-blindness check")
print("=" * 80)

# Puzzle 150 data from known public key
# P150 public key x-coordinate and r value
# From known puzzle data
p150_Px = int("673476b0d363c7f0de73d5270f6863a68b6e4bc2669e6e9c1f6c52d2b7d152a6", 16)
print(f"\nPuzzle 150 Px = {p150_Px}")
print(f"Px mod 9 = {p150_Px % 9}")

# Check orbit of P150 Px under omega_p
orbit_p150 = [p150_Px % 9, (p150_Px * omega_p) % p % 9, (p150_Px * omega2_p) % p % 9]
print(f"Px orbit mod 9 = {orbit_p150}")

def sector(r):
    if r in {1, 4, 7}: return "+1"
    if r in {2, 3, 5, 6, 8}: return "-1"
    return "0"

sectors_p150 = [sector(r) for r in orbit_p150]
print(f"Px sectors = {sectors_p150}")
print(f"Unique sectors = {set(sectors_p150)}")

# Puzzle 150's r value (from known puzzle data)
# r150 for puzzle 150
try:
    p150_r = int("96f963148b8c1a36b0d76819b232a37c13e77c7e4dce258a6a8fa77e82c3ac74", 16)
    print(f"\nP150 r = {p150_r}")
    x_kG_150 = (p150_r - delta) % p
    r_orbit_150 = [x_kG_150 % 9, (x_kG_150 * omega_p) % p % 9, (x_kG_150 * omega2_p) % p % 9]
    print(f"x_kG orbit mod 9 = {r_orbit_150}")
    print(f"x_kG sectors = {[sector(r) for r in r_orbit_150]}")
except:
    print("\nPuzzle 150 r not available - checking known-residue alternative")
    # Check from TRUE57_TRUE58 summary: Omega = +1 expected
    print("From TRUE57_TRUE58: Puzzle 150 expected Omega = +1")
    print("Check if Px orbit contains sector +1...")
    contains_plus1 = "+1" in set(sectors_p150)
    print(f"  Px orbit contains +1: {contains_plus1}")
    if not contains_plus1:
        print("  *** P150 ALSO appears Omega-blind in Px orbit!")
    else:
        print("  P150 Px orbit shows +1 - not Omega-blind")

# Summary comparison
print()
print("=" * 80)
print("SUMMARY: (Px - x_kG) ANALYSIS")
print("=" * 80)
print()
print("The key relationships between Px, x_kG, and d for solved puzzles:")
print("  Px = public key x-coordinate")
print("  x_kG = (r - delta) mod p (reconstructed nonce point x)")
print("  d = private key")
print()
print("Expected if Lambda bridge holds: Px = Lambda * rx3 mod p")
print("But x_kG relates to r, not rx3. r = x_kG mod N (from ECDSA).")
print("So (Px - x_kG) mod p has no obvious algebraic relation to d.")
print()
print("If no relationship found: the asymmetry is structural (Omega classification")
print("lives in the nonce geometry, not just the public key).")
