#!/usr/bin/env python3
"""
In-memory EC BSGS on [d_lo, d_hi) for known pubkey P = d*G.

  d = d_lo + j*m + r
  P - d_lo*G - j*(m*G) = r*G

Baby: x(r*G) -> r for r in [1, m)
Giant: walk j, lookup x in baby, verify full pubkey.
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ecdlp_full_pipeline import puzzle_band  # noqa: E402
from p135_common import (  # noqa: E402
    G,
    load_bucket_slice,
    load_target,
    point_add,
    point_neg,
    scalar_mult,
    save_hit,
    verify_candidate,
)


def bsgs_pubkey_range(
    px: int,
    py: int,
    d_lo: int,
    d_hi: int,
    m: int | None = None,
    progress: bool = True,
) -> int | None:
    width = d_hi - d_lo
    if width <= 0:
        return None
    if m is None:
        m = int(math.isqrt(width)) + 1

    target = (px, py)
    aG = scalar_mult(d_lo)
    mG = scalar_mult(m)
    if mG is None:
        return None
    neg_mG = point_neg(mG)

    baby: dict[int, int] = {}
    pt: tuple[int, int] | None = None
    t0 = time.perf_counter()
    for r in range(1, m):
        pt = G if pt is None else point_add(pt, G)
        if pt is None:
            continue
        if pt[0] not in baby:
            baby[pt[0]] = r
        if progress and r % max(1, m // 10) == 0:
            print(f"  baby {r}/{m}", flush=True)

    if progress:
        print(f"  baby table {len(baby):,} in {time.perf_counter()-t0:.1f}s", flush=True)

    Q = point_add(target, point_neg(aG)) if aG else target
    for j in range(m):
        base_d = d_lo + j * m
        if base_d >= d_hi:
            break
        if verify_candidate(base_d, px, py):
            return base_d
        if Q is not None:
            r = baby.get(Q[0])
            if r is not None:
                d = base_d + r
                if d_lo <= d < d_hi and verify_candidate(d, px, py):
                    return d
        Q = point_add(Q, neg_mG) if Q is not None else None
        if progress and j % max(1, m // 10) == 0:
            print(f"  giant j={j}/{m}", flush=True)

    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="EC BSGS in checksum bucket slice")
    ap.add_argument("--mode", choices=("upper_half", "fine", "coarse", "stack", "anchor"), default="upper_half")
    ap.add_argument("--lo", type=int, default=0)
    ap.add_argument("--hi", type=int, default=0)
    ap.add_argument("--m", type=int, default=0)
    ap.add_argument("--calibrate", type=int, default=0)
    ap.add_argument("--margin", type=int, default=100_000, help="calibrate window +/- around solved d")
    args = ap.parse_args()

    if args.calibrate:
        from puzzle_keys_53125 import parse_53125  # noqa: WPS433

        n = args.calibrate
        pk = parse_53125()[n]
        lo, hi, _ = puzzle_band(n)
        d = pk.d
        margin = args.margin
        d_lo, d_hi = max(lo, d - margin), min(hi, d + margin + 1)
        px, py = pk.px, pk.py
        print(f"calibrate P{n}: d tail ...{str(d)[-6:]}  window={d_hi-d_lo}")
    else:
        px, py, _, _, _ = load_target()
        if args.lo and args.hi:
            d_lo, d_hi = args.lo, args.hi
        else:
            d_lo, d_hi, _, label = load_bucket_slice(args.mode)
            print(f"bucket slice: {label}")

    m = args.m or None
    width = d_hi - d_lo
    est_m = m or int(math.isqrt(width)) + 1
    print(f"BSGS width~2^{width.bit_length()-1}  m~2^{est_m.bit_length()-1}")

    if est_m > 1 << 26 and not args.calibrate:
        print("ERROR: too wide for in-memory BSGS. Use run_giant_shard.py or --lo/--hi.")
        return 1

    hit = bsgs_pubkey_range(px, py, d_lo, d_hi, m=m or None)
    if hit is not None:
        if args.calibrate:
            from puzzle_keys_53125 import parse_53125  # noqa: WPS433

            expected = parse_53125()[args.calibrate].d
            ok = hit == expected
            print(f"calibrate hit d tail ...{str(hit)[-6:]}  expected ...{str(expected)[-6:]}  ok={ok}")
            return 0 if ok else 1
        save_hit(hit, source="ec_bsgs")
        return 0
    print("no hit")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
