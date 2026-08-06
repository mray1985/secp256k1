#!/usr/bin/env python3
"""P135 focused hunt: omega2 cosets x delta_k stride on mod-N anchors only."""
from __future__ import annotations

import hashlib
import sys
import time

from ecdsa import SECP256k1, SigningKey

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LO, HI = 1 << 134, (1 << 135) - 1

# RSZ (r = rx2)
R = 90653255469745952335985143920649543885181555095025199315947044135806663628368
S = 15509729875763924304053419655647994379903175655107184284998698212653288468986
Z = 66278737796829840734606014530466656889790152192829793669891337810330530090951
INV_R = pow(R, -1, N)
DELTA_K = (R * pow(S, -1, N)) % N

OMEGA2 = 37718080363155996902926221483475020450927657555482586988616620542887997980018
OMEGAS = (1, OMEGA2, pow(OMEGA2, 2, N))

# mod-N x^135 == rx2^135 roots (screenshot 15-41-22)
N_ANCHORS = {
    "N-root1": 4295241207732992648834070171909958737418321088245693014740872866482121928576,
    "N-root2": 20843592559837250438751770916128405230237688095804012051917246139229375937393,
    "N-root3=rx2": R,
}

TARGET_PUB = bytes.fromhex(
    "02145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16"
)
TARGET_H160 = hashlib.new("ripemd160", hashlib.sha256(TARGET_PUB).digest()).digest()
TARGET_X = int.from_bytes(TARGET_PUB[1:], "big")

# Wide window on focused anchors (6 unique k-bases after coset dedupe expected)
STRIDE_HALF = 50_000


def d_from_k(k: int) -> int:
    return ((S * (k % N) - Z) * INV_R) % N


def check_d(d: int) -> tuple[bool, bool]:
    """Return (hash160_match, pubkey_x_match)."""
    d %= N
    if not (LO <= d <= HI):
        return False, False
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1, hashfunc=hashlib.sha256)
    raw = sk.get_verifying_key().to_string()
    x = int.from_bytes(raw[:32], "big")
    y = int.from_bytes(raw[32:], "big")
    pub = (b"\x02" if y % 2 == 0 else b"\x03") + raw[:32]
    h = hashlib.new("ripemd160", hashlib.sha256(pub).digest()).digest()
    return h == TARGET_H160, x == TARGET_X


def band_fold(d: int) -> list[int]:
    d %= N
    out: list[int] = []
    seen: set[int] = set()
    for v in (d, d % (1 << 135), (d % (1 << 135)) | (1 << 134)):
        v %= N
        if LO <= v <= HI and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def main() -> None:
    print("=" * 80)
    print("P135 omega2-coset x delta_k stride (N-anchors only)")
    print("=" * 80)
    print(f"r == rx2: {R}")
    print(f"delta_k:  {DELTA_K}")
    print(f"stride:   +/-{STRIDE_HALF}")
    print(f"band:     [{LO}, {HI}]")
    print()

    # Build unique k bases: 3 anchors x 3 omegas
    bases: list[tuple[str, int]] = []
    seen_k: set[int] = set()
    for aname, a0 in N_ANCHORS.items():
        for oi, w in enumerate(OMEGAS):
            k0 = (a0 * w) % N
            if k0 in seen_k:
                continue
            seen_k.add(k0)
            bases.append((f"{aname}*w^{oi}", k0))

    print(f"Unique k-bases after omega2 coset: {len(bases)}")
    for lbl, k0 in bases:
        print(f"  {lbl}: {k0}")
    print()

    hits: list[tuple[str, int]] = []
    checked = 0
    in_band = 0
    t0 = time.time()
    report_every = 25_000

    for bi, (blbl, k0) in enumerate(bases):
        print(f"[{bi+1}/{len(bases)}] walking {blbl} ...")
        sys.stdout.flush()
        for t in range(-STRIDE_HALF, STRIDE_HALF + 1):
            k = (k0 + t * DELTA_K) % N
            d_raw = d_from_k(k)
            for d in band_fold(d_raw):
                in_band += 1
                checked += 1
                h_ok, x_ok = check_d(d)
                if h_ok:
                    label = f"{blbl}/t={t:+d} d={d}"
                    print(f"  *** HASH160 MATCH *** {label}")
                    hits.append((label, d))
                elif x_ok:
                    print(f"  pubkey_x match (no hash): {blbl}/t={t:+d} d={d}")
                if checked % report_every == 0:
                    elapsed = time.time() - t0
                    rate = checked / elapsed if elapsed > 0 else 0
                    print(
                        f"    ... checked={checked} in_band={in_band} "
                        f"hits={len(hits)} rate={rate:.0f}/s"
                    )
                    sys.stdout.flush()

    elapsed = time.time() - t0
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"k-bases:          {len(bases)}")
    print(f"stride half:      {STRIDE_HALF}")
    print(f"EC checks:        {checked}")
    print(f"in-band folds:    {in_band}")
    print(f"HASH160 matches:  {len(hits)}")
    print(f"elapsed:          {elapsed:.1f}s")
    if hits:
        for lbl, d in hits:
            print(f"  FOUND d={d}  ({lbl})")
    else:
        print("No d found in this window.")
        print("Next: widen STRIDE_HALF, or add kangaroo distinguished points.")


if __name__ == "__main__":
    main()
