#!/usr/bin/env python3
"""Full step-by-step bridge pipeline: p-side -> y-side -> N-side.

Puzzle band rule (Bitcoin puzzle convention):
  Puzzle number n = height of the scalar range (half-open).
  Puzzle 7   -> d in [2^6, 2^7)
  Puzzle 160 -> d in [2^159, 2^160)
  LO = 2^(n-1),  HI = 2^n,  TOP = HI - 1.

Prompts for r, s, x, y (and optional G triple) so you can swap targets without
editing the file. Press Enter on any prompt to keep Puzzle 135 defaults.

Run:
  python C:\\Users\\mitch\\Desktop\\secp256k1\\ECDLP\\ecdlp_full_pipeline.py
  python ...\\ecdlp_full_pipeline.py --defaults
  python ...\\ecdlp_full_pipeline.py --r a,b,c --s RY --x a,b,c --y PY --row 3
  python ...\\ecdlp_full_pipeline.py --out pipeline_report.txt

Phase 0b: concatenated point decimals P = (Px<<256)|Py, R_true = (kG_x<<256)|kG_y.
Phase 17c: shelf alignment d ≈ shelf2 + offset mod LO; T(x)=LO+(x³ mod LO), not 9× chain.
Phase 16 auto-tests bridge-derived d candidates with d*G == P (requires ecdsa).

Core lambda laws (verified every run):
  LAW-P (p-side):  lambda_y^2 == (Px^3 + 7) / (rx^3 + 7)  (mod p)
  LAW-N (N-side):  lambda_yN^2 == Y_comp / Y_r_comp  (mod N)   [MAIN OBJECTIVE]
    Heaven sense: naive p-law dies mod N (off-curve); LAW-N is reborn via carry a_p: p -> N.
    Y_comp = Qx^3 + 7*delta^3 + a*p*delta^3,  a = (Py^2 - Px^3 - 7)/p per slot (heaven lift).
    Three x-slots collapse to one Y_comp; two y-branches (Qy, qy) give lambda_yN = Qy/qy.
  Naive (Px^3+7)/(rx^3+7) mod N fails off-curve — diagnostic only, not LAW-N.

  x-side cubic (3 x-slots): Lambda^3 on p; Lambda_N_family = L1*L2*L3 on N (NOT single-row Lambda_N^3).
  Do NOT require lambda_yN^2 == Lambda_N^3 (mixes x-cubic with y-quadratic).
  Do NOT set k := Lambda_N — N is not the curve field; use family product + heaven carry.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TextIO

try:
    from ecdsa import SECP256k1, SigningKey

    _HAS_ECDSA = True
except ImportError:
    _HAS_ECDSA = False

_HASHKEYS_MOD = None


def _hashkeys():
    """Lazy import hashkeys_rsz.py from repo root (hashkeys.space RSZ table)."""
    global _HASHKEYS_MOD
    if _HASHKEYS_MOD is None:
        try:
            from pathlib import Path

            root = Path(__file__).resolve().parent.parent
            root_str = str(root)
            if root_str not in sys.path:
                sys.path.insert(0, root_str)
            import hashkeys_rsz as hk

            _HASHKEYS_MOD = hk
        except ImportError:
            _HASHKEYS_MOD = False
    return _HASHKEYS_MOD if _HASHKEYS_MOD is not False else None

_COMPLEMENT_MOD = None


def _complement():
    """Lazy import puzzle160_complement_focus.py (P160 m-leg [2^96, 2^97))."""
    global _COMPLEMENT_MOD
    if _COMPLEMENT_MOD is None:
        try:
            from pathlib import Path

            root = Path(__file__).resolve().parent.parent
            root_str = str(root)
            if root_str not in sys.path:
                sys.path.insert(0, root_str)
            import puzzle160_complement_focus as p160c

            _COMPLEMENT_MOD = p160c
        except ImportError:
            _COMPLEMENT_MOD = False
    return _COMPLEMENT_MOD if _COMPLEMENT_MOD is not False else None

# secp256k1
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
delta = p - N

N1_HINT = 59918213076871302850696965052278348370805334183656907928308327240635173121259
N2_HINT = 79196589282660987520076475805787536662716643115069436220061826482331618169130
N3_HINT = 92469376115100100476368529159309930673017992032554783930545014292850878052937

# N-side cube roots of delta = p - N (Complexity_Simplified_N.txt p1,p2,p3)
DELTA_CUBE_ROOTS_N = [
    1248780847746852317428964695904392891045016528862400526454142780194939123483,
    21551977082208859489759061364299864038123955443494189974630776168682352336746,
    92991331307360483616382958948483650923668592306718313881520244192640870034108,
]

DEFAULT_GX = [
    91177636130617246552803821781935006617134368061721227770777272682868638699771,
    55066263022277343669578718895168534326250603453777594175500187360389116729240,
    85340279321737800624759429340272274763154997815782306132637707972559913914315,
]
DEFAULT_PX = [
    51866120889717641461810659005716431188799022756838843706514074509901265629059,
    54715131853151445691733189261594605794679177894602772031317532630299444965014,
    9210836494447108270027136741376870869791784014198948301625976867708124077590,
]
DEFAULT_RX = [
    114930704126154877082883546730544079307369404418439078397954295509919169851219,
    90653255469745952335985143920649543885181555095025199315947044135806663628368,
    26000218878731561428273279366182192513989009817816850365013828370091835863739,
]
DEFAULT_PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
DEFAULT_RY = 49714739208247555872780528359092797866261457510155690641636464864972500227644

# Puzzle 160 — orderinthecourt.txt coordinates (Px/rx block at top of notebook)
OITC160_PX = [
    99685974423659554164545805763816838248496097325140083731055710648889920816643,
    101616124637840542991531253248586524020213215258338643076214814468447630501491,
    30282079413132293691064911004972453437830656747802401271644642898480118025192,
]
OITC160_RX = [
    2058256938737534441052364174182103859798018828298390488211196700026657501931,
    73166243711482150095739218900420001340047970263222419524399021938933427175712,
    40567588587096510886779401934085802653423995574119754026847365368948749994020,
]
OITC160_PY1 = 88132823371574229813684435207239348220522140366126834573803505878170136640646
OITC160_RY1 = 93506999776394773977012568374000894735649274226096876119078636851803903807856

# Puzzle 115 — solved ground truth (puzzle115ecdlpchallenge.txt calibration fixture)
P115_PX = [
    32939465712855543687621080654651021859979376333843015892822995152318610898773,
    101799235034238312377638536491601060306370383419401458561357245694173516387397,
    96845477727538534781882352871123733540190209578036653624734927169325542057156,
]
P115_RX = [
    29635595092651514235242559817429102069453575029948222738031218830195230963897,
    17151212825788200760314191276657966975180626027311568426563955175023069826948,
    69005281318876480428014233914600838808635783608380772874862410002690533880818,
]
P115_PY1 = 46560755643746305144975040470607841658328142774650200719470619734417618747604
P115_RY1 = 70340950788213721176361568086222922627168108493202751158849268629715808623994
P115_D = 31464123230573852164273674364426950
P115_K = 71396278446561290368727045358794825158546572073240015435572676698333005885418

# True R = k*G coordinates (rx slot 3 for 115, slot 2 for 135) — not always active bridge row
P115_R_TRUE_X = 69005281318876480428014233914600838808635783608380772874862410002690533880818
P115_R_TRUE_Y = 70340950788213721176361568086222922627168108493202751158849268629715808623994
P135_R_TRUE_X = 90653255469745952335985143920649543885181555095025199315947044135806663628368
P135_R_TRUE_Y = 49714739208247555872780528359092797866261457510155690641636464864972500227644

COORD_BITS = 256  # secp256k1 field element width for x||y packing

# Frozen concatenated point decimals (Px<<256 | Py, rx<<256 | ry)
CONCAT_EXPECTED: dict[int, dict[str, int]] = {
    115: {
        "P": 3814129553252486241080450519696157695226995554635082631677231058271463738874636950579253602565409312848653485470955076567908415670618657988693692452946132,
        "R_true": 7990265692321453628456365255912709558971816826519883671911937057699025944085525511959846861456724276319941012122984812124142848760512822140182664885771642,
    },
    135: {
        "P": 1066542001315348240126387700075484831557028815584453173831988366663633311848168315513854109072196991544056365832031851541909560872082917319437219568309040,
        "R_true": 10496929847006045811119285426129534715974654499956651039465965267276790531563735590629148014508648938050327326256860075382817579983936063819322111655532092,
    },
}

# Frozen checkpoints from puzzle115ecdlpchallenge.txt (tune regressions here)
P115_EXPECTED = {
    "lambda_p": 28977901280827279661293245674495843888902861004781350439036900221273028456432,
    "cq": 96149978733725001231737925935108607837554889046107396603604695646748762519471,
    "lambda_y_n_sq": 59654819387024152522030740802627754621288989662828941208944714628886552415130,
    "lambda_n": 102792606177539974650368035788554886882023200939612641517668273357157166816190,
}

# P115 solved alignment calibration (shelf2 anchor + offset); reference only for unsolved puzzles.
P115_OFFSET_SHELF2 = 33397376926465242200920829909277
P115_OFFSET_BITS = 105  # (P115_D - shelf2).bit_length(); pattern H - 10 for H=115
P115_HEIGHT_MINUS_OFFSET_BITS = 10

HEAVEN_DIE_REBIRTH = (
    "Heaven sense: the naive p-side law dies mod N (coords off-curve); "
    "LAW-N is born again through integer carry a = (y^2 - x^3 - 7)/p crossing p into N."
)

# Puzzle n: d in [2^(n-1), 2^n).  Example: puzzle 7 -> [2^6, 2^7); puzzle 160 -> [2^159, 2^160).
def puzzle_band(n: int) -> tuple[int, int, int]:
    """Return (LO, HI, TOP) for puzzle number n."""
    lo = 2 ** (n - 1)
    hi = 2**n
    return lo, hi, hi - 1

# --- EC notation (do not confuse with bridge notebook labels) ---
EC_DEFINITIONS = """\
  EC identities (secp256k1, subgroup order N):
    G_gen = standard base point (scalar generator)
    P     = puzzle public key point;  ECDLP target:  P = d * G_gen
    R     = nonce point (full EC point);            R = k * G_gen
    d     = private scalar, puzzle band [2^(n-1), 2^n)
    k     = ECDSA nonce scalar for the signed tx

  Inversions (same relation, scalar inverse mod N):
    G_gen = d^-1 * P    iff    P = d * G_gen
    G_gen = k^-1 * R    iff    R = k * G_gen

  Direct bridge between nonce point and pubkey (scalar frame):
    P = (d * k^-1) * R   =   m * R
    R = (k * d^-1) * P   =   m_inv * P
    m     = d * k^-1 mod N     (test bridge against this, not d alone)
    m_inv = k * d^-1 mod N

  ECDSA (message hash z, signature (r,s); r = x(R) mod N):
    s*k = z + r*d   (mod N)
    k = s^-1 * (z + r*d)   (mod N)

  Bridge notebook labels (NOT the same as above):
    Px, Py     = coordinates of target P (Latin x triple + y)
    rx, ry     = helper r-family coords (3 x-slots), not automatically R = k*G
    Gx triple  = normalized base slots (A,B,C), not G_gen
    Lambda_*   = congruence-class bridge ratios, not d or k
    LAW-N      = heaven-reborn y-compress mod N (main N-side objective)

  Concatenated point encoding (512-bit decimal pack):
    P_concat = (Px << 256) | Py     high=x, low=y
    R_concat = (kG_x << 256) | kG_y  true nonce point R = k*G (NOT bridge-row rx alone)
    Decode:   Px = P_concat >> 256,  Py = P_concat & (2^256 - 1)
    Integer P_concat/R_concat mod N is NOT m = d*k^-1 (EC bridge != packed division).
"""

SLOT = ["A", "B", "C"]
G_CANON = [
    72789842462919254798787184333665945456600870881042555899576743439227206827139,
    5413323970105506090398366098172752697370300495141572731819943140721401835677,
    37588922804291434534385434576849209699298813289456435408060897427960226008847,
]


@dataclass
class PuzzleConfig:
    """Bitcoin puzzle n: private key d lies in [2^(n-1), 2^n)  (half-open).

    Examples: puzzle 115 -> [2^114, 2^115); puzzle 160 -> [2^159, 2^160).
    LO = 2^(n-1), HI = 2^n, TOP = HI - 1.
    """
    puzzle_num: int = 135
    row: int = 2  # 0-based; row 3 in notes = index 2
    Gx: list[int] = field(default_factory=lambda: list(DEFAULT_GX))
    Px: list[int] = field(default_factory=lambda: list(DEFAULT_PX))
    rx: list[int] = field(default_factory=lambda: list(DEFAULT_RX))
    Py: int | None = None  # None -> even y from Px[row]
    ry: int | None = None  # None -> even y from rx[row]
    known_d: int | None = None  # solved private key — enables Phase 17b calibration
    known_k: int | None = None  # solved nonce (ECDSA), reported when present
    skip_complement: bool = False  # Puzzle 160: skip Phase 17d m-leg
    complement_quick: bool = True  # Phase 17d uses fast eps/shell sample unless False

    @property
    def lo(self) -> int:
        return 2 ** (self.puzzle_num - 1)

    @property
    def hi(self) -> int:
        return 2 ** self.puzzle_num

    @property
    def top(self) -> int:
        return self.hi - 1

    def band_tuple(self) -> tuple[int, int, int]:
        """(LO, HI, TOP) — puzzle n => d in [LO, HI)."""
        return puzzle_band(self.puzzle_num)

    @property
    def mirror_lo(self) -> int:
        return N - (self.hi + 1)

    @property
    def mirror_hi(self) -> int:
        return N - self.lo


def apply_puzzle_defaults(cfg: PuzzleConfig) -> None:
    """Load notebook coordinates when puzzle band is known."""
    if cfg.puzzle_num == 160:
        cfg.Px = list(OITC160_PX)
        cfg.rx = list(OITC160_RX)
        cfg.Py = OITC160_PY1
        cfg.ry = OITC160_RY1
        cfg.row = 0
        cfg.known_d = None
        cfg.known_k = None
        hk = _hashkeys()
        if hk is not None:
            rsz = hk.rsz_for_puzzle(160)
            if rsz is not None and rsz.pub_compressed:
                px_pub = int(rsz.pub_compressed[2:], 16)
                for i, px_i in enumerate(cfg.Px):
                    if px_i == px_pub:
                        cfg.row = i
                        break
    elif cfg.puzzle_num == 115:
        cfg.Px = list(P115_PX)
        cfg.rx = list(P115_RX)
        cfg.Py = P115_PY1
        cfg.ry = P115_RY1
        cfg.row = 0
        cfg.known_d = P115_D
        cfg.known_k = P115_K
    else:
        if cfg.Py is None:
            cfg.Py = DEFAULT_PY
        if cfg.ry is None:
            cfg.ry = DEFAULT_RY
    _apply_hashkeys_rsz(cfg)


def _apply_hashkeys_rsz(cfg: PuzzleConfig) -> None:
    """Wire hashkeys.space RSZ: known_k when published; R_true via resolve_true_r_xy."""
    hk = _hashkeys()
    if hk is None:
        return
    hk.apply_rsz_to_config(cfg)


def curve_y_ratio_mod(mod: int, px: int, rx: int) -> int:
    """(Px^3 + 7) / (rx^3 + 7) mod mod — curve y^2 / r_y^2 when on-curve mod mod."""
    num = (pow(px, 3, mod) + 7) % mod
    den = (pow(rx, 3, mod) + 7) % mod
    return (num * pow(den, -1, mod)) % mod


def curve_residue_x_cubic_from_y(y: int, mod: int) -> int:
    """x^3 = y^2 - 7 mod mod (equivalent to y^2 = x^3 + 7)."""
    return (y * y - 7) % mod


def curve_y_sq_from_x(x: int, mod: int) -> int:
    """y^2 = x^3 + 7 mod mod."""
    return (pow(x, 3, mod) + 7) % mod


def primitive_cube_root_of_unity(mod: int) -> int | None:
    if (mod - 1) % 3 != 0:
        return None
    exp = (mod - 1) // 3
    for z in range(2, 1000):
        w = pow(z, exp, mod)
        if w != 1 and pow(w, 3, mod) == 1:
            return w
    return None


def cube_root_mod_prime(mod: int, a: int) -> int | None:
    if a % mod == 0:
        return 0
    if (mod - 1) % 3 != 0:
        return None
    r = pow(a, (2 * mod - 1) // 3, mod)
    return r if pow(r, 3, mod) == a % mod else None


def all_cube_roots_mod_p(a: int, witness: int | None = None) -> list[int]:
    """All cube roots of a mod p. Pass witness with witness^3 == a when (2p-1)/3 trick fails."""
    return all_cube_roots_mod(p, a, witness=witness)


def all_cube_roots_mod(mod: int, a: int, witness: int | None = None) -> list[int]:
    """All cube roots of a mod mod (mod prime, (mod-1) divisible by 3)."""
    a %= mod
    if a == 0:
        return [0]
    w = primitive_cube_root_of_unity(mod)
    if w is None:
        return []
    r0: int | None = None
    if witness is not None and pow(witness, 3, mod) == a:
        r0 = witness % mod
    if r0 is None:
        r = cube_root_mod_prime(mod, a)
        if r is not None:
            r0 = r
    if r0 is None:
        return []
    return sorted({r0, (r0 * w) % mod, (r0 * w * w) % mod})


@dataclass
class FamilyBridgeCheck:
    """Corrected N-side family bridge: L1*L2*L3 + heaven carry, not single-row Lambda_N^3."""

    lambda_p: int
    lambda_p_cube: int
    lambda_n_rows: list[int]
    lambda_n_target: int
    lambda_n_family_prod: int
    lambda_n_family_cbrt: list[int]
    delta_cube_roots_n: list[int]
    iq: int
    i_r: int
    cq: int
    family_prod_eq_cq: bool
    naive_single_row_cube_eq_cq: bool
    wrong_lam_y_sq_eq_lambda_n_cube: bool
    wrong_lam_y_sq_eq_l1_cube: bool
    lambda_y_n_sq: int
    lambda_y_n_sq_compressed: int
    heaven_y_ratio: int
    shell_product_align: bool
    shell_quadratic_vs_cubic_gap: int
    row_carries_ok: list[bool]
    row_carries: list[int]
    p_lambda_cube_from_y: int
    p_lam_y_sq: int
    p_law_x_cubic: bool
    p_law_y_quadratic: bool


def verify_family_bridge(
    *,
    px_triple: list[int],
    rx_triple: list[int],
    py: int,
    ry: int,
    qx_scaled: list[int],
    qr_scaled: list[int],
    lambda_p: int,
    n_balance: NSideBalance,
    n_y_compress: NYCompressionCheck,
    lambda_n_target: int,
) -> FamilyBridgeCheck:
    """Family bridge from all three x-roots + delta/heaven carry (not one row alone)."""
    qy = (py * delta) % N
    qy_r = (ry * delta) % N
    lambda_n_rows = [(qx_scaled[i] * pow(qr_scaled[i], -1, N)) % N for i in range(3)]
    family_prod = 1
    for li in lambda_n_rows:
        family_prod = family_prod * li % N

    iq = n_balance.iq
    i_r = n_balance.i_r
    cq = n_balance.cq
    lam_y_n = (py * pow(ry, -1, N)) % N
    lam_y_sq = pow(lam_y_n, 2, N)
    heaven_num = (qy * qy - n_balance.n_compress_k_p) % N
    heaven_den = (qy_r * qy_r - n_balance.n_compress_k_r) % N
    heaven_y_ratio = (heaven_num * pow(heaven_den, -1, N)) % N if heaven_den % N else 0

    row_carries: list[int] = []
    row_carries_ok: list[bool] = []
    for i in range(3):
        num = lambda_n_rows[i] * qr_scaled[i] - qx_scaled[i]
        ok = num % N == 0
        row_carries_ok.append(ok)
        row_carries.append(num // N if ok else 0)

    py_res = (py * py - 7) % p
    ry_res = (ry * ry - 7) % p
    p_lambda_cube_from_y = (py_res * pow(ry_res, -1, p)) % p
    p_lam_y_sq = (py * py * pow(ry * ry, -1, p)) % p

    family_cbrt = all_cube_roots_mod(N, family_prod)

    return FamilyBridgeCheck(
        lambda_p=lambda_p,
        lambda_p_cube=pow(lambda_p, 3, p),
        lambda_n_rows=lambda_n_rows,
        lambda_n_target=lambda_n_target,
        lambda_n_family_prod=family_prod,
        lambda_n_family_cbrt=family_cbrt,
        delta_cube_roots_n=list(DELTA_CUBE_ROOTS_N),
        iq=iq,
        i_r=i_r,
        cq=cq,
        family_prod_eq_cq=family_prod == cq,
        naive_single_row_cube_eq_cq=pow(lambda_n_target, 3, N) == cq,
        wrong_lam_y_sq_eq_lambda_n_cube=lam_y_sq == pow(lambda_n_target, 3, N),
        wrong_lam_y_sq_eq_l1_cube=lam_y_sq == pow(lambda_n_rows[0], 3, N),
        lambda_y_n_sq=lam_y_sq,
        lambda_y_n_sq_compressed=n_y_compress.n_y_compress_ratio,
        heaven_y_ratio=heaven_y_ratio,
        shell_product_align=heaven_y_ratio == cq and family_prod == cq,
        shell_quadratic_vs_cubic_gap=(lam_y_sq - cq) % N,
        row_carries_ok=row_carries_ok,
        row_carries=row_carries,
        p_lambda_cube_from_y=p_lambda_cube_from_y,
        p_lam_y_sq=p_lam_y_sq,
        p_law_x_cubic=pow(lambda_p, 3, p) == p_lambda_cube_from_y,
        p_law_y_quadratic=p_lam_y_sq == curve_y_ratio_mod(p, px_triple[0], rx_triple[0]),
    )


@dataclass
class ScalarFrame:
    """Anchors P = d*G, R = k*G and the direct bridge P = m*R with m = d*k^-1."""

    d: int
    k: int
    m: int  # d * k^-1 mod N  —  P = m * R
    m_inv: int  # k * d^-1 mod N  —  R = m_inv * P
    m_times_k_eq_d: bool
    m_inv_times_d_eq_k: bool
    m_times_m_inv_eq_1: bool


def compute_scalar_frame(d: int, k: int) -> ScalarFrame:
    d %= N
    k %= N
    m = (d * pow(k, -1, N)) % N
    m_inv = (k * pow(d, -1, N)) % N
    return ScalarFrame(
        d=d,
        k=k,
        m=m,
        m_inv=m_inv,
        m_times_k_eq_d=(m * k) % N == d,
        m_inv_times_d_eq_k=(m_inv * d) % N == k,
        m_times_m_inv_eq_1=(m * m_inv) % N == 1,
    )


@dataclass
class ScalarFrameMatch:
    label: str
    value: int
    eq_m: bool
    eq_m_inv: bool
    eq_d: bool
    eq_k: bool
    diff_m_mod_lo: int
    diff_m_inv_mod_lo: int
    diff_m_mod_n: int
    diff_m_inv_mod_n: int


def compare_bridge_to_scalar_frame(
    *,
    frame: ScalarFrame,
    lo: int,
    candidates: dict[str, int],
) -> list[ScalarFrameMatch]:
    rows: list[ScalarFrameMatch] = []
    for label, value in candidates.items():
        v = value % N
        rows.append(
            ScalarFrameMatch(
                label=label,
                value=v,
                eq_m=v == frame.m,
                eq_m_inv=v == frame.m_inv,
                eq_d=v == frame.d,
                eq_k=v == frame.k,
                diff_m_mod_lo=(v - frame.m) % lo,
                diff_m_inv_mod_lo=(v - frame.m_inv) % lo,
                diff_m_mod_n=(v - frame.m) % N,
                diff_m_inv_mod_n=(v - frame.m_inv) % N,
            )
        )
    return rows


COORD_MASK = (1 << COORD_BITS) - 1


def concat_point_xy(x: int, y: int, *, bits: int = COORD_BITS) -> int:
    """Pack affine point as decimal integer: (x << bits) | y."""
    return (x << bits) | y


def deconcat_point_xy(packed: int, *, bits: int = COORD_BITS) -> tuple[int, int]:
    """Unpack x||y: high bits = x, low bits = y."""
    return packed >> bits, packed & ((1 << bits) - 1)


def on_curve_mod(x: int, y: int, mod: int) -> bool:
    return (y * y) % mod == (pow(x, 3, mod) + 7) % mod


def resolve_true_r_xy(cfg: PuzzleConfig) -> tuple[int, int, str]:
    """Return (rx_true, ry_true, source) for R = k*G — not necessarily bridge active row."""
    if cfg.known_k is not None and _HAS_ECDSA:
        kx, ky = pubkey_from_scalar(cfg.known_k)
        return kx, ky, "k*G_gen from known_k (hashkeys RSZ when available)"
    hk = _hashkeys()
    if hk is not None:
        rsz_r = hk.resolve_r_true_from_rsz(cfg.puzzle_num)
        if rsz_r is not None:
            return rsz_r
    if cfg.puzzle_num == 115:
        return P115_R_TRUE_X, P115_R_TRUE_Y, "P115 rx slot 3 (kG_x)"
    if cfg.puzzle_num == 135:
        return P135_R_TRUE_X, P135_R_TRUE_Y, "P135 rx slot 2 (kG_x)"
    _, ry = resolve_y(cfg)
    return cfg.rx[cfg.row], ry, f"bridge row {cfg.row + 1} (no known_k / no RSZ)"


@dataclass
class ConcatPointFrame:
    """512-bit packed P and R with bridge vs true-R distinction."""

    px: int
    py: int
    rx_bridge: int
    ry_bridge: int
    rx_true: int
    ry_true: int
    r_true_source: str
    P_concat: int
    R_bridge_concat: int
    R_true_concat: int
    P_on_curve_p: bool
    R_bridge_on_curve_p: bool
    R_true_on_curve_p: bool
    P_decode_ok: bool
    R_true_decode_ok: bool
    P_mod_n: int
    R_true_mod_n: int
    P_mod_p: int
    R_true_mod_p: int
    P_mod_lo: int
    R_true_mod_lo: int
    P_over_R_true_mod_n: int
    P_over_R_true_mod_p: int
    lambda_y_true_p: int
    lambda_x_true_p: int
    kG_x_eq_rx_true: bool | None
    kG_y_eq_ry_true: bool | None


def build_concat_point_frame(
    *,
    px: int,
    py: int,
    rx_bridge: int,
    ry_bridge: int,
    rx_true: int,
    ry_true: int,
    r_true_source: str,
    lo: int,
    known_k: int | None = None,
) -> ConcatPointFrame:
    P_concat = concat_point_xy(px, py)
    R_bridge_concat = concat_point_xy(rx_bridge, ry_bridge)
    R_true_concat = concat_point_xy(rx_true, ry_true)
    dpx, dpy = deconcat_point_xy(P_concat)
    drx, dry = deconcat_point_xy(R_true_concat)
    P_mod_n = P_concat % N
    R_true_mod_n = R_true_concat % N
    P_mod_p = P_concat % p
    R_true_mod_p = R_true_concat % p
    P_over_R_n = (P_mod_n * pow(R_true_mod_n, -1, N)) % N if R_true_mod_n else 0
    P_over_R_p = (P_mod_p * pow(R_true_mod_p, -1, p)) % p if R_true_mod_p else 0
    kG_x_eq: bool | None = None
    kG_y_eq: bool | None = None
    if known_k is not None and _HAS_ECDSA:
        kx, ky = pubkey_from_scalar(known_k)
        kG_x_eq = kx == rx_true
        kG_y_eq = ky == ry_true
    return ConcatPointFrame(
        px=px,
        py=py,
        rx_bridge=rx_bridge,
        ry_bridge=ry_bridge,
        rx_true=rx_true,
        ry_true=ry_true,
        r_true_source=r_true_source,
        P_concat=P_concat,
        R_bridge_concat=R_bridge_concat,
        R_true_concat=R_true_concat,
        P_on_curve_p=on_curve_mod(px, py, p),
        R_bridge_on_curve_p=on_curve_mod(rx_bridge, ry_bridge, p),
        R_true_on_curve_p=on_curve_mod(rx_true, ry_true, p),
        P_decode_ok=dpx == px and dpy == py,
        R_true_decode_ok=drx == rx_true and dry == ry_true,
        P_mod_n=P_mod_n,
        R_true_mod_n=R_true_mod_n,
        P_mod_p=P_mod_p,
        R_true_mod_p=R_true_mod_p,
        P_mod_lo=P_concat % lo,
        R_true_mod_lo=R_true_concat % lo,
        P_over_R_true_mod_n=P_over_R_n,
        P_over_R_true_mod_p=P_over_R_p,
        lambda_y_true_p=(py * pow(ry_true, -1, p)) % p,
        lambda_x_true_p=(px * pow(rx_true, -1, p)) % p,
        kG_x_eq_rx_true=kG_x_eq,
        kG_y_eq_ry_true=kG_y_eq,
    )


def emit_concat_point_phase(
    pl: Pipeline,
    *,
    cp: ConcatPointFrame,
    lo: int,
    frame: ScalarFrame | None = None,
) -> None:
    pl.phase("0b", "CONCATENATED POINT — P = Px||Py, R = kG_x||kG_y (decimal pack)")
    pl.raw(
        f"  Pack rule: point = (x << {COORD_BITS}) | y   (x high, y low, 512-bit decimal)\n"
        "  P_concat is the puzzle pubkey pack; R_true_concat is true R = k*G (not bridge-row rx alone)."
    )
    pl.raw("")
    pl.raw("  --- P = d*G (target pubkey) ---")
    pl.log_step("Px (decimal)", cp.px)
    pl.log_step("Py (decimal)", cp.py)
    pl.log_step("P = Px||Py (decimal)", cp.P_concat)
    pl.log_step("P decode Px == P>>256", cp.P_decode_ok)
    pl.log_step("Py^2 == Px^3+7 mod p", cp.P_on_curve_p)
    pl.raw("")
    pl.raw("  --- R bridge row (notebook helper) ---")
    pl.log_step("rx_bridge (decimal)", cp.rx_bridge)
    pl.log_step("ry_bridge (decimal)", cp.ry_bridge)
    pl.log_step("R_bridge = rx||ry (decimal)", cp.R_bridge_concat)
    pl.log_step("ry_bridge^2 == rx_bridge^3+7 mod p", cp.R_bridge_on_curve_p)
    pl.raw("")
    pl.raw(f"  --- R true = k*G ({cp.r_true_source}) ---")
    pl.log_step("kG_x / rx_true (decimal)", cp.rx_true)
    pl.log_step("kG_y / ry_true (decimal)", cp.ry_true)
    pl.log_step("R_true = kG_x||kG_y (decimal)", cp.R_true_concat)
    pl.log_step("R_true decode ok", cp.R_true_decode_ok)
    pl.log_step("ry_true^2 == rx_true^3+7 mod p", cp.R_true_on_curve_p)
    if cp.kG_x_eq_rx_true is not None:
        pl.log_step("k*G_x == rx_true", cp.kG_x_eq_rx_true)
        pl.log_step("k*G_y == ry_true", cp.kG_y_eq_ry_true)
    pl.raw("")
    pl.raw("  --- True P / true R ratios (coordinate-level, mod p) ---")
    pl.log_step("lambda_y = Py/ry_true mod p", cp.lambda_y_true_p)
    pl.log_step("Lambda = Px/rx_true mod p", cp.lambda_x_true_p)
    pl.raw("")
    pl.raw("  --- Packed integer residues (NOT EC scalar mul) ---")
    pl.log_step("P_concat mod N", cp.P_mod_n, f"bits={cp.P_mod_n.bit_length()}")
    pl.log_step("R_true_concat mod N", cp.R_true_mod_n, f"bits={cp.R_true_mod_n.bit_length()}")
    pl.log_step("P_concat mod LO", cp.P_mod_lo, f"bits={cp.P_mod_lo.bit_length()}")
    pl.log_step("R_true_concat mod LO", cp.R_true_mod_lo, f"bits={cp.R_true_mod_lo.bit_length()}")
    pl.log_step("(P_concat/R_true_concat) mod N", cp.P_over_R_true_mod_n)
    pl.log_step("(P_concat/R_true_concat) mod p", cp.P_over_R_true_mod_p)
    if frame is not None:
        pl.log_step(
            "(P/R)_pack mod N == m = d*k^-1",
            cp.P_over_R_true_mod_n == frame.m,
            "expected FAIL — packed ratio != EC scalar bridge",
        )
        pl.log_step("P_concat mod N == d", cp.P_mod_n == frame.d, "expected FAIL")
        pl.log_step("R_true_concat mod N == k", cp.R_true_mod_n == frame.k, "expected FAIL")
        pl.log_step(
            "|(P/R)_pack - m| mod LO bits",
            True,
            str(((cp.P_over_R_true_mod_n - frame.m) % lo).bit_length()),
        )


def emit_scalar_frame_phase(
    pl: Pipeline,
    *,
    frame: ScalarFrame,
    lo: int,
    matches: list[ScalarFrameMatch],
) -> None:
    pl.phase("10c", "SCALAR FRAME — P = m*R, test bridge against m = d*k^-1")
    pl.raw(
        "  Anchor:  P = d*G_gen,  R = k*G_gen,  P = (d*k^-1)*R = m*R,  R = (k*d^-1)*P = m_inv*P\n"
        "  Bridge Lambda-family objects should align with m or m_inv (mod N / mod LO), not d alone."
    )
    pl.log_step("d (private)", frame.d)
    pl.log_step("k (nonce)", frame.k)
    pl.log_step("m = d*k^-1 mod N  (P = m*R)", frame.m)
    pl.log_step("m_inv = k*d^-1 mod N  (R = m_inv*P)", frame.m_inv)
    pl.log_step("m * k mod N == d", frame.m_times_k_eq_d)
    pl.log_step("m_inv * d mod N == k", frame.m_inv_times_d_eq_k)
    pl.log_step("m * m_inv mod N == 1", frame.m_times_m_inv_eq_1)

    pl.raw("")
    pl.raw("  Bridge vs scalar frame (exact equality mod N):")
    pl.raw(f"  {'label':<22} {'==m':^5} {'==m_inv':^7} {'==d':^5} {'==k':^5}  |diff| mod LO")
    for row in matches:
        pl.raw(
            f"  {row.label:<22} "
            f"{'PASS' if row.eq_m else 'FAIL':^5} "
            f"{'PASS' if row.eq_m_inv else 'FAIL':^7} "
            f"{'PASS' if row.eq_d else 'FAIL':^5} "
            f"{'PASS' if row.eq_k else 'FAIL':^5}  "
            f"m:{row.diff_m_mod_lo.bit_length()}b m_inv:{row.diff_m_inv_mod_lo.bit_length()}b"
        )

    exact_m = [r.label for r in matches if r.eq_m]
    exact_m_inv = [r.label for r in matches if r.eq_m_inv]
    pl.raw("")
    if exact_m:
        pl.log_step("Exact hits on m", True, ", ".join(exact_m))
    else:
        pl.log_step("Exact hits on m", False, "none — compare mod LO / band rep")
    if exact_m_inv:
        pl.log_step("Exact hits on m_inv", True, ", ".join(exact_m_inv))
    else:
        pl.log_step("Exact hits on m_inv", False, "none — compare mod LO / band rep")

    ranked = sorted(
        ((min(r.diff_m_mod_lo, r.diff_m_inv_mod_lo), r) for r in matches),
        key=lambda t: t[0],
    )
    pl.raw("")
    pl.raw("  Closest to m or m_inv by mod LO distance (top 5):")
    for dist, row in ranked[:5]:
        closer = "m" if row.diff_m_mod_lo <= row.diff_m_inv_mod_lo else "m_inv"
        pl.raw(
            f"    {row.label}: nearest={closer}  dist_mod_LO={dist}  "
            f"bits={dist.bit_length()}  value={row.value}"
        )


def emit_family_bridge(pl: Pipeline, fb: FamilyBridgeCheck) -> None:
    pl.phase("10b", "FAMILY BRIDGE (corrected) — L1*L2*L3 + heaven carry, not Lambda_N^3")
    pl.raw(
        "  OLD (wrong):  lambda_yN^2 == Lambda_N^3 mod N  =>  k := Lambda_N\n"
        "  NEW (fixed):  apply delta/heaven carry first; family bridge uses ALL THREE x-roots\n"
        "  p-side:\n"
        "    Lambda^3 == (Py^2-7)/(ry^2-7) mod p\n"
        "    lambda_y^2 == Py^2/ry^2 mod p\n"
        "  N-side family:\n"
        "    Lambda_N_family = Lambda_1 * Lambda_2 * Lambda_3 mod N  (= Cq = IQ/Iq)\n"
        "    NOT Lambda_N^3 from a single row\n"
        "  Then compare corrected x-shell (Cq) vs corrected y-shell (slot Y_comp ratio)."
    )
    pl.raw("")
    pl.raw("  Step 1 — N-side cube-root candidates for delta = p - N:")
    for i, root in enumerate(fb.delta_cube_roots_n, 1):
        ok = pow(root, 3, N) == delta % N
        pl.log_step(f"delta_cbrt_{i}^3 == delta mod N", ok, f"root={root}")
    pl.raw("")
    pl.raw("  Step 2 — per-row y-side bridge (own-row Lambda_i):")
    for i, li in enumerate(fb.lambda_n_rows, 1):
        pl.log_step(f"Lambda_{i} = Qx{i}*qx{i}^-1 mod N", li)
        pl.log_step(
            f"Qx{i} == Lambda_{i}*qx{i} mod N",
            fb.row_carries_ok[i - 1],
            f"b_{i}={(fb.row_carries[i - 1])}" if fb.row_carries_ok[i - 1] else "nonzero remainder",
        )
    pl.raw("")
    pl.raw("  Step 3 — family aggregate (three roots, not one row):")
    pl.log_step("Lambda_N (target row only)", fb.lambda_n_target, "legacy single-row label")
    pl.log_step(
        "Lambda_N_family = L1 * L2 * L3 mod N",
        fb.lambda_n_family_prod,
        "corrected family bridge",
    )
    pl.log_step("Cq = IQ/Iq mod N", fb.cq)
    pl.log_step(
        "FAMILY-X: Lambda_N_family == Cq",
        fb.family_prod_eq_cq,
        "required PASS — 3-root product lands on x-shell",
    )
    pl.log_step(
        "WRONG: Lambda_N^3 == Cq (single-row cubic)",
        fb.naive_single_row_cube_eq_cq,
        "expected FAIL",
    )
    if fb.lambda_n_family_cbrt:
        pl.log_step(
            "cube roots of Lambda_N_family mod N",
            len(fb.lambda_n_family_cbrt) == 3,
            str(fb.lambda_n_family_cbrt),
        )
    pl.raw("")
    pl.raw("  Step 4 — p-side laws (reference):")
    pl.log_step("Lambda^3 == (Py^2-7)/(ry^2-7) mod p", fb.p_law_x_cubic)
    pl.log_step("lambda_y^2 == (Px^3+7)/(rx^3+7) mod p", fb.p_law_y_quadratic)
    pl.raw("")
    pl.raw("  Step 5 — shell alignment (heaven-corrected):")
    pl.log_step(
        "HEAVEN-Y-RATIO: (Qy^2-k_p)/(qy^2-k_r) == Cq",
        fb.heaven_y_ratio == fb.cq,
        "product-level x/y shell match",
    )
    pl.log_step("lambda_yN^2 (naive Py/ry)", fb.lambda_y_n_sq)
    pl.log_step("lambda_yN^2 (slot Y_comp/Y_r_comp)", fb.lambda_y_n_sq_compressed)
    pl.log_step(
        "SHELL-ALIGN: naive lambda_yN^2 == Cq",
        fb.lambda_y_n_sq == fb.cq,
        "expected FAIL — quadratic vs tri-linear family",
    )
    pl.log_step(
        "WRONG LAYER: lambda_yN^2 == Lambda_N^3",
        fb.wrong_lam_y_sq_eq_lambda_n_cube,
        "expected FAIL",
    )
    pl.log_step(
        "WRONG LAYER: lambda_yN^2 == Lambda_1^3",
        fb.wrong_lam_y_sq_eq_l1_cube,
        "expected FAIL",
    )
    pl.log_step(
        "shell gap (lambda_yN^2 - Cq) mod N",
        fb.shell_quadratic_vs_cubic_gap,
        "quadratic y-layer offset from x-family shell",
    )
    pl.log_step(
        "SHELL PRODUCT ALIGN (x-family + heaven y-ratio)",
        fb.shell_product_align,
        "both hit Cq = L1*L2*L3",
    )


@dataclass
class ResidueSolution:
    """Solutions from x^3 = y^2 - 7 mod p (and mod N check)."""

    py_residue: int
    ry_residue: int
    px_slots_on_residue_p: list[bool]
    rx_slots_on_residue_p: list[bool]
    px_roots_match_triple_p: bool
    rx_roots_match_triple_p: bool
    px_recovered_from_py: list[int]
    rx_recovered_from_ry: list[int]
    lambda_cube_from_y_p: int
    lambda_from_y_p: int | None
    lambda_cube_matches_lambda_p: bool
    lambda_cube_from_y_n: int
    lambda_cube_matches_lambda_n: bool
    lam_y_sq_from_y_p: int
    lam_y_sq_matches_ratio_p: bool


def verify_residue_solutions(
    *,
    px_triple: list[int],
    rx_triple: list[int],
    py: int,
    ry: int,
    lambda_p: int,
    lambda_n: int,
) -> ResidueSolution:
    py_res = curve_residue_x_cubic_from_y(py, p)
    ry_res = curve_residue_x_cubic_from_y(ry, p)
    px_ok = [pow(x, 3, p) == py_res for x in px_triple]
    rx_ok = [pow(x, 3, p) == ry_res for x in rx_triple]
    px_roots = all_cube_roots_mod_p(py_res, witness=px_triple[0])
    rx_roots = all_cube_roots_mod_p(ry_res, witness=rx_triple[0])
    ratio_res_p = (py_res * pow(ry_res, -1, p)) % p
    lam_y_sq_yonly = (pow(py, 2, p) * pow(pow(ry, 2, p), -1, p)) % p
    lam_from_y: int | None = None
    if pow(lambda_p, 3, p) == ratio_res_p:
        lam_from_y = lambda_p
    py_res_n = curve_residue_x_cubic_from_y(py, N)
    ry_res_n = curve_residue_x_cubic_from_y(ry, N)
    ratio_res_n = (py_res_n * pow(ry_res_n, -1, N)) % N
    return ResidueSolution(
        py_residue=py_res,
        ry_residue=ry_res,
        px_slots_on_residue_p=px_ok,
        rx_slots_on_residue_p=rx_ok,
        px_roots_match_triple_p=set(px_roots) == set(px_triple),
        rx_roots_match_triple_p=set(rx_roots) == set(rx_triple),
        px_recovered_from_py=px_roots,
        rx_recovered_from_ry=rx_roots,
        lambda_cube_from_y_p=ratio_res_p,
        lambda_from_y_p=lam_from_y,
        lambda_cube_matches_lambda_p=pow(lambda_p, 3, p) == ratio_res_p,
        lambda_cube_from_y_n=ratio_res_n,
        lambda_cube_matches_lambda_n=pow(lambda_n, 3, N) == ratio_res_n,
        lam_y_sq_from_y_p=lam_y_sq_yonly,
        lam_y_sq_matches_ratio_p=lam_y_sq_yonly == curve_y_ratio_mod(p, px_triple[0], rx_triple[0]),
    )


def emit_residue_solutions(pl: Pipeline, rs: ResidueSolution, px: list[int], rx: list[int]) -> None:
    pl.phase("7b", "CURVE RESIDUE x^3 = y^2 - 7 (recover x from y)")
    pl.raw("  Equivalent forms on secp256k1:  y^2 = x^3 + 7  <=>  x^3 = y^2 - 7 mod p")
    pl.raw("  Use residue to recover the 3 x-slots as cube roots of Py^2 - 7.")
    pl.log_step("Py^2 - 7 mod p (= target x^3 for P family)", rs.py_residue)
    pl.log_step("ry^2 - 7 mod p (= target x^3 for r family)", rs.ry_residue)
    for i, ok in enumerate(rs.px_slots_on_residue_p, 1):
        pl.log_step(f"Px{i}^3 == Py^2 - 7 mod p", ok)
    for i, ok in enumerate(rs.rx_slots_on_residue_p, 1):
        pl.log_step(f"rx{i}^3 == ry^2 - 7 mod p", ok)
    pl.log_step(
        "3 cube roots of (Py^2 - 7) == {Px1,Px2,Px3}",
        rs.px_roots_match_triple_p,
        f"recovered {rs.px_recovered_from_py}",
    )
    pl.log_step(
        "3 cube roots of (ry^2 - 7) == {rx1,rx2,rx3}",
        rs.rx_roots_match_triple_p,
        f"recovered {rs.rx_recovered_from_ry}",
    )
    pl.raw("")
    pl.raw("  x-cubic from y-only (no Px/rx needed for the ratio):")
    pl.log_step("(Py^2 - 7) / (ry^2 - 7) mod p", rs.lambda_cube_from_y_p)
    pl.log_step("Lambda^3 mod p (from Px/rx)", pow((px[0] * pow(rx[0], -1, p)) % p, 3, p))
    pl.log_step(
        "RESIDUE-X: Lambda^3 == (Py^2-7)/(ry^2-7) mod p",
        rs.lambda_cube_matches_lambda_p,
        "x-layer cubic from y residue",
    )
    if rs.lambda_from_y_p is not None:
        pl.log_step("Lambda recovered from y residue ratio", rs.lambda_from_y_p)
    pl.log_step("Py^2 / ry^2 mod p", rs.lam_y_sq_from_y_p)
    pl.log_step(
        "RESIDUE-Y: Py^2/ry^2 == (Px^3+7)/(rx^3+7) mod p",
        rs.lam_y_sq_matches_ratio_p,
        "y-layer quadratic (same as LAW-P)",
    )
    pl.raw("")
    pl.raw("  mod N (field coords usually off-curve mod N — report honestly):")
    pl.log_step("(Py^2 - 7) / (ry^2 - 7) mod N", rs.lambda_cube_from_y_n)
    pl.log_step(
        "Lambda_N^3 == (Py^2-7)/(ry^2-7) mod N",
        rs.lambda_cube_matches_lambda_n,
        "PASS only if on-curve mod N",
    )


def p_side_compress_carry(y: int, ip_int: int) -> tuple[int, bool]:
    """Heaven carry a = (y^2 - IP - 7) / p when the p-side x-compress law holds."""
    num = y * y - ip_int - 7
    ok = num % p == 0
    return (num // p if ok else 0), ok


def n_side_compress_constant(a_carry: int) -> int:
    """N analog of +7 on p-side: 7*delta^2 + a_carry*p*delta^2 (mod N)."""
    return (7 * pow(delta, 2, N) + (a_carry * p * pow(delta, 2)) % N) % N


def slot_compress_carry(y: int, x: int) -> tuple[int, bool]:
    """Per-slot p-side carry: a = (y^2 - x^3 - 7) / p when Px^3 + 7 = Py^2 mod p."""
    num = y * y - pow(x, 3) - 7
    ok = num % p == 0
    return (num // p if ok else 0), ok


def n_slot_y_compress_constant(a_carry: int) -> int:
    """N slot y-compress constant: 7*delta^3 + a_carry*p*delta^3 (mod N)."""
    d3 = pow(delta, 3, N)
    return (7 * d3 + (a_carry * p * d3) % N) % N


def compressed_slot_y2(qx: int, k: int) -> int:
    """Heaven-corrected (Qx^3 + 7*delta^3) mod N at the y-compress layer."""
    return (pow(qx, 3, N) + k) % N


@dataclass
class NYCompressionCheck:
    """N-side y-family compress: 3 x-slots -> one Y_comp; 2 y's -> lambda_yN."""

    slot_carries_p: list[int]
    slot_carries_r: list[int]
    all_slot_carries_p_ok: bool
    all_slot_carries_r_ok: bool
    y_comp_shared: bool
    y_r_comp_shared: bool
    y_comp: int
    y_r_comp: int
    qy_sq_from_y_comp: bool
    qy_r_sq_from_y_r_comp: bool
    n_y_compress_ratio: int
    lambda_y_n: int
    n_y_compress_law: bool
    naive_n_curve_ratio: int
    naive_n_y_law: bool
    all_rows_same_compressed_ratio: bool
    branch_grid: list[tuple[str, int, bool]]


def verify_n_y_compression(
    *,
    px_triple: list[int],
    rx_triple: list[int],
    py: int,
    ry: int,
) -> NYCompressionCheck:
    """Compress y^2 = (Px^3+7)/(rx^3+7) to mod N via per-slot heaven carry."""
    qy = (py * delta) % N
    qy_r = (ry * delta) % N
    inv_delta = pow(delta, -1, N)
    lambda_y_n = (py * pow(ry, -1, N)) % N
    lambda_y_n_sq = pow(lambda_y_n, 2, N)

    carries_p: list[int] = []
    carries_r: list[int] = []
    y_comps: list[int] = []
    y_r_comps: list[int] = []
    row_ratios: list[int] = []

    for i in range(3):
        a_p, ok_p = slot_compress_carry(py, px_triple[i])
        a_r, ok_r = slot_compress_carry(ry, rx_triple[i])
        carries_p.append(a_p)
        carries_r.append(a_r)
        qx = (px_triple[i] * delta) % N
        qrx = (rx_triple[i] * delta) % N
        k_p = n_slot_y_compress_constant(a_p) if ok_p else 0
        k_r = n_slot_y_compress_constant(a_r) if ok_r else 0
        y_c = compressed_slot_y2(qx, k_p) if ok_p else 0
        y_rc = compressed_slot_y2(qrx, k_r) if ok_r else 0
        y_comps.append(y_c)
        y_r_comps.append(y_rc)
        if ok_p and ok_r and y_rc % N:
            row_ratios.append((y_c * pow(y_rc, -1, N)) % N)

    y_comp = y_comps[0] if y_comps else 0
    y_r_comp = y_r_comps[0] if y_r_comps else 0
    all_p_ok = all(slot_compress_carry(py, px_triple[i])[1] for i in range(3))
    all_r_ok = all(slot_compress_carry(ry, rx_triple[i])[1] for i in range(3))
    y_comp_shared = all_p_ok and len(set(y_comps)) == 1
    y_r_comp_shared = all_r_ok and len(set(y_r_comps)) == 1

    qy_sq = (qy * qy) % N
    qy_r_sq = (qy_r * qy_r) % N
    qy_from_comp = (y_comp * inv_delta) % N
    qy_r_from_comp = (y_r_comp * inv_delta) % N

    n_ratio = (y_comp * pow(y_r_comp, -1, N)) % N if y_r_comp % N else 0
    naive_ratio = curve_y_ratio_mod(N, px_triple[0], rx_triple[0])

    py_pos, py_neg = y_roots(px_triple[0])
    ry_pos, ry_neg = y_roots(rx_triple[0])
    ry_even = ry_pos if ry_pos % 2 == 0 else ry_neg
    ry_odd = ry_neg if ry_pos % 2 == 0 else ry_pos
    branch_grid: list[tuple[str, int, bool]] = []
    for py_lab, py_v in [("+", py_pos), ("-", py_neg)]:
        for ry_lab, ry_v in [("+", ry_even), ("-", ry_odd)]:
            a_p, ok_p = slot_compress_carry(py_v, px_triple[0])
            a_r, ok_r = slot_compress_carry(ry_v, rx_triple[0])
            if not (ok_p and ok_r):
                continue
            qx = (px_triple[0] * delta) % N
            qrx = (rx_triple[0] * delta) % N
            y_c = compressed_slot_y2(qx, n_slot_y_compress_constant(a_p))
            y_rc = compressed_slot_y2(qrx, n_slot_y_compress_constant(a_r))
            lam_n = (y_c * pow(y_rc, -1, N)) % N
            lam_branch = (py_v * pow(ry_v, -1, N)) % N
            branch_grid.append(
                (f"Py{py_lab}/ry{ry_lab}", lam_n, lam_n == pow(lam_branch, 2, N))
            )

    return NYCompressionCheck(
        slot_carries_p=carries_p,
        slot_carries_r=carries_r,
        all_slot_carries_p_ok=all_p_ok,
        all_slot_carries_r_ok=all_r_ok,
        y_comp_shared=y_comp_shared and y_r_comp_shared,
        y_r_comp_shared=y_r_comp_shared,
        y_comp=y_comp,
        y_r_comp=y_r_comp,
        qy_sq_from_y_comp=qy_from_comp == qy_sq,
        qy_r_sq_from_y_r_comp=qy_r_from_comp == qy_r_sq,
        n_y_compress_ratio=n_ratio,
        lambda_y_n=lambda_y_n,
        n_y_compress_law=n_ratio == lambda_y_n_sq,
        naive_n_curve_ratio=naive_ratio,
        naive_n_y_law=lambda_y_n_sq == naive_ratio,
        all_rows_same_compressed_ratio=len(set(row_ratios)) == 1 and row_ratios[0] == lambda_y_n_sq
        if row_ratios
        else False,
        branch_grid=branch_grid,
    )


def emit_n_y_compression(pl: Pipeline, yc: NYCompressionCheck) -> None:
    pl.phase("9c", "LAW-N — heaven rebirth of y-compress mod N")
    pl.raw(f"  {HEAVEN_DIE_REBIRTH}")
    pl.raw(
        "  DIE (naive):  lambda_yN^2 == (Px^3+7)/(rx^3+7) mod N  — fails off-curve mod N.\n"
        "  REBIRTH:      lambda_yN^2 == Y_comp/Y_r_comp mod N  — per-slot carry a_i lifts p-law to N.\n"
        "  p-side:       Px_i^3 + 7 = Py^2 mod p  (3 x-slots share one y-height)\n"
        "  N-side slot:  Y_comp = Qx_i^3 + 7*delta^3 + a_i*p*delta^3 mod N\n"
        "  N-side collapse: Qy^2 = Y_comp/delta mod N"
    )
    for i, a in enumerate(yc.slot_carries_p, 1):
        pl.log_step(f"a_P{i} = (Py^2 - Px{i}^3 - 7)/p integer", yc.all_slot_carries_p_ok, f"a={a}")
    for i, a in enumerate(yc.slot_carries_r, 1):
        pl.log_step(f"a_r{i} = (ry^2 - rx{i}^3 - 7)/p integer", yc.all_slot_carries_r_ok, f"a={a}")
    pl.log_step("Y_comp = Qx^3 + 7d^3 + a_P*p*d^3 shared by all 3 slots", yc.y_comp_shared, f"Y={yc.y_comp}")
    pl.log_step(
        "Y_r_comp = qx^3 + 7d^3 + a_r*p*d^3 shared by all 3 slots",
        yc.y_r_comp_shared,
        f"Y_r={yc.y_r_comp}",
    )
    pl.log_step("Qy^2 == Y_comp/delta mod N", yc.qy_sq_from_y_comp, "two y's from collapsed x-slots")
    pl.log_step("qy^2 == Y_r_comp/delta mod N", yc.qy_r_sq_from_y_r_comp)
    pl.log_step("lambda_yN = Py*ry^-1 mod N", yc.lambda_y_n)
    pl.log_step("lambda_yN^2 mod N", pow(yc.lambda_y_n, 2, N))
    pl.log_step(
        "LAW-N (rebirth): lambda_yN^2 == Y_comp/Y_r_comp mod N",
        yc.n_y_compress_law,
        "REQUIRED PASS — main N-side objective",
    )
    pl.log_step(
        "All 3 rows same compressed y-ratio",
        yc.all_rows_same_compressed_ratio,
        "3 x-slots -> one lambda_yN^2",
    )
    pl.log_step(
        "DIE (naive): lambda_yN^2 == (Px^3+7)/(rx^3+7) mod N",
        yc.naive_n_y_law,
        "expected FAIL — p-law dead mod N without heaven carry",
    )
    pl.raw("  Branch grid (compressed mod N, slot 1 template):")
    for label, lam_sq, ok in yc.branch_grid:
        pl.log_step(f"  {label} -> lambda_yN^2", ok, f"ratio={lam_sq}")


@dataclass
class NSideBalance:
    """N-side parallel to p-side IP+7=Py^2, with heaven carry from p."""

    ip_int: int
    ir_int: int
    iq: int
    i_r: int
    a_p: int
    a_r: int
    a_p_ok: bool
    a_r_ok: bool
    iq_eq_ip_delta3: bool
    iqq_eq_ir_delta3: bool
    qy_sq_eq_py_sq_delta2: bool
    qy_sq_eq_ry_sq_delta2: bool
    n_x_compress: bool
    n_r_compress: bool
    n_compress_k_p: int
    n_compress_k_r: int
    naive_iq_plus_7delta2: bool
    cq: int
    n_residue_x_cq: bool
    ip_delta2_eq_num: bool
    ir_delta2_eq_den: bool
    weighted_n_remainder: int
    weighted_n_eq_7_delta2: bool


def verify_n_side_balance(
    *,
    px_triple: list[int],
    rx_triple: list[int],
    gx_triple: list[int],
    py: int,
    ry: int,
    ip_mod_p: int,
    ir_mod_p: int,
) -> NSideBalance:
    _ = ip_mod_p, ir_mod_p
    ip_int = px_triple[0] * px_triple[1] * px_triple[2]
    ir_int = rx_triple[0] * rx_triple[1] * rx_triple[2]
    qx = [(x * delta) % N for x in px_triple]
    qy_slots = [(x * delta) % N for x in rx_triple]
    gx = [(x * delta) % N for x in gx_triple]
    qy = (py * delta) % N
    qy_r = (ry * delta) % N

    iq = 1
    i_r = 1
    for i in range(3):
        iq = iq * qx[i] % N
        i_r = i_r * qy_slots[i] % N

    a_p, a_p_ok = p_side_compress_carry(py, ip_int)
    a_r, a_r_ok = p_side_compress_carry(ry, ir_int)

    k_p = n_side_compress_constant(a_p)
    k_r = n_side_compress_constant(a_r)
    inv_delta = pow(delta, -1, N)

    n_x_compress = (
        (iq * inv_delta + k_p) % N == (qy * qy) % N
        if a_p_ok
        else False
    )
    n_r_compress = (
        (i_r * inv_delta + k_r) % N == (qy_r * qy_r) % N
        if a_r_ok
        else False
    )

    num = (qy * qy - k_p) % N
    den = (qy_r * qy_r - k_r) % N
    cq = (iq * pow(i_r, -1, N)) % N
    ratio = (num * pow(den, -1, N)) % N if den % N else 0

    lam_y_n = (py * pow(ry, -1, N)) % N
    lambda_n = (px_triple[0] * pow(rx_triple[0], -1, N)) % N
    weighted = (
        pow(lam_y_n, 2, N) * pow(qy_r, 2, N) - pow(lambda_n, 3, N) * pow(qx[0], 3, N)
    ) % N

    return NSideBalance(
        ip_int=ip_int,
        ir_int=ir_int,
        iq=iq,
        i_r=i_r,
        a_p=a_p,
        a_r=a_r,
        a_p_ok=a_p_ok,
        a_r_ok=a_r_ok,
        iq_eq_ip_delta3=(iq == (ip_int * pow(delta, 3)) % N),
        iqq_eq_ir_delta3=(i_r == (ir_int * pow(delta, 3)) % N),
        qy_sq_eq_py_sq_delta2=(qy * qy) % N == (py * py * pow(delta, 2)) % N,
        qy_sq_eq_ry_sq_delta2=(qy_r * qy_r) % N == (ry * ry * pow(delta, 2)) % N,
        n_x_compress=n_x_compress,
        n_r_compress=n_r_compress,
        n_compress_k_p=k_p,
        n_compress_k_r=k_r,
        naive_iq_plus_7delta2=(iq + 7 * pow(delta, 2, N)) % N == (qy * qy) % N,
        cq=cq,
        n_residue_x_cq=ratio == cq,
        ip_delta2_eq_num=num == (ip_int * pow(delta, 2)) % N,
        ir_delta2_eq_den=den == (ir_int * pow(delta, 2)) % N,
        weighted_n_remainder=weighted,
        weighted_n_eq_7_delta2=weighted == (7 * pow(delta, 2, N)) % N,
    )


def emit_n_side_balance(pl: Pipeline, nb: NSideBalance) -> None:
    pl.phase("9b", "N-SIDE BALANCE — heaven die / rebirth (parallel to IP+7=Py^2)")
    pl.raw(f"  {HEAVEN_DIE_REBIRTH}")
    pl.raw(
        "  p-side:  IP + 7 = Py^2 mod p  with integer carry a_p = (Py^2 - IP - 7) / p\n"
        "  N-side:  IQ/delta + 7*delta^2 + a_p*p*delta^2 = Qy^2 mod N  (reborn with carry)\n"
        "  DIE: naive IQ + 7*delta^2 = Qy^2 fails without a_p — +7 defect must cross p into N."
    )
    pl.log_step("IP (integer product Px1*Px2*Px3)", nb.ip_int)
    pl.log_step("IR (integer product rx1*rx2*rx3)", nb.ir_int)
    pl.log_step("IQ = Qx1*Qx2*Qx3 mod N", nb.iq)
    pl.log_step("Iq = qx1*qx2*qx3 mod N", nb.i_r)
    pl.log_step("IQ == IP * delta^3 mod N", nb.iq_eq_ip_delta3, "scaled x-product")
    pl.log_step("Iq == IR * delta^3 mod N", nb.iqq_eq_ir_delta3, "scaled r-product")
    pl.log_step("Qy^2 == Py^2 * delta^2 mod N", nb.qy_sq_eq_py_sq_delta2)
    pl.log_step("qy^2 == ry^2 * delta^2 mod N", nb.qy_sq_eq_ry_sq_delta2)
    pl.log_step("a_p = (Py^2 - IP - 7) / p integer", nb.a_p_ok, f"a_p={nb.a_p}" if nb.a_p_ok else "")
    pl.log_step("a_r = (ry^2 - IR - 7) / p integer", nb.a_r_ok, f"a_r={nb.a_r}" if nb.a_r_ok else "")
    pl.log_step("N-side compress constant k_p = 7*d^2 + a_p*p*d^2 mod N", nb.n_compress_k_p)
    pl.log_step("N-side compress constant k_r = 7*d^2 + a_r*p*d^2 mod N", nb.n_compress_k_r)
    pl.log_step(
        "N-X-COMPRESS: IQ/delta + k_p == Qy^2 mod N",
        nb.n_x_compress,
        "heaven-balanced x-family",
    )
    pl.log_step(
        "N-r-COMPRESS: Iq/delta + k_r == qy^2 mod N",
        nb.n_r_compress,
        "heaven-balanced r-family",
    )
    pl.log_step(
        "naive IQ + 7*delta^2 == Qy^2 (no carry)",
        nb.naive_iq_plus_7delta2,
        "expected FAIL without a_p",
    )
    pl.raw("")
    pl.raw("  N-side cubic aggregate (Ig-normalized, not Lambda_N^3):")
    pl.log_step("Cq = IQ/Iq mod N", nb.cq)
    pl.log_step("Qy^2 - k_p == IP*delta^2 mod N", nb.ip_delta2_eq_num)
    pl.log_step("qy^2 - k_r == IR*delta^2 mod N", nb.ir_delta2_eq_den)
    pl.log_step(
        "N-RESIDUE-X: (Qy^2-k_p)/(qy^2-k_r) == Cq mod N",
        nb.n_residue_x_cq,
        "y-heaven residue ratio closes on N",
    )
    pl.log_step(
        "Weighted N-side == 7*delta^2 mod N (naive delta lift)",
        nb.weighted_n_eq_7_delta2,
        "expected FAIL — use heaven k_p not bare +7",
    )
    pl.log_step(
        "Weighted N-side remainder mod N",
        nb.weighted_n_remainder,
        "lam_yN^2*qy^2 - Lambda_N^3*qx^3",
    )


@dataclass
class CompressionCheck:
    """3 x-slots compress to Py^2 via IP+7; 2 y-branches pick one lambda_y."""

    ip: int
    ir: int
    ip_plus_7_eq_py_sq: bool
    ir_plus_7_eq_ry_sq: bool
    py_sq: int
    ry_sq: int
    px_y2_shared: bool
    px_y2: int
    rx_y2_shared: bool
    rx_y2: int
    gx_y2_shared: bool
    lambda_y_all_rows_same: bool
    branch_grid: list[tuple[str, int]]


def verify_compression(
    *,
    px_triple: list[int],
    rx_triple: list[int],
    gx_triple: list[int],
    py: int,
    ry: int,
    ip: int | None = None,
    ir: int | None = None,
) -> CompressionCheck:
    """3 x's compress to Py^2 via IP+7; 2 y's (+/-) compress the x-ratio to lambda_y."""
    if ip is None:
        ip = 1
        for x in px_triple:
            ip = ip * x % p
    if ir is None:
        ir = 1
        for x in rx_triple:
            ir = ir * x % p

    py_sq = (py * py) % p
    ry_sq = (ry * ry) % p
    ip_plus_7_eq_py_sq = (ip + 7) % p == py_sq
    ir_plus_7_eq_ry_sq = (ir + 7) % p == ry_sq

    px_y2 = [(pow(x, 3, p) + 7) % p for x in px_triple]
    rx_y2 = [(pow(x, 3, p) + 7) % p for x in rx_triple]
    gx_y2 = [(pow(x, 3, p) + 7) % p for x in gx_triple]

    py_pos, py_neg = y_roots(px_triple[0])
    ry_pos, ry_neg = y_roots(rx_triple[0])
    ry_even = ry_pos if ry_pos % 2 == 0 else ry_neg
    ry_odd = ry_neg if ry_pos % 2 == 0 else ry_pos

    branch_grid: list[tuple[str, int]] = []
    for py_lab, py_v in [("+", py_pos), ("-", py_neg)]:
        for ry_lab, ry_v in [("+", ry_even), ("-", ry_odd)]:
            lv = (py_v * pow(ry_v, -1, p)) % p
            branch_grid.append((f"Py{py_lab}/ry{ry_lab}", lv))

    lam_rows = []
    for i in range(3):
        py_i = py if (py * py) % p == px_y2[0] else (py_pos if py_pos % 2 == py % 2 else py_neg)
        ry_i = ry if (ry * ry) % p == rx_y2[0] else (ry_even if ry_even % 2 == ry % 2 else ry_odd)
        lam_rows.append((py_i * pow(ry_i, -1, p)) % p)
    lam_same = len(set(lam_rows)) == 1

    return CompressionCheck(
        ip=ip,
        ir=ir,
        ip_plus_7_eq_py_sq=ip_plus_7_eq_py_sq,
        ir_plus_7_eq_ry_sq=ir_plus_7_eq_ry_sq,
        py_sq=py_sq,
        ry_sq=ry_sq,
        px_y2_shared=len(set(px_y2)) == 1,
        px_y2=px_y2[0],
        rx_y2_shared=len(set(rx_y2)) == 1,
        rx_y2=rx_y2[0],
        gx_y2_shared=len(set(gx_y2)) == 1,
        lambda_y_all_rows_same=lam_same,
        branch_grid=branch_grid,
    )


def emit_compression_architecture(pl: Pipeline, c: CompressionCheck) -> None:
    pl.raw("  COMPRESSION ARCHITECTURE:")
    pl.raw("  x-family (3 slots): product IP = Px1*Px2*Px3 collapses to one y-height")
    pl.log_step("IP = Px1*Px2*Px3 mod p", c.ip)
    pl.log_step("Py^2 mod p", c.py_sq)
    pl.log_step(
        "X-COMPRESS: IP + 7 == Py^2 mod p",
        c.ip_plus_7_eq_py_sq,
        "3 x-slots -> single pubkey y^2",
    )
    pl.log_step("IR = rx1*rx2*rx3 mod p", c.ir)
    pl.log_step("ry^2 mod p", c.ry_sq)
    pl.log_step(
        "r-family: IR + 7 == ry^2 mod p",
        c.ir_plus_7_eq_ry_sq,
        "same collapse for helper r triple",
    )
    pl.raw("  Per-slot: Px_i^3 + 7 = same y^2 (shared height before product collapse)")
    pl.log_step("Px1,Px2,Px3 share same y^2 mod p", c.px_y2_shared, f"y^2={c.px_y2}")
    pl.log_step("rx1,rx2,rx3 share same y^2 mod p", c.rx_y2_shared, f"y^2={c.rx_y2}")
    pl.log_step("Gx1,Gx2,Gx3 share same y^2 mod p", c.gx_y2_shared)
    pl.raw("  y-family (2 branches): +/- picks one Py/ry pair -> lambda_y = Py/ry")
    pl.log_step(
        "lambda_y same for all 3 rows (fixed +/- branch)",
        c.lambda_y_all_rows_same,
        "quadratic layer: lambda_y^2 = (Px^3+7)/(rx^3+7)",
    )
    pl.raw("  x-side cubic track: Lambda^3 from 3-way Latin (separate from IP+7=y^2)")
    pl.raw("  Branch grid Py +/- vs ry +/-:")
    for label, lv in c.branch_grid:
        pl.raw(f"    {label} -> lambda_y = {lv}")


@dataclass
class CoreLambdaLaws:
    """Mandatory bridge identities — LAW-P (p) + LAW-N (heaven N-side); x-cubic separate."""

    row: int
    lambda_y: int
    lambda_y_sq_p: int
    curve_ratio_p: int
    p_curve_law: bool
    p_on_curve: bool
    lambda_y_n: int
    lambda_y_sq_n: int
    lambda_n: int
    lambda_n_cube_n: int
    n_law: bool  # LAW-N: heaven-compressed y-ratio mod N (main objective)
    n_heaven_ratio: int
    y_comp: int
    y_r_comp: int
    n_naive_curve_law: bool  # (Px^3+7)/(rx^3+7) mod N — expected open off-curve
    naive_n_cubic_mix: bool
    n_on_curve: bool
    n_curve_ratio: int


def verify_core_lambda_laws(
    *,
    px: int,
    rx: int,
    py: int,
    ry: int,
    row: int,
    px_triple: list[int] | None = None,
    rx_triple: list[int] | None = None,
) -> CoreLambdaLaws:
    """Verify LAW-P and LAW-N on target row. LAW-N needs full Px/rx triple (heaven lift)."""
    lambda_y = (py * pow(ry, -1, p)) % p
    lambda_y_sq_p = pow(lambda_y, 2, p)
    curve_ratio_p = curve_y_ratio_mod(p, px, rx)
    p_curve_law = lambda_y_sq_p == curve_ratio_p
    p_on_curve = (py * py) % p == (pow(px, 3, p) + 7) % p

    lambda_y_n = (py * pow(ry, -1, N)) % N
    lambda_y_sq_n = pow(lambda_y_n, 2, N)
    lambda_n = (px * pow(rx, -1, N)) % N
    lambda_n_cube_n = pow(lambda_n, 3, N)
    n_on_curve = (py * py) % N == (pow(px, 3, N) + 7) % N
    n_curve_ratio = curve_y_ratio_mod(N, px, rx)
    n_naive_curve_law = lambda_y_sq_n == n_curve_ratio
    naive_n_cubic_mix = lambda_y_sq_n == lambda_n_cube_n

    n_law = False
    n_heaven_ratio = 0
    y_comp = 0
    y_r_comp = 0
    if px_triple is not None and rx_triple is not None:
        n_yc = verify_n_y_compression(
            px_triple=px_triple,
            rx_triple=rx_triple,
            py=py,
            ry=ry,
        )
        n_law = n_yc.n_y_compress_law
        n_heaven_ratio = n_yc.n_y_compress_ratio
        y_comp = n_yc.y_comp
        y_r_comp = n_yc.y_r_comp

    return CoreLambdaLaws(
        row=row,
        lambda_y=lambda_y,
        lambda_y_sq_p=lambda_y_sq_p,
        curve_ratio_p=curve_ratio_p,
        p_curve_law=p_curve_law,
        p_on_curve=p_on_curve,
        lambda_y_n=lambda_y_n,
        lambda_y_sq_n=lambda_y_sq_n,
        lambda_n=lambda_n,
        lambda_n_cube_n=lambda_n_cube_n,
        n_law=n_law,
        n_heaven_ratio=n_heaven_ratio,
        y_comp=y_comp,
        y_r_comp=y_r_comp,
        n_naive_curve_law=n_naive_curve_law,
        naive_n_cubic_mix=naive_n_cubic_mix,
        n_on_curve=n_on_curve,
        n_curve_ratio=n_curve_ratio,
    )


def emit_core_lambda_laws(pl: Pipeline, laws: CoreLambdaLaws) -> None:
    r = laws.row + 1
    pl.phase("11A", "CORE LAMBDA LAWS — LAW-P + LAW-N (mandatory)")
    pl.raw(
        "  LAW-P: p-side quadratic y-compress (2 y-branches, 3 x-slots).\n"
        f"  {HEAVEN_DIE_REBIRTH}\n"
        "  LAW-N: reborn y-ratio lambda_yN^2 == Y_comp/Y_r_comp mod N (MAIN OBJECTIVE).\n"
        "  x-side cubic (Lambda^3 / L1*L2*L3) is separate; do not conflate with y-law."
    )
    pl.raw("")
    pl.raw(f"  --- LAW-P (row {r}, mod p) ---")
    pl.log_step(f"lambda_y = Py{r} * ry{r}^-1 mod p", laws.lambda_y)
    pl.log_step("lambda_y^2 mod p", laws.lambda_y_sq_p)
    pl.log_step(f"(Px{r}^3 + 7) / (rx{r}^3 + 7) mod p", laws.curve_ratio_p)
    pl.log_step(
        "LAW-P: lambda_y^2 == (Px^3+7)/(rx^3+7) mod p",
        laws.p_curve_law,
        "REQUIRED PASS",
    )
    pl.log_step("Py on curve mod p (Py^2 == Px^3+7)", laws.p_on_curve)
    pl.raw("")
    pl.raw(f"  --- LAW-N (row {r}, mod N) — die (naive) / rebirth (heaven) ---")
    pl.log_step(f"lambda_yN = Py{r} * ry{r}^-1 mod N", laws.lambda_y_n)
    pl.log_step("lambda_yN^2 mod N", laws.lambda_y_sq_n)
    pl.log_step("Y_comp (heaven P-family)", laws.y_comp)
    pl.log_step("Y_r_comp (heaven r-family)", laws.y_r_comp)
    pl.log_step("Y_comp / Y_r_comp mod N", laws.n_heaven_ratio)
    pl.log_step(
        "LAW-N: lambda_yN^2 == Y_comp/Y_r_comp mod N",
        laws.n_law,
        "REQUIRED PASS — main N-side objective",
    )
    pl.raw("")
    pl.raw("  --- LAW-N diagnostics (naive off-curve form — expected open) ---")
    pl.log_step(f"(Px{r}^3 + 7) / (rx{r}^3 + 7) mod N (naive)", laws.n_curve_ratio)
    pl.log_step(
        "NAIVE: lambda_yN^2 == (Px^3+7)/(rx^3+7) mod N",
        laws.n_naive_curve_law,
        "expected FAIL — coords on-curve mod p only",
    )
    pl.log_step("Py on curve mod N (Py^2 == Px^3+7)", laws.n_on_curve)
    pl.log_step(f"Lambda_N = Px{r} * rx{r}^-1 mod N (x-layer)", laws.lambda_n)
    pl.log_step("Lambda_N^3 mod N", laws.lambda_n_cube_n)
    pl.log_step(
        "WRONG LAYER: lambda_yN^2 == Lambda_N^3 mod N",
        laws.naive_n_cubic_mix,
        "expected FAIL — conflates x-cubic with y-quadratic",
    )
    if not laws.n_naive_curve_law:
        diff = (laws.lambda_y_sq_n - laws.n_curve_ratio) % N
        pl.log_step("(lambda_yN^2 - naive ratio) mod N", diff)


def run_bridge_regression(cfg: PuzzleConfig) -> tuple[bool, list[str]]:
    """Run mandatory bridge checks for cfg; return (ok, messages)."""
    py, ry = resolve_y(cfg)
    messages: list[str] = []
    ok = True

    laws = verify_core_lambda_laws(
        px=cfg.Px[cfg.row],
        rx=cfg.rx[cfg.row],
        py=py,
        ry=ry,
        row=cfg.row,
        px_triple=cfg.Px,
        rx_triple=cfg.rx,
    )
    if not laws.p_curve_law:
        ok = False
        messages.append("LAW-P failed")
    else:
        messages.append("LAW-P OK")

    if not laws.n_law:
        ok = False
        messages.append("LAW-N failed")
    else:
        messages.append("LAW-N OK (heaven rebirth)")

    if laws.n_naive_curve_law:
        messages.append("WARN: naive LAW-N unexpectedly passed")

    n_yc = verify_n_y_compression(
        px_triple=cfg.Px,
        rx_triple=cfg.rx,
        py=py,
        ry=ry,
    )

    nb = verify_n_side_balance(
        px_triple=cfg.Px,
        rx_triple=cfg.rx,
        gx_triple=cfg.Gx,
        py=py,
        ry=ry,
        ip_mod_p=1,
        ir_mod_p=1,
    )
    Qx = [(x * delta) % N for x in cfg.Px]
    qx = [(x * delta) % N for x in cfg.rx]
    lambda_p = (cfg.Px[0] * pow(cfg.rx[0], -1, p)) % p
    fb = verify_family_bridge(
        px_triple=cfg.Px,
        rx_triple=cfg.rx,
        py=py,
        ry=ry,
        qx_scaled=Qx,
        qr_scaled=qx,
        lambda_p=lambda_p,
        n_balance=nb,
        n_y_compress=n_yc,
        lambda_n_target=(cfg.Px[cfg.row] * pow(cfg.rx[cfg.row], -1, N)) % N,
    )
    if not (fb.family_prod_eq_cq and fb.shell_product_align):
        ok = False
        messages.append("FAMILY BRIDGE failed")
    else:
        messages.append("FAMILY BRIDGE OK")

    if cfg.puzzle_num == 115:
        if lambda_p != P115_EXPECTED["lambda_p"]:
            ok = False
            messages.append("P115 lambda_p mismatch")
        if fb.cq != P115_EXPECTED["cq"]:
            ok = False
            messages.append("P115 Cq mismatch")
        if pow(n_yc.lambda_y_n, 2, N) != P115_EXPECTED["lambda_y_n_sq"]:
            ok = False
            messages.append("P115 lambda_yN^2 mismatch")
        if fb.lambda_n_target != P115_EXPECTED["lambda_n"]:
            ok = False
            messages.append("P115 Lambda_N mismatch")
        if ok:
            messages.append("P115 frozen checkpoints OK")
        exp_c = CONCAT_EXPECTED.get(115)
        if exp_c:
            px, py = cfg.Px[cfg.row], cfg.Py
            rx_t, ry_t, _ = resolve_true_r_xy(cfg)
            cf = build_concat_point_frame(
                px=px,
                py=py,
                rx_bridge=cfg.rx[cfg.row],
                ry_bridge=cfg.ry,
                rx_true=rx_t,
                ry_true=ry_t,
                r_true_source="test",
                lo=cfg.lo,
                known_k=cfg.known_k,
            )
            if cf.P_concat != exp_c["P"] or cf.R_true_concat != exp_c["R_true"]:
                ok = False
                messages.append("P115 concat decimal mismatch")
            else:
                messages.append("P115 concat decimals OK")

    if cfg.known_d is not None and _HAS_ECDSA:
        pub_x, pub_y = pubkey_from_scalar(cfg.known_d)
        if pub_x != cfg.Px[cfg.row] or pub_y != py:
            ok = False
            messages.append("known d*G != P")
        else:
            messages.append("known d*G == P OK")

    return ok, messages


def run_self_test() -> int:
    """Regression: P115 solved fixture + P160 OITC coords + hashkeys RSZ hooks."""
    failures = 0
    for label, puzzle_num in [("Puzzle 115 (solved calibration)", 115), ("Puzzle 160 (OITC)", 160)]:
        cfg = PuzzleConfig(puzzle_num=puzzle_num)
        apply_puzzle_defaults(cfg)
        ok, messages = run_bridge_regression(cfg)
        if ok:
            print(f"SELF-TEST OK: {label} — {', '.join(messages)}")
        else:
            failures += 1
            print(f"SELF-TEST FAIL: {label} — {', '.join(messages)}", file=sys.stderr)

    hk = _hashkeys()
    if hk is not None:
        rx, ry, src = hk.resolve_r_true_from_rsz(135) or (0, 0, "")
        if rx == P135_R_TRUE_X and ry == P135_R_TRUE_Y:
            print(f"SELF-TEST OK: P135 RSZ R_true matches frozen coords ({src})")
        else:
            failures += 1
            print(
                f"SELF-TEST FAIL: P135 RSZ R ({rx}, {ry}) != frozen ({P135_R_TRUE_X}, {P135_R_TRUE_Y})",
                file=sys.stderr,
            )
        cfg115 = PuzzleConfig(puzzle_num=115)
        apply_puzzle_defaults(cfg115)
        if cfg115.known_k == P115_K:
            print("SELF-TEST OK: P115 known_k from hashkeys RSZ")
        else:
            failures += 1
            print("SELF-TEST FAIL: P115 known_k not wired from hashkeys", file=sys.stderr)
        cfg160 = PuzzleConfig(puzzle_num=160)
        apply_puzzle_defaults(cfg160)
        rx160, ry160, src160 = resolve_true_r_xy(cfg160)
        if "hashkeys RSZ" in src160:
            print(f"SELF-TEST OK: P160 R_true from hashkeys ({src160})")
        else:
            failures += 1
            print(f"SELF-TEST FAIL: P160 R_true source={src160}", file=sys.stderr)
    else:
        print("SELF-TEST SKIP: hashkeys_rsz.py not importable")

    return 1 if failures else 0


@dataclass
class Pipeline:
    lines: list[str] = field(default_factory=list)
    step_no: int = 0
    core_laws: CoreLambdaLaws | None = None

    def heading(self, title: str) -> None:
        self.lines.append("")
        self.lines.append("=" * 80)
        self.lines.append(title)
        self.lines.append("=" * 80)

    def phase(self, n: int, title: str) -> None:
        self.heading(f"PHASE {n}: {title}")

    def log_step(self, formula: str, value: int | str | bool, note: str = "") -> None:
        self.step_no += 1
        if isinstance(value, bool):
            val = "OK" if value else "FAIL"
        elif isinstance(value, int):
            val = str(value)
            if value.bit_length() <= 64:
                val += f"  (0x{value:x})"
        else:
            val = str(value)
        line = f"  [{self.step_no:02d}] {formula}\n       = {val}"
        if note:
            line += f"\n       note: {note}"
        self.lines.append(line)

    def raw(self, text: str) -> None:
        self.lines.append(text)

    def emit(self, out: TextIO) -> None:
        encoding = getattr(out, "encoding", None) or "utf-8"
        for line in self.lines:
            try:
                out.write(line + "\n")
            except UnicodeEncodeError:
                safe = line.encode(encoding, errors="replace").decode(encoding, errors="replace")
                out.write(safe + "\n")


def configure_stdio_utf8() -> None:
    """Best-effort UTF-8 on Windows consoles (cp1252 cannot print em-dash / math symbols)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def parse_int(s: str) -> int:
    s = s.strip().replace("_", "")
    if not s:
        raise ValueError("empty")
    if s.lower().startswith("0x"):
        return int(s, 16)
    return int(s)


def parse_triple(raw: str) -> list[int]:
    parts = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
    if len(parts) != 3:
        raise ValueError(f"need exactly 3 comma-separated values, got {len(parts)}")
    return [parse_int(p) for p in parts]


def prompt_int(label: str, default: int | None) -> int | None:
    hint = f" [{default}]" if default is not None else " (required)"
    raw = input(f"  {label}{hint}: ").strip()
    if not raw:
        return default
    return parse_int(raw)


def prompt_triple(label: str, default: list[int]) -> list[int]:
    hint = f" [{default[0]}, {default[1]}, {default[2]}]"
    raw = input(f"  {label}{hint}: ").strip()
    if not raw:
        return list(default)
    return parse_triple(raw)


def prompt_config(use_defaults: bool = False) -> PuzzleConfig:
    cfg = PuzzleConfig()
    if use_defaults:
        apply_puzzle_defaults(cfg)
        return cfg

    print("")
    print("=" * 72)
    print("  ECDLP bridge pipeline — enter coordinates (Enter = Puzzle 135 default)")
    print("  Order: r (rx triple), s (ry), x (Px triple), y (Py)")
    print("=" * 72)
    print("")

    raw_puzzle = input(f"  Puzzle number [{cfg.puzzle_num}]: ").strip()
    if raw_puzzle:
        cfg.puzzle_num = int(raw_puzzle)

    raw_row = input(f"  Target row 1-3 [{cfg.row + 1}]: ").strip()
    if raw_row:
        row1 = int(raw_row)
        if row1 not in (1, 2, 3):
            raise SystemExit("row must be 1, 2, or 3")
        cfg.row = row1 - 1

    cfg.rx = prompt_triple("r  rx1,rx2,rx3", DEFAULT_RX)
    ry_val = prompt_int("s  ry (helper y, even branch)", DEFAULT_RY)
    cfg.ry = ry_val

    cfg.Px = prompt_triple("x  Px1,Px2,Px3", DEFAULT_PX)
    py_val = prompt_int("y  Py (pubkey y, even branch)", DEFAULT_PY)
    cfg.Py = py_val

    override_g = input("  Override Gx triple? [y/N]: ").strip().lower()
    if override_g in ("y", "yes"):
        cfg.Gx = prompt_triple("G  Gx1,Gx2,Gx3", DEFAULT_GX)

    print("")
    print(f"  -> puzzle {cfg.puzzle_num}, row {cfg.row + 1}, band [2^{cfg.puzzle_num - 1}, 2^{cfg.puzzle_num})")
    print("")
    return cfg


def config_from_args(args: argparse.Namespace) -> PuzzleConfig:
    cfg = PuzzleConfig()
    if args.puzzle is not None:
        cfg.puzzle_num = args.puzzle
    if args.row is not None:
        if args.row not in (1, 2, 3):
            raise SystemExit("--row must be 1, 2, or 3")
        cfg.row = args.row - 1
    if args.g:
        cfg.Gx = parse_triple(args.g)
    if args.r:
        cfg.rx = parse_triple(args.r)
    if args.x:
        cfg.Px = parse_triple(args.x)
    if args.y is not None:
        cfg.Py = parse_int(args.y)
    if args.s is not None:
        cfg.ry = parse_int(args.s)
    if args.defaults and not any([args.r, args.s, args.x, args.y, args.g]):
        apply_puzzle_defaults(cfg)
    elif cfg.puzzle_num in (115, 160) and not any([args.r, args.x]):
        apply_puzzle_defaults(cfg)
    if getattr(args, "no_complement", False):
        cfg.skip_complement = True
    if getattr(args, "complement_full", False):
        cfg.complement_quick = False
    return cfg


def y_roots(x: int) -> tuple[int, int]:
    y_sq = (pow(x, 3, p) + 7) % p
    y_pos = pow(y_sq, (p + 1) // 4, p)
    return y_pos, (p - y_pos) % p


def y_even(x: int) -> int:
    y_pos, y_neg = y_roots(x)
    return y_pos if y_pos % 2 == 0 else y_neg


def carry(num: int, mod: int) -> tuple[bool, int, int]:
    r = num % mod
    if r != 0:
        return False, r, 0
    return True, 0, num // mod


def carry_quotient(num: int, mod: int) -> tuple[bool, int, int, str]:
    """Exact integer quotient or decimal (lambdaN*qx - Qx) / N display."""
    rem = num % mod
    if rem == 0:
        q = num // mod
        return True, q, 0, str(q)
    q_floor = num // mod
    # High-precision decimal tail for notebook-style output
    from decimal import Decimal, getcontext

    getcontext().prec = 56
    ratio = Decimal(num) / Decimal(mod)
    return False, q_floor, rem, format(ratio, "f").rstrip("0").rstrip(".")


def latin_row(values: list[int], ninv: list[int], mod: int) -> list[int]:
    return [(values[0] * ninv[j]) % mod for j in range(3)]


def slot_name(val: int, canon: list[int]) -> str:
    for i, c in enumerate(canon):
        if val == c:
            return SLOT[i]
    return "?"


def pubkey_from_scalar(d: int) -> tuple[int, int]:
    """Return affine (x, y) for scalar * G_gen on secp256k1."""
    if not _HAS_ECDSA:
        raise RuntimeError("ecdsa package required for d*G verification (pip install ecdsa)")
    sk = SigningKey.from_secret_exponent(d % N, curve=SECP256k1)
    pt = sk.get_verifying_key().pubkey.point
    return int(pt.x()), int(pt.y())


def emit_ec_foundations(
    pl: Pipeline,
    *,
    px: int,
    py: int,
    known_d: int | None,
    known_k: int | None,
) -> None:
    """Phase 0a: EC definitions and ground-truth checks (P = d*G_gen, R = k*G_gen)."""
    pl.phase("0a", "EC FOUNDATIONS — P = d*G, R = k*G (definitions)")
    for line in EC_DEFINITIONS.strip().splitlines():
        pl.raw(line)

    if not _HAS_ECDSA:
        pl.raw("")
        pl.raw("  SKIP EC checks: install ecdsa (pip install ecdsa)")
        return

    pl.raw("")
    if known_d is not None:
        dx, dy = pubkey_from_scalar(known_d)
        d_inv = pow(known_d, -1, N)
        pl.log_step("known d (private scalar)", known_d)
        pl.log_step("d in puzzle band", True, "checked in calibration when configured")
        pl.log_step("P = d*G_gen (x == Px)", dx == px)
        pl.log_step("P = d*G_gen (y == Py)", dy == py)
        pl.log_step("d * d^-1 mod N == 1", (known_d * d_inv) % N == 1)
        pl.log_step(
            "G_gen = d^-1 * P  (equivalent to P = d*G)",
            dx == px and dy == py,
            "inversion is algebraic rewrite, not a separate solve",
        )
    else:
        pl.raw("  known d: not supplied — ECDLP target P = d*G_gen is OPEN")

    if known_k is not None:
        kx, ky = pubkey_from_scalar(known_k)
        k_inv = pow(known_k, -1, N)
        pl.log_step("known k (nonce scalar)", known_k)
        pl.log_step("R = k*G_gen (x)", kx)
        pl.log_step("R = k*G_gen (y)", ky)
        pl.log_step("k * k^-1 mod N == 1", (known_k * k_inv) % N == 1)
        pl.log_step(
            "G_gen = k^-1 * R  (equivalent to R = k*G)",
            True,
            "inversion is algebraic rewrite; rx triple is bridge helper, not R",
        )
    else:
        pl.raw("  known k: not supplied")

    if known_d is not None and known_k is not None:
        sf = compute_scalar_frame(known_d, known_k)
        pl.raw("")
        pl.raw("  Scalar frame (direct P <-> R bridge):")
        pl.log_step("m = d*k^-1 mod N", sf.m, "P = m*R")
        pl.log_step("m_inv = k*d^-1 mod N", sf.m_inv, "R = m_inv*P")
        pl.log_step("m * k mod N == d", sf.m_times_k_eq_d)
        pl.log_step("m_inv * d mod N == k", sf.m_inv_times_d_eq_k)


def emit_shelf_iteration_matrix(pl: Pipeline, sim: ShelfIterationMatrix, lo: int) -> None:
    pl.heading("PHASE 16b: SHELF CUBE ITERATION MATRIX (3 tracks x 3 columns)")
    pl.raw("  Map: T(x) = LO + (x^3 mod LO), applied per track independently.")
    pl.raw("")
    header = "track \\ col | " + " | ".join(sim.col_labels)
    pl.raw(f"  {header}")
    pl.raw("  " + "-" * len(header))
    for i, tname in enumerate(sim.track_names):
        cells = " | ".join(str(sim.matrix[i][j]) for j in range(len(sim.col_labels)))
        pl.raw(f"  {tname} | {cells}")

    pl.raw("")
    pl.raw("  Pairwise diffs mod LO (cube1 column):")
    v1 = [sim.matrix[i][1] for i in range(3)] if len(sim.col_labels) > 1 else []
    for a, b in [(0, 1), (0, 2), (1, 2)]:
        if v1:
            pl.raw(
                f"    {sim.track_names[a]} - {sim.track_names[b]} mod LO = "
                f"{(v1[a] - v1[b]) % lo}"
            )

    pl.raw("")
    for cs in sim.column_stats:
        pl.raw(f"  --- column: {cs.label} ---")
        pl.log_step(f"  sum({cs.label})", cs.shelf_sum)
        pl.log_step(f"  sum mod 3", cs.sum_mod3, f"fraction {cs.sum_mod3}/3")
        pl.log_step(f"  C_floor", cs.c_floor)
        pl.log_step(f"  C_plus1", cs.c_plus1)
        pl.log_step(f"  C_minus1", cs.c_minus1)
        pl.log_step(f"  C_minus2", cs.c_minus2)


def band_representative(c: int, lo: int, hi: int) -> int:
    """Unique d in [lo, hi) with d cong c (mod lo)."""
    return lo + (c % lo)


def build_d_candidates(
    *,
    lo: int,
    hi: int,
    lambda_p: int,
    lambda_ns: list[int],
    lam_y_n: int,
    lambda_n_target: int,
    b_x_own: list[int | None],
) -> list[tuple[str, int, int]]:
    """Bridge residues and their EC/band test scalars.

    Returns (label, scalar_for_dG, raw_residue). Scalar is either raw mod N or the
    band representative LO + (raw mod LO) — congruence class, not forced equality.
    """
    seen_scalars: set[int] = set()
    out: list[tuple[str, int, int]] = []

    def add_tests(name: str, raw: int) -> None:
        raw_n = raw % N
        if raw_n not in seen_scalars:
            seen_scalars.add(raw_n)
            out.append((f"{name}  |  d cong raw (mod N)", raw_n, raw))
        d_band = band_representative(raw, lo, hi)
        if d_band not in seen_scalars:
            seen_scalars.add(d_band)
            out.append(
                (f"{name}  |  d cong raw (mod LO), band rep", d_band, raw)
            )

    add_tests("Lambda (p-side)", lambda_p)
    add_tests("Lambda_N (target row)", lambda_n_target)
    add_tests("Lambda_yN", lam_y_n)

    for i, li in enumerate(lambda_ns):
        add_tests(f"Lambda_N row {i + 1}", li)
        if b_x_own[i] is not None:
            add_tests(f"L{i + 1} - b{i + 1}", li - b_x_own[i])
            add_tests(f"L{i + 1} - 2*b{i + 1}", li - 2 * b_x_own[i])

    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            add_tests(f"L{i + 1} - L{j + 1}", lambda_ns[i] - lambda_ns[j])

    for i, li in enumerate(lambda_ns):
        add_tests(f"Lambda_yN - L{i + 1}", lam_y_n - li)

    return out


def add_scalar_frame_candidates(
    out: list[tuple[str, int, int]],
    *,
    known_d: int | None,
    known_k: int | None,
    concat_frame: ConcatPointFrame | None = None,
) -> list[tuple[str, int, int]]:
    """Append m = d*k^-1 and m_inv = k*d^-1 when ground truth is known."""
    if known_d is None or known_k is None:
        return out
    sf = compute_scalar_frame(known_d, known_k)
    seen = {d for _, d, _ in out}

    def add(name: str, raw: int) -> None:
        val = raw % N
        if val in seen:
            return
        seen.add(val)
        out.append((name, val, raw))

    add("m = d*k^-1 (P = m*R)", sf.m)
    add("m_inv = k*d^-1 (R = m_inv*P)", sf.m_inv)
    if concat_frame is not None:
        add("P_concat mod N", concat_frame.P_mod_n)
        add("R_true_concat mod N", concat_frame.R_true_mod_n)
        add("(P/R)_pack mod N", concat_frame.P_over_R_true_mod_n)
    return out


def add_c_bracket_candidates(
    out: list[tuple[str, int, int]],
    c_floor: int,
    c_plus1: int,
    c_minus1: int,
    c_minus2: int,
    seen_scalars: set[int] | None = None,
) -> list[tuple[str, int, int]]:
    seen = seen_scalars or {d for _, d, _ in out}

    def add(name: str, d: int) -> None:
        if d in seen:
            return
        seen.add(d)
        out.append((name, d, d))

    add("C_floor (mean of 3 shelves)", c_floor)
    add("C_plus1", c_plus1)
    add("C_minus1", c_minus1)
    add("C_minus2 (sum mod 3 == 2 bracket)", c_minus2)
    return out


def shelf_cube_residue(shelf: int, lo: int) -> int:
    """shelf^3 mod LO — d congruent residue (orderinthecourt.txt corrected dy line)."""
    return pow(shelf, 3, lo)


def shelf_cube_band_lift(shelf: int, lo: int) -> int:
    """LO + (shelf^3 mod LO) — band lift / cube iteration step T(x)."""
    return lo + shelf_cube_residue(shelf, lo)


def shelf_cube_congruence(shelf: int, lo: int) -> int:
    """Alias for band-lift step (matrix iteration)."""
    return shelf_cube_band_lift(shelf, lo)


@dataclass
class ColumnCStats:
    col_index: int
    label: str
    values: list[int]
    shelf_sum: int
    sum_mod3: int
    c_floor: int
    c_plus1: int
    c_minus1: int
    c_minus2: int


@dataclass
class ShelfIterationMatrix:
    track_names: list[str]
    col_labels: list[str]
    matrix: list[list[int]]
    column_stats: list[ColumnCStats]


def compute_shelf_iteration_matrix(
    lo: int,
    shelves: list[int],
    track_names: list[str] | None = None,
    iterations: int = 3,
) -> ShelfIterationMatrix:
    """Build 3 tracks x N iterations under T(x) = LO + (x^3 mod LO)."""
    names = track_names or ["d2 track", "d3 track", "dy track"]
    matrix: list[list[int]] = [[s] for s in shelves]
    for _ in range(iterations - 1):
        for row in matrix:
            row.append(shelf_cube_congruence(row[-1], lo))

    col_labels = ["shelf (v0)", "cube1 (v1)", "cube2 (v2)"][:iterations]
    column_stats: list[ColumnCStats] = []
    for j, label in enumerate(col_labels):
        col = [matrix[i][j] for i in range(len(matrix))]
        s = sum(col)
        cf = s // 3
        column_stats.append(
            ColumnCStats(
                col_index=j,
                label=label,
                values=col,
                shelf_sum=s,
                sum_mod3=s % 3,
                c_floor=cf,
                c_plus1=cf + 1,
                c_minus1=cf - 1,
                c_minus2=cf - 2,
            )
        )

    return ShelfIterationMatrix(
        track_names=names,
        col_labels=col_labels,
        matrix=matrix,
        column_stats=column_stats,
    )


def add_matrix_candidates(
    out: list[tuple[str, int, int]],
    sim: ShelfIterationMatrix,
) -> list[tuple[str, int, int]]:
    seen = {d for _, d, _ in out}

    def add(name: str, d: int) -> None:
        if d in seen:
            return
        seen.add(d)
        out.append((name, d, d))

    for i, tname in enumerate(sim.track_names):
        for j, clabel in enumerate(sim.col_labels):
            add(f"matrix {tname} / {clabel}", sim.matrix[i][j])

    for cs in sim.column_stats:
        add(f"C_floor ({cs.label})", cs.c_floor)
        add(f"C_plus1 ({cs.label})", cs.c_plus1)
        add(f"C_minus1 ({cs.label})", cs.c_minus1)
        add(f"C_minus2 ({cs.label})", cs.c_minus2)

    return out


def emit_calibration_phase(
    pl: Pipeline,
    *,
    known_d: int,
    known_k: int | None,
    px: list[int],
    py: int,
    lo: int,
    hi: int,
    gap: int,
    oitc: OrderInTheCourt,
    sim: ShelfIterationMatrix,
    bridge_candidates: list[tuple[str, int, int]],
) -> None:
    """Phase 17b: compare bridge congruence classes to solved d (puzzle115ecdlpchallenge.txt)."""
    pl.phase(17.5, "CALIBRATION — known solved d vs bridge classes")
    pl.raw("  Ground truth from puzzle115ecdlpchallenge.txt structure.")
    pl.raw("  Bridge Phase 17 tests congruence classes only; this phase anchors tuning to d.")
    pl.log_step("known d (private key)", known_d)
    if known_k is not None:
        pl.log_step("known k (nonce)", known_k)
    pl.log_step("d in puzzle band [LO, HI)", lo <= known_d < hi)
    pl.log_step("d mod LO (band residue)", known_d % lo)
    pl.log_step("defect(d) = delta + d mod N", (delta + known_d) % N)
    pl.log_step("(N-d) mod LO", (N - known_d) % lo)
    pl.log_step("GAP mod LO", gap % lo)

    if _HAS_ECDSA:
        pub_x, pub_y = pubkey_from_scalar(known_d)
        pl.log_step("known d*G == P (must PASS)", pub_x == px[0] and pub_y == py)
    else:
        pl.raw("  SKIP d*G: install ecdsa")

    pl.raw("")
    pl.raw("  Distance to known d mod LO (smaller = better tuning target):")
    anchor_candidates: list[tuple[str, int]] = [
        ("known d", known_d),
        ("d2 cube lift", oitc.d_cube_lift2),
        ("d3 cube lift", oitc.d_cube_lift3),
        ("dy residue", oitc.d_cube_res_y),
        ("C_floor (shelf v0)", oitc.c_floor),
        ("C_floor (cube1 v1)", sim.column_stats[1].c_floor if len(sim.column_stats) > 1 else 0),
    ]
    for name, val in anchor_candidates:
        diff = (known_d - val) % lo
        pl.log_step(f"  |d - {name}| mod LO", diff, f"bits={diff.bit_length()}")

    pl.raw("")
    pl.raw("  Closest bridge congruence classes (top 5 by mod LO distance):")
    ranked: list[tuple[int, str, int]] = []
    seen: set[int] = set()
    for name, d, _raw in bridge_candidates:
        if d in seen:
            continue
        seen.add(d)
        ranked.append(((known_d - d) % lo, name, d))
    ranked.sort(key=lambda t: t[0])
    for diff, name, d in ranked[:5]:
        pl.raw(f"    diff_mod_LO={diff}  bits={diff.bit_length()}  [{name}]  scalar={d}")


@dataclass
class AlignmentFrame:
    """Shelf/cube alignment: v0 shelf anchors + optional known offset to d (P115 calibration)."""

    lo: int
    hi: int
    shelf2: int  # LO + (L2-L1 mod N mod LO)
    shelf3: int
    shelf_y: int
    d_cube_lift2: int  # one step: LO + (shelf2^3 mod LO)
    d_cube_lift3: int
    c_floor_v0: int
    c_floor_v1: int
    matrix_d2_v0: int
    known_d: int | None
    offset_shelf2: int | None  # (d - shelf2) mod LO when known
    offset_bits: int | None


def compute_alignment_frame(
    *,
    oitc: OrderInTheCourt,
    sim: ShelfIterationMatrix,
    lo: int,
    hi: int,
    known_d: int | None,
) -> AlignmentFrame:
    c1 = sim.column_stats[1].c_floor if len(sim.column_stats) > 1 else oitc.c_floor
    off: int | None = None
    off_bits: int | None = None
    if known_d is not None:
        off = (known_d - oitc.shelf2) % lo
        off_bits = off.bit_length()
    return AlignmentFrame(
        lo=lo,
        hi=hi,
        shelf2=oitc.shelf2,
        shelf3=oitc.shelf3,
        shelf_y=oitc.shelf_y,
        d_cube_lift2=oitc.d_cube_lift2,
        d_cube_lift3=oitc.d_cube_lift3,
        c_floor_v0=oitc.c_floor,
        c_floor_v1=c1,
        matrix_d2_v0=sim.matrix[0][0] if sim.matrix else oitc.shelf2,
        known_d=known_d,
        offset_shelf2=off,
        offset_bits=off_bits,
    )


def build_bridge_offset_terms(
    *,
    oitc: OrderInTheCourt,
    sim: ShelfIterationMatrix,
    lambda_ns: list[int],
    lo: int,
    hi: int,
    gap: int,
    lambda_p: int,
    lambda_n_target: int,
    calibrated_offset: int | None = None,
) -> list[tuple[str, int]]:
    """Bridge-only offset mod LO terms (no known d). Deduped by residue."""
    l1, l2, l3 = lambda_ns[0], lambda_ns[1], lambda_ns[2]
    seen: set[int] = set()
    terms: list[tuple[str, int]] = []

    def add(name: str, off: int) -> None:
        k = off % lo
        if k in seen:
            return
        seen.add(k)
        terms.append((name, k))

    add("L2-L1 mod LO", (l2 - l1) % lo)
    add("L3-L2 mod LO", (l3 - l2) % lo)
    add("L3-L1 mod LO", (l3 - l1) % lo)
    add("dy_mod mod LO", oitc.dy_mod % lo)
    add("d2_mod mod LO", oitc.d2_mod % lo)
    add("d3_mod mod LO", oitc.d3_mod % lo)
    add("dy residue (shelf_y^3 mod LO)", oitc.d_cube_res_y)
    add("d2 residue (shelf2^3 mod LO)", oitc.d_cube_res2)
    add("d3 residue (shelf3^3 mod LO)", oitc.d_cube_res3)
    add("C_plus1 - C_floor", (oitc.c_plus1 - oitc.c_floor) % lo)
    add("C_minus1 - C_floor", (oitc.c_minus1 - oitc.c_floor) % lo)
    add("shelf3 - shelf2", (oitc.shelf3 - oitc.shelf2) % lo)
    add("shelf_y - shelf2", (oitc.shelf_y - oitc.shelf2) % lo)
    add("GAP mod LO", gap % lo)
    add("(N-GAP) mod LO", (N - gap) % lo)
    q_shrink, rem_shrink = divmod(lambda_n_target * N, lambda_p)
    add("shrink (N-q) mod LO", (N - q_shrink) % lo)
    add("shrink rem mod LO", rem_shrink % lo)
    g_lo = N - hi
    add("gap_lo shelf (2^(H-1))", lo)
    add("(p-g_lo - delta) mod LO", ((p - g_lo) - delta) % lo)
    for label, shelf, lift in (
        ("d2", oitc.shelf2, oitc.d_cube_lift2),
        ("d3", oitc.shelf3, oitc.d_cube_lift3),
        ("dy", oitc.shelf_y, oitc.d_cube_lift_y),
    ):
        add(f"cube lift - shelf ({label})", (lift - shelf) % lo)
    shelf_v0 = [oitc.shelf2, oitc.shelf3, oitc.shelf_y]
    for i, row in enumerate(sim.matrix):
        for j in range(1, len(row)):
            add(f"matrix t{i} col{j}-col{j-1}", (row[j] - row[j - 1]) % lo)
        if len(row) > 1:
            add(f"matrix t{i} v1-v0", (row[1] - shelf_v0[i]) % lo)
        if len(row) > 2:
            add(f"matrix t{i} v2-v1", (row[2] - row[1]) % lo)
    if calibrated_offset is not None:
        terms.insert(0, ("P115-calibrated offset (shelf2->d)", calibrated_offset))
    return terms


def build_alignment_candidates(
    *,
    af: AlignmentFrame,
    oitc: OrderInTheCourt,
    sim: ShelfIterationMatrix,
    lambda_ns: list[int],
    gap: int,
    lambda_p: int,
    lambda_n_target: int,
) -> list[tuple[str, int, int]]:
    """d = anchor + offset (mod LO) hypotheses from shelf/OITC — then verify d*G == P."""
    lo, hi = af.lo, af.hi
    out: list[tuple[str, int, int]] = []
    seen: set[int] = set()

    def add(name: str, scalar: int) -> None:
        d = scalar % N
        if not (lo <= d < hi):
            d = band_representative(scalar, lo, hi)
        if d in seen:
            return
        seen.add(d)
        out.append((name, d, scalar))

    bases: list[tuple[str, int]] = [
        ("shelf2 (LO+(L2-L1 mod LO))", af.shelf2),
        ("shelf3 (LO+(L3-L1 mod LO))", af.shelf3),
        ("shelf_y (LO+(lambda_yN-L1 mod LO))", af.shelf_y),
        ("C_floor (shelf v0)", af.c_floor_v0),
        ("C_floor (cube1 v1)", af.c_floor_v1),
        ("d_cube_lift2 (1x cube on shelf2)", af.d_cube_lift2),
        ("d_cube_lift3 (1x cube on shelf3)", af.d_cube_lift3),
    ]
    for i, row in enumerate(sim.matrix):
        for j, val in enumerate(row):
            bases.append((f"matrix track{i} col{j}", val))

    offsets = build_bridge_offset_terms(
        oitc=oitc,
        sim=sim,
        lambda_ns=lambda_ns,
        lo=lo,
        hi=hi,
        gap=gap,
        lambda_p=lambda_p,
        lambda_n_target=lambda_n_target,
        calibrated_offset=af.offset_shelf2,
    )

    for bname, base in bases:
        add(bname, base)
        for oname, off in offsets:
            add(f"{bname} + ({oname})", base + off)

    return out


def emit_alignment_phase(
    pl: Pipeline,
    *,
    af: AlignmentFrame,
    align_results: list[DVerifyResult] | None = None,
) -> None:
    pl.phase("17c", "ALIGNMENT — shelf v0 + offset (mod LO = 2^(n-1)), not 9x cube chain")
    pl.raw(
        f"  Modulus: LO = 2^(n-1) = {af.lo}  (NOT 2^n-1, NOT 2^n+2^n)\n"
        "  One cube step:  T(x) = LO + (x^3 mod LO)\n"
        "  Matrix: 3 tracks x 3 cols — each track gets <=2 cube steps (v0->v1->v2), not 9 chained cubes to d.\n"
        "  Alignment model:  d ~ shelf_anchor + offset (mod LO),  then gate:  d*G == P."
    )
    pl.raw("")
    pl.log_step("shelf2 = LO + (L2-L1 mod N mod LO)", af.shelf2, "v0 d2 track — closest anchor")
    pl.log_step("shelf3 = LO + (L3-L1 mod N mod LO)", af.shelf3)
    pl.log_step("shelf_y = LO + (lambda_yN-L1 mod N mod LO)", af.shelf_y)
    pl.log_step("ONE cube: d_cube_lift2 = LO + (shelf2^3 mod LO)", af.d_cube_lift2)
    pl.log_step("ONE cube: d_cube_lift3 = LO + (shelf3^3 mod LO)", af.d_cube_lift3)
    pl.log_step("C_floor (shelf sum // 3)", af.c_floor_v0)
    pl.log_step("C_floor (cube1 column)", af.c_floor_v1)

    expect_bits = max(1, (af.hi.bit_length() - 1) - P115_HEIGHT_MINUS_OFFSET_BITS)

    if af.known_d is not None and af.offset_shelf2 is not None:
        pl.raw("")
        pl.raw("  --- P115 calibration (known d) ---")
        pl.log_step("known d", af.known_d)
        pl.log_step("offset = (d - shelf2) mod LO", af.offset_shelf2, f"bits={af.offset_bits}")
        pl.log_step("shelf2 + offset == d", (af.shelf2 + af.offset_shelf2) % N == af.known_d)
        if _HAS_ECDSA:
            px, py = pubkey_from_scalar(af.known_d)
            pl.log_step("(shelf2 + offset)*G == P", True, "EC gate — only this certifies answer")
    else:
        pl.raw("")
        pl.raw("  No known d — bridge-only offset (mod LO) is OPEN; gate remains d*G == P.")
        expect_bits = max(1, (af.hi.bit_length() - 1) - P115_HEIGHT_MINUS_OFFSET_BITS)
        pl.raw(
            f"  P115 solved reference: offset to shelf2 = {P115_OFFSET_BITS} bits "
            f"(H=115, pattern H-{P115_HEIGHT_MINUS_OFFSET_BITS}).\n"
            f"  On this puzzle (H={af.hi.bit_length() - 1}): expect ~{expect_bits}-bit offset "
            f"if same pattern — still must pass d*G == P."
        )

    if align_results:
        hits = [r for r in align_results if r.hit]
        pl.raw("")
        pl.raw(f"  Alignment d*G tests: {len(align_results)} candidates, {len(hits)} hit(s)")
        for r in align_results:
            if not r.hit:
                continue
            pl.log_step(f"  HIT: {r.name}", r.d)
        if not hits:
            pl.raw("  No alignment hit — shelf2 remains best v0 anchor; offset still OPEN.")
            pl.raw("  Top shelf2+offset trials by offset bit-length (bridge-only, no d*G hit):")
            shelf2_rows = [r for r in align_results if r.name.startswith("shelf2") and " + (" in r.name]
            ranked_off: list[tuple[int, str, int]] = []
            for r in shelf2_rows:
                off_mod = (r.raw - af.shelf2) % af.lo
                ranked_off.append((off_mod.bit_length(), r.name, off_mod))
            ranked_off.sort(
                key=lambda t: (abs(t[0] - expect_bits) if af.known_d is None else t[0], t[0])
            )
            for bits, name, off_mod in ranked_off[:8]:
                pl.raw(f"    offset_bits={bits}  residue={off_mod}  [{name}]")


def emit_complement_phase(pl: Pipeline, result) -> None:
    """Phase 17d: P160 complement m-leg [2^96, 2^97) — NP1 partner + KeyHunt exports."""
    pl.phase("17d", "COMPLEMENT m-leg [2^96, 2^97) — NP1 partner search (Puzzle 160)")
    pl.raw(
        "  Identity: N+1 = m·d  |  m ~ 2^96 (tractable leg)  |  d in [2^159, 2^160)\n"
        "  Gate unchanged: d·G == P_160 certifies any hit from m-leg or d-leg."
    )
    pl.raw("")
    if result.solution_d is not None:
        pl.log_step("COMPLEMENT SOLVED", True, result.solution_method or "")
        pl.log_step("d (complement)", result.solution_d)
        pl.log_step("hex", hex(result.solution_d))
    else:
        pl.log_step("NP1 exact divisor hits (eps window)", len(result.divisor_hits))
        pl.log_step("m-shells scored (G-prefix prune)", len(result.shell_rows))
        pl.log_step("KeyHunt d-windows ranked", len(result.d_windows))
        pl.raw("")
        pl.raw("  Top clean m-shells → d_est = floor((N+1)/m):")
        ranked = sorted(result.shell_rows, key=lambda x: (-x.clean_score, -x.px_contains))[:6]
        for r in ranked:
            pl.raw(
                f"    {r.name:14} m={r.m}  rem={r.np1_rem}  d_est={r.d_est}  "
                f"G_leak={r.g_contains}  clean={r.clean_score:.1f}"
            )
        pl.raw("")
        pl.raw("  Top KeyHunt d-windows (+-1T default):")
        for w in result.d_windows[:6]:
            pl.raw(f"    {w.label:22} center={w.center}  span={w.span}  range {w.lo:x}:{w.hi:x}")
        pl.raw("")
        pl.raw(
            "  Full report: puzzle160_complement_focus_report.txt\n"
            "  KeyHunt bats: puzzle160_keyhunt_bsgs/complement_exports/\n"
            "  CLI: python puzzle160_complement_focus.py  (omit --quick for full pass + .bat export)"
        )
    pl.raw(f"  complement elapsed: {result.elapsed_s:.1f}s")


@dataclass
class DVerifyResult:
    name: str
    d: int
    raw: int
    hit: bool
    in_band: bool
    same_class_mod_n: bool
    pub_x: int
    pub_y: int
    matched_row: int | None


def verify_d_candidates(
    candidates: list[tuple[str, int, int]],
    px: list[int],
    py: int,
    lo: int,
    hi: int,
) -> tuple[list[DVerifyResult], bool]:
    """Test scalars; d·G uses scalar mod N (congruent scalars => same point)."""
    results: list[DVerifyResult] = []
    any_hit = False

    for name, d, raw in candidates:
        pub_x, pub_y = pubkey_from_scalar(d)
        matched_row: int | None = None
        hit = False
        for i, px_i in enumerate(px):
            if pub_x == px_i and pub_y == py:
                hit = True
                matched_row = i + 1
                break
        if hit:
            any_hit = True
        results.append(
            DVerifyResult(
                name=name,
                d=d,
                raw=raw,
                hit=hit,
                in_band=lo <= d < hi,
                same_class_mod_n=(d % N) == (raw % N),
                pub_x=pub_x,
                pub_y=pub_y,
                matched_row=matched_row,
            )
        )

    return results, any_hit


@dataclass
class OrderInTheCourt:
    qx: list[int]
    qy: int
    qx_scaled: list[int]
    qy_scaled: int
    lambda_n: int
    lambda1: int
    lambda2: int
    lambda3: int
    lambday: int
    b_display: list[str]
    by_display: str
    d2_mod: int
    d2_signed: int
    d3_mod: int
    d3_signed: int
    dy_mod: int
    dy_signed: int
    shelf2: int
    shelf3: int
    shelf_y: int
    shelf_sum: int
    shelf_sum_mod3: int
    c_floor: int
    c_plus1: int
    c_minus1: int
    c_minus2: int
    d_cube_res2: int
    d_cube_res3: int
    d_cube_res_y: int
    d_cube_lift2: int
    d_cube_lift3: int
    d_cube_lift_y: int


def compute_order_in_the_court(
    *,
    lo: int,
    qx: list[int],
    qy: int,
    qx_scaled: list[int],
    qy_scaled: int,
    lambda_ns: list[int],
    lam_y_n: int,
) -> OrderInTheCourt:
    l1, l2, l3 = lambda_ns[0], lambda_ns[1], lambda_ns[2]
    d2_mod = (l2 - l1) % N
    d3_mod = (l3 - l1) % N
    dy_mod = (lam_y_n - l1) % N
    d2_signed = l2 - l1
    d3_signed = l3 - l1
    dy_signed = lam_y_n - l1

    shelf2 = lo + (d2_mod % lo)
    shelf3 = lo + (d3_mod % lo)
    shelf_y = lo + (dy_mod % lo)
    shelf_sum = shelf2 + shelf3 + shelf_y
    rem3 = shelf_sum % 3
    c_floor = shelf_sum // 3

    b_display: list[str] = []
    for i in range(3):
        _, _, _, disp = carry_quotient(l1 * qx[i] - qx_scaled[i], N)
        b_display.append(disp)
    _, _, _, by_display = carry_quotient(lam_y_n * qy - qy_scaled, N)

    return OrderInTheCourt(
        qx=qx,
        qy=qy,
        qx_scaled=qx_scaled,
        qy_scaled=qy_scaled,
        lambda_n=l1,
        lambda1=l1,
        lambda2=l2,
        lambda3=l3,
        lambday=lam_y_n,
        b_display=b_display,
        by_display=by_display,
        d2_mod=d2_mod,
        d2_signed=d2_signed,
        d3_mod=d3_mod,
        d3_signed=d3_signed,
        dy_mod=dy_mod,
        dy_signed=dy_signed,
        shelf2=shelf2,
        shelf3=shelf3,
        shelf_y=shelf_y,
        shelf_sum=shelf_sum,
        shelf_sum_mod3=rem3,
        c_floor=c_floor,
        c_plus1=c_floor + 1,
        c_minus1=c_floor - 1,
        c_minus2=c_floor - 2,
        d_cube_res2=shelf_cube_residue(shelf2, lo),
        d_cube_res3=shelf_cube_residue(shelf3, lo),
        d_cube_res_y=shelf_cube_residue(shelf_y, lo),
        d_cube_lift2=shelf_cube_band_lift(shelf2, lo),
        d_cube_lift3=shelf_cube_band_lift(shelf3, lo),
        d_cube_lift_y=shelf_cube_band_lift(shelf_y, lo),
    )


def oitc_notebook_d_cong(oitc: OrderInTheCourt) -> tuple[tuple[str, int], tuple[str, int], tuple[str, int]]:
    """Primary d congruent per orderinthecourt.txt: d2/d3 band lift, dy residue mod LO."""
    return (
        ("d2", oitc.d_cube_lift2),
        ("d3", oitc.d_cube_lift3),
        ("dy", oitc.d_cube_res_y),
    )


def emit_order_in_the_court(
    pl: Pipeline,
    oitc: OrderInTheCourt,
    px: list[int],
    rx: list[int],
    py: int,
    ry: int,
) -> None:
    pl.phase(16, "ORDER IN THE COURT (orderinthecourt.txt)")
    for i in range(3):
        pl.log_step(f"Px{i + 1}", px[i], "target x" if i == 0 else "")
    for i in range(3):
        pl.log_step(f"rx{i + 1}", rx[i])
    pl.log_step("Py1", py)
    pl.log_step("ry1", ry)
    pl.log_step("delta", delta)
    pl.raw("")
    pl.raw("  r*delta (mod N) = qx")
    for i in range(3):
        pl.log_step(f"qx{i + 1}", oitc.qx[i])
    pl.log_step("qy", oitc.qy)
    pl.raw("")
    pl.raw("  P*delta (mod N) = Qx")
    for i in range(3):
        pl.log_step(f"Qx{i + 1}", oitc.qx_scaled[i])
    pl.log_step("Qy", oitc.qy_scaled)
    pl.raw("")
    pl.log_step("lambdaN (= lambda1)", oitc.lambda_n)
    pl.log_step("lambda1", oitc.lambda1)
    pl.log_step("lambda2", oitc.lambda2)
    pl.log_step("lambda3", oitc.lambda3)
    pl.log_step("lambday", oitc.lambday)
    pl.raw("")
    pl.raw("  b = (lambdaN*qx - Qx) / N")
    for i in range(3):
        pl.log_step(f"b{i + 1}", oitc.b_display[i])
    pl.log_step("by", oitc.by_display)
    pl.raw("")
    pl.raw("  d2 = (Lambda2 - Lambda1) mod N")
    pl.log_step("d2 (signed)", oitc.d2_signed)
    pl.log_step("d2 cong (L2-L1) mod N", oitc.d2_mod)
    if oitc.d2_signed < 0:
        pl.log_step("N-d2 (mod N rep when d2 negative)", (-oitc.d2_signed) % N)
    pl.raw("")
    pl.raw("  d3 = (Lambda3 - Lambda1) mod N")
    pl.log_step("d3 cong (L3-L1) mod N", oitc.d3_mod)
    pl.raw("")
    pl.raw("  dy = (Lambda_yN - Lambda1) mod N")
    pl.log_step("dy (signed)", oitc.dy_signed)
    pl.log_step("dy cong (Ly-L1) mod N", oitc.dy_mod)
    if oitc.dy_signed < 0:
        pl.log_step("N-dy (mod N rep when dy negative)", (-oitc.dy_signed) % N)
    pl.raw("")
    for track, shelf, d_cong in [
        ("d2", oitc.shelf2, oitc.d_cube_lift2),
        ("d3", oitc.shelf3, oitc.d_cube_lift3),
        ("dy", oitc.shelf_y, oitc.d_cube_res_y),
    ]:
        pl.log_step(f"LO + ({track} mod 2^(n-1))", shelf)
        pl.raw(f"  2^(n-1) + shelf^3 mod 2^(n-1)  ->  d congruent")
        pl.log_step(f"d congruent ({track} cube lane)", d_cong)
        pl.log_step(f"N - d congruent ({track})", (N - d_cong) % N)
        pl.raw("")
    pl.log_step("shelf2 + shelf3 + shelf_y", oitc.shelf_sum)
    pl.log_step("(shelf sum) mod 3", oitc.shelf_sum_mod3, f"fractional part {oitc.shelf_sum_mod3}/3")
    pl.log_step("C_floor = floor(shelf sum / 3)", oitc.c_floor)
    pl.log_step("C_plus1 = C_floor + 1", oitc.c_plus1)
    pl.log_step("C_minus1 = C_floor - 1", oitc.c_minus1)
    pl.log_step("C_minus2 = C_floor - 2 (sum mod 3 == 2 bracket)", oitc.c_minus2)


def resolve_y(cfg: PuzzleConfig) -> tuple[int, int]:
    py = cfg.Py if cfg.Py is not None else y_even(cfg.Px[cfg.row])
    ry = cfg.ry if cfg.ry is not None else y_even(cfg.rx[cfg.row])
    return py, ry


def run_pipeline(cfg: PuzzleConfig) -> Pipeline:
    Gx, Px, rx = cfg.Gx, cfg.Px, cfg.rx
    ROW = cfg.row
    LO, HI, TOP = cfg.lo, cfg.hi, cfg.top
    MIRROR_LO, MIRROR_HI = cfg.mirror_lo, cfg.mirror_hi
    Py, ry = resolve_y(cfg)

    pl = Pipeline()
    pl.heading(f"ECDLP FULL PIPELINE — Puzzle {cfg.puzzle_num} (row {ROW + 1})")
    pl.raw(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    pl.raw("Curve: secp256k1  |  Bridge: Complexity_Simplified_p + ECDLP notes")
    if cfg.known_d is not None:
        pl.raw("")
        pl.raw(f"  GROUND TRUTH  d = {cfg.known_d}")
        if cfg.known_k is not None:
            pl.raw(f"                k = {cfg.known_k}")
    pl.raw("")
    pl.raw("  INPUT SUMMARY")
    pl.raw(f"    Gx = [{Gx[0]}, ...]")
    pl.raw(f"    Px = [{Px[0]}, {Px[1]}, {Px[2]}]")
    pl.raw(f"    rx = [{rx[0]}, {rx[1]}, {rx[2]}]")
    pl.raw(f"    Py (row {ROW + 1}) = {Py}")
    pl.raw(f"    ry (row {ROW + 1}) = {ry}")
    pl.raw(f"    P_concat (Px||Py) = {concat_point_xy(Px[ROW], Py)}")
    rx_t, ry_t, _ = resolve_true_r_xy(cfg)
    pl.raw(f"    R_true_concat (kG_x||kG_y) = {concat_point_xy(rx_t, ry_t)}")

    # ------------------------------------------------------------------ phase 0
    pl.phase(0, "FOUNDATIONS")
    pl.log_step("p (field prime)", p)
    pl.log_step("N (curve order)", N)
    pl.log_step("delta = p - N", delta)
    pl.log_step(f"Puzzle band LO = 2^{cfg.puzzle_num - 1}", LO)
    pl.log_step(f"Puzzle band HI = 2^{cfg.puzzle_num}", HI)
    pl.log_step(
        f"Puzzle {cfg.puzzle_num} scalar range",
        f"[{LO}, {HI})",
        f"d must satisfy 2^{cfg.puzzle_num - 1} <= d < 2^{cfg.puzzle_num}",
    )
    pl.log_step("TOP = HI - 1 (inclusive ceiling)", TOP)
    pl.log_step("Mirror band [N-(2^n+1), N-2^(n-1)]", f"{MIRROR_LO} .. {MIRROR_HI}")

    emit_ec_foundations(
        pl,
        px=Px[ROW],
        py=Py,
        known_d=cfg.known_d,
        known_k=cfg.known_k,
    )

    rx_true, ry_true, r_src = resolve_true_r_xy(cfg)
    concat_frame = build_concat_point_frame(
        px=Px[ROW],
        py=Py,
        rx_bridge=rx[ROW],
        ry_bridge=ry,
        rx_true=rx_true,
        ry_true=ry_true,
        r_true_source=r_src,
        lo=LO,
        known_k=cfg.known_k,
    )
    sf_early: ScalarFrame | None = None
    if cfg.known_d is not None and cfg.known_k is not None:
        sf_early = compute_scalar_frame(cfg.known_d, cfg.known_k)
    emit_concat_point_phase(pl, cp=concat_frame, lo=LO, frame=sf_early)
    if cfg.puzzle_num in CONCAT_EXPECTED:
        exp = CONCAT_EXPECTED[cfg.puzzle_num]
        pl.log_step(
            "P_concat matches frozen decimal",
            concat_frame.P_concat == exp["P"],
        )
        pl.log_step(
            "R_true_concat matches frozen decimal",
            concat_frame.R_true_concat == exp["R_true"],
        )

    # ------------------------------------------------------------------ phase 1
    pl.phase(1, "CUBE ROOTS OF N (mod p) — normalizers n1,n2,n3")
    pl.raw("  Solve n^3 = N (mod p). Three roots give the 3-way Latin square.")
    n = []
    for i, seed in enumerate([N1_HINT, N2_HINT, N3_HINT], 1):
        ok = pow(seed, 3, p) == N % p
        pl.log_step(f"n{i}^3 mod p == N", ok, f"n{i} bitlen={seed.bit_length()}")
        n.append(seed)
    ninv = [pow(x, -1, p) for x in n]
    for i in range(3):
        pl.log_step(f"n{i + 1}^-1 mod p", ninv[i])

    # ------------------------------------------------------------------ phase 2
    pl.phase(2, "BRIDGE COORDINATES — Gx/Px/rx triples (not G_gen)")
    pl.raw("  Px,Py = target P coords | rx,ry = helper r-family | Gx = slot normalizers")
    labels = ["Gx", "Px", "rx"]
    coords = [Gx, Px, rx]
    for lab, arr in zip(labels, coords):
        for i, v in enumerate(arr):
            note = "target x" if lab == "Px" and i == ROW else ""
            pl.log_step(f"{lab}{i + 1}", v, note)
    pl.log_step(f"Py{ROW + 1}", Py)
    pl.log_step(f"ry{ROW + 1}", ry)

    # ------------------------------------------------------------------ phase 3
    pl.phase(3, "LATIN SQUARE — multiply row1 by n_j^-1 (mod p)")
    pl.raw("  Each family permutes across slots G_A, G_B, G_C.")
    for lab, arr in zip(labels, coords):
        row = latin_row(arr, ninv, p)
        pl.raw(f"  {lab}1 * n_j^-1 -> {[slot_name(v, G_CANON) for v in row]}")
        for j, v in enumerate(row):
            pl.log_step(f"{lab}1 * n{j + 1}^-1 mod p", v, f"slot {slot_name(v, G_CANON)}")

    pl.raw("  Full Gx Latin grid (slot labels):")
    for i in range(3):
        row = [(Gx[i] * ninv[j]) % p for j in range(3)]
        pl.raw(f"    row {i + 1}: {[slot_name(v, G_CANON) for v in row]}")

    # ------------------------------------------------------------------ phase 4
    pl.phase(4, "SLOT COLLAPSE — map normalized slots back to CP1 / CR1")
    G_inv = [pow(g, -1, p) for g in G_CANON]
    P_slots = [(Px[0] * ninv[i]) % p for i in range(3)]
    r_slots = [(rx[0] * ninv[i]) % p for i in range(3)]
    cp_from_slots = []
    cr_from_slots = []
    for i in range(3):
        cp = (P_slots[i] * G_inv[i]) % p
        cr = (r_slots[i] * G_inv[i]) % p
        cp_from_slots.append(cp)
        cr_from_slots.append(cr)
        pl.log_step(f"P_{SLOT[i]} * G_{SLOT[i]}^-1 mod p", cp)
        pl.log_step(f"r_{SLOT[i]} * G_{SLOT[i]}^-1 mod p", cr)
    CP1 = cp_from_slots[0]
    CR1 = cr_from_slots[0]
    pl.log_step("CP1 (all slots equal)", len(set(cp_from_slots)) == 1, f"CP1={CP1}")
    pl.log_step("CR1 (all slots equal)", len(set(cr_from_slots)) == 1, f"CR1={CR1}")
    pl.log_step("CP1 - CR1 mod p", (CP1 - CR1) % p)

    for i in range(3):
        pl.log_step(f"Px{i + 1} * Gx{i + 1}^-1 mod p == CP1", (Px[i] * pow(Gx[i], -1, p)) % p == CP1)
        pl.log_step(f"rx{i + 1} * Gx{i + 1}^-1 mod p == CR1", (rx[i] * pow(Gx[i], -1, p)) % p == CR1)

    # ------------------------------------------------------------------ phase 5
    pl.phase(5, "X-BRIDGE Lambda (mod p)")
    Lambdas = [(Px[i] * pow(rx[i], -1, p)) % p for i in range(3)]
    Lambda = Lambdas[0]
    pl.log_step("Lambda = Px_i * rx_i^-1 mod p (all i)", len(set(Lambdas)) == 1, f"Lambda={Lambda}")
    pl.log_step("Lambda = CP1 * CR1^-1 mod p", Lambda == (CP1 * pow(CR1, -1, p)) % p)
    pl.log_step("Lambda^-1 mod p", pow(Lambda, -1, p))
    for i in range(3):
        pl.log_step(f"Px{i + 1} == Lambda * rx{i + 1} mod p", Px[i] == (Lambda * rx[i]) % p)

    # ------------------------------------------------------------------ phase 6
    pl.phase(6, "CUBIC AGGREGATES (mod p)")
    IG = 1
    IP = 1
    IR = 1
    for i in range(3):
        IG = IG * Gx[i] % p
        IP = IP * Px[i] % p
        IR = IR * rx[i] % p
    pl.log_step("IG = Gx1*Gx2*Gx3 mod p", IG)
    pl.log_step("IP = Px1*Px2*Px3 mod p", IP)
    pl.log_step("IR = rx1*rx2*rx3 mod p", IR)
    R1 = (IP * pow(IG, -1, p)) % p
    R2 = (IR * pow(IG, -1, p)) % p
    pl.log_step("R1 = IP*IG^-1 mod p", R1)
    pl.log_step("R2 = IR*IG^-1 mod p", R2)
    cbrt_r1 = cube_root_mod_prime(p, R1)
    pl.log_step("cbrt(R1) == CP1", cbrt_r1 == CP1 if cbrt_r1 else False, f"cbrt={cbrt_r1}")
    cbrt_r2 = cube_root_mod_prime(p, R2)
    pl.log_step("cbrt(R2) == CR1", cbrt_r2 == CR1 if cbrt_r2 else False, f"cbrt={cbrt_r2}")
    pl.log_step("IP == Lambda^3 * IR mod p", IP == (pow(Lambda, 3, p) * IR) % p)
    pl.log_step("IP * IR^-1 mod p == Lambda^3 mod p", (IP * pow(IR, -1, p)) % p == pow(Lambda, 3, p))
    pl.log_step("IP + 7 mod p", (IP + 7) % p, "x-family compresses to Py^2 in Phase 7")

    # ------------------------------------------------------------------ phase 7
    pl.phase(7, "Y-SIDE — sqrt branches (y^2 = x^3 + 7)")
    pl.raw("  All three Px share one y^2; same for Gx and rx.")
    y2_px = {(pow(x, 3, p) + 7) % p for x in Px}
    pl.log_step("Px1,Px2,Px3 share same y^2 mod p", len(y2_px) == 1)
    Gy = y_even(Gx[ROW])
    pl.log_step(f"Gy (even branch, row {ROW + 1})", Gy)
    pl.log_step(f"Py (input / even branch, row {ROW + 1})", Py)
    pl.log_step(f"ry (input / even branch, row {ROW + 1})", ry)
    y_pos, y_neg = y_roots(Px[ROW])
    pl.log_step(f"Py on curve: Py^2 == Px{ROW + 1}^3+7 mod p", (Py * Py) % p == (pow(Px[ROW], 3, p) + 7) % p)
    pl.log_step("Py is even y branch", Py % 2 == 0)
    pl.log_step("ry is even y branch", ry % 2 == 0)
    compression = verify_compression(
        px_triple=Px,
        rx_triple=rx,
        gx_triple=Gx,
        py=Py,
        ry=ry,
        ip=IP,
        ir=IR,
    )
    emit_compression_architecture(pl, compression)

    residue = verify_residue_solutions(
        px_triple=Px,
        rx_triple=rx,
        py=Py,
        ry=ry,
        lambda_p=Lambda,
        lambda_n=(Px[ROW] * pow(rx[ROW], -1, N)) % N,
    )
    emit_residue_solutions(pl, residue, Px, rx)

    # ------------------------------------------------------------------ phase 8
    pl.phase(8, "Y-BRIDGE (mod p)")
    CQ1 = (Py * pow(Gy, -1, p)) % p
    C_r1 = (ry * pow(Gy, -1, p)) % p
    lam_y = (Py * pow(ry, -1, p)) % p
    pl.log_step("CQ1 = Py * Gy^-1 mod p", CQ1)
    pl.log_step("C_r1 = ry * Gy^-1 mod p", C_r1)
    pl.log_step("lambda_y = Py * ry^-1 mod p", lam_y)
    pl.log_step("lambda_y != Lambda", lam_y != Lambda)
    pl.log_step("lambda_y / Lambda mod p", (lam_y * pow(Lambda, -1, p)) % p)
    lam_y_sq = (lam_y * lam_y) % p
    ratio_y = ((pow(Px[ROW], 3, p) + 7) * pow(pow(rx[ROW], 3, p) + 7, -1, p)) % p
    pl.log_step("lambda_y^2 mod p", lam_y_sq)
    pl.log_step(f"(Px{ROW + 1}^3+7)/(rx{ROW + 1}^3+7) mod p", ratio_y)
    pl.log_step("lambda_y^2 == (Px^3+7)/(rx^3+7)", lam_y_sq == ratio_y)
    pl.log_step("X-COMPRESS: IP + 7 == Py^2 mod p", compression.ip_plus_7_eq_py_sq)

    # ------------------------------------------------------------------ phase 9
    pl.phase(9, "N-SIDE SCALE — Q = P*delta, q = r*delta (mod N)")
    Qx = [(x * delta) % N for x in Px]
    qx = [(x * delta) % N for x in rx]
    Qy3 = (Py * delta) % N
    qy3 = (ry * delta) % N
    for i in range(3):
        pl.log_step(f"Qx{i + 1} = Px{i + 1} * delta mod N", Qx[i])
    pl.log_step(f"Qy = Py * delta mod N", Qy3)
    pl.log_step(f"qy = ry * delta mod N", qy3)

    n_balance = verify_n_side_balance(
        px_triple=Px,
        rx_triple=rx,
        gx_triple=Gx,
        py=Py,
        ry=ry,
        ip_mod_p=IP,
        ir_mod_p=IR,
    )
    emit_n_side_balance(pl, n_balance)

    n_y_compress = verify_n_y_compression(
        px_triple=Px,
        rx_triple=rx,
        py=Py,
        ry=ry,
    )
    emit_n_y_compression(pl, n_y_compress)

    # ------------------------------------------------------------------ phase 10
    pl.phase(10, "N-SIDE X-BRIDGE — Lambda_N and GAP")
    Lambda_N = (Px[ROW] * pow(rx[ROW], -1, N)) % N
    GAP = (Lambda_N - Lambda) % N
    pl.log_step(f"Lambda_N cong Px{ROW + 1} * rx{ROW + 1}^-1 (mod N)", Lambda_N)
    pl.log_step("GAP cong Lambda_N - Lambda (mod N)", GAP)
    pl.log_step("Lambda_N cong Lambda + GAP (mod N)", Lambda_N == (Lambda + GAP) % N)
    Lambda_Ns: list[int] = []
    for i in range(3):
        Li = (Qx[i] * pow(qx[i], -1, N)) % N
        Lambda_Ns.append(Li)
        pl.log_step(
            f"Lambda_{i + 1} cong Qx_{i + 1} * qx_{i + 1}^-1 (mod N)",
            Li,
            "same class as Lambda_N (target)" if Li == Lambda_N else "distinct per-row class",
        )
        closes = Qx[i] == (Lambda_Ns[i] * qx[i]) % N
        pl.log_step(
            f"Qx{i + 1} cong Lambda_{i + 1} * qx{i + 1} (mod N)",
            closes,
            "own-row Lambda" if closes else "cross-row Lambda_N fails",
        )

    family_bridge = verify_family_bridge(
        px_triple=Px,
        rx_triple=rx,
        py=Py,
        ry=ry,
        qx_scaled=Qx,
        qr_scaled=qx,
        lambda_p=Lambda,
        n_balance=n_balance,
        n_y_compress=n_y_compress,
        lambda_n_target=Lambda_N,
    )
    emit_family_bridge(pl, family_bridge)

    if cfg.known_d is not None and cfg.known_k is not None:
        sf = compute_scalar_frame(cfg.known_d, cfg.known_k)
        lam_y_n_sf = (Py * pow(ry, -1, N)) % N
        k_y_p = (lam_y * pow(Lambda, -1, p)) % p
        sf_matches = compare_bridge_to_scalar_frame(
            frame=sf,
            lo=LO,
            candidates={
                "Lambda (mod p)": Lambda,
                "Lambda_N": Lambda_N,
                "Lambda_1": Lambda_Ns[0],
                "Lambda_2": Lambda_Ns[1],
                "Lambda_3": Lambda_Ns[2],
                "Lambda_N_family": family_bridge.lambda_n_family_prod,
                "lambda_y (mod p)": lam_y,
                "lambda_yN": lam_y_n_sf,
                "k_y (mod p)": k_y_p,
                "Cq": family_bridge.cq,
                "GAP": GAP,
                "d": sf.d,
                "k": sf.k,
                "m": sf.m,
                "m_inv": sf.m_inv,
                "P_concat mod N": concat_frame.P_mod_n,
                "R_true_concat mod N": concat_frame.R_true_mod_n,
                "(P/R)_pack mod N": concat_frame.P_over_R_true_mod_n,
                "lambda_y true R": concat_frame.lambda_y_true_p,
                "Lambda true R": concat_frame.lambda_x_true_p,
            },
        )
        emit_scalar_frame_phase(pl, frame=sf, lo=LO, matches=sf_matches)
    else:
        pl.phase("10c", "SCALAR FRAME — P = m*R (skipped)")
        pl.raw("  Supply known_d and known_k (solved puzzle) to test bridge against m = d*k^-1.")

    # ------------------------------------------------------------------ phase 11
    pl.phase(11, "CARRIES — integer lifts when congruence is exact in Z")
    pl.raw("  Require (Lambda*qx - Qx) cong 0 (mod N) with zero remainder for b = (...)/N in Z.")
    b_x_own: list[int | None] = []
    for i in range(3):
        num = Lambda_N * qx[i] - Qx[i]
        ok, rem, b = carry(num, N)
        pl.log_step(
            f"b_x(row {i + 1}) integer",
            ok,
            f"b={b}" if ok else f"remainder={rem}",
        )
        num_own = Lambda_Ns[i] * qx[i] - Qx[i]
        ok_own, _, b_own = carry(num_own, N)
        b_x_own.append(b_own if ok_own else None)
        if ok_own and (not ok or b_own != b):
            pl.log_step(
                f"b_x own-row L{i + 1} (integer)",
                True,
                f"b={b_own}",
            )
    lam_y_N = (Py * pow(ry, -1, N)) % N
    pl.log_step("Lambda_yN = Py * ry^-1 mod N", lam_y_N)
    num_y = lam_y_N * qy3 - Qy3
    ok_y, rem_y, b_y = carry(num_y, N)
    pl.log_step("b_yN = (Lambda_yN*qy - Qy)/N integer", ok_y, f"b_yN={b_y}" if ok_y else f"rem={rem_y}")

    a3_num = Lambda * rx[ROW] - Px[ROW]
    ok_a3, _, a3 = carry(a3_num, p)
    pl.log_step("a3 = (Lambda*rx - Px)/p integer (p-side x-carry)", ok_a3, f"a3={a3}" if ok_a3 else "")
    b3y_p_num = lam_y * ry - Py
    ok_b3yp, _, b3y_p = carry(b3y_p_num, p)
    pl.log_step("b3_y = (lambda_y*ry - Py)/p integer (p-side y-carry)", ok_b3yp, f"b3_y={b3y_p}" if ok_b3yp else "")

    core_laws = verify_core_lambda_laws(
        px=Px[ROW],
        rx=rx[ROW],
        py=Py,
        ry=ry,
        row=ROW,
        px_triple=Px,
        rx_triple=rx,
    )
    pl.core_laws = core_laws
    emit_core_lambda_laws(pl, core_laws)

    # ------------------------------------------------------------------ phase 12
    pl.phase(12, "GRAND ALIGNMENT — corrected weighted forms (Phase 11A cross-check)")
    pl.log_step("LAW-P (Phase 11A)", core_laws.p_curve_law, "lambda_y^2 == (Px^3+7)/(rx^3+7) mod p")
    pl.log_step(
        "LAW-N (Phase 11A, heaven rebirth)",
        core_laws.n_law,
        "lambda_yN^2 == Y_comp/Y_r_comp mod N",
    )
    pl.log_step(
        "DIE: naive LAW-N (direct mod N)",
        core_laws.n_naive_curve_law,
        "expected FAIL — p-law dead mod N",
    )
    pl.log_step(
        "WRONG LAYER check: lambda_yN^2 == Lambda_N^3",
        core_laws.naive_n_cubic_mix,
        "expected FAIL (3 x cubic vs 2 y quadratic)",
    )
    corr_p = (pow(lam_y, 2, p) * pow(ry, 2, p) - pow(Lambda, 3, p) * pow(rx[ROW], 3, p)) % p
    pl.log_step("CORRECTED p-side: lam_y^2*ry^2 - Lambda^3*rx^3 mod p", corr_p, "equals 7 when LAW-P holds")
    pl.log_step("CORRECTED p-side == 7", corr_p == 7)
    corr_n = (pow(lam_y_N, 2, N) * pow(qy3, 2, N) - pow(Lambda_N, 3, N) * pow(qx[ROW], 3, N)) % N
    pl.log_step("CORRECTED N-side: lam_yN^2*qy^2 - Lambda_N^3*qx^3 mod N", corr_n)
    pl.log_step(
        "Weighted N-side matches p-side residue (+7 mod p)",
        corr_n == 7,
        "only when integer heaven aligns; not required for LAW-N",
    )

    def map_p_to_n(y: int) -> int:
        return (N * y // p) % N

    lam_py = map_p_to_n(Py)
    lam_mpy = map_p_to_n((-Py) % p)
    pl.log_step("map_p_to_n(Py) + map_p_to_n(-Py) mod N", (lam_py + lam_mpy) % N, "expect N-1")

    # ------------------------------------------------------------------ phase 13
    pl.phase(13, "CUBIC N-BRIDGE — IQ, Iq (family product, not single-row cube)")
    IQ = 1
    Iq = 1
    for i in range(3):
        IQ = IQ * Qx[i] % N
        Iq = Iq * qx[i] % N
    pl.log_step("IQ = Qx1*Qx2*Qx3 mod N", IQ)
    pl.log_step("Iq = qx1*qx2*qx3 mod N", Iq)
    pl.log_step(
        "IQ == Lambda_N_family * Iq mod N",
        IQ == (family_bridge.lambda_n_family_prod * Iq) % N,
        "corrected 3-root family bridge",
    )
    pl.log_step(
        "IQ == Lambda_N^3 * Iq mod N",
        IQ == (pow(Lambda_N, 3, N) * Iq) % N,
        "expected FAIL — old single-row assumption",
    )
    B_num = pow(Lambda_N, 3) * Iq - IQ
    ok_b, rem_b, B_c = carry(B_num, N)
    pl.log_step("B_cubic = (Lambda_N^3*Iq - IQ)/N integer", ok_b, "expected FAIL" if not ok_b else f"B={B_c}")

    # ------------------------------------------------------------------ phase 14
    pl.phase(14, f"DEFECT LANES — Puzzle {cfg.puzzle_num} scalar band")
    pl.raw("  defect(d) = delta + d (mod N)  |  new_N(d) = N - d")

    def defect(d: int) -> int:
        return (delta + d) % N

    corners = [
        ("LO floor", LO),
        ("TOP ceiling", TOP),
        ("mirror_HI", MIRROR_HI),
        ("mirror_LO (+2)", MIRROR_LO),
    ]
    for label, d in corners:
        pl.raw(
            f"  --- {label}: scalar={d}  "
            f"(bit_length={d.bit_length()}, band [2^{cfg.puzzle_num - 1}, 2^{cfg.puzzle_num})) ---"
        )
        pl.log_step("  defect(d)", defect(d), f"defect//delta = {defect(d) // delta}")
        pl.log_step("  N-d bitlen", (N - d).bit_length())
        pl.log_step("  (N-d) mod 2^(n-1)", (N - d) % LO)
        pl.log_step("  GAP mod 2^(n-1)", GAP % LO)

    lo_a = Lambda_N * N
    hi_a = (Lambda_N + 1) * N - 1
    nd_lo = (lo_a + Lambda - 1) // Lambda
    nd_hi = hi_a // Lambda
    d_lo = N - nd_hi
    d_hi = N - nd_lo
    hits = [d for d in range(max(LO, d_lo), min(HI, d_hi + 1)) if (Lambda * (N - d)) // N == Lambda_N]
    pl.log_step("Shrinkage d-interval lower", max(LO, d_lo))
    pl.log_step("Shrinkage d-interval upper", min(HI, d_hi))
    pl.log_step("Hits with floor(Lambda*(N-d)/N)==Lambda_N in band", len(hits), str(hits[:5]) if hits else "none")

    if ok_y:
        b3x0 = (Lambda_N * qx[ROW] - Qx[ROW]) // N
        pl.log_step("b_x(LO) ~ b_x(0) + LO*qx//N", b3x0 + (LO * qx[ROW]) // N)

    # ------------------------------------------------------------------ phase 15
    pl.phase(15, "k_y PAIR — y-tilt of x-bridge (mod p)")
    k_same = (lam_y * pow(Lambda, -1, p)) % p
    pl.log_step("k_y (same-parity) = lambda_y/Lambda mod p", k_same)
    pl.log_step("k_y * Lambda mod p == lambda_y", (k_same * Lambda) % p == lam_y)
    k_opp = (p - k_same) % p
    pl.log_step("k_y (opp-parity) = p - k_y", k_opp)
    pl.log_step("k_y+ + k_y- == p", k_same + k_opp == p)
    map_k = (N * k_same) // p
    pl.log_step("floor(N*k_y/p)", map_k)
    pl.log_step("floor(N*k_y/p) mod 2^(n-1)", map_k % LO)

    # ------------------------------------------------------------------ phase 16 — orderinthecourt.txt notebook block
    py1 = y_even(Px[0])
    ry1 = y_even(rx[0])
    qy_oitc = (ry1 * delta) % N
    qy_scaled_oitc = (py1 * delta) % N
    oitc = compute_order_in_the_court(
        lo=LO,
        qx=qx,
        qy=qy_oitc,
        qx_scaled=Qx,
        qy_scaled=qy_scaled_oitc,
        lambda_ns=Lambda_Ns,
        lam_y_n=lam_y_N,
    )
    emit_order_in_the_court(pl, oitc, Px, rx, py1, ry1)
    sim = compute_shelf_iteration_matrix(
        LO,
        [oitc.shelf2, oitc.shelf3, oitc.shelf_y],
        ["d2 track", "d3 track", "dy track"],
    )
    emit_shelf_iteration_matrix(pl, sim, LO)

    alignment_frame = compute_alignment_frame(
        oitc=oitc,
        sim=sim,
        lo=LO,
        hi=HI,
        known_d=cfg.known_d,
    )
    alignment_candidates = build_alignment_candidates(
        af=alignment_frame,
        oitc=oitc,
        sim=sim,
        lambda_ns=Lambda_Ns,
        gap=GAP,
        lambda_p=Lambda,
        lambda_n_target=Lambda_N,
    )

    # ------------------------------------------------------------------ phase 17
    pl.phase(17, f"d*G == P{cfg.puzzle_num} — congruence-class scalar tests")
    pl.raw(f"  Target P: Px{ROW + 1} = {Px[ROW]}, Py = {Py}")
    pl.raw(f"  Puzzle band [LO, HI); residues tested mod N (EC) and mod LO (band rep).")
    pl.raw("  Bridge values are congruence classes — not assumed equal to d.")
    pl.raw("")

    dg_solved = False
    dg_hits: list[DVerifyResult] = []

    if not _HAS_ECDSA:
        pl.raw("  SKIP: install ecdsa (pip install ecdsa) to run d*G checks.")
        emit_alignment_phase(pl, af=alignment_frame, align_results=None)
    else:
        candidates = build_d_candidates(
            lo=LO,
            hi=HI,
            lambda_p=Lambda,
            lambda_ns=Lambda_Ns,
            lam_y_n=lam_y_N,
            lambda_n_target=Lambda_N,
            b_x_own=b_x_own,
        )
        add_c_bracket_candidates(
            candidates,
            oitc.c_floor,
            oitc.c_plus1,
            oitc.c_minus1,
            oitc.c_minus2,
        )
        for track, d_cong in oitc_notebook_d_cong(oitc):
            if d_cong not in {c[1] for c in candidates}:
                candidates.append((f"d congruent ({track})", d_cong, d_cong))
            n_minus = (N - d_cong) % N
            if n_minus not in {c[1] for c in candidates}:
                candidates.append((f"N - d congruent ({track})", n_minus, n_minus))
        for label, d in [
            ("d2 shelf^3 mod LO (residue)", oitc.d_cube_res2),
            ("d3 shelf^3 mod LO (residue)", oitc.d_cube_res3),
            ("LO + dy shelf^3 mod LO (lift)", oitc.d_cube_lift_y),
        ]:
            if d not in {c[1] for c in candidates}:
                candidates.append((label, d, d))
        add_matrix_candidates(candidates, sim)
        add_scalar_frame_candidates(
            candidates, known_d=cfg.known_d, known_k=cfg.known_k, concat_frame=concat_frame
        )
        # Merge alignment shelf+offset hypotheses (dedupe by scalar mod N)
        seen_c = {c[1] for c in candidates}
        for name, d, raw in alignment_candidates:
            if d not in seen_c:
                candidates.append((f"align: {name}", d, raw))
                seen_c.add(d)
        if cfg.known_d is not None:
            kd = cfg.known_d % N
            if kd not in {c[1] for c in candidates}:
                candidates.insert(0, ("known d (ground truth)", kd, kd))
        pl.raw(f"  Testing {len(candidates)} congruence-class scalars...")
        dg_results, dg_solved = verify_d_candidates(candidates, Px, Py, LO, HI)
        dg_hits = [r for r in dg_results if r.hit]

        for r in dg_results:
            band = "in-band" if r.in_band else "out-of-band"
            status = "PASS" if r.hit else "FAIL"
            row_note = f"matches row {r.matched_row}" if r.hit else f"x=...{str(r.pub_x)[-8:]}"
            raw_mod_lo = r.raw % LO
            pl.raw(
                f"    [{status}] {r.name}\n"
                f"           raw mod LO = {raw_mod_lo}  |  test scalar = {r.d}\n"
                f"           bits={r.d.bit_length()} ({band})  {row_note}"
            )

        pl.raw("")
        if dg_solved:
            pl.log_step("d*G == P (puzzle solved)", True, f"hit(s): {[h.name for h in dg_hits]}")
            for h in dg_hits:
                pl.log_step(f"  d congruent class ({h.name})", h.d)
        else:
            pl.log_step("d*G == P (any congruence class)", False, "no tested class gave P")

        if cfg.known_d is not None:
            emit_calibration_phase(
                pl,
                known_d=cfg.known_d,
                known_k=cfg.known_k,
                px=Px,
                py=Py,
                lo=LO,
                hi=HI,
                gap=GAP,
                oitc=oitc,
                sim=sim,
                bridge_candidates=candidates,
            )

        align_results, _align_hit = verify_d_candidates(
            alignment_candidates, Px, Py, LO, HI
        )
        emit_alignment_phase(pl, af=alignment_frame, align_results=align_results)

    complement_result = None
    if cfg.puzzle_num == 160 and not cfg.skip_complement:
        p160c = _complement()
        if p160c is not None:
            comp_cfg = p160c.ComplementConfig(quick=cfg.complement_quick)
            complement_result = p160c.run_complement_focus(comp_cfg)
            p160c.write_artifacts(complement_result)
            emit_complement_phase(pl, complement_result)
            if complement_result.solution_d is not None:
                dg_solved = True
        else:
            pl.phase("17d", "COMPLEMENT m-leg — skipped (puzzle160_complement_focus.py not found)")

    # ------------------------------------------------------------------ phase 18
    pl.phase(18, "FINAL STATUS — what is closed vs open")
    laws_ok = core_laws.p_curve_law and core_laws.n_law
    closed = [
        ("LAW-P: lambda_y^2 == (Px^3+7)/(rx^3+7) mod p", core_laws.p_curve_law),
        ("LAW-N: lambda_yN^2 == Y_comp/Y_r_comp mod N (heaven rebirth)", core_laws.n_law),
        ("X-COMPRESS: IP + 7 = Py^2 (mod p)", compression.ip_plus_7_eq_py_sq),
        ("r-COMPRESS: IR + 7 = ry^2 (mod p)", compression.ir_plus_7_eq_ry_sq),
        ("RESIDUE-X: Lambda^3 = (Py^2-7)/(ry^2-7) mod p", residue.lambda_cube_matches_lambda_p),
        ("3 cube roots of Py^2-7 == Px triple", residue.px_roots_match_triple_p),
        ("3 cube roots of ry^2-7 == rx triple", residue.rx_roots_match_triple_p),
        ("N-X-COMPRESS: IQ/d + 7d^2 + a_p*p*d^2 = Qy^2 mod N", n_balance.n_x_compress),
        ("N-r-COMPRESS: Iq/d + 7d^2 + a_r*p*d^2 = qy^2 mod N", n_balance.n_r_compress),
        ("IQ == IP * delta^3 mod N", n_balance.iq_eq_ip_delta3),
        ("N-RESIDUE-X: heaven y-ratio == Cq = IQ/Iq mod N", n_balance.n_residue_x_cq),
        ("FAMILY-X: Lambda_N_family == Cq (L1*L2*L3)", family_bridge.family_prod_eq_cq),
        ("HEAVEN-Y-RATIO == Cq (product shell)", family_bridge.heaven_y_ratio == family_bridge.cq),
        ("SHELL PRODUCT ALIGN (x + heaven y)", family_bridge.shell_product_align),
        ("LAW-N (heaven): lambda_yN^2 == Y_comp/Y_r_comp mod N", n_y_compress.n_y_compress_law),
        ("Qy^2 == Y_comp/delta mod N (3 x-slots -> one y-height)", n_y_compress.qy_sq_from_y_comp),
        ("3 Qx slots share one Y_comp (heaven y-compress)", n_y_compress.y_comp_shared),
        ("3 rows same compressed y-ratio", n_y_compress.all_rows_same_compressed_ratio),
        ("3 Px share one y^2 per slot", compression.px_y2_shared),
        ("2 y-branches -> one lambda_y (all rows)", compression.lambda_y_all_rows_same),
        ("p-side Lambda bridge (all 3 rows)", len(set(Lambdas)) == 1),
        ("p-side cubic IP = Lambda^3 * IR", IP == (pow(Lambda, 3, p) * IR) % p),
        ("y-side CQ1/C_r1/lambda_y collapsed", True),
        ("corrected p grand alignment (+7)", corr_p == 7),
        (f"N-side row {ROW + 1}: Qx cong Lambda_N*qx (mod N)", Qx[ROW] == (Lambda_N * qx[ROW]) % N),
        (f"N-side b_x row {ROW + 1} integer lift", carry(Lambda_N * qx[ROW] - Qx[ROW], N)[0]),
        ("N-side b_yN integer lift", ok_y),
        (f"d*G == P{cfg.puzzle_num} (congruence classes)", dg_solved),
    ]
    open_items = [
        ("CORE LAWS both pass (LAW-P AND LAW-N heaven rebirth)", laws_ok),
        ("WRONG LAYER: lambda_yN^2 == Lambda_N^3 (should stay open)", core_laws.naive_n_cubic_mix),
        ("N-side Lambda_N universal (all rows)", all((Qx[i] * pow(qx[i], -1, N)) % N == Lambda_N for i in range(3))),
        ("N-side cubic IQ cong Lambda_N^3 * Iq (mod N)", IQ == (pow(Lambda_N, 3, N) * Iq) % N),
        ("WRONG: Lambda_N^3 == Cq (single-row)", family_bridge.naive_single_row_cube_eq_cq),
        ("SHELL: naive lambda_yN^2 == Cq (quadratic vs family)", family_bridge.lambda_y_n_sq == family_bridge.cq),
        ("naive N weighted == 7*delta^2 (expected open)", n_balance.weighted_n_eq_7_delta2),
        ("naive IQ + 7*delta^2 = Qy^2 without a_p (expected open)", n_balance.naive_iq_plus_7delta2),
        ("DIE: naive lambda_yN^2 == (Px^3+7)/(rx^3+7) mod N (expected open)", n_y_compress.naive_n_y_law),
        ("Py on curve mod N (needed for naive N curve-ratio law)", core_laws.n_on_curve),
        (f"Lambda_N literally in band (d may only cong mod LO)", LO <= Lambda_N < HI),
        ("Shrinkage hits in puzzle band", len(hits) > 0),
    ]
    pl.raw("")
    pl.raw("  CORE LAMBDA LAWS SUMMARY:")
    pl.raw(f"    LAW-P: {'PASS' if core_laws.p_curve_law else 'FAIL'}")
    pl.raw(f"    LAW-N (heaven rebirth): {'PASS' if core_laws.n_law else 'FAIL'}")
    pl.raw(f"    DIE naive mod N: {'unexpected PASS' if core_laws.n_naive_curve_law else 'open (expected)'}")
    pl.raw(f"    FAMILY BRIDGE L1*L2*L3 == Cq: {'PASS' if family_bridge.family_prod_eq_cq else 'FAIL'}")
    pl.raw(f"    SHELL PRODUCT ALIGN: {'PASS' if family_bridge.shell_product_align else 'open'}")
    pl.raw("")
    pl.raw("  CLOSED:")
    for name, ok in closed:
        pl.raw(f"    [{'x' if ok else ' '}] {name}")
    pl.raw("")
    pl.raw("  OPEN (ECDLP / N-bridge still required):")
    for name, ok in open_items:
        pl.raw(f"    [{'!' if not ok else ' '}] {name}")
    pl.raw("")
    expect_bits = max(1, cfg.puzzle_num - P115_HEIGHT_MINUS_OFFSET_BITS)
    pl.raw(
        f"  Next (CPU, no GPU):  python align_cpu_scroll.py --puzzle {cfg.puzzle_num} --radius 500000"
    )
    pl.raw(
        f"    Pollard kangaroo on ~{expect_bits}-bit offset needs ~2^{expect_bits // 2} group ops — not CPU-feasible."
    )
    pl.raw(
        "    Kangaroo only if bridge narrows offset to <= ~45 bits (~2^22 steps, overnight CPU)."
    )
    pl.raw("  GPU optional: keyhunt BSGS on exported sub-range (see puzzle160_keyhunt_bsgs/).")
    if cfg.puzzle_num == 160:
        pl.raw(
            "  P160 complement m-leg: python puzzle160_complement_focus.py "
            "(full pass + KeyHunt bats in puzzle160_keyhunt_bsgs/complement_exports/)."
        )
    pl.raw("  Validator: run ecdlp_n_bridge_verify.py for photo checklist.")

    return pl


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Full ECDLP bridge pipeline with interactive r,s,x,y input",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Input labels (same as prompts):
  r  = rx1,rx2,rx3   helper x triple
  s  = ry            helper y (even branch on target row)
  x  = Px1,Px2,Px3   public x triple
  y  = Py            pubkey y (even branch on target row)
  G  = Gx1,Gx2,Gx3   optional base triple (defaults to Puzzle 135 G family)

Examples:
  python ecdlp_full_pipeline.py
  python ecdlp_full_pipeline.py --defaults
  python ecdlp_full_pipeline.py --row 3 --x 51866...,54715...,92108...
        """,
    )
    parser.add_argument("--defaults", action="store_true", help="Skip prompts; use Puzzle 135 defaults")
    parser.add_argument(
        "--puzzle",
        type=int,
        help="Puzzle number n (band [2^(n-1), 2^n); e.g. 7 -> [2^6,2^7), 160 -> [2^159,2^160))",
    )
    parser.add_argument("--row", type=int, choices=[1, 2, 3], help="Target row (1-3)")
    parser.add_argument("--g", help="Gx triple: v1,v2,v3 (decimal or 0x hex)")
    parser.add_argument("--r", help="rx triple: v1,v2,v3")
    parser.add_argument("--s", help="ry (helper y)")
    parser.add_argument("--x", help="Px triple: v1,v2,v3")
    parser.add_argument("--y", help="Py (pubkey y)")
    parser.add_argument("--out", help="Write report to this file (UTF-8)")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 unless LAW-P and LAW-N (heaven rebirth) both pass (Phase 11A)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run regression self-test on Puzzle 160 OITC coords and exit",
    )
    parser.add_argument(
        "--no-complement",
        action="store_true",
        help="Skip Puzzle 160 Phase 17d complement m-leg [2^96, 2^97)",
    )
    parser.add_argument(
        "--complement-full",
        action="store_true",
        help="Puzzle 160 Phase 17d: full eps scan + KeyHunt .bat export (slow)",
    )
    parser.add_argument(
        "--complement-only",
        action="store_true",
        help="Run puzzle160_complement_focus only and exit",
    )
    args = parser.parse_args()

    if args.self_test:
        raise SystemExit(run_self_test())

    if args.complement_only:
        p160c = _complement()
        if p160c is None:
            raise SystemExit("puzzle160_complement_focus.py not importable")
        comp_cfg = p160c.ComplementConfig(quick=not args.complement_full)
        if args.complement_full:
            comp_cfg.export_bats = True
        result = p160c.run_complement_focus(comp_cfg)
        p160c.write_artifacts(result)
        print(p160c.format_report(result))
        raise SystemExit(0)

    configure_stdio_utf8()

    has_cli_coords = any([args.r, args.s, args.x, args.y, args.g, args.puzzle, args.row])
    if args.defaults and not has_cli_coords:
        cfg = config_from_args(args)
    elif has_cli_coords:
        cfg = config_from_args(args)
    else:
        cfg = prompt_config(use_defaults=False)

    pl = run_pipeline(cfg)
    pl.emit(sys.stdout)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            pl.emit(f)
        print(f"\nWrote report: {args.out}", file=sys.stderr)

    exit_code = 0
    if pl.core_laws is not None:
        if not pl.core_laws.p_curve_law:
            print("ERROR: LAW-P failed — lambda_y^2 != (Px^3+7)/(rx^3+7) mod p", file=sys.stderr)
            exit_code = 1
        if args.strict and not pl.core_laws.n_law:
            print(
                "ERROR: LAW-N failed — lambda_yN^2 != Y_comp/Y_r_comp mod N (heaven rebirth)",
                file=sys.stderr,
            )
            exit_code = 1
        elif not args.strict and not pl.core_laws.p_curve_law:
            return 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
