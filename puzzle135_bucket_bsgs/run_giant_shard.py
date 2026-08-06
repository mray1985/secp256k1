#!/usr/bin/env python3
"""
Giant-step shard: search only inside checksum bucket slice.

  d = d_lo + j*M + r
  Harvest: start at (d_lo + j*M)*G, add G each r, match hash160 + verify pubkey.

Parallelize by --j across machines.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from p135_common import (  # noqa: E402
    G,
    M_DEFAULT,
    load_bucket_slice,
    load_target,
    point_add,
    pubkey_h160,
    save_hit,
    scalar_mult,
    verify_candidate,
)
from paths import GIANT_DIR  # noqa: E402


def load_checkpoint(cp: Path) -> int:
    if not cp.exists():
        return 0
    return int(json.loads(cp.read_text(encoding="utf-8")).get("next_r", 0))


def save_checkpoint(cp: Path, j: int, next_r: int, checked: int) -> None:
    cp.write_text(
        json.dumps({"j": j, "next_r": next_r, "checked": checked, "ts": time.time()}),
        encoding="utf-8",
    )


def scan_j(
    j: int,
    m: int,
    d_lo: int,
    d_hi: int,
    px: int,
    py: int,
    target_h160: bytes,
    r_start: int,
    r_end: int,
    cp: Path,
) -> int | None:
    base_d = d_lo + j * m
    if base_d >= d_hi:
        return None
    r_end = min(r_end, m, d_hi - base_d)
    if r_start >= r_end:
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
        d = base_d + r
        if pubkey_h160(pt) == target_h160:
            if verify_candidate(d, px, py):
                save_hit(d, source="giant_shard", j=j, r=r, m=m, hit_path=cp.parent / "HIT.txt")
                return d
        checked += 1
        if checked % 500_000 == 0:
            save_checkpoint(cp, j, r + 1, checked)
            rate = checked / max(time.time() - t0, 1e-9)
            print(f"  j={j} r={r:,} d_tail...{str(d)[-8:]}  {rate:,.0f} hash/s", flush=True)

    save_checkpoint(cp, j, r_end, checked)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="P135 bucket giant shard")
    ap.add_argument("--j", type=int, required=True)
    ap.add_argument("--m", type=int, default=M_DEFAULT)
    ap.add_argument("--r-end", type=int, default=0)
    ap.add_argument("--mode", choices=("upper_half", "fine", "coarse", "stack"), default="upper_half")
    ap.add_argument("--work-dir", type=Path, default=GIANT_DIR)
    args = ap.parse_args()

    d_lo, d_hi, chk, label = load_bucket_slice(args.mode)
    px, py, target_h160, _, _ = load_target()
    width = d_hi - d_lo
    j_max = (width + args.m - 1) // args.m

    args.work_dir.mkdir(parents=True, exist_ok=True)
    cp = args.work_dir / f"shard_j{args.j:012d}.json"
    r_end = args.r_end if args.r_end else args.m
    r_start = load_checkpoint(cp)

    print("P135 bucket BSGS giant shard")
    print(f"  {label}")
    print(f"  checksum=0x{chk:08x}")
    print(f"  d_lo...{str(d_lo)[-12:]}  d_hi...{str(d_hi)[-12:]}")
    print(f"  width~2^{width.bit_length()-1}  j_max={j_max:,}  M={args.m:,}")
    print(f"  shard j={args.j}  r=[{r_start},{r_end})")
    print(f"  target h160={target_h160.hex()}")

    if args.j >= j_max:
        print("j out of range for bucket slice")
        return 1

    hit = scan_j(args.j, args.m, d_lo, d_hi, px, py, target_h160, r_start, r_end, cp)
    return 0 if hit is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
