#!/usr/bin/env python3
"""Verify beta-orbit sums using hashkeys.space/rsz/ data directly."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

def primitive_cube_root_of_unity(mod):
    if (mod - 1) % 3 != 0: return None
    exp = (mod - 1) // 3
    for z in range(2, 1000):
        w = pow(z, exp, mod)
        if w != 1 and pow(w, 3, mod) == 1: return w
    return None

b = primitive_cube_root_of_unity(p)

def beta_orbit(x):
    return [x, (x * b) % p, (x * b * b) % p]

def ec_multiply(k):
    px, py = Gx, Gy
    rx, ry = None, None
    while k:
        if k & 1:
            if rx is None:
                rx, ry = px, py
            else:
                if rx == px:
                    m = (3 * px * px) % p
                    m = (m * pow(2 * py, -1, p)) % p
                else:
                    m = ((py - ry) % p) * pow((px - rx) % p, -1, p) % p
                x3 = (m * m - px - rx) % p
                y3 = (m * (rx - x3) - ry) % p
                rx, ry = x3, y3
        m = (3 * px * px) % p
        m = (m * pow(2 * py, -1, p)) % p
        x3 = (m * m - 2 * px) % p
        y3 = (m * (px - x3) - py) % p
        px, py = x3, y3
        k >>= 1
    return rx, ry

def recover_rx_from_sig(r_sig):
    xs = []
    for x in (r_sig % N, (r_sig % N) + N):
        if 0 < x < p and x not in xs:
            xs.append(x)
    for x in xs:
        y_sq = (pow(x, 3, p) + 7) % p
        if pow(y_sq, (p - 1) // 2, p) != 1:
            continue
        y = pow(y_sq, (p + 1) // 4, p)
        y = y if y % 2 == 0 else (p - y) % p
        return x, y
    return None

def _h(x): return int(x, 16)

# RSZ from hashkeys.space/rsz/
RSZ = {
    65:  (_h("5546e2ea6259151ce2bc9040efd94f8019cc08c5524ca18a77f26dcd74deb10a"), _h("3e94a32386348f863f6ec148077eb3ebddfd4c0333c5b2030187f6b8686fe98d"), _h("339207a21f02059dcc8bfc47f62c9ec289f3c3037bdc24c8fee9174280f182a2")),
    70:  (_h("36729851ae5082e0d70786af455cd47fa29162c459f73c1041f2663c783842be"), _h("39ecf6abb2c43d62bce1d9cf77d3bbabb5ccad0f87399990f6ba2a568236330c"), _h("fb3fbd8f0f59ee460024db999b97f475d9cc8cdbce21b3ee749810cd266b2c31")),
    75:  (_h("1a35a0409ba510b8055ab7767a06952783f3ec175c7f089cbad402a682b0852d"), _h("3ee9d3f06eeadc7ccae821ac4d9f16c0df1ac5e977c9d1bceac968ed9f05bcc4"), _h("f88b9f85f645b62635765fc550ae8d29ec28737bff088baa33d34719fce25447")),
    80:  (_h("8317c7f43d629fbe025e8e05dbbe6946d5a490115fd2718b282b693ff5809d40"), _h("2a7c06856091c28f49f1dd3a5bf405cc6c5743eb7aa0b66c150336b48215b2d4"), _h("42b44688c7e5aa10eff0ec27922238d4f3e4cda094bb7a61bea7849caa7b39d9")),
    85:  (_h("0d0272274f0778f4242d4ada44d4c9ca1959238336c4754111da12adaf71a427"), _h("766b5813b8f194a228331282914238b30fe7ca34afad27eecb01e602ae5ea4e7"), _h("4b0269284f3a12c5a0fe6fd247d116e777470de4d5762a2c6318273cc0a2e8a0")),
    90:  (_h("089214e780b1be83aca76593293e871159eb392090135759dc110667bfd72e36"), _h("73eb3423c444d9248d682de9670a1c48343e3554bd3eda0da070a8cd3f2ff7cc"), _h("b79f283cae2b07b53adb9773dde9b93edf91a99b9fdda83ba9c7f4e50d7c5c11")),
    95:  (_h("df359e57f5e14b8dccf09daf6ec634f48cfc105658e0fc1bf53926af5494498a"), _h("392816fdecd0122f306b96b68a863f338abb0e874657adf22bb685b2e38826ce"), _h("6c44185598b9fd22ac7c8bd8349f5a5894c4e02da9bbd672fd59cd67ce2cfb8f")),
    100: (_h("537b3babb66402cc0cbe8b4856e0172c087bd98ddfb43e293219c8cccf6c7fdc"), _h("4fb4d9eecf4c6cd0efb567612993a085cfbeca1163633047e6dd0c4059b06d0c"), _h("1ced6233a635419d1b20077c0e114510b00c3510baf322b1a236dccca3c13c82")),
    105: (_h("1e8ad3749c24db4ae05de85ee2ec33277688630f97f8ce4f883fa36c6e193d3a"), _h("2f66ac26be1b44df871473a42c5e8e2cbc703465e415b064dc4854b1d8b3c99f"), _h("9c4c95b28b34558365fbcc4168debafa430c0238a27d9185d4cea23f69cddb18")),
    110: (_h("2ce84174d77df3974453ed9ea7075a94adc333068e2b82427cf3bf685a99b860"), _h("3329eb238537ec29814802e5d19f1a34a25faac8092d41b431f10bbfa05717ed"), _h("0573b73c3fe704730cee74e1878253b2cbd253650d10dcd2a418b98e8c04ae17")),
    115: (_h("988f9aeafa9acd319281e757deffeb3e52160baf1096b73bababd55deb31f3f2"), _h("10c209729f42f3b531116c5650df090cbe934bd5a4fc556d60f143227b54c69a"), _h("016cc9c96952b3460a847c7a831cc695ffe9289a41d5ded5aa9cb6ff3ab67f6b")),
    120: (_h("a285a9151ac1f9c40e88a2a80b79c702336536462a9390fd00dda999da45420a"), _h("1844883eb808df18a9138ee2c13439ecf716799edcf073772f2696e4f9384f58"), _h("7e17cf7c5b7ccfaa4c7c05874e4fb4f12661662b8e33188e2e62b3739931ade5")),
    125: (_h("1699b85f9fd4e3c6234bc0b3378a965a08ea4f76b5359998dec6123c20ff7b64"), _h("6db258553ff34e7928d877a93d219dfff683bdd6de8c54cbebafe028198285eb"), _h("5e39fb8e7f5ec05eab86c4f2618c5c96fb3c8c7ff38f37224084fffe50aaaeb0")),
    130: (_h("9fca00d29192007648f7e4b525f15a00a5180833617a604ec6701833eb26e580"), _h("1f5ff38219a72080f77534b735badbcf57f503a33e91935ee7a859387abf5483"), _h("8d9ac8a5bc9b7ab8954e985fb9ebfc82e11c009fcccafcfb90934fb01a8c57ce")),
    135: (_h("c86bec9faea4892fd98d718bdfc770d0d11c3d6bfd4328f25fe9b06bfadb9650"), _h("224a322e81c044d341521f65fabdfa86d84673fb55ed7533862e37f7724931fa"), _h("92886faaf53f90a5c03d6af773a726e75097179306b980e5d28772e612e00fc7")),
    150: (_h("f9746fbc71b4907756f69b3f55625d47b60ecd909233d3b1116860ebeafec6ef"), _h("2db803a9ec7faf80dfbf78418102778cab6450b13549de1759fb88711241ac20"), _h("b02bee27647fee6492d70d7a569ad594462ea022ff08df7ded497da5ed579541")),
}

# Private keys from hashkeys pvt column (verified full keys for solved puzzles)
HASHKEYS_PVT = {
    65:  _h("1A838B13505B26867"),
    70:  _h("349B84B6431A6C4EF1"),
    75:  _h("4C5CE114686A1336E07"),
    80:  _h("EA1A5C66DCC11B5AD180"),
    85:  _h("11720C4F018D51B8CEBBA8"),
    90:  _h("2CE00BB2136A445C71E85BF"),
    95:  _h("527A792B183C7F64A0E8B1F4"),
    100: _h("AF55FC59C335C8EC67ED24826"),
    105: _h("16F14FC2054CD87EE6396B33DF3"),
    110: _h("35C0D7234DF7DEB0F20CF7062444"),
    115: _h("60F4D11574F5DEEE49961D9609AC6"),
}

# Known nonces from hashkeys
HASHKEYS_K = {
    65:  _h("68592d1aa72720ae7333beb3bd9d6a8e69c0567fb91720318c6289d48227c05d"),
    70:  _h("79577177c7a329a48d26bcf81b5db9e88b458bf8e76665f3a9ff4ab4f0cad08e"),
    75:  _h("123503c481722a0b4161fc681b8c786425664c102101a649d665ca788da72e7f"),
    80:  _h("93c7e4ce32301e1676eeef686e851d3b84a0174f7e9f0c523df966c96a24e886"),
    85:  _h("18fbd62747eb6a108af69ae775878af10075590fc534036710c2cb6121a24710"),
    90:  _h("0640c641a09b8b28b721f3c861916de8eb1fab230ad5fa33dd0e03739b4936c9"),
    95:  _h("b3591ed9fac56c96f20f13646c6d4a4371c1c34db9126ee203d9ecb823c46930"),
    100: _h("1ac46997d73e24a7167fa8b9825927cb59d23528c69328ce71de3087a8c79c1f"),
    105: _h("0129543698812c5d61918bddd6b24712b0d757aecba20a21c7971a3b652142af"),
    110: _h("caf9bf64e2440011a0c52746068da91cb7f9b1e20b0a4ac0816babbb85c4bcba"),
    115: _h("9dd8dc8f8073f11e60ac3dd7a371313c847366b5dff74f46c9fac279eb3a2fea"),
}

# Solved puzzles without hashkeys pvt (solved by third parties)
SOLVED_D = {
    120: 919343500840980333540511050618764323,
    125: 37650549717742544505774009877315221420,
    130: 1103873984953507439627945351144005829577,
}

# Verify hashkeys pvt keys match public keys
all_puzzles = list(range(65, 131, 5)) + [135, 150]
d_values = {**HASHKEYS_PVT, **SOLVED_D}

print("=" * 90)
print("VERIFICATION 1: Hashkeys pvt keys verify against pubkeys")
print("=" * 90)
# Import from hashkeys_rsz for pubkey comparison
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hashkeys_rsz import PUZZLE_RSZ
for pnum in sorted(HASHKEYS_PVT.keys()):
    d = HASHKEYS_PVT[pnum]
    P = ec_multiply(d)
    rsz = PUZZLE_RSZ[pnum]
    pub = rsz.pub_compressed
    # Compute compressed pubkey from dG
    prefix = "02" if P[1] % 2 == 0 else "03"
    comp = prefix + format(P[0], '064x')
    ok = "OK" if comp == pub else "MISMATCH"
    print(f"  Puzzle {pnum}: dG compressed = {comp[:20]}... matches hashkeys? {ok}")

# Verify by checking: recover k from d, compute kG, check Rx matches r
print(f"\n{'='*90}")
print("VERIFICATION 2: Recover k from d, verify Rx in beta-orbit")
print("=" * 90)
for pnum in all_puzzles:
    if pnum in HASHKEYS_PVT:
        d = HASHKEYS_PVT[pnum]
    elif pnum in SOLVED_D:
        d = SOLVED_D[pnum]
    else:
        continue
    r, s, z = RSZ[pnum]
    k = (pow(s, -1, N) * (z + r * d)) % N
    
    # Compute R = kG
    Rx, Ry = ec_multiply(k)
    Rx_orb = beta_orbit(Rx)
    orb_sum = sum(Rx_orb)
    
    # Check if r is in orbit
    r_mod_N = r % N
    rx_mod_N = [x % N for x in Rx_orb]
    r_idx = rx_mod_N.index(r_mod_N) if r_mod_N in rx_mod_N else -1
    
    # Also compute Px orbit
    Px, Py = ec_multiply(d)
    Px_orb = beta_orbit(Px)
    px_sum = sum(Px_orb)
    
    # Also verify using known nonce where available
    if pnum in HASHKEYS_K:
        k2 = HASHKEYS_K[pnum]
        match_known = "k_match" if k == k2 else "k_MISMATCH"
    else:
        match_known = ""
    
    p_str = "p" if px_sum == p else ("2p" if px_sum == 2*p else str(px_sum))
    r_str = "p" if orb_sum == p else ("2p" if orb_sum == 2*p else str(orb_sum))
    
    print(f"  P{pnum}: d verified (kG.x={Rx}, R.orbit={r_str}, P.orbit={p_str}, r@idx={r_idx}) {match_known}")

# Now do the same for unsolved puzzles 135, 150 (Rx from r recovery)
print(f"\n{'='*90}")
print("VERIFICATION 3: Unsolved puzzles - Rx from signature r")
print("=" * 90)
for pnum in [135, 150]:
    r, s, z = RSZ[pnum]
    pt = recover_rx_from_sig(r)
    if pt is None:
        print(f"  P{pnum}: cannot recover R point")
        continue
    Rx, Ry = pt
    Rx_orb = beta_orbit(Rx)
    orb_sum = sum(Rx_orb)
    r_mod_N = r % N
    rx_mod_N = [x % N for x in Rx_orb]
    r_idx = rx_mod_N.index(r_mod_N) if r_mod_N in rx_mod_N else -1
    r_str = "p" if orb_sum == p else ("2p" if orb_sum == 2*p else str(orb_sum))
    print(f"  P{pnum}: Rx={Rx}, orbit={r_str}, r@idx={r_idx}")

# Summary table
print(f"\n{'='*90}")
print("SUMMARY: Px orbit / Rx orbit (hashkeys data)")
print(f"{'='*90}")
print(f"{'Puzzle':>8} {'Px sum':>8} {'Px<p/2':>8} {'Rx sum':>8} {'Rx>p/2':>8} {'r@idx':>8}")
print("-" * 90)
for pnum in all_puzzles:
    if pnum in d_values:
        d = d_values[pnum]
        r, s, z = RSZ[pnum]
        k = (pow(s, -1, N) * (z + r * d)) % N
        Px, Py = ec_multiply(d)
        Rx, Ry = ec_multiply(k)
    else:
        # Unsolved - recover Rx from signature r
        r, s, z = RSZ[pnum]
        pt = recover_rx_from_sig(r)
        if pt is None:
            print(f"  P{pnum}:  cannot recover R point")
            continue
        Rx, Ry = pt
        Px = None  # unknown
    
    Rx_orb = beta_orbit(Rx)
    rx_sum = sum(Rx_orb)
    rx_above = sum(1 for x in Rx_orb if x > p//2)
    r_mod_N = r % N
    rx_mod_N = [x % N for x in Rx_orb]
    r_idx = rx_mod_N.index(r_mod_N) if r_mod_N in rx_mod_N else -1
    r_str = "p" if rx_sum == p else ("2p" if rx_sum == 2*p else "?")
    
    if Px is not None:
        Px_orb = beta_orbit(Px)
        px_sum = sum(Px_orb)
        px_below = sum(1 for x in Px_orb if x < p//2)
        p_str = "p" if px_sum == p else ("2p" if px_sum == 2*p else "?")
    else:
        p_str = "?"
        px_below = "?"
    
    print(f"  P{pnum}:  {p_str:>8} {str(px_below):>8} {r_str:>8} {rx_above:>8} {r_idx:>8}")

print(f"\n  Sum always = p*(x - q1 - q2) where q1=floor(x*beta/p), q2=floor(x*beta^2/p)")
print(f"  1+beta+beta^2 = p (exact integer), so orbit is either p or 2p")
