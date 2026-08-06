#!/usr/bin/env python3
"""Compare x^135 root orbits mod p vs mod N — rotation / cube-root-of-unity structure."""
from __future__ import annotations

import hashlib
import math

from ecdsa import SECP256k1, SigningKey

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
EXP = 135
LO, HI = 1 << 134, (1 << 135) - 1

BETA = 55594575648329892869085402983802832744385952214688224221778511981742606582254
OMEGA_P = BETA  # primitive cube root of unity mod p
OMEGA_P_SQ = pow(OMEGA_P, 2, p)
OMEGA_N = 37718080363155996902926221483475020450927657555482586988616620542887997980018
OMEGA_N_SQ = pow(OMEGA_N, 2, N)

rx = [114930704126154877082883546730544079307369404418439078397954295509919169851219,
      90653255469745952335985143920649543885181555095025199315947044135806663628368,
      26000218878731561428273279366182192513989009817816850365013828370091835863739]

# Prior mod p downloads: x^135 ≡ a (mod p)
PX_P = [51866120889717641461810659005716431188799022756838843706514074509901265629059,
        54715131853151445691733189261594605794679177894602772031317532630299444965014,
        9210836494447108270027136741376870869791784014198948301625976867708124077590]
GX_P = [55066263022277343669578718895168534326250603453777594175500187360389116729240,
        85340279321737800624759429340272274763154997815782306132637707972559913914315,
        91177636130617246552803821781935006617134368061721227770777272682868638699771]

# NEW screenshot 15-31-19 mod p: x^135 ≡ rx2^135 (mod p)  -> roots ARE rx3,rx2,rx1
A_RX2_P = pow(rx[1], EXP, p)
RX_P = [rx[2], rx[1], rx[0]]  # Wolfram order: rx3, rx2, rx1

# NEW screenshot 15-41-22 mod N: x^135 ≡ rx2^135 (mod N)
A_RX2_N = pow(rx[1], EXP, N)
RX_N = [4295241207732992648834070171909958737418321088245693014740872866482121928576,
        20843592559837250438751770916128405230237688095804012051917246139229375937393,
        rx[1]]


def ratios(roots: list[int], mod: int) -> dict[str, int]:
    r1, r2, r3 = roots
    return {
        "r2/r1": (r2 * pow(r1, -1, mod)) % mod,
        "r3/r1": (r3 * pow(r1, -1, mod)) % mod,
        "r3/r2": (r3 * pow(r2, -1, mod)) % mod,
    }


def verify(name: str, roots: list[int], residue: int, mod: int) -> dict[str, int]:
    print(f"\n--- {name} ---")
    print(f"  gcd(135, mod-1) = {math.gcd(EXP, mod - 1)}")
    print(f"  residue a = {residue}")
    for i, r in enumerate(roots, 1):
        print(f"  root{i}: {r}")
        print(f"    root{i}^135 == a: {pow(r, EXP, mod) == residue}")
    rat = ratios(roots, mod)
    for k, v in rat.items():
        print(f"  {k} = {v}")
    if mod == p:
        print(f"  r2/r1 == beta:     {rat['r2/r1'] == OMEGA_P}")
        print(f"  r2/r1 == beta^2:   {rat['r2/r1'] == OMEGA_P_SQ}")
        print(f"  r3/r1 == beta^2:   {rat['r3/r1'] == OMEGA_P_SQ}")
    else:
        print(f"  r2/r1 == omega_N:  {rat['r2/r1'] == OMEGA_N}")
        print(f"  r3/r1 == omega_N^2:{rat['r3/r1'] == OMEGA_N_SQ}")
    return rat


def check_band_d(label: str, k: int) -> bool:
    k %= N
    if not (LO <= k <= HI):
        return False
    sk = SigningKey.from_secret_exponent(k, curve=SECP256k1, hashfunc=hashlib.sha256)
    raw = sk.get_verifying_key().to_string()
    pub = (b"\x02" if int.from_bytes(raw[32:], "big") % 2 == 0 else b"\x03") + raw[:32]
    th = hashlib.new("ripemd160", hashlib.sha256(pub).digest()).digest()
    target = hashlib.new("ripemd160", hashlib.sha256(
        bytes.fromhex("02145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16")
    ).digest()).digest()
    if th == target:
        print(f"  *** MATCH *** {label} d={k}")
        return True
    return False


def main() -> None:
    print("=" * 80)
    print("x^135 ROOT ORBITS — mod p (field) vs mod N (scalar)")
    print("=" * 80)

    rp = verify("Px orbit mod p (prior)", PX_P, pow(PX_P[0], EXP, p), p)
    rg = verify("Gx orbit mod p (prior)", GX_P, pow(GX_P[0], EXP, p), p)
    rrxp = verify("rx orbit mod p (NEW 15-31-19: x^135 == rx2^135)", RX_P, A_RX2_P, p)
    rrxn = verify("rx2^135 orbit mod N (NEW 15-41-22)", RX_N, A_RX2_N, N)

    print("\n" + "=" * 80)
    print("ROTATION CONSTANT TABLE")
    print("=" * 80)
    print(f"{'Orbit':<35} {'Mod':<4} {'r2/r1':>5} {'=omega?':>12}")
    print("-" * 80)
    rows = [
        ("Px (Px1,Px2,Px3)", "p", rp["r2/r1"], "beta"),
        ("Gx (Gx2,Gx3,Gx1)", "p", rg["r2/r1"], "beta"),
        ("rx (rx3,rx2,rx1)", "p", rrxp["r2/r1"], "beta^-1 = beta^2"),
        ("rx2^135 roots", "N", rrxn["r2/r1"], "omega_N"),
    ]
    for name, mod, val, tag in rows:
        print(f"{name:<35} {mod:<4} {val}")
        print(f"{'':35} {'':4} -> {tag}")

    print("\n" + "=" * 80)
    print("KEY STRUCTURAL FINDINGS")
    print("=" * 80)
    print("1. gcd(135, p-1) = gcd(135, N-1) = 3  =>  exactly 3 roots in BOTH rings")
    print("2. r2/r1 and r3/r1 are ALWAYS omega and omega^2 within each modulus")
    print("3. omega_p = beta (field);  omega_N = omega2 (scalar defect algebra)")
    print(f"   omega_p = {OMEGA_P}")
    print(f"   omega_N = {OMEGA_N}")
    print(f"   omega_p == omega_N: {OMEGA_P == OMEGA_N}")
    print("4. mod p rx orbit recovers framework rx3,rx2,rx1 exactly")
    print(f"   root3 == rx2 (signature r): {RX_N[2] == rx[1]}")
    print("5. mod N orbit is a DISTINCT scalar-side 3-orbit — not rx1/rx3 integers")
    print(f"   N-root1 == rx1? {RX_N[0] == rx[0]}")
    print(f"   N-root2 == rx3? {RX_N[1] == rx[2]}")

    print("\n" + "=" * 80)
    print("BAND SCAN — mod N roots as d / k proxies")
    print("=" * 80)
    S = 15509729875763924304053419655647994379903175655107184284998698212653288468986
    Z = 66278737796829840734606014530466656889790152192829793669891337810330530090951
    inv_r = pow(rx[1], -1, N)
    hits = 0
    for i, r in enumerate(RX_N, 1):
        if check_band_d(f"N-root{i}", r):
            hits += 1
        d = ((S * r - Z) * inv_r) % N
        if check_band_d(f"d_from_k(N-root{i})", d):
            hits += 1
        v = (d % (1 << 135)) | (1 << 134)
        if LO <= v <= HI and check_band_d(f"d_fold(N-root{i})", v):
            hits += 1
    print(f"  HASH160 matches: {hits}")


if __name__ == "__main__":
    main()
