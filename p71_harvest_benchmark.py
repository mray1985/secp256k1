#!/usr/bin/env python3
"""Benchmark harvester scroll rate with hash160 gate for P71."""

from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import N, pubkey_from_scalar  # noqa: E402

P71_LO = 1 << 70
TARGET_H160 = bytes.fromhex("F6F5431D25BBF7B12E8ADD9AF5E3475C44A0A5B8")
P_FIELD = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8


def hash160(x: int, y: int) -> bytes:
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    return hashlib.new(
        "ripemd160",
        hashlib.sha256(pref + x.to_bytes(32, "big")).digest(),
    ).digest()


def point_add(P1: tuple[int, int] | None, P2: tuple[int, int] | None) -> tuple[int, int] | None:
    if P1 is None:
        return P2
    if P2 is None:
        return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2 and (y1 + y2) % P_FIELD == 0:
        return None
    if P1 == P2:
        lam = (3 * x1 * x1) * pow(2 * y1, -1, P_FIELD) % P_FIELD
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, P_FIELD) % P_FIELD
    x3 = (lam * lam - x1 - x2) % P_FIELD
    y3 = (lam * (x1 - x3) - y1) % P_FIELD
    return x3, y3


G = (GX, GY)
NEG_G = (GX, (-GY) % P_FIELD)


def bench_naive(n_steps: int, d0: int) -> tuple[float, int]:
    hits = 0
    t0 = time.perf_counter()
    for i in range(n_steps):
        d = d0 + i
        x, y = pubkey_from_scalar(d)
        if hash160(x, y) == TARGET_H160:
            hits += 1
    return time.perf_counter() - t0, hits


def bench_harvester(n_steps: int, d0: int, *, forward: bool = True) -> tuple[float, int]:
    from ecdsa import SECP256k1, SigningKey

    sk = SigningKey.from_secret_exponent(d0 % N, curve=SECP256k1)
    pt = sk.get_verifying_key().pubkey.point
    P: tuple[int, int] = (int(pt.x()), int(pt.y()))
    step = G if forward else NEG_G
    hits = 0
    t0 = time.perf_counter()
    for i in range(n_steps):
        if i > 0:
            P2 = point_add(P, step)
            assert P2 is not None
            P = P2
        if hash160(P[0], P[1]) == TARGET_H160:
            hits += 1
    return time.perf_counter() - t0, hits


def main() -> int:
    steps = 50_000
    d0 = P71_LO + 777_777

    print("P71 harvester hash160 scroll benchmark")
    print(f"  steps per method: {steps:,}")
    print(f"  target: {TARGET_H160.hex()}")
    print()

    for label, fn in [
        ("naive: full scalar mult + hash160 compare", lambda: bench_naive(steps, d0)),
        ("harvester: P+=G + hash160 compare", lambda: bench_harvester(steps, d0, forward=True)),
        ("harvester: P-=G + hash160 compare", lambda: bench_harvester(steps, d0, forward=False)),
    ]:
        elapsed, hits = fn()
        rate = steps / elapsed
        print(f"  {label}")
        print(f"    {rate:,.0f} keys/s   ({elapsed:.2f}s)   hits={hits}")
        print()

    # sustained 5s run
    print("  sustained harvester (5s)...")
    from ecdsa import SECP256k1, SigningKey

    sk = SigningKey.from_secret_exponent(d0 % N, curve=SECP256k1)
    pt = sk.get_verifying_key().pubkey.point
    P: tuple[int, int] = (int(pt.x()), int(pt.y()))
    t_end = time.perf_counter() + 5.0
    count = 0
    t_start = time.perf_counter()
    while time.perf_counter() < t_end:
        P2 = point_add(P, G)
        assert P2 is not None
        P = P2
        if hash160(P[0], P[1]) == TARGET_H160:
            print("  UNEXPECTED HIT")
        count += 1
    elapsed = time.perf_counter() - t_start
    rate = count / elapsed
    print(f"    sustained: {rate:,.0f} keys/s over {count:,} steps")
    print()

    band = 1 << 70
    for r in (rate, 5_000, 10_000, 20_000):
        years = band / r / 86400 / 365.25
        print(f"  full band 2^70 @ {r:,.0f}/s -> {years:,.0f} years")

    print()
    print("  puzzle71_harvester default: ~100 anchors x +/-100k = ~20M keys")
    print(f"  @ {rate:,.0f}/s that's ~{20_000_000/rate:.0f}s per full harvester pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
