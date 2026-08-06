#!/usr/bin/env python3
"""
Search only inside a checksum bucket slice of the puzzle band.

Two modes:
  fine   - one of 2^32 buckets keyed by checksum u32 (00000000 .. FFFFFFFF)
  coarse - one of 8 buckets (N as 32 bytes / 8 = 4-byte lanes)

For a fixed target pubkey (P135), checksum is fixed. Bucket search means:
  slice d in [LO, HI) to the sub-range implied by that checksum label,
  then verify d*G == P (checksum check is redundant once pubkey matches).

Usage:
  python bucket_slice_search.py --puzzle 135
  python bucket_slice_search.py --puzzle 135 --mode coarse --bucket 3
  python bucket_slice_search.py --puzzle 135 --scan 1000
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import pubkey_from_scalar, puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402

CHK_MAX = 0xFFFFFFFF
NUM_COARSE = 8


def checksum_u32(px: int, py: int) -> int:
    comp = (b"\x02" if py % 2 == 0 else b"\x03") + px.to_bytes(32, "big")
    sha = hashlib.sha256(comp).digest()
    h160 = hashlib.new("ripemd160", sha).digest()
    vh = b"\x00" + h160
    return int.from_bytes(hashlib.sha256(hashlib.sha256(vh).digest()).digest()[:4], "big")


def band_midpoint(lo: int, hi: int) -> int:
    """Halfway between lo and hi: lo + (hi-lo)/2.  For P135: 2^134 + 2^133."""
    return lo + (hi - lo) // 2


def upper_half_bounds(lo: int, hi: int) -> tuple[int, int]:
    """Upper half of puzzle band [mid, hi) where mid is halfway lo..hi."""
    return band_midpoint(lo, hi), hi


def intersect_bounds(a_lo: int, a_hi: int, b_lo: int, b_hi: int) -> tuple[int, int] | None:
    lo = max(a_lo, b_lo)
    hi = min(a_hi, b_hi)
    if lo >= hi:
        return None
    return lo, hi


def bucket_bounds(
    lo: int,
    hi: int,
    *,
    mode: str,
    bucket: int | None = None,
    chk_u32: int | None = None,
    clip_upper_half: bool = False,
) -> tuple[int, int, int, str]:
    """
    Return (d_lo, d_hi, bucket_id, label) half-open [d_lo, d_hi) inside [lo, hi).

    upper_half: [mid, hi) from halfway lo..hi to hi (P135: 2^134+2^133 .. 2^135)
    fine:   bucket = chk u32 in [0, 2^32-1]; width = (hi-lo)/2^32
    coarse: bucket = top 3 bits 0..7; width = (hi-lo)/8
    stack:  intersect fine checksum bucket with upper_half
    anchor: use chk/FFFF as center fraction (single-point estimate, not a slice)
    """
    width = hi - lo

    if mode == "upper_half":
        d_lo, d_hi = upper_half_bounds(lo, hi)
        mid = d_lo
        label = f"upper half [mid, hi) mid=2^{mid.bit_length()-1}+2^{mid.bit_length()-2}"
        return d_lo, d_hi, 0, label

    if mode == "stack":
        b_lo, b_hi, bid, blabel = bucket_bounds(
            lo, hi, mode="fine", bucket=bucket, chk_u32=chk_u32
        )
        u_lo, u_hi = upper_half_bounds(lo, hi)
        hit = intersect_bounds(b_lo, b_hi, u_lo, u_hi)
        if hit is None:
            label = f"stack EMPTY (fine {blabel} cap upper_half)"
            return b_lo, b_lo, bid, label
        d_lo, d_hi = hit
        label = f"stack fine checksum INTERSECT upper_half"
        return d_lo, d_hi, bid, label
    if mode == "fine":
        if bucket is None:
            if chk_u32 is None:
                raise ValueError("fine mode needs --bucket or target pubkey checksum")
            bucket = chk_u32
        if not 0 <= bucket <= CHK_MAX:
            raise ValueError(f"fine bucket must be 0..{CHK_MAX:#x}")
        d_lo = lo + (width * bucket) // (CHK_MAX + 1)
        d_hi = lo + (width * (bucket + 1)) // (CHK_MAX + 1)
        label = f"fine bucket 0x{bucket:08x} ({bucket}/{CHK_MAX})"
        return d_lo, d_hi, bucket, label

    if mode == "coarse":
        if bucket is None:
            if chk_u32 is None:
                raise ValueError("coarse mode needs --bucket or target pubkey checksum")
            bucket = chk_u32 >> 29
        if not 0 <= bucket < NUM_COARSE:
            raise ValueError(f"coarse bucket must be 0..{NUM_COARSE - 1}")
        d_lo = lo + (width * bucket) // NUM_COARSE
        d_hi = lo + (width * (bucket + 1)) // NUM_COARSE
        label = f"coarse bucket {bucket}/8 (chk top 3 bits)"
        return d_lo, d_hi, bucket, label

    if mode == "anchor":
        if chk_u32 is None:
            raise ValueError("anchor mode needs target checksum")
        frac = chk_u32 / CHK_MAX
        # +/- half a fine bucket around anchor
        half = width // (2 * (CHK_MAX + 1))
        center = lo + int(width * frac)
        d_lo = max(lo, center - half)
        d_hi = min(hi, center + half + 1)
        label = f"anchor frac={frac:.8f} +/- half fine bucket"
        out = d_lo, d_hi, chk_u32, label
    else:
        raise ValueError(f"unknown mode: {mode}")
        out = None  # unreachable

    if clip_upper_half and mode not in ("upper_half", "stack"):
        d_lo, d_hi, bid, label = out
        u_lo, u_hi = upper_half_bounds(lo, hi)
        hit = intersect_bounds(d_lo, d_hi, u_lo, u_hi)
        if hit is None:
            return d_lo, d_lo, bid, f"{label} cap upper_half -> EMPTY"
        d_lo, d_hi = hit
        label = f"{label} cap upper_half"
        return d_lo, d_hi, bid, label
    return out


def verify_candidate(d: int, px: int, py: int, target_chk: int | None = None) -> bool:
    gx, gy = pubkey_from_scalar(d)
    if gx != px or gy != py:
        return False
    if target_chk is not None and checksum_u32(gx, gy) != target_chk:
        return False
    return True


def scan_range(d_lo: int, d_hi: int, px: int, py: int, target_chk: int, limit: int) -> int | None:
    end = min(d_hi, d_lo + limit)
    for d in range(d_lo, end):
        if verify_candidate(d, px, py, target_chk):
            return d
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Slice puzzle band to checksum bucket")
    ap.add_argument("--puzzle", type=int, default=135)
    ap.add_argument(
        "--mode",
        choices=("upper_half", "fine", "coarse", "anchor", "stack"),
        default="upper_half",
    )
    ap.add_argument("--bucket", type=int, default=None, help="override bucket id")
    ap.add_argument("--scan", type=int, default=0, help="brute-force first N keys in slice (demo)")
    args = ap.parse_args()

    n = args.puzzle
    lo, hi, top = puzzle_band(n)
    rsz = PUZZLE_RSZ[n]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn
    chk = checksum_u32(px, py)

    d_lo, d_hi, bid, label = bucket_bounds(
        lo, hi, mode=args.mode, bucket=args.bucket, chk_u32=chk
    )
    slice_w = d_hi - d_lo
    full_w = hi - lo
    mid = band_midpoint(lo, hi)

    print(f"P{n} search slice")
    print(f"  band midpoint (halfway 2^{n-1}..2^{n}): ...{str(mid)[-12:]}")
    print(f"  target Px tail ...{str(px)[-6:]}")
    print(f"  checksum: 0x{chk:08x}  (00000000 .. ffffffff)")
    print(f"  full band: [{lo}, {hi})  width ~ 2^{full_w.bit_length() - 1}")
    print(f"  mode: {args.mode}")
    print(f"  slice: {label}")
    print(f"  d_lo tail ...{str(d_lo)[-12:]}")
    print(f"  d_hi tail ...{str(d_hi)[-12:]}")
    print(f"  slice width ~ 2^{slice_w.bit_length() - 1}  ({slice_w:.3e} keys)")
    print(f"  reduction: 1/{full_w // max(slice_w, 1)} of full band")
    print()
    print("Search loop (only this bucket):")
    print("  for d in range(d_lo, d_hi):")
    print("      if verify_candidate(d, px, py, target_chk): return d")
    print()
    print("Kangaroo / BSGS: set range [d_lo, d_hi) instead of [lo, hi).")

    if args.scan > 0:
        print()
        print(f"Demo scan: first {args.scan} keys in slice ...")
        hit = scan_range(d_lo, d_hi, px, py, chk, args.scan)
        print(f"  hit: {hit}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
