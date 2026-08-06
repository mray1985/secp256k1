p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

r = 90653255469745952335985143920649543885181555095025199315947044135806663628368
s = 15509729875763924304053419655647994379903175655107184284998698212653288468986
z = 66278737796829840734606014530466656889790152192829793669891337810330530090951
A = 80184233617433755134183875136831551618578922487806929476230322368028862899169
x2 = A - 7

# x2^3 mod s = C1
C1 = pow(x2, 3, s)
print(f"C1 = x2^3 mod s = {C1}")

# x2^3 mod N = C1N
C1N = pow(x2, 3, N)
print(f"x2^3 mod N = C1N = {C1N}")
print(f"C1N hex = {hex(C1N)}")
print()

# The 9 s-side roots from the file
file_roots = [
    573607990413771774330660150338470777282684101820002707407326044178689925190,
    1037622267039375860770424440147576644036988876824633854748801820544033215852,
    2635584238614133613916776858591579719063044212271008051236831304762420554232,
    3099598515239737700356541148400685585817348987275639198578307081127763844894,
    4640324220577404408449972586882647982238828469966881796778592517750577015938,
    6702300468777766248036089295135756924019188580417887140608097778334307644980,
    7773744950252354499456455900312557616057608432512217286346144123929830284478,
    8237759226877958585896220190121663482811913207516848433687619900295173575140,
    11840461180415987133575768336856734821013752800659096375717410597501717375226,
]

print("=== Verify 9 s-side roots all satisfy root^3 ≡ C1 mod s ===")
for i, root in enumerate(file_roots):
    ok = pow(root, 3, s) == C1
    if not ok:
        print(f"  root[{i}] FAILS: {pow(root, 3, s)} != {C1}")
print("   All verified" if all(pow(r, 3, s) == C1 for r in file_roots) else "   Some FAILED")
print()

# Verify x2 itself is also a cube root of C1 mod s
print(f"x2^3 mod s == C1? {pow(x2, 3, s) == C1}")
print()

# The 9 roots and x2 together make 10 cube roots
# This means there are 10 cube roots of unity mod s
# So the group of cube roots has order 10

# Find all cube roots of unity mod s by pairwise ratios
print("=== Cube roots of unity from pairwise ratios ===")
all_10_roots = file_roots + [x2]
cube_roots_unity = set()
for root in all_10_roots:
    # root = x2 * w  =>  w = root * x2^(-1) mod s
    w = (root * pow(x2, -1, s)) % s
    if pow(w, 3, s) == 1:
        cube_roots_unity.add(w)

print(f"Found {len(cube_roots_unity)} cube roots of unity mod s:")
for i, w in enumerate(sorted(cube_roots_unity)):
    print(f"  w[{i}] = {w}")
    print(f"    w^3 mod s = {pow(w, 3, s)}")
print()

# These should match lines 2-11 of mod by itself.txt (x^3 ≡ 1 mod s)
# Let's check
print(f"x=1 in set? {1 in cube_roots_unity}")
print(f"count = {len(cube_roots_unity)}")
print()

# Now verify square roots of unity (y^2 ≡ 1 mod s)
# These reveal the factorization of s
print("=== s factorization via sqrt(1) ===")
from math import gcd

# Quick factorization using sqrt(1) pairs
solutions_s_y = [
    1,
    381792376602234173771085364898831817100603104878235301245872629949439781561,
    3984801190317821150857613234581568094823244331513602849333590824033198111039,
    4366593566920055324628698599480399911923847436391838150579463453982637892601,
    5254315050089489013919553254627727194352245805530756212424565787965532584533,
    5507028882152145791734082436641035456526479308306354620748796340755678210291,
    5636107426691723187690638619526559011452848910408991513670438417914972366095,
    5888821258754379965505167801539867273627082413184589921994668970705117991853,
    9620908617009544338548251854108127106276093241922594363004029241948170477133,
    987362244907220111636278103612536536845032674698192771328259794738316102891,
    10002700993611778512319337219006958923376696346800829664249901871897610258695,
    10255414825674435290133866401020267185550929849576428072574132424687755884453,
    11143136308843868979424721056167594467979328218715346134419234758670650576385,
    11524928685446103153195806421066426285079931323593581435665107388620090357947,
    15127937499161690130282334290749162562802572550228948983752825582703848687425,
    s - 1
]

print(f"s has {len(solutions_s_y)} square roots of unity")
factors = set()
for y in solutions_s_y[1:-1]:
    f = gcd(y - 1, s)
    if f > 1 and f < s:
        factors.add(f)
        factors.add(s // f)

print(f"\nDistinct non-trivial factors from sqrt(1):")
for f in sorted(factors, reverse=True):
    print(f"  {f}")
print()

# Small prime factors of s
print("Small prime factors of s:")
temp = s
for p_ in [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]:
    count = 0
    while temp % p_ == 0:
        temp //= p_
        count += 1
    if count:
        print(f"  {p_}^{count}")
print(f"  remaining cofactor: {temp}")
print(f"  remaining bits: {temp.bit_length()}")
print()

# Key insight: s = ECDSA signature s value
# r = ECDSA signature r value  
# x2 = A-7 where A = IP (intermediate point)
# x2^3 mod s = C1
# x2^3 mod N = C1N
# n2 = x2 is one of the N-side cube roots of C1N  

# The N-side roots of C1N mod N
print("=== N-side cube root structure ===")
# From check_A_derivation.py:
n1 = 40220395037450137658562871366385094182673796545182808438190875548898232062868 
n2 = x2  # confirmed
n3 = 111179549819748498054395223514159169904422409525160070850789128366109228026644

print(f"n1 = {n1}")
print(f"n2 = {n2}")
print(f"n3 = {n3}")
print(f"n1^3 mod N = {pow(n1, 3, N)}")
print(f"n2^3 mod N = {pow(n2, 3, N)}")
print(f"n3^3 mod N = {pow(n3, 3, N)}")
print(f"All equal? {pow(n1,3,N) == pow(n2,3,N) == pow(n3,3,N)}")
print(f"Sum n1+n2+n3 = {(n1 + n2 + n3) % (2*N)}")
print()

# P-side (mod p) roots
print("=== P-side cube root structure ===")
p1 = 9210836494447108270027136741376870869791784014198948301625976867708124077590
p2 = 51866120889717641461810659005716431188799022756838843706514074509901265629059
p3 = 54715131853151445691733189261505694605794679177894602772031317532630299444965014  # wrong length?
print(f"p1 = {p1}")
print(f"p2 = {p2}")
print(f"p1^3 mod p = {pow(p1, 3, p)}")
print(f"p2^3 mod p = {pow(p2, 3, p)}")
print(f"Sum p1+p2+p3 = {p1 + p2 + p3} == p? {p1 + p2 + p3 == p}")
