p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

def modinv(x, mod):
    return pow(x, -1, mod)

def point_add(P1, P2):
    if P1 is None: return P2
    if P2 is None: return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2:
        if y1 != y2: return None
        if y1 == 0: return None
        lam = (3 * x1 * x1) * modinv(2 * y1, p) % p
    else:
        lam = (y2 - y1) * modinv(x2 - x1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)

def point_mul(k, P):
    result = None
    addend = P
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result

G = (Gx, Gy)

# From Complexity_Simplified_135.txt
rx1 = 114930704126154877082883546730544079307369404418439078397954295509919169851219
rx2 = 90653255469745952335985143920649543885181555095025199315947044135806663628368
rx3 = 26000218878731561428279366182192513989009817816850365013828370091835863739

Gx1 = 91177636130617246552803821781935006617134368061721227770777272682868638699771
Gx2 = 55066263022277343669578718895168534326250603453777594175500187360389116729240  # = Gx
Gx3 = 85340279321737800624759429340272274763154997815782306132637707972559913914315

Px1 = 51866120889717641461810659005716431188799022756838843706514074509901265629059
Px2 = 54715131853151445691733189261594605794679177894602772031317532630299444965014
Px3 = 9210836494447108270027136741376870869791784014198948301625976867708124077590  # X_puzzle

d1 = 1248780847746852317428964695904392891045016528862400526454142780194939123483
d2 = 21551977082208859489759061364299864038123955443494189974630776168682352336746
d3 = 92991331307360483616382958948483650923668592306718313881520244192640870034108

omega2 = 37718080363155996902926221483475020450927657555482586988616620542887997980018
lam = 78074008874160198520644763525212887401909906723592317393988542598630163514318

Lambda = 97451685862885086182458552040892158509924235661624603229050850812487253689501
Lambda_inv_p = pow(Lambda, -1, p)

# Check: does rx3 * G give a point with x-coordinate = rx2?
print("Checking if rx3 is the nonce k:")
R_rx3 = point_mul(rx3, G)
print(f"  rx3 * G.x mod N = {R_rx3[0] % N}")
print(f"  rx2 = r          = {rx2}")
print(f"  Match? {R_rx3[0] % N == rx2}")

# Check: rx1
print("\nChecking rx1:")
R_rx1 = point_mul(rx1 % N, G)  # rx1 > N, reduce
print(f"  (rx1 mod N) * G.x mod N = {R_rx1[0] % N}")
print(f"  rx2 = r                  = {rx2}")
print(f"  Match? {R_rx1[0] % N == rx2}")

# Check: is Gx1 = rx1 * G?
print("\nGx family check:")
R_gx1 = point_mul(rx1 % N, G)
print(f"  rx1 * G.x = {R_gx1[0]}")
print(f"  Gx1       = {Gx1}")
print(f"  Match? {R_gx1[0] == Gx1}")

R_gx2 = point_mul(rx2, G)
print(f"  r * G.x = {R_gx2[0]}")
print(f"  Gx2 (Gx)= {Gx2}")
print(f"  Match? {R_gx2[0] == Gx2}")

R_gx3 = point_mul(rx3, G)
print(f"  rx3 * G.x = {R_gx3[0]}")
print(f"  Gx3       = {Gx3}")
print(f"  Match? {R_gx3[0] == Gx3}")

# Check Px family relationship
print("\nPx family (defect root bridge):")
# Px_i = Lambda * rx_i mod p
print(f"  Lambda * rx1 mod p = {(Lambda * rx1) % p}")
print(f"  Px1                = {Px1}")
print(f"  Match? {(Lambda * rx1) % p == Px1}")

print(f"  Lambda * rx2 mod p = {(Lambda * rx2) % p}")
print(f"  Px2                = {Px2}")
print(f"  Match? {(Lambda * rx2) % p == Px2}")

print(f"  Lambda * rx3 mod p = {(Lambda * rx3) % p}")
print(f"  Px3                = {Px3}")
print(f"  Match? {(Lambda * rx3) % p == Px3}")

# Check defect root alignment
print("\nDefect root alignment for Gx family:")
for i, (name, gx) in enumerate([('Gx1', Gx1), ('Gx2', Gx2), ('Gx3', Gx3)]):
    for di_name, di in [('d1', d1), ('d2', d2), ('d3', d3)]:
        val = gx * pow(di, -1, N) % N
        print(f"  {name} * {di_name}^-1 mod N = {val}")
        
# Check: is Px * d_j^-1 = constant?
print("\nPx * d_j^-1 mod N test:")
for di_name, di in [('d1', d1), ('d2', d2), ('d3', d3)]:
    val = Px3 * pow(di, -1, N) % N
    print(f"  X_puzzle * {di_name}^-1 mod N = {val}")

# The key: if Px * d_j^-1 = some constant T, then T * d_j = Px
# and d = T^-1 * something

# Check: the formula says delta_k = r * s^-1 mod N
s = 15509729875763924304053419655647994379903175655107184284998698212653288468986
z = 71064462160542359496608045361802369442136853116296444512644642138879838172892

delta_k = rx2 * pow(s, -1, N) % N
print(f"\ndelta_k = r * s^-1 mod N = {delta_k}")
print(f"From file: delta_k = 42518748094800190364691662520829255725760545190387351376607655495124216557634")
print(f"Match? {delta_k == 42518748094800190364691662520829255725760545190387351376607655495124216557634}")

# d = candidate from the alignment
# Candidate 4: rx3 * d3^-1 mod N
cand4 = rx3 * pow(d3, -1, N) % N
print(f"\nCandidate 4 = rx3 * d3^-1 mod N = {cand4}")
print(f"From file: cand4 = 34706299379050942770522757347675977362549089194729674146344199561864973356492")
print(f"Match? {cand4 == 34706299379050942770522757347675977362549089194729674146344199561864973356492}")

# Candidate 5 = d from cand4 * delta_k?
# If k = delta_k * d (scaled by some delta), then:
# If d = candidate4, and k = candidate4 * delta_k mod N
cand5 = cand4 * delta_k % N
print(f"\nCandidate 5 = cand4 * delta_k mod N = {cand5}")
print(f"From file: cand5 = 66403955407895824054248351372224921354707870334246805226508675908722401065510")
print(f"Match? {cand5 == 66403955407895824054248351372224921354707870334246805226508675908722401065510}")

# Check: does cand5 = d? If so, cand5 * G should have x-coord = X_puzzle
print(f"\nVerify: cand5 * G.x should equal X_puzzle if cand5 = d")
d_cand5 = point_mul(cand5, G)
print(f"  cand5 * G.x = {d_cand5[0]}")
print(f"  X_puzzle    = {Px3}")
print(f"  Match? {d_cand5[0] == Px3}")

# Also check using ECDSA: s * k = z + r * d
# If d = cand5, then k = s^-1 * (z + r * d)
d_test = cand5
k_test = (z + rx2 * d_test) * pow(s, -1, N) % N
print(f"\nECDSA consistency for d=cand5:")
print(f"  d = {d_test}")
print(f"  d bits = {d_test.bit_length()}")
print(f"  d in [2^134, 2^135)? {21778071482940061661655974875633165533184 <= d_test < 43556142965880123323311949751266331066367}")
print(f"  k = s^-1 * (z + r*d) mod N = {k_test}")

# Check if this k gives x-coord = r
R_k_test = point_mul(k_test, G)
print(f"  k*G.x mod N = {R_k_test[0] % N}")
print(f"  r           = {rx2}")
print(f"  Match? {R_k_test[0] % N == rx2}")

# Try other candidates
print("\n\n=== All 5 candidates ===")
candidates = {
    'cand1 (rx3)': rx3 % N,
    'cand2 (rx3 * Lambda^-1 mod N)': (rx3 * pow(Lambda, -1, N)) % N,
    'cand3 (d3)': d3,
    'cand4 (rx3 * d3^-1 mod N)': cand4,
    'cand5 (cand4 * delta_k mod N)': cand5,
}

for name, d_val in candidates.items():
    # Compute k from d
    k_val = (z + rx2 * d_val) * pow(s, -1, N) % N
    Rk = point_mul(k_val, G)
    match_r = Rk[0] % N == rx2
    in_range = 21778071482940061661655974875633165533184 <= d_val < 43556142965880123323311949751266331066367
    print(f"  {name:35s}: d bits={d_val.bit_length():3d}, range={in_range}, r-match={match_r}")
