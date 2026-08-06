#!/usr/bin/env python3
"""
Giant-step shard for Puzzle 71 hash160 BSGS.

For j in [j_start, j_end):  d = LO + j*M + r,  r in [0, M)
Harvester: P0 = (LO + j*M)*G, then P += G for each r, check hash160.

Parallelize by j-shard across machines / processes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

from paths import BABY_DIR, GIANT_DIR
from p71_common import LO, TARGET_ADDR, TARGET_H160, TOP, save_p71_hit

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G = (Gx, Gy)

M_DEFAULT = 1 << 35


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


def load_checkpoint(cp: Path) -> int:
    if not cp.exists():
        return 0
    data = json.loads(cp.read_text(encoding="utf-8"))
    return int(data.get("next_r", 0))


def save_checkpoint(cp: Path, j: int, next_r: int, checked: int) -> None:
    cp.write_text(
        json.dumps({"j": j, "next_r": next_r, "checked": checked, "ts": time.time()}),
        encoding="utf-8",
    )


def scan_j(j: int, m: int, r_start: int, r_end: int, cp: Path) -> int | None:
    base_d = LO + j * m
    if base_d > TOP:
        return None
    pt = scalar_mult(base_d + r_start)
    if pt is None:
        return None

    checked = 0
    t0 = time.time()
    for r in range(r_start, r_end):
        if r > r_start:
            pt = point_add(pt, G)
            if pt is None:
                break
        if pubkey_h160(pt) == TARGET_H160:
            d = base_d + r
            save_p71_hit(
                d,
                source="giant_shard",
                j=j,
                r=r,
                m=m,
                hit_path=cp.parent / "HIT.txt",
            )
            return d
        checked += 1
        if checked % 1_000_000 == 0:
            save_checkpoint(cp, j, r + 1, checked)
            rate = checked / (time.time() - t0)
            print(f"  j={j} r={r:,}  {rate:,.0f} hash/s", flush=True)
    save_checkpoint(cp, j, r_end, checked)
    return None


def try_baby_scan(j: int, m: int, baby_dir: Path, work_dir: Path) -> int | None:
    """Return d if baby table hit (j=0 lane), None if no hit / skipped."""
    if j != 0:
        return None
    try:
        from scan_baby_h160 import resolve_baby_path, scan_baby_table
    except ImportError:
        return None

    try:
        baby_path = resolve_baby_path(baby_dir)
    except FileNotFoundError:
        print(f"baby scan skipped: no {baby_dir / 'baby_h160.bin'}", flush=True)
        return None

    print("Puzzle 71 baby table scan (j=0 lane) before giant scroll", flush=True)
    result = scan_baby_table(baby_path, m=m, prefix_len=1, progress_every=50_000_000)
    if result is None:
        return None
    r, d = result
    save_p71_hit(
        d,
        source="baby_h160_scan",
        j=0,
        r=r,
        m=m,
        hit_path=work_dir / "HIT.txt",
    )
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--j", type=int, required=True, help="giant index j")
    ap.add_argument("--m", type=int, default=M_DEFAULT)
    ap.add_argument("--r-end", type=int, default=0, help="limit r (0 = full m)")
    ap.add_argument("--work-dir", type=Path, default=GIANT_DIR)
    ap.add_argument("--baby-dir", type=Path, default=BABY_DIR)
    ap.add_argument("--skip-baby-scan", action="store_true")
    args = ap.parse_args()

    args.work_dir.mkdir(parents=True, exist_ok=True)
    cp = args.work_dir / f"shard_j{args.j:010d}.json"
    r_end = args.r_end if args.r_end else args.m
    r_start = load_checkpoint(cp)

    print(f"Puzzle 71 giant shard j={args.j}  r=[{r_start},{r_end})  M={args.m}", flush=True)
    print(f"target={TARGET_ADDR}", flush=True)
    print(f"checkpoint={cp}", flush=True)

    if not args.skip_baby_scan:
        baby_hit = try_baby_scan(args.j, args.m, args.baby_dir, args.work_dir)
        if baby_hit is not None:
            return 0

    hit = scan_j(args.j, args.m, r_start, r_end, cp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
