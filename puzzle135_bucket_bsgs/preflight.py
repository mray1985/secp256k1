#!/usr/bin/env python3
"""Preflight: bucket slice + BSGS shard plan for P135."""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from p135_common import M_DEFAULT, load_bucket_slice, load_target  # noqa: E402
from paths import BSGS_ROOT, BABY_DIR, GIANT_DIR  # noqa: E402


def main() -> int:
    px, py, h160, chk, _ = load_target()
    print("P135 stack: checksum bucket + BSGS + pubkey")
    print(f"  Px tail ...{str(px)[-6:]}")
    print(f"  Py tail ...{str(py)[-6:]}")
    print(f"  hash160={h160.hex()}")
    print(f"  checksum=0x{chk:08x}")
    print(f"  BSGS root: {BSGS_ROOT}")
    print()

    for mode in ("upper_half", "fine", "coarse", "stack"):
        d_lo, d_hi, _, label = load_bucket_slice(mode)
        w = d_hi - d_lo
        m = M_DEFAULT
        j_max = (w + m - 1) // m
        sqrt_m = int(math.isqrt(w)) + 1
        print(f"=== mode={mode} ===")
        print(f"  {label}")
        print(f"  d_lo ...{str(d_lo)[-14:]}")
        print(f"  d_hi ...{str(d_hi)[-14:]}")
        print(f"  width ~ 2^{w.bit_length()-1}")
        print(f"  giant M={m:,}  -> j shards: {j_max:,}  (~2^{j_max.bit_length()-1})")
        print(f"  optimal BSGS m=sqrt(width) ~ 2^{sqrt_m.bit_length()-1}  (infeasible at full width)")
        print(f"  baby table @ M: {m * 25 / 1e9:.1f} GB h160")
        print()

    print("Run:")
    print("  1. python puzzle135_bucket_bsgs/preflight.py")
    print("  2. python puzzle135_bucket_bsgs/build_baby_h160.py --auto-fit")
    print("  3. python puzzle135_bucket_bsgs/run_giant_shard.py --j 0")
    print("  4. parallel --j 1..N on more cores/machines")
    print()
    print("Calibrate EC BSGS on solved puzzle (small window):")
    print("  python puzzle135_bucket_bsgs/ec_bsgs.py --calibrate 130")
    print()
    print("Narrow further with transport-tower anchor:")
    print("  python puzzle135_bucket_bsgs/ec_bsgs.py --lo LO --hi HI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
