#!/usr/bin/env python3
"""Frozen RSZ table from https://hashkeys.space/rsz/ (puzzle spend tx).

Site notation: x = private key (pvt), m = message hash (Z), k = nonce.
ECDSA: s*k = z + r*d  (mod N)  =>  k = s^-1 * (z + r*d) mod N
"""

from __future__ import annotations

from dataclasses import dataclass

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F

# Outgoing puzzle tx: 17e4e323cfbc68d7f0071cad09364e8193eedf8fefbcbd8a21b4b65717a4b3d3
HASHKEYS_TXID = "17e4e323cfbc68d7f0071cad09364e8193eedf8fefbcbd8a21b4b65717a4b3d3"


@dataclass(frozen=True)
class PuzzleRSZ:
    puzzle_num: int
    r: int
    s: int
    z: int
    pub_compressed: str
    pvt_hex: str | None = None  # partial hex on site for some puzzles
    nonce_hex: str | None = None

    @property
    def k(self) -> int | None:
        if self.nonce_hex:
            return int(self.nonce_hex, 16)
        return None

    def verify_ecdsa(self, d: int) -> bool:
        if self.k is None:
            return False
        return (self.s * self.k) % N == (self.z + self.r * d) % N

    def recover_k_from_d(self, d: int) -> int:
        return (pow(self.s, -1, N) * (self.z + self.r * d)) % N


def _h(x: str) -> int:
    return int(x, 16)


# Source: hashkeys.space/rsz/ (2026 fetch)
PUZZLE_RSZ: dict[int, PuzzleRSZ] = {
    65: PuzzleRSZ(65, _h("5546e2ea6259151ce2bc9040efd94f8019cc08c5524ca18a77f26dcd74deb10a"), _h("3e94a32386348f863f6ec148077eb3ebddfd4c0333c5b2030187f6b8686fe98d"), _h("339207a21f02059dcc8bfc47f62c9ec289f3c3037bdc24c8fee9174280f182a2"), "0230210c23b1a047bc9bdbb13448e67deddc108946de6de639bcc75d47c0216b1b", "1A838B13505B26867", "68592d1aa72720ae7333beb3bd9d6a8e69c0567fb91720318c6289d48227c05d"),
    70: PuzzleRSZ(70, _h("36729851ae5082e0d70786af455cd47fa29162c459f73c1041f2663c783842be"), _h("39ecf6abb2c43d62bce1d9cf77d3bbabb5ccad0f87399990f6ba2a568236330c"), _h("fb3fbd8f0f59ee460024db999b97f475d9cc8cdbce21b3ee749810cd266b2c31"), "0290e6900a58d33393bc1097b5aed31f2e4e7cbd3e5466af958665bc0121248483", "349B84B6431A6C4EF1", "79577177c7a329a48d26bcf81b5db9e88b458bf8e76665f3a9ff4ab4f0cad08e"),
    75: PuzzleRSZ(75, _h("1a35a0409ba510b8055ab7767a06952783f3ec175c7f089cbad402a682b0852d"), _h("3ee9d3f06eeadc7ccae821ac4d9f16c0df1ac5e977c9d1bceac968ed9f05bcc4"), _h("f88b9f85f645b62635765fc550ae8d29ec28737bff088baa33d34719fce25447"), "03726b574f193e374686d8e12bc6e4142adeb06770e0a2856f5e4ad89f66044755", "4C5CE114686A1336E07", "123503c481722a0b4161fc681b8c786425664c102101a649d665ca788da72e7f"),
    80: PuzzleRSZ(80, _h("8317c7f43d629fbe025e8e05dbbe6946d5a490115fd2718b282b693ff5809d40"), _h("2a7c06856091c28f49f1dd3a5bf405cc6c5743eb7aa0b66c150336b48215b2d4"), _h("42b44688c7e5aa10eff0ec27922238d4f3e4cda094bb7a61bea7849caa7b39d9"), "037e1238f7b1ce757df94faa9a2eb261bf0aeb9f84dbf81212104e78931c2a19dc", "EA1A5C66DCC11B5AD180", "93c7e4ce32301e1676eeef686e851d3b84a0174f7e9f0c523df966c96a24e886"),
    85: PuzzleRSZ(85, _h("0d0272274f0778f4242d4ada44d4c9ca1959238336c4754111da12adaf71a427"), _h("766b5813b8f194a228331282914238b30fe7ca34afad27eecb01e602ae5ea4e7"), _h("4b0269284f3a12c5a0fe6fd247d116e777470de4d5762a2c6318273cc0a2e8a0"), "0329c4574a4fd8c810b7e42a4b398882b381bcd85e40c6883712912d167c83e73a", "11720C4F018D51B8CEBBA8", "18fbd62747eb6a108af69ae775878af10075590fc534036710c2cb6121a24710"),
    90: PuzzleRSZ(90, _h("089214e780b1be83aca76593293e871159eb392090135759dc110667bfd72e36"), _h("73eb3423c444d9248d682de9670a1c48343e3554bd3eda0da070a8cd3f2ff7cc"), _h("b79f283cae2b07b53adb9773dde9b93edf91a99b9fdda83ba9c7f4e50d7c5c11"), "035c38bd9ae4b10e8a250857006f3cfd98ab15a6196d9f4dfd25bc7ecc77d788d5", "2CE00BB2136A445C71E85BF", "0640c641a09b8b28b721f3c861916de8eb1fab230ad5fa33dd0e03739b4936c9"),
    95: PuzzleRSZ(95, _h("df359e57f5e14b8dccf09daf6ec634f48cfc105658e0fc1bf53926af5494498a"), _h("392816fdecd0122f306b96b68a863f338abb0e874657adf22bb685b2e38826ce"), _h("6c44185598b9fd22ac7c8bd8349f5a5894c4e02da9bbd672fd59cd67ce2cfb8f"), "02967a5905d6f3b420959a02789f96ab4c3223a2c4d2762f817b7895c5bc88a045", "527A792B183C7F64A0E8B1F4", "b3591ed9fac56c96f20f13646c6d4a4371c1c34db9126ee203d9ecb823c46930"),
    100: PuzzleRSZ(100, _h("537b3babb66402cc0cbe8b4856e0172c087bd98ddfb43e293219c8cccf6c7fdc"), _h("4fb4d9eecf4c6cd0efb567612993a085cfbeca1163633047e6dd0c4059b06d0c"), _h("1ced6233a635419d1b20077c0e114510b00c3510baf322b1a236dccca3c13c82"), "03d2063d40402f030d4cc71331468827aa41a8a09bd6fd801ba77fb64f8e67e617", "AF55FC59C335C8EC67ED24826", "1ac46997d73e24a7167fa8b9825927cb59d23528c69328ce71de3087a8c79c1f"),
    105: PuzzleRSZ(105, _h("1e8ad3749c24db4ae05de85ee2ec33277688630f97f8ce4f883fa36c6e193d3a"), _h("2f66ac26be1b44df871473a42c5e8e2cbc703465e415b064dc4854b1d8b3c99f"), _h("9c4c95b28b34558365fbcc4168debafa430c0238a27d9185d4cea23f69cddb18"), "03bcf7ce887ffca5e62c9cabbdb7ffa71dc183c52c04ff4ee5ee82e0c55c39d77b", "16F14FC2054CD87EE6396B33DF3", "0129543698812c5d61918bddd6b24712b0d757aecba20a21c7971a3b652142af"),
    110: PuzzleRSZ(110, _h("2ce84174d77df3974453ed9ea7075a94adc333068e2b82427cf3bf685a99b860"), _h("3329eb238537ec29814802e5d19f1a34a25faac8092d41b431f10bbfa05717ed"), _h("0573b73c3fe704730cee74e1878253b2cbd253650d10dcd2a418b98e8c04ae17"), "0309976ba5570966bf889196b7fdf5a0f9a1e9ab340556ec29f8bb60599616167d", "35C0D7234DF7DEB0F20CF7062444", "caf9bf64e2440011a0c52746068da91cb7f9b1e20b0a4ac0816babbb85c4bcba"),
    115: PuzzleRSZ(115, _h("988f9aeafa9acd319281e757deffeb3e52160baf1096b73bababd55deb31f3f2"), _h("10c209729f42f3b531116c5650df090cbe934bd5a4fc556d60f143227b54c69a"), _h("016cc9c96952b3460a847c7a831cc695ffe9289a41d5ded5aa9cb6ff3ab67f6b"), "0248d313b0398d4923cdca73b8cfa6532b91b96703902fc8b32fd438a3b7cd7f55", "60F4D11574F5DEEE49961D9609AC6", "9dd8dc8f8073f11e60ac3dd7a371313c847366b5dff74f46c9fac279eb3a2fea"),
    120: PuzzleRSZ(120, _h("a285a9151ac1f9c40e88a2a80b79c702336536462a9390fd00dda999da45420a"), _h("1844883eb808df18a9138ee2c13439ecf716799edcf073772f2696e4f9384f58"), _h("7e17cf7c5b7ccfaa4c7c05874e4fb4f12661662b8e33188e2e62b3739931ade5"), "02ceb6cbbcdbdf5ef7150682150f4ce2c6f4807b349827dcdbdd1f2efa885a2630", None, None),
    125: PuzzleRSZ(125, _h("1699b85f9fd4e3c6234bc0b3378a965a08ea4f76b5359998dec6123c20ff7b64"), _h("6db258553ff34e7928d877a93d219dfff683bdd6de8c54cbebafe028198285eb"), _h("5e39fb8e7f5ec05eab86c4f2618c5c96fb3c8c7ff38f37224084fffe50aaaeb0"), "0233709eb11e0d4439a729f21c2c443dedb727528229713f0065721ba8fa46f00e", None, None),
    130: PuzzleRSZ(130, _h("9fca00d29192007648f7e4b525f15a00a5180833617a604ec6701833eb26e580"), _h("1f5ff38219a72080f77534b735badbcf57f503a33e91935ee7a859387abf5483"), _h("8d9ac8a5bc9b7ab8954e985fb9ebfc82e11c009fcccafcfb90934fb01a8c57ce"), "03633cbe3ec02b9401c5effa144c5b4d22f87940259634858fc7e59b1c09937852", None, None),
    135: PuzzleRSZ(135, _h("c86bec9faea4892fd98d718bdfc770d0d11c3d6bfd4328f25fe9b06bfadb9650"), _h("224a322e81c044d341521f65fabdfa86d84673fb55ed7533862e37f7724931fa"), _h("92886faaf53f90a5c03d6af773a726e75097179306b980e5d28772e612e00fc7"), "02145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16", None, None),
    140: PuzzleRSZ(140, _h("e41046e4b1b7cff1a35f8d6b0eb3448a0403885b17dbf0a0d2ff634de6d03d68"), _h("213396378381f50c084aef327f2b14893b0250a917335bd1fe95431c9d2451a3"), _h("fc51df8026a78f2106970d089b81e2dad52d9a927edafd922f049c3efa3427ce"), "031f6a332d3c5c4f2de2378c012f429cd109ba07d69690c6c701b6bb87860d6640", None, None),
    145: PuzzleRSZ(145, _h("975bf9ee76637ce33f4539397ebb9fd2cd2cb77d79fccfefc291d8e4bd4464bb"), _h("13ca9514a84bc640b2841c09d15f4d35b5d6f2cf484e69202ca589477fea1e2f"), _h("100cd5c53eadad64b97cd46d3c7f2e8f02f5c55c4333f71585c149bd3a693eed"), "03afdda497369e219a2c1c369954a930e4d3740968e5e4352475bcffce3140dae5", None, None),
    150: PuzzleRSZ(150, _h("f9746fbc71b4907756f69b3f55625d47b60ecd909233d3b1116860ebeafec6ef"), _h("2db803a9ec7faf80dfbf78418102778cab6450b13549de1759fb88711241ac20"), _h("b02bee27647fee6492d70d7a569ad594462ea022ff08df7ded497da5ed579541"), "03137807790ea7dc6e97901c2bc87411f45ed74a5629315c4e4b03a0a102250c49", None, None),
    155: PuzzleRSZ(155, _h("f09bcda859dc5400124aebf36be6333655f1d10ef96adfe335cabbbec865cd5c"), _h("19fb464ad88a144592c5deeee49609ee255ddf3ee17a0df3adbcde69c03257c9"), _h("84fdc53f18e9feec7c7f398e653ea001e3eb9c853c7f90aa597acacd12bfebfd"), "035cd1854cae45391ca4ec428cc7e6c7d9984424b954209a8eea197b9e364c05f6", None, None),
    160: PuzzleRSZ(160, _h("59b071030ee30f7b32c6c6b5f4e89c6ebcada66ebc84c94c5f9a8adc7c4f8824"), _h("2cb230880dd2dcb03c8dbf0674c372a5b65b4583c30b45ad9eccd7c0232c425f"), _h("aa9b5f47c69338130fc9e949ef9965379d5f99652acaa660142f6d9a290d1154"), "02e0a8b039282faf6fe0fd769cfbc4b6b4cf8758ba68220eac420e32b91ddfa673", None, None),
}

# Puzzle 7 — solved early puzzle (53125.txt); no RSZ row on hashkeys (no partial spend)
P7_D = 76
P7_PX = 67990777350807742601404023085488753338978132210207570380931332031538910989091
P7_PY = 85792528080009126161701413187313528408286619337671538805045464108358228475888
P7_PUB_COMPRESSED = "0296516a8f65774275278d0d7420a88df0ac44bd64c7bae07c3fe397c5b3300b23"

EARLY_SOLVED: dict[int, int] = {
    5: 21,
    6: 49,
    7: P7_D,
    8: 224,
}


def rsz_bridge_features(puzzle_num: int) -> list[tuple[str, int]]:
    """Scalars derived from RSZ for offset-term matching."""
    rsz = PUZZLE_RSZ.get(puzzle_num)
    if rsz is None:
        return []
    out: list[tuple[str, int]] = []
    for name, val in (
        ("R", rsz.r),
        ("S", rsz.s),
        ("Z", rsz.z),
        ("R^S mod N", (rsz.r * rsz.s) % N),
        ("Z+R mod N", (rsz.z + rsz.r) % N),
        ("Z-R mod N", (rsz.z - rsz.r) % N),
    ):
        out.append((f"rsz_{puzzle_num}_{name}", val))
    if rsz.k is not None:
        out.append((f"rsz_{puzzle_num}_k", rsz.k))
        out.append((f"rsz_{puzzle_num}_k-R", (rsz.k - rsz.r) % N))
    return out


def y_roots_from_x(x: int) -> tuple[int, int]:
    y_sq = (pow(x, 3, p) + 7) % p
    y_pos = pow(y_sq, (p + 1) // 4, p)
    return y_pos, (p - y_pos) % p


def recover_r_point_from_sig(r_sig: int, *, prefer_even_y: bool = True) -> tuple[int, int] | None:
    """Recover affine R = k*G from ECDSA signature r (x-coordinate mod N)."""
    xs: list[int] = []
    for x in (r_sig % N, (r_sig % N) + N):
        if 0 < x < p and x not in xs:
            xs.append(x)
    for x in xs:
        y_sq = (pow(x, 3, p) + 7) % p
        if pow(y_sq, (p - 1) // 2, p) != 1:
            continue
        y_pos, y_neg = y_roots_from_x(x)
        if prefer_even_y:
            y = y_pos if y_pos % 2 == 0 else y_neg
        else:
            y = y_pos if y_pos % 2 == 1 else y_neg
        return x, y
    return None


def resolve_r_true_from_rsz(puzzle_num: int) -> tuple[int, int, str] | None:
    """R point from hashkeys spend signature (works without known d/k)."""
    rsz = PUZZLE_RSZ.get(puzzle_num)
    if rsz is None:
        return None
    pt = recover_r_point_from_sig(rsz.r)
    if pt is None:
        return None
    return pt[0], pt[1], f"hashkeys RSZ r -> R (puzzle {puzzle_num} spend tx)"


def apply_rsz_to_config(cfg) -> bool:
    """Attach known_k from hashkeys when the spend nonce is published."""
    rsz = PUZZLE_RSZ.get(getattr(cfg, "puzzle_num", None))
    if rsz is None or rsz.k is None:
        return False
    cfg.known_k = rsz.k
    return True


def rsz_for_puzzle(puzzle_num: int) -> PuzzleRSZ | None:
    return PUZZLE_RSZ.get(puzzle_num)
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent / "ECDLP"))
    from ecdlp_full_pipeline import P115_D, P115_K  # noqa: E402

    p115 = PUZZLE_RSZ[115]
    print("P115 ECDSA verify:", p115.verify_ecdsa(P115_D))
    print("P115 k match pipeline:", p115.k == P115_K)
    print("P115 recover k from d:", p115.recover_k_from_d(P115_D) == P115_K)
    print("Puzzle 7 d=76 (no RSZ row):", EARLY_SOLVED[7])
    print("P135 has RSZ pub:", PUZZLE_RSZ[135].pub_compressed[:20], "...")
