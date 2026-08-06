#!/usr/bin/env python3
"""
Harvester-style Puzzle 71 scanner (address / hash160 target only).

No pubkey on-chain — verify with RIPEMD160(SHA256(compressed_pubkey)).
No giant table: one scalar mult at anchor, then P += G / P -= G.

Anchors: barcode clusters, D/A q-slices, lane midpoints, P70 tail geometry.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from dataclasses import dataclass

# secp256k1
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G = (Gx, Gy)

LO = 1 << 70
HI = 1 << 71
TOP = HI - 1

TARGET_ADDR = "1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU"
TARGET_H160 = bytes.fromhex("F6F5431D25BBF7B12E8ADD9AF5E3475C44A0A5B8")

P68 = 219898266213316039825
P69 = 297274491920375905804
P70 = 970436974005023690481

# D/A mid-band template (rem=0 algebra, not claimed real key)
DA_MID = 1770887431076116955135

# Barcode / notes clusters (in-band 22-digit chunks from puzzle71barcode.txt)
BARCODE_ANCHORS = [
    1936492198895840244483,
    1930550710048680267915,
    1929421851610687679281,
    2198895840244483013614,
    2196111411241235534079,
    2185161068767928179375,
    1988958402444830136140,
    1841771929421851610687,
    1578272286558922829743,
    1361409881258637808013,
    1409881258637808013424,
    1258637808013424319364,
    1342431936492198895840,
    2286558922829743051708,
    2282974305170862777312,
    1708627773121961114112,
    1219611141124123553407,
    1961114112412355340791,
    1411241235534079193055,
    1241235534079193055071,
    1235534079193055071004,
    2355340791930550710048,
]


def inv_mod(a: int, m: int) -> int:
    return pow(a % m, -1, m)


def point_add(P1: tuple[int, int] | None, P2: tuple[int, int] | None) -> tuple[int, int] | None:
    if P1 is None:
        return P2
    if P2 is None:
        return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    if P1 == P2:
        lam = (3 * x1 * x1) * inv_mod(2 * y1, p) % p
    else:
        lam = (y2 - y1) * inv_mod(x2 - x1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)


def scalar_mult(k: int, point: tuple[int, int] = G) -> tuple[int, int] | None:
    k %= N
    result = None
    addend: tuple[int, int] | None = point
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result


def neg_point(P: tuple[int, int]) -> tuple[int, int]:
    x, y = P
    return (x, (-y) % p)


NEG_G = neg_point(G)


def pubkey_h160(point: tuple[int, int]) -> bytes:
    x, y = point
    prefix = b"\x02" if y % 2 == 0 else b"\x03"
    pubkey = prefix + x.to_bytes(32, "big")
    return hashlib.new("ripemd160", hashlib.sha256(pubkey).digest()).digest()


def privkey_to_address(k: int) -> str:
    pt = scalar_mult(k)
    assert pt is not None
    h160 = pubkey_h160(pt)
    vh = b"\x00" + h160
    chk = hashlib.sha256(hashlib.sha256(vh).digest()).digest()[:4]
    payload = vh + chk
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n = int.from_bytes(payload, "big")
    result = ""
    while n:
        n, r = divmod(n, 58)
        result = alphabet[r] + result
    for byte in payload:
        if byte == 0:
            result = "1" + result
        else:
            break
    return result


def in_range(d: int) -> bool:
    return LO <= d <= TOP


@dataclass(frozen=True)
class Anchor:
    label: str
    d: int


def clamp_anchor(label: str, d: int) -> Anchor | None:
    d %= N
    if in_range(d):
        return Anchor(label, d)
    return None


def q_slice_center(q: int) -> int:
    lo = max(LO, q * P68)
    hi = min(TOP, (q + 1) * P68 - 1)
    if lo > hi:
        return (lo + hi) // 2
    return (lo + hi) // 2


def build_anchors() -> list[Anchor]:
    anchors: dict[int, str] = {}

    def add(label: str, d: int) -> None:
        a = clamp_anchor(label, d)
        if a:
            anchors.setdefault(a.d, a.label)

    # Band geometry
    D = HI - LO
    mid = LO + D // 2
    d8 = D // 8
    for name, d in [
        ("LO", LO),
        ("TOP", TOP),
        ("mid", mid),
        ("mid-D/8", mid - d8),
        ("mid+D/8", mid + d8),
        ("2^70+2^69", LO + (1 << 69)),
    ]:
        add(name, d)

    # D/A multiplier-area q slices (floor 5 .. height 10)
    for q in range(5, 11):
        add(f"q{q}_slice_mid", q_slice_center(q))
        add(f"q{q}_slice_lo", max(LO, q * P68))
        add(f"q{q}_slice_hi", min(TOP, (q + 1) * P68 - 1))

    add("DA_mid_q7", DA_MID)
    add("P70+P68", P70 + P68)
    add("P70+P69", P70 + P69)
    add("P69+P68", P69 + P68)
    add("2*P70-P68", 2 * P70 - P68)
    add("P70+mid_offset", P70 + (mid - LO))

    for i, d in enumerate(BARCODE_ANCHORS):
        add(f"barcode_{i}", d)

    # Mirror band: d and TOP - (d - LO)
    base_vals = list(anchors.keys())
    for d in base_vals:
        u = d - LO
        add(f"mirror({anchors[d]})", TOP - u)

    return [Anchor(anchors[d], d) for d in sorted(anchors)]


def scan_anchor(anchor: Anchor, radius: int) -> tuple[str, int] | None:
    d0 = anchor.d
    p0 = scalar_mult(d0)
    if p0 is None:
        return None

    if pubkey_h160(p0) == TARGET_H160:
        return f"{anchor.label} exact", d0

    fwd = p0
    bwd = p0
    for i in range(1, radius + 1):
        d_fwd = d0 + i
        if d_fwd <= TOP:
            fwd = point_add(fwd, G)
            if fwd and pubkey_h160(fwd) == TARGET_H160:
                return f"{anchor.label} +{i}", d_fwd

        d_bwd = d0 - i
        if d_bwd >= LO:
            bwd = point_add(bwd, NEG_G)
            if bwd and pubkey_h160(bwd) == TARGET_H160:
                return f"{anchor.label} -{i}", d_bwd

    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Puzzle 71 Harvester scan (hash160 target)")
    parser.add_argument("--radius", type=int, default=100_000)
    parser.add_argument("--max-anchors", type=int, default=0)
    parser.add_argument("--log", type=str, default="")
    args = parser.parse_args()

    # Sanity check address derivation
    assert privkey_to_address(1) == "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH"

    anchors = build_anchors()
    if args.max_anchors:
        anchors = anchors[: args.max_anchors]

    log_lines: list[str] = []

    def emit(msg: str) -> None:
        print(msg, flush=True)
        log_lines.append(msg)

    emit("=" * 80)
    emit("PUZZLE 71 HARVESTER (hash160 / address target)")
    emit("=" * 80)
    emit(f"target_addr={TARGET_ADDR}")
    emit(f"target_h160={TARGET_H160.hex()}")
    emit(f"band=[{LO}, {TOP}]")
    emit(f"anchors={len(anchors)} radius=±{args.radius}")
    emit("")

    t0 = time.time()
    checked = 0
    for idx, anchor in enumerate(anchors, 1):
        result = scan_anchor(anchor, args.radius)
        fwd_span = min(args.radius, anchor.d - LO)
        bwd_span = min(args.radius, TOP - anchor.d)
        checked += 1 + fwd_span + bwd_span
        if result:
            method, d = result
            emit("*** PUZZLE 71 SOLVED ***")
            emit(f"anchor={idx}/{len(anchors)} {anchor.label} d0={anchor.d}")
            emit(f"method={method}")
            emit(f"d={d}")
            emit(f"hex={hex(d)}")
            addr = privkey_to_address(d)
            emit(f"address={addr}")
            out = (
                f"PUZZLE 71 PRIVATE KEY\n"
                f"method={method}\n"
                f"anchor={anchor.label}\n"
                f"d={d}\n"
                f"hex={hex(d)}\n"
                f"address={addr}\n"
            )
            path = r"C:\Users\mitch\Desktop\secp256k1\PUZZLE71_SOLVED.txt"
            with open(path, "w", encoding="utf-8") as f:
                f.write(out)
            emit(f"saved {path}")
            if args.log:
                with open(args.log, "w", encoding="utf-8") as f:
                    f.write("\n".join(log_lines))
            return 0
        if idx % 10 == 0 or idx == len(anchors):
            emit(
                f"  anchors {idx}/{len(anchors)} "
                f"checked~{checked:,} elapsed={time.time()-t0:.1f}s"
            )

    emit("NO SOLUTION in harvester windows")
    emit(f"checked~{checked:,} elapsed={time.time()-t0:.1f}s")
    emit("First 15 anchors:")
    for a in anchors[:15]:
        emit(f"  d={a.d}  {a.label}")
    if args.log:
        with open(args.log, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))
    return 1


if __name__ == "__main__":
    sys.exit(main())
