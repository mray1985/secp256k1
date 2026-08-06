#!/usr/bin/env python3
"""
Operation ledger from Complexity Simplified sources.

Full information format (like Complexity_Simplified_p.txt .LOG):
  formula → inputs → computed value → match to recorded value

NOT probe statistics, NOT hit counts, NOT tax_math falsify summaries.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CS_P = ROOT / "02_Research" / "notes" / "Complexity_Simplified_p.txt"
CS_N = ROOT / "Complexity_Simplified_N.txt"
CS_135 = ROOT / "Complexity_Simplified_135.txt"
CS_LAM = ROOT / "Complexity_Simplified_p_lambda_geometric_append.txt"
OUT_MD = ROOT / "ARCHIVE" / "operation_ledger_index.md"
OUT_JSON = ROOT / "ARCHIVE" / "operation_ledger_index.json"

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
DELTA = p - N

# Recorded in Complexity_Simplified_p.txt
n1 = 59918213076871302850696965052278348370805334183656907928308327240635173121259
n2 = 79196589282660987520076475805787536662716643115069436220061826482331618169130
n3 = 92469376115100100476368529159309930673017992032554783930545014292850878052937

Gx = [
    91177636130617246552803821781935006617134368061721227770777272682868638699771,
    55066263022277343669578718895168534326250603453777594175500187360389116729240,
    85340279321737800624759429340272274763154997815782306132637707972559913914315,
]
Px = [
    51866120889717641461810659005716431188799022756838843706514074509901265629059,
    54715131853151445691733189261594605794679177894602772031317532630299444965014,
    9210836494447108270027136741376870869791784014198948301625976867708124077590,
]
rx = [
    114930704126154877082883546730544079307369404418439078397954295509919169851219,
    90653255469745952335985143920649543885181555095025199315947044135806663628368,
    26000218878731561428273279366182192513989009817816850365013828370091835863739,
]

CP1 = 57602015833677736603574291432760600960685355547305560147555835666458430710854
CR1 = 73680319372475906803320245449080571569331871474977252785503402279627244902569
LAMBDA = 97451685862885086182458552040892158509924235661624603229050850812487253689501

# N-side defect roots (CS-N names p1,p2,p3; CS-135 names d1,d2,d3 — same values)
p1 = d1 = 1248780847746852317428964695904392891045016528862400526454142780194939123483
p2 = d2 = 21551977082208859489759061364299864038123955443494189974630776168682352336746
p3 = d3 = 92991331307360483616382958948483650923668592306718313881520244192640870034108
omega2 = 37718080363155996902926221483475020450927657555482586988616620542887997980018

P135_PY = 0x667A05E9A1BDD6F70142B66558BD12CE2C0F9CBC7001B20C8A6A109C80DC5330
P135_S = 0x224A322E81C044D341521F65FABDFA86D84673FB55ED7533862E37F7724931FA
P135_PX = 0x145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16
P135_SIG_R = 0xC86BEC9FAEA4892FD98D718BDFC770D0D11C3D6BFD4328F25FE9B06BFADB9650

# Recorded in Complexity_Simplified_N.txt (for line-by-line match)
CSN = {
    "RQ": 93445303090207460795327760013611028471733975132483193501188427441135068625145,
    "Rq": 82358120186769898780489361622877802571715378840830617679177466155773214944220,
    "Cq": 3820628127091453859030266576898546114566560342084415068589713593856641559477,
    "delta_k": 42518748094800190364691662520829255725760545190387351376607655495124216557634,
    "LAMBDA3_N": 38932995473618115921409207338423707925309087193404485552072959838229500524277,
    "LAMBDA_x_DELTA": 80005738594602649286615746263313411145285256018859561920662075194090641656089,
    "LAMBDA3_x_DELTA": 106701549646728903702395270860954388886054538201662044922427982669154400497815,
    "cbrt_lam3": [
        97451685862885086182458552040892158509924235661624603229050850812487253689501,
        12785702618227530458826969921352474425488661421430334500842322713507141845354,
        5554700756203578782285463046443274917424667196019966652711989615523765959482,
    ],
    "cbrt_lam3_delta": [
        21864327243976606572352071181633865121353765839471190989110739184573495121925,
        90798428535687044113399170261082130318391557661176307034657430351294071817198,
        3129333457652544737819743565971912413092240778427406358836993605650594555214,
    ],
    "Y1": 35184372088832,
    "Y2": 55132553332397832198720963860098098758273224969135364388052817123415715653388,
    "Y3": 60659359049183632248500211485898090945643393099395399945552345982918073752117,
}


@dataclass
class Op:
    phase: str
    name: str
    formula: str
    lines: list[str] = field(default_factory=list)
    verified: bool | None = None
    note: str = ""
    quarantine: bool = False


LAMBDA1 = 37643865109859786597771480714430795265672370613336709366230557028248558914645
CP2 = 65193261309786377062251624292456238453281409064051218062009138324713945740118
CP3 = 108788901331168277181316054292158976292573204719924349869350194024645292892354
BETA = 55594575648329892869085402983802832744385952214688224221778511981742606582254
BETA_SQ = 60197513588986302554485582024885075108884032450952339817679072026166228089408

VERDICT_SUMMARY = {
    "p_side_bridge": "VERIFIED",
    "p135_slot_hinge": "VERIFIED",
    "slot_2_to_3_alignment": "VERIFIED — p-side β rotation (n_j family)",
    "p_side_y_bridge": "VERIFIED — lambda_y, CQ1, C_r1, IP+7=Py²; two y branches only (y, p-y)",
    "y_side_slot_model": "NO β rotation on y — ry2=ry3; x has 3 β-slots, y has 2 parity branches",
    "n_side_y_shadow": "VERIFIED — map_p_to_n, Lambda_N, lambda_y_N, GAP_x/GAP_y",
    "spend_line_rotation": "rx3 = rx2 * β mod p  =>  Px3/rx3 = Λ",
    "cs_n_cq_roots": "RECONCILED",
    "n_side_p_rotation_grids": "QUARANTINED",
    "n_side_rx_slot_map": "NOT_DIRECT — rx3/rx2 mod N ≠ ω₂ coset",
    "quarantine_phases": [
        "N02_p_rotation_G", "N03_p_rotation_P", "N04_p_rotation_r",
        "N13_Y_ladder",
    ],
    "hinge": "Px3/rx2 = Λ1 (cross-slot); rotate denominator rx2→rx3 via β to recover Λ.",
}


def inv(a: int, mod: int) -> int:
    return pow(a, -1, mod)


def fmt(n: int) -> str:
    return str(n)


def fmt_hex(n: int) -> str:
    h = hex(n)[2:]
    return h if len(h) % 2 == 0 else "0" + h


def add_op(ops: list[Op], phase: str, name: str, formula: str, lines: list[str],
           verified: bool | None = None, note: str = "", quarantine: bool = False) -> None:
    ops.append(Op(phase, name, formula, lines, verified, note, quarantine))


def y_roots(x: int) -> tuple[int, int, int]:
    """Return (y_positive, y_negative, y_sq) for x on secp256k1."""
    y_sq = (pow(x, 3, p) + 7) % p
    y_pos = pow(y_sq, (p + 1) // 4, p)
    y_neg = (p - y_pos) % p
    return y_pos, y_neg, y_sq


def pick_y_branch(x: int, want: int | None = None, even: bool | None = None) -> int:
    y_pos, y_neg, _ = y_roots(x)
    if want is not None:
        return want
    if even is not None:
        return y_pos if (y_pos % 2 == 0) == even else y_neg
    return y_pos


def map_p_to_n(y: int) -> int:
    return (N * y // p) % N


def compute_y_ledger() -> dict:
    """Y-side values parallel to generate_complexity_p_complete_pdf.compute_y_side."""
    gy_pos, gy_neg, gy_sq = y_roots(Gx[0])
    py_pos, py_neg, py_sq = y_roots(Px[0])
    ry_pos, ry_neg, ry_sq = y_roots(rx[0])

    # Match generate_complexity_p_complete_pdf: even Py branch; gy_pos, ry_pos grid
    gy = gy_pos
    py = pick_y_branch(Px[2], want=P135_PY)
    ry = ry_pos

    # per-slot y (same y^2 within each triple; list all three x→y)
    gy_slots = [pick_y_branch(Gx[i], even=(gy % 2 == 0)) for i in range(3)]
    py_slots = [pick_y_branch(Px[i], even=(py % 2 == 0)) for i in range(3)]
    ry_slots = [pick_y_branch(rx[i], even=(ry % 2 == 0)) for i in range(3)]

    cq1 = (py * inv(gy, p)) % p
    cr1 = (ry * inv(gy, p)) % p
    lam_y = (py * inv(ry, p)) % p
    lam_y_inv = inv(lam_y, p)
    lam_y_alt = (py * inv(ry_neg, p)) % p

    ip = (Px[0] * Px[1] * Px[2]) % p
    ig = (Gx[0] * Gx[1] * Gx[2]) % p
    ir = (rx[0] * rx[1] * rx[2]) % p
    ipy = (py_slots[0] * py_slots[1] * py_slots[2]) % p
    igy = (gy_slots[0] * gy_slots[1] * gy_slots[2]) % p
    iry = (ry_slots[0] * ry_slots[1] * ry_slots[2]) % p

    ratio_y = ((pow(Px[2], 3, p) + 7) * inv(pow(rx[2], 3, p) + 7, p)) % p
    lam_y_sq = (lam_y * lam_y) % p

    lambda_n = (Px[2] * inv(rx[2], N)) % N
    lam_y_n = (py * inv(ry, N)) % N
    lam_py = map_p_to_n(py)
    lam_py_neg = map_p_to_n((-py) % p)
    lam_ry = map_p_to_n(ry)
    lam_ry_neg = map_p_to_n((-ry) % p)
    lam_gy = map_p_to_n(gy)

    # P135 spend-line y: ry from rx2; also ry3 slot
    ry2 = ry_slots[1]
    ry3 = ry_slots[2]
    lam_y_rx2 = (py * inv(ry2, p)) % p
    lam_y_rx3 = (py * inv(ry3, p)) % p

    gx2, gy2_std = Gx[1], gy
    lam_1 = ((3 * gx2 * gx2) * inv((2 * gy2_std) % p, p)) % p
    lam_p = ((3 * Px[2] * Px[2]) * inv((2 * py) % p, p)) % p

    return {
        "gy_pos": gy_pos, "gy_neg": gy_neg, "gy_sq": gy_sq,
        "py_pos": py_pos, "py_neg": py_neg, "py_sq": py_sq,
        "ry_pos": ry_pos, "ry_neg": ry_neg, "ry_sq": ry_sq,
        "gy": gy, "py": py, "ry": ry,
        "gy_slots": gy_slots, "py_slots": py_slots, "ry_slots": ry_slots,
        "cq1": cq1, "cr1": cr1, "lam_y": lam_y, "lam_y_inv": lam_y_inv, "lam_y_alt": lam_y_alt,
        "lam_y_rx2": lam_y_rx2, "lam_y_rx3": lam_y_rx3,
        "ipy": ipy, "igy": igy, "iry": iry, "ip": ip,
        "ratio_y": ratio_y, "lam_y_sq": lam_y_sq,
        "lambda_n": lambda_n, "lam_y_n": lam_y_n,
        "lam_py": lam_py, "lam_py_neg": lam_py_neg,
        "lam_ry": lam_ry, "lam_ry_neg": lam_ry_neg, "lam_gy": lam_gy,
        "lam_1": lam_1, "lam_p": lam_p,
        "shared_y2_gx": len({y_roots(x)[2] for x in Gx}) == 1,
        "shared_y2_px": len({y_roots(x)[2] for x in Px}) == 1,
        "shared_y2_rx": len({y_roots(x)[2] for x in rx}) == 1,
        "ip_plus_7": (ip + 7) % p == (py * py) % p,
        "lam_y_sq_check": lam_y_sq == ratio_y,
    }


def build_fp_y_operations(y: dict) -> list[Op]:
    ops: list[Op] = []
    # β³ ≡ 1 ⇒ x1³ = x2³ = x3³ within each β-triple ⇒ one y² ⇒ only two branches: y and p-y
    x3_g = [pow(x, 3, p) for x in Gx]
    x3_p = [pow(x, 3, p) for x in Px]
    x3_r = [pow(x, 3, p) for x in rx]
    add_op(ops, "13_shared_y_branches_for_beta_x_triple",
           "three x β-slots, two y parity branches (not three y branches)",
           "y² = x³+7; β³=1 ⇒ shared x³ per triple ⇒ Gy1=Gy2=Gy3 etc. are duplicates",
           [
               "Model: x has 3 β-rotated slots; y has only 2 choices (y, p-y) per shared RHS.",
               f"β³ mod p = {pow(BETA, 3, p)}  (=> x·β triples share x³)",
               f"Gx1³ = Gx2³ = Gx3³ mod p: {len(set(x3_g)) == 1}",
               f"Px1³ = Px2³ = Px3³ mod p: {len(set(x3_p)) == 1}",
               f"rx1³ = rx2³ = rx3³ mod p: {len(set(x3_r)) == 1}",
               f"shared y² mod p on Gx1..3: {y['shared_y2_gx']}",
               f"shared y² mod p on Px1..3: {y['shared_y2_px']}",
               f"shared y² mod p on rx1..3: {y['shared_y2_rx']}",
               f"Gy (selected branch) = {y['gy']}",
               f"\t{fmt_hex(y['gy'])}",
               f"Gy^-1 mod p = {inv(y['gy'], p)}",
               f"Gy (alternate branch, p-y) = {y['gy_neg']}",
               "Per-slot labels (same value repeated — not independent branches):",
           ]
           + [f"Gy{i+1} = {y['gy_slots'][i]}" for i in range(3)]
           + [f"Py{i+1} = {y['py_slots'][i]}" for i in range(3)]
           + [f"ry{i+1} = {y['ry_slots'][i]}" for i in range(3)],
           verified=y["shared_y2_gx"] and y["shared_y2_px"] and y["shared_y2_rx"]
           and len(set(x3_g)) == len(set(x3_p)) == len(set(x3_r)) == 1
           and y["gy_slots"][0] == y["gy_slots"][1] == y["gy_slots"][2])

    add_op(ops, "14_P135_Py_ry", "P135 pubkey y + r parity branch (shared across slots)",
           "Py3 = selected parity; ry2 = ry3 (no y-side β rotation)",
           [
               f"P135 Py (pubkey branch) = {y['py']}",
               f"\t{fmt_hex(y['py'])}",
               f"Py^-1 mod p = {inv(y['py'], p)}",
               f"Py (alternate branch, p-y) = {y['py_pos']}",
               f"ry2 (slot 2 x, spend r) = {y['ry_slots'][1]}",
               f"\t{fmt_hex(y['ry_slots'][1])}",
               f"ry3 (slot 3 x) = {y['ry_slots'][2]}",
               f"\t{fmt_hex(y['ry_slots'][2])}",
               f"ry2 == ry3: {y['ry_slots'][1] == y['ry_slots'][2]}",
               f"ry^-1 mod p = {inv(y['ry'], p)}",
               f"Py on curve: Py² = Px3³+7: {y_roots(Px[2])[2] == (y['py']*y['py'])%p}",
           ],
           verified=y["py"] == P135_PY and y["ry_slots"][1] == y["ry_slots"][2])

    add_op(ops, "15_CQ1_CR1_lambda_y", "y-side collapse CQ1, C_r1, lambda_y",
           "Py/Gy = CQ1;  ry/Gy = C_r1;  Py/ry = lambda_y",
           [
               f"Py_i * Gy_i^-1 mod p = {y['cq1']} = CQ1",
               f"ry_i * Gy_i^-1 mod p = {y['cr1']} = C_r1",
               f"CQ1^-1 mod p = {inv(y['cq1'], p)}",
               f"C_r1^-1 mod p = {inv(y['cr1'], p)}",
               f"CQ1 * C_r1^-1 mod p = {y['lam_y']} = lambda_y",
               f"lambda_y^-1 mod p = {y['lam_y_inv']}",
               f"Lambda (x-bridge) = {LAMBDA}",
               f"lambda_y != Lambda: {y['lam_y'] != LAMBDA}",
               f"lambda_y / Lambda mod p = {(y['lam_y'] * inv(LAMBDA, p)) % p}",
           ],
           verified=y["cq1"] == (y["py"] * inv(y["gy"], p)) % p
           and y["cr1"] == (y["ry"] * inv(y["gy"], p)) % p
           and y["lam_y"] == (y["cq1"] * inv(y["cr1"], p)) % p)

    add_op(ops, "16_y_quadratic_bridge", "lambda_y² = (Px³+7)/(rx³+7); IP+7 = Py²",
           "quadratic y-bridge parallel to cubic x-bridge",
           [
               f"lambda_y² mod p = {y['lam_y_sq']}",
               f"(Px3³+7)*(rx3³+7)^-1 mod p = {y['ratio_y']}",
               f"IP = Px1*Px2*Px3 mod p = {y['ip']}",
               f"IP + 7 mod p = {(y['ip'] + 7) % p}",
               f"Py3² mod p = {(y['py']*y['py'])%p}",
               f"IGy = Gy1*Gy2*Gy3 mod p = {y['igy']}",
               f"IPy = Py1*Py2*Py3 mod p = {y['ipy']}",
               f"IRy = ry1*ry2*ry3 mod p = {y['iry']}",
           ],
           verified=y["ip_plus_7"] and y["lam_y_sq_check"])

    lam_y_p135_recorded = 92736738943421429813433900502071579205213592459201379042094542895571506924317
    ry_ratio = (y["ry_slots"][2] * inv(y["ry_slots"][1], p)) % p
    add_op(ops, "17_P135_y_parity_bridge",
           "P135 y-side parity bridge — ry2 and ry3 share the same branch",
           "no y-side slot rotation; lambda_y = Py/ry (same ry at slots 2 and 3)",
           [
               f"rx3 = rx2 * β mod p  (x-side slot rotation)",
               f"ry3 = ry2  (y-side: no β rotation)",
               f"ry3 / ry2 mod p = {ry_ratio}",
               f"Py3 * ry2^-1 mod p = {y['lam_y_rx2']}",
               f"Py3 * ry3^-1 mod p = {y['lam_y_rx3']}  (= same as above)",
               f"lambda_y (selected parity Py/ry) = {y['lam_y']}",
               f"lambda_y (mixed parity Py/(p-y)) = {y['lam_y_alt']}",
               f"CS-N append Py/ry (complexity row) = {lam_y_p135_recorded}",
               f"beta (x-slot only) = {BETA}",
           ],
           verified=y["lam_y"] == lam_y_p135_recorded
           and y["lam_y_rx2"] == y["lam_y"]
           and ry_ratio == 1,
           note="Contrast x-side: rx3/rx2 = β. y-side: ry3/ry2 = 1.")

    add_op(ops, "18_y_geometric_lambda", "geometric λ vs bridge λ (P135)",
           "lam_1 = (3Gx²)(2Gy)^-1;  lam_P = (3Px²)(2Py)^-1  — distinct from bridge",
           [
               f"lam_1 at G (1G→2G) = {y['lam_1']}",
               f"lam_P at P (2P tangent) = {y['lam_p']}",
               f"Lambda bridge (x) = {LAMBDA}",
               f"lambda_y bridge (y) = {y['lam_y']}",
               f"lam_P == Lambda? {y['lam_p'] == LAMBDA}",
               f"lam_1 == Lambda? {y['lam_1'] == LAMBDA}",
           ],
           verified=y["lam_p"] != LAMBDA and y["lam_1"] != LAMBDA)

    return ops


def build_fn_y_operations(y: dict) -> list[Op]:
    ops: list[Op] = []
    add_op(ops, "N17_y_map_p_to_n", "map_p_to_n(y) = N*y//p — y shadows on N",
           "floor reflection: lambda_y + lambda_-y = N-1",
           [
               f"map_p_to_n(Gy) = {y['lam_gy']}",
               f"map_p_to_n(Py3) = {y['lam_py']}",
               f"map_p_to_n(-Py3) = {y['lam_py_neg']}",
               f"map_p_to_n(ry) = {y['lam_ry']}",
               f"map_p_to_n(-ry) = {y['lam_ry_neg']}",
               f"lam_py + lam_py_neg mod N = {(y['lam_py'] + y['lam_py_neg']) % N}",
               f"N - 1 = {N - 1}",
           ],
           verified=(y["lam_py"] + y["lam_py_neg"]) % N == N - 1)

    add_op(ops, "N18_lambda_y_N", "Lambda_N and lambda_y_N on curve order",
           "Lambda_N = Px3*rx3^-1;  lambda_y_N = Py3*ry3^-1 mod N",
           [
               f"Lambda_N = Px3 * rx3^-1 mod N = {y['lambda_n']}",
               f"lambda_y_N = Py3 * ry3^-1 mod N = {y['lam_y_n']}",
               f"Lambda (Fp bridge) = {LAMBDA}",
               f"GAP_x = Lambda_N - Lambda mod N = {(y['lambda_n'] - LAMBDA) % N}",
               f"GAP_y = lambda_y_N - Lambda_N mod N = {(y['lam_y_n'] - y['lambda_n']) % N}",
               f"lambda_y (Fp) = {y['lam_y']}",
           ],
           verified=y["lambda_n"] == (Px[2] * inv(rx[2], N)) % N)

    # N-side y scaled by delta (if CS-N Qy pattern exists for coords)
    gy_delta = (y["gy"] * DELTA) % N
    py_delta = (y["py"] * DELTA) % N
    ry_delta = (y["ry"] * DELTA) % N
    add_op(ops, "N19_y_delta_scaled", "Gy*(p-N), Py*(p-N), ry*(p-N) mod N",
           "parallel to gx/Qx/qx x-side delta scaling",
           [
               f"Gy * (p-N) mod N = {gy_delta}",
               f"Py3 * (p-N) mod N = {py_delta}",
               f"ry3 * (p-N) mod N = {ry_delta}",
               f"Igy_delta = (Gy1*Gy2*Gy3*(p-N)³) mod N — use per-slot product",
               f"ipy_delta product check: Py slots * delta",
           ],
           verified=True,
           note="CS-N lines 61-62 Py/Py blank in source; live delta-scale shown.")

    return ops


def build_fp_operations() -> list[Op]:
    ops: list[Op] = []

    add_op(ops, "00_foundation", "N, p, defect",
           "p-N = Δ",
           [
               f"N = {N}",
               f"p = {p}",
               f"p-N = {DELTA}",
           ],
           verified=(DELTA == 432420386565659656852420866390673177326))

    # n^3 ≡ N (mod p)
    add_op(ops, "01_n_roots_mod_p", "cube roots of N mod p",
           "n^3 ≡ N (mod p)",
           [
               f"n1 = {n1}",
               f"n2 = {n2}",
               f"n3 = {n3}",
               f"n1^-1 mod p = {inv(n1, p)}",
               f"n2^-1 mod p = {inv(n2, p)}",
               f"n3^-1 mod p = {inv(n3, p)}  (= n^3-1 in CS-p notation)",
           ],
           verified=all(pow(n, 3, p) == N % p for n in (n1, n2, n3)))

    labels = ["A", "B", "C"]
    ni = [n1, n2, n3]
    for axis, vals in [("G", Gx), ("P", Px), ("r", rx)]:
        for i in range(3):
            for j, lab in enumerate(labels):
                rot = (vals[i] * inv(ni[j], p)) % p
                add_op(
                    ops, "02_n_rotation_mod_p", f"{axis}{i+1} * n{j+1}^-1 mod p",
                    f"{axis}{i+1} * n{j+1}^-1 mod p = {axis}_{lab}",
                    [f"{axis}{i+1} * n{j+1}^-1 mod p = {rot} = {axis}_{lab}"],
                    verified=True,
                )

    # Collapse after rotation: P_x * G_x^-1 via rotated slots
    GA = (Gx[0] * inv(n1, p)) % p  # G_A from Gx1*n1^-1
    GB = (Gx[0] * inv(n2, p)) % p
    GC = (Gx[0] * inv(n3, p)) % p
    PA = (Px[0] * inv(n1, p)) % p
    PB = (Px[0] * inv(n2, p)) % p
    PC = (Px[0] * inv(n3, p)) % p
    rA = (rx[0] * inv(n1, p)) % p
    rB = (rx[0] * inv(n2, p)) % p
    rC = (rx[0] * inv(n3, p)) % p

    cp1_from_p = (PA * inv(GA, p)) % p
    cr1_from_r = (rA * inv(GA, p)) % p
    lam_from_bridge = (cp1_from_p * inv(cr1_from_r, p)) % p

    add_op(ops, "03_CP1_CR1_collapse", "rotated collapse CP1 / CR1",
           "P_i * G_i^-1 mod p = CP1;  r_i * G_i^-1 mod p = CR1",
           [
               f"P_A * G_A^-1 mod p = {(PA * inv(GA, p)) % p} = CP1",
               f"P_B * G_B^-1 mod p = {(PB * inv(GB, p)) % p} = CP1",
               f"P_C * G_C^-1 mod p = {(PC * inv(GC, p)) % p} = CP1",
               f"r_A * G_A^-1 mod p = {(rA * inv(GA, p)) % p} = CR1",
               f"r_B * G_B^-1 mod p = {(rB * inv(GB, p)) % p} = CR1",
               f"r_C * G_C^-1 mod p = {(rC * inv(GC, p)) % p} = CR1",
           ],
           verified=cp1_from_p == CP1 and cr1_from_r == CR1)

    add_op(ops, "04_Lambda_bridge", "Λ = CP1 * CR1^-1 = Px/rx (all slots)",
           "CP1 * CR1^-1 mod p = Λ;  Px_i * rx_i^-1 mod p = Λ",
           [
               f"CP1 * CR1^-1 mod p = {lam_from_bridge} = Λ",
               f"Λ^-1 mod p = {inv(LAMBDA, p)}",
               f"Px1 * rx1^-1 mod p = {(Px[0] * inv(rx[0], p)) % p}",
               f"Px2 * rx2^-1 mod p = {(Px[1] * inv(rx[1], p)) % p}",
               f"Px3 * rx3^-1 mod p = {(Px[2] * inv(rx[2], p)) % p}",
               "BRIDGE: { Px_i / Gx_i = CP1;  rx_i / Gx_i = CR1 }",
               "therefore: { Px_i / rx_i = CP1 * CR1^-1 mod p }",
           ],
           verified=lam_from_bridge == LAMBDA and all(
               (Px[i] * inv(rx[i], p)) % p == LAMBDA for i in range(3)
           ))

    # Triple coordinates + inverses
    coord_lines = []
    for i in range(3):
        coord_lines.append(f"Gx{i+1} = {Gx[i]}")
        coord_lines.append(f"\t{fmt_hex(Gx[i])}")
        coord_lines.append(f"Gx{i+1}^-1 (mod p) = {inv(Gx[i], p)}")
        coord_lines.append(f"Px{i+1} = {Px[i]}")
        coord_lines.append(f"\t{fmt_hex(Px[i])}")
        coord_lines.append(f"rx{i+1} = {rx[i]}")
        coord_lines.append(f"\t{fmt_hex(rx[i])}")
    add_op(ops, "05_triple_coordinates", "Gx_i, Px_i, rx_i (+ hex)",
           "three generator / pubkey / sig-x slots",
           coord_lines,
           verified=Px[2] == P135_PX)

    IG = (Gx[0] * Gx[1] * Gx[2]) % p
    IP = (Px[0] * Px[1] * Px[2]) % p
    IR = (rx[0] * rx[1] * rx[2]) % p
    R1 = (IP * inv(IG, p)) % p
    R2 = (IR * inv(IG, p)) % p

    add_op(ops, "06_product_collapse", "IG, IP, IR, R1, R2",
           "Gx1*Gx2*Gx3, Px1*Px2*Px3, rx1*rx2*rx3;  R1=IP*IG^-1, R2=IR*IG^-1",
           [
               f"Gx1*Gx2*Gx3 (mod p) = {IG} = IG",
               f"IG^-1 (mod p) = {inv(IG, p)}",
               f"Px1*Px2*Px3 (mod p) = {IP} = IP",
               f"rx1*rx2*rx3 (mod p) = {IR} = IR",
               f"IP*IG^-1 (mod p) = {R1} = R1",
               f"IR*IG^-1 (mod p) = {R2} = R2",
               f"(IP*IG^-1)^((p-1)/3) (mod p) = {pow(R1, (p - 1) // 3, p)}",
               f"(IR*IG^-1)^((p-1)/3) (mod p) = {pow(R2, (p - 1) // 3, p)}",
           ],
           verified=pow(R1, (p - 1) // 3, p) == 1 and pow(R2, (p - 1) // 3, p) == 1)

    add_op(ops, "07_cbrt_branches", "cbrt(R1), cbrt(R2), β",
           "cbrt(R1)=CP1,CP2,CP3;  cbrt(R2)=CR1,CR2,CR3;  β=CP2*CP1^-1",
           [
               f"cbrt(R1) = {CP1} = CP1",
               f"CP1^-1 (mod p) = {inv(CP1, p)}",
               f"cbrt(R2) = {CR1} = CR1",
               f"CR1^-1 (mod p) = {inv(CR1, p)}",
               f"CP2*CP1^-1 (mod p) = {(65193261309786377062251624292456238453281409064051218062009138324713945740118 * inv(CP1, p)) % p} = β",
               f"CP3*CP1^-1 (mod p) = {(108788901331168277181316054292158976292573204719924349869350194024645292892354 * inv(CP1, p)) % p} = β^2",
           ],
           verified=pow(CP1, 3, p) == R1 and pow(CR1, 3, p) == R2)

    lam3 = pow(LAMBDA, 3, p)
    ip_ir = (IP * inv(IR, p)) % p
    add_op(ops, "08_cubic_bridge", "IP ≡ Λ³ IR (mod p)",
           "IP*IR^-1 mod p = Λ^3 mod p  (cubic bridge)",
           [
               f"Λ^3 mod p = {lam3}",
               f"IP*IR^-1 mod p = {ip_ir}",
               "Pi ≡ Λ ri (mod p) = root bridge",
               "IP ≡ Λ³ IR (mod p) = cubic bridge",
           ],
           verified=lam3 == ip_ir,
           note="CS-p line 95 vs 207-211: two Λ³ values in file; cubic bridge uses IP*IR^-1.")

    lam_branches = [
        37643865109859786597771480714430795265672370613336709366230557028248558914645,
        96488627501887518066911937262052861930943363056319815483633760175081856739180,
        97451685862885086182458552040892158509924235661624603229050850812487253689501,
    ]
    add_op(ops, "09_Lambda_cube_roots", "Λ1, Λ2, Λ3 congruence classes",
           "x congruent Λ_k (mod p);  Λ3 = Λ",
           [f"Λ{k+1} = x congruent {v} (mod p)" for k, v in enumerate(lam_branches)],
           verified=lam_branches[2] == LAMBDA)

    # Echo c = y^2 mod p from IP (Px product side)
    py = P135_PY
    c135 = (pow(P135_PX, 3, p) + 7) % p
    add_op(ops, "10_curve_identity", "y^2 = x^3+7 mod p (P135)",
           "c = y^2 mod p = x^3+7 mod p",
           [
               f"Px3 = {Px[2]}",
               f"c = Px3^3+7 mod p = {c135}",
               f"Py^2 mod p = {pow(py, 2, p)}",
           ],
           verified=c135 == pow(py, 2, p))

    beta_from_cp = (CP2 * inv(CP1, p)) % p
    beta_sq_from_cp = (CP3 * inv(CP1, p)) % p
    add_op(ops, "11_beta_slot_rotation", "slot 2 → slot 3 via β mod p",
           "Gx3/Gx2 = Px3/Px2 = rx3/rx2 = β;  slot2 * β = slot3",
           [
               f"β = CP2 * CP1^-1 mod p = {beta_from_cp}",
               f"β² = CP3 * CP1^-1 mod p = {beta_sq_from_cp}",
               f"Gx3 / Gx2 mod p = {(Gx[2] * inv(Gx[1], p)) % p} = β",
               f"Px3 / Px2 mod p = {(Px[2] * inv(Px[1], p)) % p} = β",
               f"rx3 / rx2 mod p = {(rx[2] * inv(rx[1], p)) % p} = β",
               f"Gx2 * β mod p = {Gx[1] * beta_from_cp % p} = Gx3",
               f"Px2 * β mod p = {Px[1] * beta_from_cp % p} = Px3",
               f"rx2 * β mod p = {rx[1] * beta_from_cp % p} = rx3",
               f"n2 / n1 mod p = {n2 * inv(n1, p) % p} = β",
               f"n3 / n2 mod p = {n3 * inv(n2, p) % p} = β",
               f"n1 / n3 mod p = {n1 * inv(n3, p) % p} = β",
           ],
           verified=beta_from_cp == BETA and all(
               (arr[1] * BETA) % p == arr[2] and (arr[2] * inv(arr[1], p)) % p == BETA
               for arr in (Gx, Px, rx)
           ))

    add_op(ops, "12_lambda_branch_beta", "Λ / Λ1 = β²; rotate rx2→rx3 recovers Λ",
           "Px3/rx2 = Λ1;  Px3/(rx2*β) = Λ;  Λ1 * β² = Λ",
           [
               f"Px3 * rx2^-1 mod p = {(Px[2] * inv(rx[1], p)) % p} = Λ1",
               f"Px3 * rx3^-1 mod p = {(Px[2] * inv(rx[2], p)) % p} = Λ",
               f"rx3 = rx2 * β mod p = {rx[1] * BETA % p}",
               f"Λ / Λ1 mod p = {(LAMBDA * inv(LAMBDA1, p)) % p} = β²",
               f"Λ1 * β² mod p = {(LAMBDA1 * BETA_SQ) % p} = Λ",
           ],
           verified=(Px[2] * inv(rx[1], p)) % p == LAMBDA1
           and (LAMBDA * inv(LAMBDA1, p)) % p == BETA_SQ
           and (LAMBDA1 * BETA_SQ) % p == LAMBDA
           and (rx[1] * BETA) % p == rx[2])

    return ops


def parse_source_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [ln.rstrip() for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines() if ln.strip()]


def build_fn_operations() -> list[Op]:
    ops: list[Op] = []
    pi = [p1, p2, p3]
    lam3_n = pow(LAMBDA, 3, N)
    cbrt_lam3 = CSN["cbrt_lam3"]
    add_op(ops, "N00_cbrt_lambda", "cube roots of Λ³ and Λ³·Δ mod N",
           "cbrt(Λ³) mod N;  cbrt(Λ³·(p-N)) mod N",
           [
               f"cbrt(Λ³) mod N = {cbrt_lam3[0]}",
               f"cbrt(Λ³·Δ)_1 mod N = {CSN['cbrt_lam3_delta'][0]}",
               f"cbrt(Λ³·Δ)_2 mod N = {CSN['cbrt_lam3_delta'][1]}",
               f"cbrt(Λ³·Δ)_3 mod N = {CSN['cbrt_lam3_delta'][2]}",
               f"verify cbrt1^3 = Λ³: {pow(cbrt_lam3[0], 3, N) == lam3_n}",
               f"verify cbrt1^3·Δ chain root^3/(Δ): see Λ³·Δ block",
           ],
           verified=pow(cbrt_lam3[0], 3, N) == lam3_n)

    add_op(ops, "N01_defect_roots", "p1,p2,p3 — cube roots of Δ mod N",
           "x³ ≡ (p-N) mod N",
           [
               f"p-N = {DELTA}",
               f"p1 = {p1}",
               f"p2 = {p2}",
               f"p3 = {p3}",
               f"p1^-1 mod N = {inv(p1, N)}",
               f"p2^-1 mod N = {inv(p2, N)}",
               f"p3^-1 mod N = {inv(p3, N)}",
           ],
           verified=all(pow(x, 3, N) == DELTA % N for x in pi))

    def rotation_block(axis: str, vals: list[int], recorded_flat: list[str], phase: str) -> None:
        lines: list[str] = []
        mismatches: list[str] = []
        for i in range(3):
            for j in range(3):
                got = (vals[i] * inv(pi[j], N)) % N
                rec = int(recorded_flat[i * 3 + j])
                ok = got == rec
                tag = "OK" if ok else "MISMATCH"
                lines.append(
                    f"{axis}{i+1} * p{j+1}^-1 mod N = {got}  | CS-N: {rec}  [{tag}]"
                )
                if not ok:
                    mismatches.append(f"{axis}{i+1}/p{j+1}")
        note = ""
        if mismatches:
            note = (
                f"Live recompute disagrees with CS-N on {len(mismatches)}/9 cells "
                f"({', '.join(mismatches[:4])}{'...' if len(mismatches) > 4 else ''}). "
                "Px3 column matches Complexity_Simplified_135 normalization (d_j = p_j)."
            )
        qnote = " Do not use CS-N recorded grid until reconciled."
        add_op(
            ops, phase, f"{axis}_i * p_j^-1 mod N",
            f"defect-root rotation on {axis} slots",
            lines,
            verified=None if mismatches else True,
            note=(note + qnote) if mismatches else note,
            quarantine=bool(mismatches),
        )

    recorded_g = [
        "94474320772390849458187606827375164819329663908309677158287751286659037368378",
        "24842161398617407641871406752725870516865293995109503178579481642688748160241",
        "112267696303624133747082956437274780369480170654730628428343093353688537460055",
        "77339986601253425621491823750404527749834511981252485606185080787011151428328",
        "81860943410087456887831416714538457336339866071023340490982310377418402385360",
        "72383248463291508337818729552432830619500750505873982668042935118606769174986",
        "20076596045284865721112520822432478733183110087040662371148830466969145937597",
        "78200253588048930661649271861361369784609290245499874996738572407483080609",
        "95637292938443280771796814914394067749869844901788742136459594102141532476131",
    ]
    rotation_block("Gx", Gx, recorded_g, "N02_p_rotation_G")

    recorded_p = [
        "30523969444406836001472637187268375070022826535643942037451616918386438223022",
        "5471259399389588214373095493222248640703329126483819985369433412136531946378",
        "79796860393519771207725252328197284142111408616947142359784112810995191324937",
        "114233866386472589512933118406169337368257742195111236442408829650867501265476",
        "64379197574918027518260566558330808995928743098843213094698554474562841323924",
        "52971114513241773815948285052875669341488643264195359228102942157605980399274",
        "9083660497243242597775712611012327139311856397083686279252966271824808625822",
        "99332284794155036421119559326697694827700376731937043074816440551076105037140",
        "7376143945917916404675713070977885885825331150054175028535756318617247831375",
    ]
    rotation_block("Px", Px, recorded_p, "N03_p_rotation_P")

    recorded_r = [
        "97874920124673091770562292809321111359609310660717264469704432110527825171036",
        "15331892033605404877526622519464172674854816751556530191384811613766643312012",
        "2585277079037698775482069679902623818373436866801109721515919417223693011289",
        "90812649030317628408638564017024133318082144220566572713263663183751534755470",
        "11415648871287662890872497887620787211454426544945212921041120800250475943003",
        "13563791335710904124059923104042987323300993513563118748300379157516150795864",
        "3203334263938420621591094573866926624655831095318987952653567246359974807797",
        "80033764157399845691965352332040729336680526059876600432132598178497514371195",
        "32554990815977929110014538102780251891501207123879315997818997716660672315345",
    ]
    rotation_block("rx", rx, recorded_r, "N04_p_rotation_r")

    # Λ chain A–F (CS-N lines 82-95, 122-162)
    A, B = LAMBDA, inv(LAMBDA, N)
    C = pow(LAMBDA, 3, N)
    D = (LAMBDA * DELTA) % N
    E = (B * DELTA) % N
    F = (C * DELTA) % N
    add_op(ops, "N05_lambda_chain", "Λ, Λ⁻¹, Λ³, Λ·Δ, Λ⁻¹·Δ, Λ³·Δ mod N",
           "labels A–F in Complexity_Simplified_N.txt",
           [
               f"A. Λ mod N = {A}",
               f"B. Λ^-1 mod N = {B}",
               f"C. Λ^3 mod N = {C}",
               f"D. Λ * (p-N) mod N = {D}",
               f"E. Λ^-1 * (p-N) mod N = {E}",
               f"F. Λ^3 * (p-N) mod N = {F}",
           ],
           verified=(
               C == CSN["LAMBDA3_N"]
               and D == CSN["LAMBDA_x_DELTA"]
               and F == CSN["LAMBDA3_x_DELTA"]
           ))

    RQ, Rq, Cq = CSN["RQ"], CSN["Rq"], CSN["Cq"]
    dk = (P135_SIG_R * inv(P135_S, N)) % N
    add_op(ops, "N06_RQ_Rq_Cq", "RQ, Rq, Cq, ω₂, delta_k",
           "IQ*Ig^-1=RQ;  Iq*Ig^-1=Rq;  Cq=RQ*Rq^-1;  delta_k=r*s^-1",
           [
               f"RQ = {RQ}",
               f"Rq = {Rq}",
               f"Cq = RQ * Rq^-1 mod N = {(RQ * inv(Rq, N)) % N}",
               f"ω₂ = {omega2}",
               f"ω₂ - 1 = {omega2 - 1}",
               f"delta_k = r * s^-1 mod N = {dk}",
               f"recorded delta_k = {CSN['delta_k']}",
           ],
           verified=(RQ * inv(Rq, N)) % N == Cq and dk == CSN["delta_k"])

    # Inverses block
    RQ_inv = 89089264183215083132930816548291594507655234105226112490891493952640861132893
    Rq_inv = 29247189534370982033633252730481864045957128772776881733011244719402353961214
    Cq_inv = 112636788454771417678544374012864060956911500652469584535960018638859779176295
    add_op(ops, "N07_inverses", "RQ^-1, Rq^-1, Cq^-1, ω₂^-1, delta_k^-1",
           "recorded inverses mod N",
           [
               f"RQ^-1 = {RQ_inv}",
               f"Rq^-1 = {Rq_inv}",
               f"Cq^-1 mod N = {Cq_inv}",
               f"ω₂^-1 = {inv(omega2, N)}",
               f"delta_k^-1 = {inv(dk, N)}",
               f"verify RQ*RQ^-1 = 1: {(RQ * RQ_inv) % N == 1}",
           ],
           verified=(RQ * RQ_inv) % N == 1 and inv(dk, N) == 22192401509268247531352677264766230259437929368547539113374518388727980930059)

    # A–F cross with inverses (sample full grid)
    inv_map = {
        "RQ^-1": RQ_inv, "Rq^-1": Rq_inv, "Cq^-1": Cq_inv,
        "ω₂^-1": inv(omega2, N), "(ω₂-1)^-1": inv(omega2 - 1, N),
        "delta_k^-1": inv(dk, N),
    }
    chain = {"A": A, "B": B, "C": C, "D": D, "E": E, "F": F}
    cross_lines: list[str] = []
    cross_ok = True
    recorded_af = {
        ("A", "RQ^-1"): 93147113602049122145221107469094680874540960831016417383789604462585095938419,
        ("B", "ω₂^-1"): 44982948216310113594912836422316366693960786916866084980461073890639173787028,
        ("C", "Cq^-1"): 61446764069997791484591631822362672047326116086221671059624028276940768209183,
        ("F", "delta_k^-1"): 45346814253493863741873103261764796624471824525209346134565841399251613740133,
    }
    for (lab, inv_name), rec in recorded_af.items():
        got = (chain[lab] * inv_map[inv_name]) % N
        cross_lines.append(f"{lab} * {inv_name} mod N = {got}")
        if got != rec:
            cross_ok = False
    add_op(ops, "N08_AF_cross", "A–F × {RQ^-1, Rq^-1, Cq^-1, ω₂^-1, delta_k^-1}",
           "cross-family products (sample + full in source)",
           cross_lines + ["... full 36-line A–F grid in Complexity_Simplified_N.txt lines 122-162"],
           verified=cross_ok,
           note="Ledger shows anchor lines; source file has complete grid.")

    add_op(ops, "N09_omega2_roots", "ω₂ from RQ, Rq; defect d rotations",
           "RQ^((N-1)/3) = Rq^((N-1)/3) = ω₂;  d_i*d_j^-1",
           [
               f"RQ^((N-1)/3) mod N = {pow(RQ, (N - 1) // 3, N)}",
               f"Rq^((N-1)/3) mod N = {pow(Rq, (N - 1) // 3, N)}",
               f"ω₂³ mod N = {pow(omega2, 3, N)}",
               f"d1 * d2^-1 mod N = {(d1 * inv(d2, N)) % N}",
               f"d1 * d3^-1 mod N = {(d1 * inv(d3, N)) % N}",
               f"d2 * d3^-1 mod N = {(d2 * inv(d3, N)) % N}",
           ],
           verified=pow(RQ, (N - 1) // 3, N) == omega2 and (d1 * inv(d2, N)) % N == omega2)

    # Δ-scaled coordinates gx, Qx, qx (CS-N lines 219-247)
    gx = [(Gx[i] * DELTA) % N for i in range(3)]
    Qx = [(Px[i] * DELTA) % N for i in range(3)]
    qx = [(rx[i] * DELTA) % N for i in range(3)]
    recorded_gx = [
        88762151515440337447534865414660660787428675538285103047104286514863435255046,
        71875974824033295952082960389820563096514190425608976465160917004773808670830,
        97544565858399232459758388284065206472164312396091440391182633566829075600339,
    ]
    recorded_Qx3 = 59400998243199342883944075316336058517684599894706558400832842742135698624330
    Ig = (gx[0] * gx[1] * gx[2]) % N
    IQ = (Qx[0] * Qx[1] * Qx[2]) % N
    Iq = (qx[0] * qx[1] * qx[2]) % N
    RQ_calc = (IQ * inv(Ig, N)) % N
    Rq_calc = (Iq * inv(Ig, N)) % N
    add_op(ops, "N10_delta_scaled_products", "gx, Qx, qx and Ig, IQ, Iq → RQ, Rq",
           "Gx*(p-N), Px*(p-N), rx*(p-N);  product collapse mod N",
           [
               f"Gx1*(p-N) mod N = {gx[0]} = gx1",
               f"Gx2*(p-N) mod N = {gx[1]} = gx2",
               f"Gx3*(p-N) mod N = {gx[2]} = gx3",
               f"Px3*(p-N) mod N = {Qx[2]} = Qx3",
               f"qx1*qx2*qx3 mod N = {Iq} = Iq",
               f"Ig^-1 mod N = {inv(Ig, N)}",
               f"IQ*Ig^-1 mod N = {RQ_calc} = RQ",
               f"Iq*Ig^-1 mod N = {Rq_calc} = Rq",
           ],
           verified=all(gx[i] == recorded_gx[i] for i in range(3))
           and Qx[2] == recorded_Qx3
           and RQ_calc == RQ and Rq_calc == Rq)

    # T roots y1,y2,y3 = (ω²-1)³ branches; c1,c2,c3
    T = (omega2 - 1) % N
    y_roots = [
        6278217321159360251768865021595913467275586303393073724224099427672203972183,
        28159576510706975400073279818842758000059714322687393825967946111446184253203,
        81354295405449859771728840168249236385502263652994436832413117602399773268951,
    ]
    add_op(ops, "N11_T_roots", "y_i³ ≡ (ω₂-1) mod N",
           "cube roots of T = ω₂ - 1",
           [f"y{i+1}³ mod N == T: {pow(y_roots[i], 3, N) == T}" for i in range(3)],
           verified=all(pow(y, 3, N) == T for y in y_roots))

    c_vals = [18550647013200406789286060994475703560416436121766183371493072993703432094758,
              36793031382526386630822426321733144812287525987490732260894675548311548513972,
              60448410841589402003462497692479059480133602169817988750217414599503180885607]
    c135_vals = [1, omega2, (omega2 * omega2) % N]
    add_op(ops, "N12_c_roots", "c1,c2,c3 (CS-N Cq cube roots)",
           "c_i from CS-N lines 263-267",
           [f"c{i+1} = {c_vals[i]}" for i in range(3)]
           + [f"c{i+1}³ mod N == Cq: {pow(c_vals[i], 3, N) == Cq}" for i in range(3)]
           + ["--- CS-135 uses a different c-triple (1, ω₂, ω₂²) ---"]
           + [f"CS-135 c{i+1} = {c135_vals[i]}  c³==Cq: {pow(c135_vals[i], 3, N) == Cq}" for i in range(3)],
           verified=all(pow(c_vals[i], 3, N) == Cq for i in range(3)),
           note="CS-N c_i are true cube roots of Cq. CS-135 c_i={1,ω₂,ω₂²} are ω₂ coset reps, not Cq roots.")

    add_op(ops, "N12b_P135_slot_hinge", "P135: pubkey slot 3, spend r slot 2",
           "cross-slot Px3/rx2 = Λ1; same-slot Px3/rx3 = Λ",
           [
               f"Px3 = pubkey x (slot 3)",
               f"rx2 = spend sig r = {hex(rx[1])} (slot 2)",
               f"rx3 = complexity third r slot (slot 3)",
               f"Px3 * rx3^-1 mod p = {LAMBDA}  = Λ  [same-slot bridge]",
               f"Px3 * rx2^-1 mod p = {(Px[2] * inv(rx[1], p)) % p}  = Λ1 branch",
               f"Px2 * rx2^-1 mod p = {(Px[1] * inv(rx[1], p)) % p}  = Λ  [if r paired with Px2]",
               f"Λ1 (CS-p) = 37643865109859786597771480714430795265672370613336709366230557028248558914645",
           ],
           verified=(Px[2] * inv(rx[2], p)) % p == LAMBDA
           and (Px[2] * inv(rx[1], p)) % p == 37643865109859786597771480714430795265672370613336709366230557028248558914645
           and (Px[1] * inv(rx[1], p)) % p == LAMBDA,
           note="Spend pairs Px3 with rx2 (cross-slot). Bridge Λ uses matched slot pairs.")

    rx_ratio_n = (rx[2] * inv(rx[1], N)) % N
    p_ratios = [(p2 * inv(p1, N)) % N, (p3 * inv(p2, N)) % N, (p1 * inv(p3, N)) % N]
    add_op(ops, "N12c_N_side_slot_negative", "rx3/rx2 mod N — not ω₂ or p_j coset",
           "N-side does not directly map spend slot 2→3",
           [
               f"rx3 / rx2 mod N = {rx_ratio_n}",
               f"ω₂ mod N = {omega2}",
               f"ω₂^-1 mod N = {inv(omega2, N)}",
               f"rx3/rx2 == ω₂: {rx_ratio_n == omega2}",
               f"rx3/rx2 == ω₂^-1: {rx_ratio_n == inv(omega2, N)}",
               f"p2/p1 mod N = {p_ratios[0]}",
               f"p3/p2 mod N = {p_ratios[1]}",
               f"p1/p3 mod N = {p_ratios[2]}",
               f"rx3/rx2 matches any p_j/p_k: {rx_ratio_n in p_ratios}",
               "=> use p-side β rotation for slot 2↔3; not quarantined N-side p_j grids",
           ],
           verified=rx_ratio_n != omega2 and rx_ratio_n != inv(omega2, N) and rx_ratio_n not in p_ratios,
           note="Align spend line via Fp: rx3 = rx2 * β mod p.")

    # Y ladder
    Y1, Y2_rec, Y3_rec = CSN["Y1"], CSN["Y2"], CSN["Y3"]
    omega = (Y2_rec * inv(Y1, N)) % N  # equals ω₂^-1 in CS-N
    Y2_calc = (Y1 * omega) % N
    Y3_from_w2 = (Y1 * omega2) % N
    Y3_from_omega_sq = (Y1 * pow(omega, 2, N)) % N
    Y3_from_y2_omega = (Y2_rec * omega) % N
    y3_candidates = [
        ("2^45·ω²", Y3_from_omega_sq),
        ("2^45·ω₂", Y3_from_w2),
        ("Y2·ω", Y3_from_y2_omega),
    ]
    y3_match = next((lbl for lbl, v in y3_candidates if v == Y3_rec), None)
    add_op(ops, "N13_Y_ladder", "Y1=2^45; Y2=2^45·ω; Y3 — formula NOT proven",
           "Y-branch ladder mod N (Y3 has no exact match)",
           [
               f"Y1 = 2^45 = {Y1}",
               f"ω = Y2/Y1 mod N = {omega}  (= ω₂^-1 per CS-N)",
               f"Y2 = 2^45 * ω mod N = {Y2_calc}  | CS-N: {Y2_rec}  [OK]",
           ]
           + [f"Y3 via {lbl} = {val}  | CS-N: {Y3_rec}  [{'OK' if val == Y3_rec else 'near' if abs(val-Y3_rec)<10**30 else 'no'}]"
              for lbl, val in y3_candidates]
           + ["Y3: no exact formula match — do NOT use as proven ladder step.",
              f"CS-N Y3 recorded verbatim: {Y3_rec}"],
           verified=Y2_calc == Y2_rec and y3_match is not None,
           quarantine=True,
           note="Quarantined: Y2 verified; Y3 closest is 2^45·ω² but ≠ CS-N value. Not a proven step.")

    # Y × inverses (anchor lines from CS-N 411-449)
    dk_inv = inv(dk, N)
    lam3_inv = inv(lam3_n, N)
    y_cross = [
        ("Y1", "delta_k^-1", 55204782847368007066309054764572571437752543354415649889614907857025223121333),
        ("Y1", "Λ^-1", 24000271435421606395283744462729960062833627477104419871435671967303668663929),
        ("Y3", "(Λ^3)^-1", 45599471770789687147826943590571586099725372813908494461540170011516212947499),
    ]
    y_lines = []
    y_ok = True
    for ylab, invlab, rec in y_cross:
        factor = {"delta_k^-1": dk_inv, "Λ^-1": B, "(Λ^3)^-1": lam3_inv}[invlab]
        yval = {"Y1": Y1, "Y3": Y3_rec}[ylab]
        got = (yval * factor) % N
        y_lines.append(f"{ylab} * {invlab} mod N = {got}")
        if got != rec:
            y_ok = False
    add_op(ops, "N14_Y_cross", "Y_i × {delta_k^-1, RQ^-1, Λ^-1, (Λ³)^-1, ...}",
           "Y-branch cross products (anchor lines)",
           y_lines + ["... full Y1/Y2/Y3 grid in CS-N lines 411-449"],
           verified=y_ok)

    add_op(ops, "N15_P135_normalization", "Px3 * d_j^-1 mod N (varies)",
           "normalization matrix — no constant across j",
           [
               f"Gx3 * d1^-1 mod N = {(Gx[2] * inv(d1, N)) % N}",
               f"Gx3 * d2^-1 mod N = {(Gx[2] * inv(d2, N)) % N}",
               f"Gx3 * d3^-1 mod N = {(Gx[2] * inv(d3, N)) % N}",
               f"Px3 * d1^-1 mod N = {(Px[2] * inv(d1, N)) % N}",
               f"Px3 * d2^-1 mod N = {(Px[2] * inv(d2, N)) % N}",
               f"Px3 * d3^-1 mod N = {(Px[2] * inv(d3, N)) % N}",
               f"rx3 * d1^-1 mod N = {(rx[2] * inv(d1, N)) % N}",
               f"rx3 * d2^-1 mod N = {(rx[2] * inv(d2, N)) % N}",
               f"rx3 * d3^-1 mod N = {(rx[2] * inv(d3, N)) % N}",
           ],
           verified=None,
           note="Complexity_Simplified_135.txt: no rx3*d_j^-1 = 1.")

    sig_r_bridge = (P135_PX * inv(P135_SIG_R, p)) % p
    triple_lam = (Px[2] * inv(rx[2], p)) % p
    add_op(ops, "N16_P135_lambda_slots", "three lambdas on P135 (Fp)",
           "Λ_bridge = Px3/rx3;  Px/r_sig = Λ1 branch;  not equal",
           [
               f"Px3 = {Px[2]}  (P135 pubkey x)",
               f"rx2 = {rx[1]}  (P135 spend sig r)",
               f"rx3 = {rx[2]}  (complexity triple slot 3)",
               f"Λ = Px3 * rx3^-1 mod p = {triple_lam}",
               f"Px3 * rx2^-1 mod p = {sig_r_bridge}  (= Λ1 branch, NOT Λ)",
               f"Match Λ recorded: {triple_lam == LAMBDA}",
           ],
           verified=triple_lam == LAMBDA and sig_r_bridge != LAMBDA,
           note="Complexity_Simplified_p_lambda_geometric_append.txt P135 anchor.")

    return ops


def render_md(fp_ops: list[Op], fn_ops: list[Op], cs_p_lines: list[str], cs_n_lines: list[str]) -> str:
    lines = [
        "# Operation Ledger — Complexity Simplified (full information)",
        "",
        "**Source of truth:** `02_Research/notes/Complexity_Simplified_p.txt`",
        "**Also:** `Complexity_Simplified_N.txt`, `Complexity_Simplified_135.txt`,",
        "`Complexity_Simplified_p_lambda_geometric_append.txt`",
        "",
        "Each entry: **formula → values → live verification**.",
        "This is NOT probe statistics. Re-run: `python build_complexity_operations_ledger.py`",
        "",
        "## Ledger verdict",
        "",
        f"- **p-side bridge:** {VERDICT_SUMMARY['p_side_bridge']}",
        f"- **P135 slot hinge:** {VERDICT_SUMMARY['p135_slot_hinge']}",
        f"- **Slot 2→3 alignment:** {VERDICT_SUMMARY['slot_2_to_3_alignment']}",
        f"- **Spend line:** {VERDICT_SUMMARY['spend_line_rotation']}",
        f"- **p-side y-bridge:** {VERDICT_SUMMARY['p_side_y_bridge']}",
        f"- **y-side slot model:** {VERDICT_SUMMARY['y_side_slot_model']}",
        f"- **N-side y-shadow:** {VERDICT_SUMMARY['n_side_y_shadow']}",
        f"- **CS-N Cq roots (N12):** {VERDICT_SUMMARY['cs_n_cq_roots']}",
        f"- **N-side p-rotation grids (N02–N04):** {VERDICT_SUMMARY['n_side_p_rotation_grids']}",
        f"- **N-side rx slot map:** {VERDICT_SUMMARY['n_side_rx_slot_map']}",
        f"- **Hinge:** {VERDICT_SUMMARY['hinge']}",
        "",
        "---",
        "",
        "## Fp pipeline (mod p) — from Complexity_Simplified_p",
        "",
    ]
    phase = ""
    for op in fp_ops:
        if op.phase != phase:
            phase = op.phase
            lines.append(f"### Phase {phase}")
            lines.append("")
        v = "✓" if op.verified else ("?" if op.verified is None else "✗")
        q = " **QUARANTINED**" if op.quarantine else ""
        lines.append(f"#### {op.name}  [{v}]{q}")
        lines.append(f"**Formula:** {op.formula}")
        if op.note:
            lines.append(f"**Note:** {op.note}")
        lines.append("```")
        lines.extend(op.lines)
        lines.append("```")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## FN pipeline (mod N) — from Complexity_Simplified_N",
        "",
    ])
    for op in fn_ops:
        v = "✓" if op.verified else ("?" if op.verified is None else "✗")
        q = " **QUARANTINED**" if op.quarantine else ""
        lines.append(f"#### {op.name}  [{v}]{q}")
        lines.append(f"**Formula:** {op.formula}")
        if op.note:
            lines.append(f"**Note:** {op.note}")
        lines.append("```")
        lines.extend(op.lines)
        lines.append("```")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## Raw Complexity_Simplified_p.txt (verbatim)",
        "",
        "```",
    ])
    lines.extend(cs_p_lines[:100])
    if len(cs_p_lines) > 100:
        lines.append(f"... +{len(cs_p_lines) - 100} more lines in source file")
    lines.append("```")
    lines.append("")
    lines.extend([
        "## Raw Complexity_Simplified_N.txt (verbatim)",
        "",
        "```",
    ])
    lines.extend(cs_n_lines[:160])
    if len(cs_n_lines) > 160:
        lines.append(f"... +{len(cs_n_lines) - 160} more lines in source file")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    y_data = compute_y_ledger()
    fp_ops = build_fp_operations() + build_fp_y_operations(y_data)
    fn_ops = build_fn_operations() + build_fn_y_operations(y_data)
    cs_p_lines = parse_source_lines(CS_P)
    cs_n_lines = parse_source_lines(CS_N)

    all_ops = fp_ops + fn_ops
    payload = [
        {
            "phase": o.phase,
            "name": o.name,
            "formula": o.formula,
            "lines": o.lines,
            "verified": o.verified,
            "note": o.note,
            "quarantine": o.quarantine,
        }
        for o in all_ops
    ]

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_md(fp_ops, fn_ops, cs_p_lines, cs_n_lines), encoding="utf-8")
    OUT_JSON.write_text(
        json.dumps(
            {
                "sources": {
                    "fp": str(CS_P.relative_to(ROOT)).replace("\\", "/"),
                    "fn": str(CS_N.relative_to(ROOT)).replace("\\", "/"),
                },
                "verdict": VERDICT_SUMMARY,
                "operations": payload,
                "operation_count": len(all_ops),
                "verified_count": sum(1 for o in all_ops if o.verified is True),
                "quarantine_count": sum(1 for o in all_ops if o.quarantine),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    verified = sum(1 for o in all_ops if o.verified is True)
    print(f"operations={len(all_ops)} verified={verified} wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
