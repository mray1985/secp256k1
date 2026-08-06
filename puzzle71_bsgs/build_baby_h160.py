#!/usr/bin/env python3
"""Build baby-step table for Puzzle 71 BSGS (hash160 + optional x-coord)."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import struct
import sys
import time
from pathlib import Path

from paths import BABY_DIR, M_FULL

# secp256k1
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G = (Gx, Gy)

LO = 1 << 70
M_DEFAULT = M_FULL  # sqrt(2^70)
H160_RECORD = 25  # 20 hash160 + uint40 r
X_RECORD = 36  # 32-byte x + uint32 r


def inv_mod(a: int, m: int) -> int:
    return pow(a % m, -1, m)


def point_add(p1: tuple[int, int] | None, p2: tuple[int, int] | None) -> tuple[int, int] | None:
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if p1 == p2:
        lam = (3 * x1 * x1) * inv_mod(2 * y1, P) % P
    else:
        lam = (y2 - y1) * inv_mod(x2 - x1, P) % P
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
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


def pubkey_h160(point: tuple[int, int]) -> bytes:
    x, y = point
    pk = (b"\x02" if y % 2 == 0 else b"\x03") + x.to_bytes(32, "big")
    return hashlib.new("ripemd160", hashlib.sha256(pk).digest()).digest()


def pack_h160(h160: bytes, r: int, *, base_r: int = 0) -> bytes:
    rel = r - base_r
    if rel < 0 or rel >= 1 << 40:
        raise ValueError(f"relative r out of uint40 range: {rel} (r={r} base={base_r})")
    return h160 + rel.to_bytes(5, "big")


def pack_x(x: int, r: int) -> bytes:
    return x.to_bytes(32, "big") + struct.pack(">I", r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=BABY_DIR, help="baby output dir (default: E:\\puzzle71_bsgs\\baby)")
    ap.add_argument("--m", type=int, default=M_DEFAULT, help="baby step count (default 2^35)")
    ap.add_argument("--start-r", type=int, default=0, help="resume from r")
    ap.add_argument("--limit", type=int, default=0, help="max r to build (0 = full m)")
    ap.add_argument(
        "--auto-fit",
        action="store_true",
        help="set limit from free space on output drive (h160 only, keeps --m)",
    )
    ap.add_argument("--h160", action="store_true", default=True)
    ap.add_argument("--x", action="store_true", help="also write x-coord table for EC-BSGS")
    args = ap.parse_args()

    m = args.m
    if not args.out_dir.drive or not os.path.exists(str(args.out_dir.drive) + "\\"):
        print(f"ERROR: output drive not available: {args.out_dir}", file=sys.stderr)
        return 1

    usage_path = str(args.out_dir.drive) + "\\"
    if args.auto_fit and not args.limit:
        free = shutil.disk_usage(usage_path).free
        reserve = 2_000_000_000
        args.limit = max(0, int((free - reserve) // H160_RECORD))
        print(f"auto-fit: free={free/1e9:.2f} GB -> limit={args.limit:,} baby steps")
    count = args.limit if args.limit else m
    end_r = args.start_r + count
    if args.start_r == 0:
        end_r = min(end_r, m)

    need_h160 = args.h160
    need_x = args.x
    bytes_needed = 0
    if need_h160:
        bytes_needed += (end_r - args.start_r) * H160_RECORD
    if need_x:
        bytes_needed += (end_r - args.start_r) * X_RECORD

    free = shutil.disk_usage(usage_path).free
    if bytes_needed > free:
        print(
            f"ERROR: need {bytes_needed/1e9:.2f} GB, only {free/1e9:.2f} GB free on {args.out_dir.drive}",
            file=sys.stderr,
        )
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    h160_path = args.out_dir / "baby_h160.bin"
    x_path = args.out_dir / "baby_x.bin"

    print(f"LO={LO}")
    print(f"baby steps r in [{args.start_r}, {end_r})")
    print(f"output dir: {args.out_dir}")
    print(f"estimated write: {bytes_needed / 1e9:.2f} GB")
    print(f"h160 file: {h160_path}")
    if need_x:
        print(f"x file:    {x_path}")
    print()

    # Harvester: start at LO + start_r
    d = LO + args.start_r
    pt = scalar_mult(d)
    if pt is None:
        print("ERROR: invalid start point", file=sys.stderr)
        return 1

    # Mid-band windows always rewrite baby_h160.bin (not append to LO..0 table).
    mode_h160 = "wb"
    mode_x = "wb"
    fh = open(h160_path, mode_h160) if need_h160 else None
    fx = open(x_path, mode_x) if need_x else None

    t0 = time.time()
    batch = 0
    try:
        for r in range(args.start_r, end_r):
            if r > args.start_r:
                pt = point_add(pt, G)
                if pt is None:
                    print(f"ERROR: point at infinity at r={r}", file=sys.stderr)
                    return 1
            h160 = pubkey_h160(pt)
            if fh:
                fh.write(pack_h160(h160, r, base_r=args.start_r))
            if fx:
                fx.write(pack_x(pt[0], r))
            batch += 1
            if batch % 500_000 == 0:
                rate = batch / (time.time() - t0)
                done = r + 1 - args.start_r
                remain = end_r - args.start_r - done
                eta = remain / rate if rate else 0
                print(
                    f"  r={r:,}  {done:,}/{end_r - args.start_r:,}  "
                    f"{rate:,.0f} steps/s  ETA {eta/3600:.1f}h",
                    flush=True,
                )
    finally:
        if fh:
            fh.close()
        if fx:
            fx.close()

    elapsed = time.time() - t0
    print(f"Done. {batch:,} baby steps in {elapsed:.1f}s ({batch/elapsed:,.0f}/s)")
    meta = args.out_dir / "baby_meta.txt"
    target_src = Path(__file__).resolve().parent / "TARGET.txt"
    if target_src.exists():
        (args.out_dir / "TARGET.txt").write_text(
            target_src.read_text(encoding="utf-8"), encoding="utf-8"
        )
    meta.write_text(
        f"LO={LO}\nM={m}\nM_full={M_FULL}\nstart_r={args.start_r}\nend_r={end_r}\n"
        f"h160_bytes={H160_RECORD}\nx_bytes={X_RECORD}\n"
        f"baby_coverage={end_r/m:.4f}\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
