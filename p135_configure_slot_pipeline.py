#!/usr/bin/env python3
"""P135 extended: slots 1-3, wide RSZ stride, d0 offset, cross-slot beta walks."""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
DELTA = p - N
EXP = 135
LO, HI = 1 << 134, (1 << 135) - 1
STRIDE_HALF = 300
STRIDE_WIDE = 10_000  # slot-3 RSZ k-line only

# P135 RSZ (r = rx2 slot-2, not pubkey Px3)
R_SIG = 90653255469745952335985143920649543885181555095025199315947044135806663628368
S_SIG = 15509729875763924304053419655647994379903175655107184284998698212653288468986
Z_SIG = 66278737796829840734606014530466656889790152192829793669891337810330530090951
INV_R_SIG = pow(R_SIG, -1, N)
DELTA_K = (R_SIG * pow(S_SIG, -1, N)) % N
INV_DELTA_K = pow(DELTA_K, -1, N)
D0 = (-Z_SIG * INV_R_SIG) % N  # d0 = -z*r^-1

RSZ_JSON = Path(__file__).resolve().parent / (
    "ARCHIVE/briefcase/The Real Decimal/P135/rsz_courtroom.json"
)

Gx = {
    1: 91177636130617246552803821781935006617134368061721227770777272682868638699771,
    2: 55066263022277343669578718895168534326250603453777594175500187360389116729240,
    3: 85340279321737800624759429340272274763154997815782306132637707972559913914315,
}
Px = {
    1: 51866120889717641461810659005716431188799022756838843706514074509901265629059,
    2: 54715131853151445691733189261594605794679177894602772031317532630299444965014,
    3: 9210836494447108270027136741376870869791784014198948301625976867708124077590,
}
rx = {
    1: 114930704126154877082883546730544079307369404418439078397954295509919169851219,
    2: 90653255469745952335985143920649543885181555095025199315947044135806663628368,
    3: 26000218878731561428273279366182192513989009817816850365013828370091835863739,
}
n_slot = {
    1: 59918213076871302850696965052278348370805334183656907928308327240635173121259,
    2: 79196589282660987520076475805787536662716643115069436220061826482331618169130,
    3: 92469376115100100476368529159309930673017992032554783930545014292850878052937,
}
d_defect = {
    1: 1248780847746852317428964695904392891045016528862400526454142780194939123483,
    2: 21551977082208859489759061364299864038123955443494189974630776168682352336746,
    3: 92991331307360483616382958948483650923668592306718313881520244192640870034108,
}
G_BRIDGE = {
    "A": 72789842462919254798787184333665945456600870881042555899576743439227206827139,
    "B": 5413323970105506090398366098172752697370300495141572731819943140721401835677,
    "C": 37588922804291434534385434576849209699298813289456435408060897427960226008847,
}

LAMBDA = 97451685862885086182458552040892158509924235661624603229050850812487253689501
CP1 = 57602015833677736603574291432760600960685355547305560147555835666458430710854
CR1 = 73680319372475906803320245449080571569331871474977252785503402279627244902569
BETA = 55594575648329892869085402983802832744385952214688224221778511981742606582254
BETA_SQ = pow(BETA, 2, p)
GEN_X = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798

TARGET_PUBKEY = bytes.fromhex(
    "02145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16"
)
TARGET_HASH160 = hashlib.new("ripemd160", hashlib.sha256(TARGET_PUBKEY).digest()).digest()
TARGET_X = Px[3]
G_PAIR = {1: "A", 2: "C", 3: "B"}


@dataclass
class CheckResult:
    label: str
    value: int
    hash_match: bool
    pubkey_x_match: bool


def d_from_k(k: int) -> int:
    return ((S_SIG * (k % N) - Z_SIG) * INV_R_SIG) % N


def in_band(k: int) -> bool:
    return LO <= (k % N) <= HI


def band_folds(k: int) -> list[tuple[str, int]]:
    k = k % N
    out: list[tuple[str, int]] = []
    seen: set[int] = set()

    def add(tag: str, v: int) -> None:
        v = v % N
        if v in seen or not (LO <= v <= HI):
            return
        seen.add(v)
        out.append((tag, v))

    add("as-is", k)
    add("mod2^135", k % (1 << 135))
    add("mod2^135|2^134", (k % (1 << 135)) | (1 << 134))
    if k.bit_length() > 135:
        add(">>excess", k >> (k.bit_length() - 135))
    for t in range(1, 4):
        add(f"-{t}N", k - t * N)
    return out


def check_scalar(label: str, k: int) -> CheckResult | None:
    k = k % N
    if not in_band(k):
        return None
    sk = SigningKey.from_secret_exponent(k, curve=SECP256k1, hashfunc=hashlib.sha256)
    raw = sk.get_verifying_key().to_string()
    x = int.from_bytes(raw[:32], "big")
    y_int = int.from_bytes(raw[32:], "big")
    pub = (b"\x02" if y_int % 2 == 0 else b"\x03") + raw[:32]
    h = hashlib.new("ripemd160", hashlib.sha256(pub).digest()).digest()
    return CheckResult(label, k, h == TARGET_HASH160, x == TARGET_X)


def px_candidates(slot: int) -> list[tuple[str, int]]:
    i = slot
    qx = (Px[i] * DELTA) % N
    qrx = (rx[i] * DELTA) % N
    return [
        (f"s{slot}/rx{i}", rx[i] % N),
        (f"s{slot}/rx{i}L^-1", (rx[i] * pow(LAMBDA, -1, N)) % N),
        (f"s{slot}/Px{i}d1^-1", (Px[i] * pow(d_defect[1], -1, N)) % N),
        (f"s{slot}/Px{i}d2^-1", (Px[i] * pow(d_defect[2], -1, N)) % N),
        (f"s{slot}/Px{i}d3^-1", (Px[i] * pow(d_defect[3], -1, N)) % N),
        (f"s{slot}/rx{i}d1^-1", (rx[i] * pow(d_defect[1], -1, N)) % N),
        (f"s{slot}/rx{i}d2^-1", (rx[i] * pow(d_defect[2], -1, N)) % N),
        (f"s{slot}/rx{i}d3^-1", (rx[i] * pow(d_defect[3], -1, N)) % N),
        (f"s{slot}/Qx{i}", qx),
        (f"s{slot}/qx{i}", qrx),
        (f"s{slot}/Qx{i}d3^-1", (qx * pow(d_defect[3], -1, N)) % N),
    ]


def gx_candidates(slot: int) -> list[tuple[str, int]]:
    i = slot
    gx = (Gx[i] * DELTA) % N
    gk = G_PAIR[i]
    return [
        (f"s{slot}/Gx{i}", Gx[i] % N),
        (f"s{slot}/gx{i}", gx),
        (f"s{slot}/Gx{i}d1^-1", (Gx[i] * pow(d_defect[1], -1, N)) % N),
        (f"s{slot}/Gx{i}d2^-1", (Gx[i] * pow(d_defect[2], -1, N)) % N),
        (f"s{slot}/Gx{i}d3^-1", (Gx[i] * pow(d_defect[3], -1, N)) % N),
        (f"s{slot}/gx{i}d1^-1", (gx * pow(d_defect[1], -1, N)) % N),
        (f"s{slot}/gx{i}d2^-1", (gx * pow(d_defect[2], -1, N)) % N),
        (f"s{slot}/gx{i}d3^-1", (gx * pow(d_defect[3], -1, N)) % N),
        (f"s{slot}/gx{i}G{gk}^-1", (gx * pow(G_BRIDGE[gk], -1, N)) % N),
        (f"s{slot}/n{i}", n_slot[i] % N),
        (f"s{slot}/n{i}d3^-1", (n_slot[i] * pow(d_defect[3], -1, N)) % N),
    ]


def section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def run_d_scan(hits: list[CheckResult], items: list[tuple[str, int]], use_folds: bool = True) -> int:
    checked = 0
    for label, d in items:
        candidates = band_folds(d) if use_folds else [("direct", d)]
        for tag, val in candidates:
            res = check_scalar(f"{label}::{tag}", val)
            if res is None:
                continue
            checked += 1
            if res.hash_match:
                print(f"  *** MATCH *** {res.label} d={res.value}")
                hits.append(res)
    return checked


def collect_anchors(raw: list[tuple[str, int]]) -> list[tuple[str, int]]:
    seen: set[int] = set()
    out: list[tuple[str, int]] = []
    for lbl, v in raw:
        for tag, folded in band_folds(v):
            if folded in seen:
                continue
            seen.add(folded)
            out.append((f"{lbl}::{tag}", folded))
    return out


def iter_rsz_k_stride(anchor_k: int, half: int, step: int = 1):
    anchor_k = anchor_k % N
    for t in range(-half, half + 1, step):
        k = (anchor_k + t * DELTA_K) % N
        yield t, k, d_from_k(k)


def main() -> None:
    section("RSZ + ORBIT SETUP")
    print(f"r_sig == rx2: {R_SIG == rx[2]}")
    print(f"r_sig == Px3: {R_SIG == Px[3]}")
    print(f"rx3 == rx2*beta mod p: {(rx[2] * BETA) % p == rx[3]}")
    print(f"Px3 == Px2*beta mod p: {(Px[2] * BETA) % p == Px[3]}")
    print(f"delta_k = r*s^-1: verified")
    print(f"d0 = -z*r^-1 = {D0}")

    all_raw: list[tuple[str, int]] = []
    slot3_raw: list[tuple[str, int]] = []
    slot2_raw: list[tuple[str, int]] = []
    for slot in (1, 2, 3):
        px = [(f"Px/{n}", v) for n, v in px_candidates(slot)]
        gx = [(f"Gx/{n}", v) for n, v in gx_candidates(slot)]
        all_raw += px + gx
        if slot == 3:
            slot3_raw = px + gx
        if slot == 2:
            slot2_raw = px + gx

    hits: list[CheckResult] = []

    section("PHASE 1 — band-fold scan (all slots)")
    n1 = run_d_scan(hits, all_raw)
    print(f"  EC checks: {n1}, matches: {len(hits)}")

    section("PHASE 2 — RSZ d_from_k on courtroom k_candidates")
    k_list: list[int] = []
    if RSZ_JSON.exists():
        data = json.loads(RSZ_JSON.read_text(encoding="utf-8"))
        for rec in data.get("k_candidates", []):
            k_list.append(int(rec["k"]))
        print(f"  Loaded {len(k_list)} k_candidates from rsz_courtroom.json")
    else:
        print("  rsz_courtroom.json not found — skipping")
    rsz_items = [(f"rsz/k{i}", d_from_k(k)) for i, k in enumerate(k_list)]
    n2 = run_d_scan(hits, rsz_items, use_folds=True)
    print(f"  EC checks: {n2}, matches: {len(hits)}")

    section("PHASE 3 — wide RSZ k-stride (+/-10000) on slot-3 anchors")
    s3_anchors = collect_anchors(slot3_raw)
    print(f"  Slot-3 band-folded anchors: {len(s3_anchors)}")
    wide_items: list[tuple[str, int]] = []
    for lbl, anchor in s3_anchors:
        for t, k, d in iter_rsz_k_stride(anchor, STRIDE_WIDE):
            wide_items.append((f"{lbl}/k{t:+d}", d))
    print(f"  d values from k-stride: {len(wide_items)}")
    n3 = run_d_scan(hits, wide_items, use_folds=True)
    print(f"  EC checks: {n3}, matches: {len(hits)}")

    section("PHASE 4 — d0 offset + Delta_d from anchors")
    d0_items: list[tuple[str, int]] = []
    for lbl, anchor in collect_anchors(all_raw):
        delta_d = (anchor * INV_DELTA_K) % N
        d0_items.append((f"{lbl}/d0+Δd", (D0 + delta_d) % N))
        d0_items.append((f"{lbl}/d0-Δd", (D0 - delta_d) % N))
    # also stride d0 + t for small window
    for t in range(-STRIDE_HALF, STRIDE_HALF + 1):
        d0_items.append((f"d0+{t}", (D0 + t) % N))
    n4 = run_d_scan(hits, d0_items, use_folds=True)
    print(f"  EC checks: {n4}, matches: {len(hits)}")

    section("PHASE 5 — cross-slot beta walks (slot2 -> slot3)")
    cross_items: list[tuple[str, int]] = []
    s2_anchors = collect_anchors(slot2_raw)
    print(f"  Slot-2 anchors: {len(s2_anchors)}")
    for lbl, v2 in s2_anchors:
        # p-side beta lift then N reduce
        for name, coord in [
            ("v2*Bp", (v2 * BETA) % p),
            ("v2*Bp2", (v2 * BETA_SQ) % p),
            ("v2*Bn", (v2 * BETA) % N),
            ("v2*Bn2", (v2 * BETA_SQ) % N),
            ("v2*CP1", (v2 * CP1) % N),
        ]:
            cross_items.append((f"{lbl}/{name}", coord % N))
            cross_items.append((f"{lbl}/{name}->d", d_from_k(coord)))
        # RSZ stride from slot2 anchor on k-line, map via beta on k
        for t in range(-STRIDE_HALF, STRIDE_HALF + 1):
            k2 = (v2 + t * DELTA_K) % N
            k3 = (k2 * BETA) % N
            k3b = (k2 * BETA) % p
            cross_items.append((f"{lbl}/k2{t}->k3b", d_from_k(k3b)))
            cross_items.append((f"{lbl}/k2{t}->k3n", d_from_k(k3)))
    n5 = run_d_scan(hits, cross_items)
    print(f"  EC checks: {n5}, matches: {len(hits)}")

    section("PHASE 6 — narrow RSZ k-stride (+/-300) all anchors")
    narrow_items: list[tuple[str, int]] = []
    for lbl, anchor in collect_anchors(all_raw):
        for t, k, d in iter_rsz_k_stride(anchor, STRIDE_HALF):
            narrow_items.append((f"{lbl}/k{t:+d}", d))
    n6 = run_d_scan(hits, narrow_items, use_folds=True)
    print(f"  EC checks: {n6}, matches: {len(hits)}")

    section("SUMMARY")
    print(f"Pubkey: Px3, signature r: rx2 (slot 2)")
    print(f"Total HASH160 matches: {len(hits)}")
    if hits:
        for h in hits:
            print(f"  FOUND d = {h.value} ({h.label})")
    else:
        print("No d found — RSZ stride + cross-slot + d0 offset exhausted for current anchors.")


if __name__ == "__main__":
    main()
