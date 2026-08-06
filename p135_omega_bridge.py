#!/usr/bin/env python3
"""Bridge mod-N rx2^135 orbit to mod-p rx family via map_p_to_n, defect norm, omega alignment."""
from __future__ import annotations

import hashlib

from ecdsa import SECP256k1, SigningKey

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
DELTA = p - N
LO, HI = 1 << 134, (1 << 135) - 1

BETA = 55594575648329892869085402983802832744385952214688224221778511981742606582254
OMEGA_N = 37718080363155996902926221483475020450927657555482586988616620542887997980018
OMEGA_N_SQ = pow(OMEGA_N, 2, N)

rx = {
    1: 114930704126154877082883546730544079307369404418439078397954295509919169851219,
    2: 90653255469745952335985143920649543885181555095025199315947044135806663628368,
    3: 26000218878731561428273279366182192513989009817816850365013828370091835863739,
}
Px3 = 9210836494447108270027136741376870869791784014198948301625976867708124077590

# mod N orbit (screenshot 15-41-22): x^135 == rx2^135 mod N
RX_N = {
    1: 4295241207732992648834070171909958737418321088245693014740872866482121928576,
    2: 20843592559837250438751770916128405230237688095804012051917246139229375937393,
    3: rx[2],  # rx2 = r_sig
}

d_defect = {
    1: 1248780847746852317428964695904392891045016528862400526454142780194939123483,
    2: 21551977082208859489759061364299864038123955443494189974630776168682352336746,
    3: 92991331307360483616382958948483650923668592306718313881520244192640870034108,
}

S_SIG = 15509729875763924304053419655647994379903175655107184284998698212653288468986
Z_SIG = 66278737796829840734606014530466656889790152192829793669891337810330530090951
INV_R = pow(rx[2], -1, N)

TARGET_HASH = hashlib.new(
    "ripemd160",
    hashlib.sha256(
        bytes.fromhex("02145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16")
    ).digest(),
).digest()


def map_p_to_n(x: int) -> int:
    return (N * (x % p)) // p


def q_lift(x: int) -> int:
    """Delta-scaled N-side lift: x * (p-N) mod N."""
    return (x * DELTA) % N


def section(t: str) -> None:
    print()
    print("=" * 80)
    print(t)
    print("=" * 80)


def eq(a: int, b: int, mod: int) -> bool:
    return (a - b) % mod == 0


def check_d(label: str, d: int) -> bool:
    d %= N
    if not (LO <= d <= HI):
        return False
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1, hashfunc=hashlib.sha256)
    raw = sk.get_verifying_key().to_string()
    pub = (b"\x02" if int.from_bytes(raw[32:], "big") % 2 == 0 else b"\x03") + raw[:32]
    h = hashlib.new("ripemd160", hashlib.sha256(pub).digest()).digest()
    if h == TARGET_HASH:
        print(f"  *** HASH160 MATCH *** {label} d={d}")
        return True
    return False


def d_from_k(k: int) -> int:
    return ((S_SIG * (k % N) - Z_SIG) * INV_R) % N


def main() -> None:
    section("1. map_p_to_n -- field rx to scalar floor")
    for i in (1, 2, 3):
        m = map_p_to_n(rx[i])
        print(f"  map_p_to_n(rx{i}) = {m}")
        print(f"    == rx{i} mod N? {m == rx[i] % N}")
        print(f"    == RX_N[{i}]?    {m == RX_N[i]}")
    print(f"  map_p_to_n(Px3)   = {map_p_to_n(Px3)}")

    section("2. omega_N rotation on mod-N orbit vs rx framework")
    n1 = RX_N[1]
    for k, tag in [(0, "w^0"), (1, "w^1"), (2, "w^2")]:
        val = (n1 * pow(OMEGA_N, k, N)) % N
        print(f"  N-root1 * {tag} = {val}")
        for j in (1, 2, 3):
            match = val == rx[j] % N
            match_n = val == RX_N[j]
            if match or match_n:
                print(f"    == rx{j}: {match}  == RX_N[{j}]: {match_n}")
    print("  Built-in orbit check:")
    print(f"    N-root1 * w   == N-root2: {eq(n1 * OMEGA_N, RX_N[2], N)}")
    print(f"    N-root1 * w^2 == N-root3: {eq(n1 * OMEGA_N_SQ, RX_N[3], N)}")
    print(f"    N-root3 == rx2:           {RX_N[3] == rx[2]}")

    section("3. beta (omega_p) on field rx vs omega_N on N-orbit -- cross bridge")
    print("  Field: rx2 == rx3 * beta^-1 mod p:", eq(rx[2], rx[3] * pow(BETA, -1, p), p))
    print("  Field: rx1 == rx3 * beta   mod p:", eq(rx[1], rx[3] * BETA % p, p))
    # Does map_p_to_n commute with beta rotation?
    m3 = map_p_to_n(rx[3])
    m2 = map_p_to_n(rx[2])
    m1 = map_p_to_n(rx[1])
    print(f"  map(rx3)*w_N == map(rx2)? {eq(m3 * OMEGA_N, m2, N)}")
    print(f"  map(rx3)*w_N^2== map(rx1)? {eq(m3 * OMEGA_N_SQ, m1, N)}")
    print(f"  map(rx2)*w_N == map(rx1)? {eq(m2 * OMEGA_N, m1, N)}")
    print(f"  map(rx2)*w_N == N-root2?  {eq(m2 * OMEGA_N % N, RX_N[2], N)}")
    print(f"  map(rx3)*w_N == N-root1?  {eq(m3 * OMEGA_N % N, RX_N[1], N)}")

    section("4. Defect normalization matrix -- N-roots vs rx vs map(rx)")
    objects = {
        "N-root1": RX_N[1],
        "N-root2": RX_N[2],
        "N-root3": RX_N[3],
        "rx1": rx[1] % N,
        "rx2": rx[2] % N,
        "rx3": rx[3] % N,
        "map(rx1)": map_p_to_n(rx[1]),
        "map(rx2)": map_p_to_n(rx[2]),
        "map(rx3)": map_p_to_n(rx[3]),
        "qx1": q_lift(rx[1]),
        "qx2": q_lift(rx[2]),
        "qx3": q_lift(rx[3]),
    }
    print(f"  {'object':<12} {'d1^-1':>6} {'d2^-1':>6} {'d3^-1':>6}  collapse?")
    for name, obj in objects.items():
        row = []
        for j in (1, 2, 3):
            row.append((obj * pow(d_defect[j], -1, N)) % N)
        collapsed = len(set(row)) == 1
        print(f"  {name:<12} {str(row[0])[:20]}...  {collapsed}")
    # look for row equality across defect branches
    print("\n  Seeking constant column (same value for all objects * d_j^-1):")
    for j in (1, 2, 3):
        col = {name: (obj * pow(d_defect[j], -1, N)) % N for name, obj in objects.items()}
        vals = set(col.values())
        print(f"    d{j}^-1 branch: {len(vals)} distinct values")

    section("5. N-root1 * w^k * d_j^-1 alignment with rx slots")
    hits_align = []
    for k in range(3):
        base = (RX_N[1] * pow(OMEGA_N, k, N)) % N
        for j in (1, 2, 3):
            val = (base * pow(d_defect[j], -1, N)) % N
            for slot, ref in [("rx1", rx[1]), ("rx2", rx[2]), ("rx3", rx[3])]:
                if val == ref % N:
                    hits_align.append(f"N-root1*w^{k}*d{j}^-1 == {slot}")
            for ni, ref in RX_N.items():
                if val == ref:
                    hits_align.append(f"N-root1*w^{k}*d{j}^-1 == N-root{ni}")
    if hits_align:
        for h in hits_align:
            print(f"  {h}")
    else:
        print("  No exact rx / N-root identity on defect-normalized w-rotations")

    section("6. Bridge pipeline candidates -- band HASH160")
    candidates: list[tuple[str, int]] = []
    for i in (1, 2, 3):
        candidates.append((f"N-root{i}", RX_N[i]))
        candidates.append((f"N-root{i}*w", (RX_N[i] * OMEGA_N) % N))
        candidates.append((f"N-root{i}*w^2", (RX_N[i] * OMEGA_N_SQ) % N))
    for i in (1, 2, 3):
        candidates.append((f"map(rx{i})", map_p_to_n(rx[i])))
        candidates.append((f"qx{i}", q_lift(rx[i])))
        for j in (1, 2, 3):
            candidates.append((f"N-root{i}*d{j}^-1", (RX_N[i] * pow(d_defect[j], -1, N)) % N))
            candidates.append((f"map(rx{i})*d{j}^-1", (map_p_to_n(rx[i]) * pow(d_defect[j], -1, N)) % N))
            candidates.append((f"qx{i}*d{j}^-1", (q_lift(rx[i]) * pow(d_defect[j], -1, N)) % N))
    # cross: map_p_to_n of beta-rotated field rx
    for i in (1, 2, 3):
        for k, tag in [(0, "id"), (1, "beta"), (2, "beta^2")]:
            field = (rx[3] * pow(BETA, k, p)) % p  # rotate from rx3 anchor
            candidates.append((f"map(rx3*{tag})", map_p_to_n(field)))
            candidates.append((f"d_from_k(N-root{i})", d_from_k(RX_N[i])))
            candidates.append((f"d_from_k(map(rx{i}))", d_from_k(map_p_to_n(rx[i]))))

    hash_hits = 0
    checked = 0
    for label, val in candidates:
        for tag, folded in [
            ("direct", val % N),
            ("mod2^135", val % (1 << 135)),
            ("mod2^135|2^134", (val % (1 << 135)) | (1 << 134)),
        ]:
            if LO <= (folded % N) <= HI:
                checked += 1
                if check_d(f"{label}::{tag}", folded):
                    hash_hits += 1
    print(f"  In-band EC checks: {checked}")
    print(f"  HASH160 matches: {hash_hits}")

    section("SUMMARY")
    print("  map_p_to_n(rx) != RX_N roots -- floor map gives a third, distinct scalar shadow")
    print("  map(rx)*w_N does NOT preserve beta-orbit (floor and rotation do not commute)")
    print("  N-orbit is self-contained: N-root1 * w^k -> N-root2, N-root3")
    print("  KEY BRIDGE: N-root1 * w^2 == rx2 == N-root3 == r_sig (exact integer match)")
    print("  Field beta-orbit: rx3 -> rx2 -> rx1;  N-orbit: N-root1 -> N-root2 -> rx2")
    print("  Defect d_j^-1: no column collapse; each object projects to distinct branch")
    print("  HASH160: 0 matches on all bridge candidates")


if __name__ == "__main__":
    main()
