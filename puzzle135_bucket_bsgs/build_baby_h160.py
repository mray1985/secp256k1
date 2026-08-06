#!/usr/bin/env python3
"""Build hash160 baby table for P135 bucket BSGS (r*G for r in [0, M))."""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from p135_common import G, H160_RECORD, M_DEFAULT, load_bucket_slice, point_add, pubkey_h160, scalar_mult  # noqa: E402
from paths import BABY_DIR  # noqa: E402


def pack_h160(h160: bytes, r: int) -> bytes:
    if r < 0 or r >= 1 << 40:
        raise ValueError(f"r out of uint40 range: {r}")
    return h160 + r.to_bytes(5, "big")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build P135 bucket baby h160 table")
    ap.add_argument("--out-dir", type=Path, default=BABY_DIR)
    ap.add_argument("--m", type=int, default=M_DEFAULT)
    ap.add_argument("--start-r", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--auto-fit", action="store_true")
    ap.add_argument("--mode", choices=("upper_half", "fine", "coarse", "stack"), default="upper_half")
    args = ap.parse_args()

    d_lo, d_hi, _, label = load_bucket_slice(args.mode)
    m = args.m
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    drive = str(out.drive or out.anchor) + "\\"
    if not os.path.exists(drive):
        print(f"ERROR: drive missing: {out}", file=sys.stderr)
        return 1

    if args.auto_fit and not args.limit:
        free = shutil.disk_usage(drive).free - 2_000_000_000
        args.limit = max(0, int(free // H160_RECORD))

    count = args.limit if args.limit else m
    end_r = min(args.start_r + count, m)

    path = out / "baby_h160.bin"
    meta = out / "baby_meta.txt"
    target_txt = out / "TARGET.txt"

    px, py, h160, chk, _ = __import__("p135_common", fromlist=["load_target"]).load_target()

    print(f"P135 bucket baby build")
    print(f"  slice: {label}")
    print(f"  d_lo tail ...{str(d_lo)[-12:]}")
    print(f"  M={m:,}  r=[{args.start_r},{end_r})")
    print(f"  out={path}")

    mode = "ab" if args.start_r else "wb"
    t0 = time.perf_counter()
    pt = scalar_mult(args.start_r) if args.start_r else None
    if args.start_r == 0:
        pt = None

    with path.open(mode) as fh:
        for r in range(args.start_r, end_r):
            if r == 0:
                pt = None
            elif r == 1 or pt is None:
                pt = scalar_mult(1)
            else:
                pt = point_add(pt, G)
            if pt is None:
                continue
            fh.write(pack_h160(pubkey_h160(pt), r))

    elapsed = time.perf_counter() - t0
    batch = end_r - args.start_r
    meta.write_text(
        "\n".join(
            [
                f"M={m}",
                f"start_r={args.start_r}",
                f"end_r={end_r}",
                f"h160_bytes={(end_r - args.start_r) * H160_RECORD}",
                f"d_lo={d_lo}",
                f"d_hi={d_hi}",
                f"bucket_mode={args.mode}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    target_txt.write_text(
        f"h160={h160.hex()}\n"
        f"checksum=0x{chk:08x}\n"
        f"Px={px}\n"
        f"Py={py}\n"
        f"M={m}\n",
        encoding="utf-8",
    )
    print(f"Done {batch:,} steps in {elapsed:.1f}s ({batch/max(elapsed,1e-9):,.0f}/s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
