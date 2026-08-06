#!/usr/bin/env python3
"""
P135 precision hunt: finite algebraic closure of public roots.

Claim:
  True nonce k lies in the multiplicative group generated (with small exponents)
  by {N-roots, rx slots, map_p_to_n(rx), defect roots, beta, omega2, Lambda, CP1, CR1}
  under the ring Z/NZ.

Method:
  1. Build finite candidate set for k (exponents in {-1,0,1,2} on a short generator list).
  2. Nonce gate: [k]G.x == r  (definitive for ECDSA nonce).
  3. If gate passes: d = (s*k - z)*r^-1 mod N; check band + HASH160.
"""
from __future__ import annotations

import hashlib
import itertools
import time

from ecdsa import SECP256k1, SigningKey

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
DELTA = p - N
LO, HI = 1 << 134, (1 << 135) - 1

R = 90653255469745952335985143920649543885181555095025199315947044135806663628368
S = 15509729875763924304053419655647994379903175655107184284998698212653288468986
Z = 66278737796829840734606014530466656889790152192829793669891337810330530090951
INV_R = pow(R, -1, N)

BETA = 55594575648329892869085402983802832744385952214688224221778511981742606582254
OMEGA2 = 37718080363155996902926221483475020450927657555482586988616620542887997980018
LAMBDA = 97451685862885086182458552040892158509924235661624603229050850812487253689501
CP1 = 57602015833677736603574291432760600960685355547305560147555835666458430710854
CR1 = 73680319372475906803320245449080571569331871474977252785503402279627244902569

rx = {
    1: 114930704126154877082883546730544079307369404418439078397954295509919169851219,
    2: R,
    3: 26000218878731561428273279366182192513989009817816850365013828370091835863739,
}
N_ROOT = {
    1: 4295241207732992648834070171909958737418321088245693014740872866482121928576,
    2: 20843592559837250438751770916128405230237688095804012051917246139229375937393,
    3: R,
}
d_def = {
    1: 1248780847746852317428964695904392891045016528862400526454142780194939123483,
    2: 21551977082208859489759061364299864038123955443494189974630776168682352336746,
    3: 92991331307360483616382958948483650923668592306718313881520244192640870034108,
}

TARGET_PUB = bytes.fromhex(
    "02145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16"
)
TARGET_H160 = hashlib.new("ripemd160", hashlib.sha256(TARGET_PUB).digest()).digest()
TARGET_X = int.from_bytes(TARGET_PUB[1:], "big")


def map_p_to_n(x: int) -> int:
    return (N * (x % p)) // p


def d_from_k(k: int) -> int:
    return ((S * (k % N) - Z) * INV_R) % N


def ec_x(scalar: int) -> int | None:
    scalar %= N
    if scalar == 0:
        return None
    sk = SigningKey.from_secret_exponent(scalar, curve=SECP256k1, hashfunc=hashlib.sha256)
    return int.from_bytes(sk.get_verifying_key().to_string()[:32], "big")


def hash160_ok(d: int) -> bool:
    d %= N
    if not (LO <= d <= HI):
        return False
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1, hashfunc=hashlib.sha256)
    raw = sk.get_verifying_key().to_string()
    pub = (b"\x02" if int.from_bytes(raw[32:], "big") % 2 == 0 else b"\x03") + raw[:32]
    return hashlib.new("ripemd160", hashlib.sha256(pub).digest()).digest() == TARGET_H160


def mul_pow(base: int, e: int) -> int:
    """base^e mod N for e in {-1,0,1,2}."""
    if e == 0:
        return 1
    if e == 1:
        return base % N
    if e == 2:
        return pow(base, 2, N)
    if e == -1:
        return pow(base, -1, N)
    raise ValueError(e)


def build_generators() -> list[tuple[str, int]]:
    gens: list[tuple[str, int]] = []
    for i in (1, 2, 3):
        gens.append((f"Nr{i}", N_ROOT[i]))
        gens.append((f"rx{i}", rx[i] % N))
        gens.append((f"mrx{i}", map_p_to_n(rx[i])))
        gens.append((f"qx{i}", (rx[i] * DELTA) % N))
        gens.append((f"d{i}", d_def[i]))
    gens += [
        ("beta", BETA % N),
        ("w2", OMEGA2),
        ("Lam", LAMBDA % N),
        ("CP1", CP1 % N),
        ("CR1", CR1 % N),
        ("Delta", DELTA % N),
    ]
    # dedupe by value
    seen: set[int] = set()
    out: list[tuple[str, int]] = []
    for name, val in gens:
        val %= N
        if val in (0, 1) or val in seen:
            continue
        seen.add(val)
        out.append((name, val))
    return out


def main() -> None:
    print("=" * 80)
    print("P135 PRECISION: finite algebraic closure + nonce gate")
    print("=" * 80)
    print("Claim: k is a short product of public generators with exponents in {-1,0,1,2}")
    print("Gate:  [k]G.x == r  then  d = (s*k-z)*r^-1")
    print()

    gens = build_generators()
    print(f"Generators ({len(gens)}):")
    for n, v in gens:
        print(f"  {n}")
    print()

    # Tier A: single generator powers  (tiny)
    # Tier B: products of TWO generators with exponents in {-1,0,1,2} excluding all-zero
    # Tier C: products of THREE from a core subset (N-roots, omega2, defect, beta)
    exps = (-1, 0, 1, 2)

    candidates: dict[int, str] = {}

    def add(label: str, k: int) -> None:
        k %= N
        if k == 0:
            return
        if k not in candidates:
            candidates[k] = label

    # Tier A
    for name, g in gens:
        for e in exps:
            if e == 0:
                continue
            add(f"{name}^{e}", mul_pow(g, e))

    # Tier B: all pairs
    print("Building Tier B (pairs)...")
    for (n1, g1), (n2, g2) in itertools.combinations(gens, 2):
        for e1, e2 in itertools.product(exps, repeat=2):
            if e1 == 0 and e2 == 0:
                continue
            k = (mul_pow(g1, e1) * mul_pow(g2, e2)) % N
            add(f"{n1}^{e1}*{n2}^{e2}", k)

    # Tier C: core triples (N-roots x omega/defect/beta x Lambda/CP1/CR1)
    core_a = [(f"Nr{i}", N_ROOT[i]) for i in (1, 2, 3)]
    core_b = [("w2", OMEGA2), ("beta", BETA % N), ("d1", d_def[1]), ("d2", d_def[2]), ("d3", d_def[3])]
    core_c = [("Lam", LAMBDA % N), ("CP1", CP1 % N), ("CR1", CR1 % N), ("Delta", DELTA % N)]
    print("Building Tier C (core triples)...")
    for (n1, g1), (n2, g2), (n3, g3) in itertools.product(core_a, core_b, core_c):
        for e1, e2, e3 in itertools.product((0, 1, 2, -1), repeat=3):
            if e1 == 0 and e2 == 0 and e3 == 0:
                continue
            k = (mul_pow(g1, e1) * mul_pow(g2, e2) * mul_pow(g3, e3)) % N
            add(f"{n1}^{e1}*{n2}^{e2}*{n3}^{e3}", k)

    # Also: d_from_k inverted — treat each generator as a *d* candidate and recover k
    # From k = (z + r*d)*s^-1 = z*s^-1 + d*delta_k
    delta_k = (R * pow(S, -1, N)) % N
    z_s_inv = (Z * pow(S, -1, N)) % N
    print("Building Tier D (generators-as-d -> implied k)...")
    for name, g in gens:
        for e in exps:
            if e == 0:
                continue
            d_cand = mul_pow(g, e)
            k_imp = (z_s_inv + d_cand * delta_k) % N
            add(f"k_from_d({name}^{e})", k_imp)
            # band-fold d then imply k
            for d_fold in (d_cand % (1 << 135), (d_cand % (1 << 135)) | (1 << 134)):
                if LO <= d_fold <= HI:
                    k_imp2 = (z_s_inv + d_fold * delta_k) % N
                    add(f"k_from_dfold({name}^{e})", k_imp2)

    print(f"Unique k candidates: {len(candidates)}")
    print()
    print("Running nonce gate [k]G.x == r ...")
    t0 = time.time()
    nonce_hits: list[tuple[str, int]] = []
    checked = 0
    for k, label in candidates.items():
        checked += 1
        x = ec_x(k)
        if x == R:
            print(f"  *** NONCE GATE PASS *** {label}")
            print(f"      k = {k}")
            nonce_hits.append((label, k))
        if checked % 2000 == 0:
            print(f"    ... {checked}/{len(candidates)}")

    print()
    print("=" * 80)
    print("NONCE GATE RESULTS")
    print("=" * 80)
    print(f"Checked: {checked}  elapsed: {time.time()-t0:.1f}s")
    print(f"Nonce hits ([k]G.x == r): {len(nonce_hits)}")

    d_hits = []
    for label, k in nonce_hits:
        # also try -k (ECDSA allows R = -kG with same x)
        for sign, kk in (("+", k), ("-", N - k)):
            d = d_from_k(kk)
            print(f"  {sign}k from {label}: d={d} bits={d.bit_length()} in_band={LO<=d<=HI}")
            if hash160_ok(d):
                print(f"  *** HASH160 MATCH *** d={d}")
                d_hits.append((label, kk, d))
            # band folds of d
            for tag, df in [
                ("mod2^135", d % (1 << 135)),
                ("|2^134", (d % (1 << 135)) | (1 << 134)),
            ]:
                if LO <= df <= HI and hash160_ok(df):
                    print(f"  *** HASH160 MATCH fold {tag} *** d={df}")
                    d_hits.append((f"{label}/{tag}", kk, df))

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Algebraic k candidates: {len(candidates)}")
    print(f"Nonce gate passes:      {len(nonce_hits)}")
    print(f"HASH160 matches:        {len(d_hits)}")
    if not nonce_hits:
        print("Precision claim FALSIFIED for this generator set / exponent bound.")
        print("True k is not a short product of these public constants.")
    elif not d_hits:
        print("Found k with [k]G.x == r but derived d failed HASH160/band.")
        print("Check sign of k / RSZ wiring.")
    else:
        for label, k, d in d_hits:
            print(f"  SOLVED: d={d} from {label} k={k}")


if __name__ == "__main__":
    main()
