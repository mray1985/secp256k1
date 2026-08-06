#!/usr/bin/env python3
"""
P71 scaled search: MITM unique S + 2^29 remainder dial + hash160 gate.

T = S + r
S = sum of selected 536870912(i) for i in 1..42
r in [max(0, LO-S), min(M-1, HI-S)]

Sharded on left partial-sum index (2^21 left masks).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

from ecdsa import SECP256k1

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "puzzle71_bsgs"))

from puzzle_catalog import load_catalog
from p71_common import LO, TOP, save_p71_hit, TARGET_H160, TARGET_ADDR

M = 536870912
HI = TOP
S_LO = LO - (M - 1)
MID = 21
OUT = ROOT / "ARCHIVE" / "briefcase" / "The Real Decimal" / "P71" / "scaled_search"
CACHE = OUT / "cache"

G = SECP256k1.generator
N_ORDER = SECP256k1.order


def load_contribs() -> list[int]:
    cat = load_catalog()
    return [M * cat[i].private_key for i in range(1, 43)]


def build_half(path: Path, contribs: list[int], lo: int, hi: int, *, bit_required: int | None = None) -> list[int]:
    if path.exists():
        raw = path.read_bytes()
        n = len(raw) // 32
        return [int.from_bytes(raw[i * 32 : (i + 1) * 32], "big") for i in range(n)]
    vals: list[int] = []
    width = hi - lo
    for mask in range(1, 1 << width):
        if bit_required is not None and not (mask & (1 << bit_required)):
            continue
        s = sum(contribs[lo + b] for b in range(width) if mask & (1 << b))
        vals.append(s)
    vals.sort()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        for v in vals:
            fh.write(v.to_bytes(32, "big"))
    return vals


def hash160_from_point(x: int, y: int) -> bytes:
    comp = (b"\x02" if y % 2 == 0 else b"\x03") + x.to_bytes(32, "big")
    return hashlib.new("ripemd160", hashlib.sha256(comp).digest()).digest()


def check_point(pt) -> bool:
    return hash160_from_point(pt.x(), pt.y()) == TARGET_H160


def scan_s_remainders(s: int, *, meta: dict) -> int | None:
    r0 = max(0, LO - s)
    r1 = min(M - 1, HI - s)
    if r0 > r1:
        return None
    meta["remainder_windows"] += 1
    steps = r1 - r0 + 1
    meta["remainder_steps"] += steps
    stride = meta.get("stride", 1)
    pt = G * (s % N_ORDER)
    # advance to r0
    if r0 > 0:
        pt = pt + (G * r0)
    r = r0
    while r <= r1:
        meta["candidates"] += 1
        if check_point(pt):
            return s + r
        r += stride
        if r <= r1:
            pt = pt + (G * stride)
    return None


def scan_shard(
    left: list[int],
    right: list[int],
    *,
    shard_id: int,
    shard_count: int,
    require_idx42: bool,
    dry_run: bool,
    stride: int,
    log_every: int,
) -> dict:
    meta = {
        "shard_id": shard_id,
        "shard_count": shard_count,
        "unique_s": 0,
        "remainder_windows": 0,
        "remainder_steps": 0,
        "candidates": 0,
        "hit": None,
        "stride": stride,
    }
    n_left = len(left)
    chunk = (n_left + shard_count - 1) // shard_count
    i0 = shard_id * chunk
    i1 = min(n_left, i0 + chunk)
    t0 = time.time()

    import bisect

    for li in range(i0, i1):
        ls = left[li]
        # reachable S window for remainder dial
        j0 = bisect.bisect_left(right, S_LO - ls)
        j1 = bisect.bisect_right(right, HI - ls)
        if j1 <= j0:
            continue
        # dedupe unique S in slice
        prev = None
        for rs in right[j0:j1]:
            s = ls + rs
            if s == prev:
                continue
            prev = s
            meta["unique_s"] += 1
            if dry_run:
                r0 = max(0, LO - s)
                r1 = min(M - 1, HI - s)
                if r0 <= r1:
                    meta["remainder_windows"] += 1
                    meta["remainder_steps"] += (r1 - r0 + 1 + stride - 1) // stride
                continue
            hit = scan_s_remainders(s, meta=meta)
            if hit is not None:
                meta["hit"] = str(hit)
                save_p71_hit(int(hit), source=f"scaled_mitm_shard_{shard_id}")
                return meta
        if log_every and li % log_every == 0 and li > i0:
            elapsed = time.time() - t0
            print(
                f"shard {shard_id}: ls {li-i0}/{i1-i0} unique_s={meta['unique_s']:,} "
                f"candidates={meta['candidates']:,} elapsed={elapsed:.0f}s",
                flush=True,
            )
    meta["elapsed_s"] = round(time.time() - t0, 2)
    return meta


def main() -> int:
    ap = argparse.ArgumentParser(description="P71 scaled MITM + remainder search")
    ap.add_argument("--shard-id", type=int, default=0)
    ap.add_argument("--shard-count", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true", help="count unique S and remainder steps only")
    ap.add_argument("--stride", type=int, default=1, help="remainder stride (testing)")
    ap.add_argument("--log-every", type=int, default=5000)
    ap.add_argument("--require-idx42", action="store_true", help="right half must include index 42")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    contribs = load_contribs()

    right_path = CACHE / ("right_sums_idx42.bin" if args.require_idx42 else "right_sums.bin")
    bit42 = (42 - MID - 1) if args.require_idx42 else None
    right = build_half(right_path, contribs, MID, 42, bit_required=bit42)
    left = build_half(CACHE / "left_sums.bin", contribs, 0, MID)

    print(f"target={TARGET_ADDR}", flush=True)
    print(f"left={len(left):,} right={len(right):,} shard {args.shard_id}/{args.shard_count}", flush=True)

    meta = scan_shard(
        left,
        right,
        shard_id=args.shard_id,
        shard_count=args.shard_count,
        require_idx42=args.require_idx42,
        dry_run=args.dry_run,
        stride=args.stride,
        log_every=args.log_every,
    )
    out_path = OUT / f"shard_{args.shard_id:04d}_result.json"
    out_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2), flush=True)
    return 0 if meta.get("hit") else 1


if __name__ == "__main__":
    raise SystemExit(main())
