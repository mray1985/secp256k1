#!/usr/bin/env python3
"""
Fixed RIPEMD160 BSGS / band scan (from rmdbsgs.txt).

Original issues fixed:
  - target_hash is actually checked
  - correct interval meet: x = start + i*m + j
  - calibrate on solved puzzle, then scan P134/P135 bands (sample or full subrange)

Full P134/P135 band (~2^133 values) is infeasible for BSGS (~2^66 memory).
Use --sample N or --subrange-lo/hi for practical runs.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import sys
import time
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

DEFAULT_TARGET = "F6F5431D25BBF7B12E8ADD9AF5E3475C44A0A5B8"  # Puzzle 71 address hash160
P71_LO = 1 << 70
P71_HI = (1 << 71) - 1
P71_ADDRESS = "1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU"

P134_LO = 1 << 133
P134_HI = (1 << 134) - 1
P135_LO = 1 << 134
P135_HI = (1 << 135) - 1


def ripemd160(data: bytes) -> str:
    return hashlib.new("ripemd160", data).hexdigest()


def hash160_compressed(px: int, even_y: bool) -> str:
    prefix = b"\x02" if even_y else b"\x03"
    pub = prefix + px.to_bytes(32, "big")
    return ripemd160(hashlib.sha256(pub).digest())


def make_hasher(mode: str) -> Callable[[int], str]:
    if mode == "dec":
        return lambda x: ripemd160(str(x).encode())
    if mode == "hex":
        return lambda x: ripemd160(format(x, "x").encode())
    if mode == "hex64":
        return lambda x: ripemd160(format(x, "064x").encode())
    if mode == "bytes":
        return lambda x: ripemd160(x.to_bytes(max(1, (x.bit_length() + 7) // 8), "big"))
    raise ValueError(f"unknown mode {mode}")


def bsgs_preimage(
    target: str,
    start: int,
    end: int,
    hasher: Callable[[int], str],
    progress_every: int = 0,
) -> int | None:
    """Find x in [start,end] with hasher(x) == target (lowercase hex)."""
    target = target.lower()
    n = end - start + 1
    if n <= 0:
        return None
    m = int(math.isqrt(n)) + 1

    # baby: [start, start+m)
    table: dict[str, int] = {}
    for j in range(m):
        x = start + j
        if x > end:
            break
        h = hasher(x)
        if h == target:
            return x
        table[h] = x

    # giant blocks: x = start + i*m + j
    for i in range(m):
        base = start + i * m
        if base > end:
            break
        for j in range(m):
            x = base + j
            if x > end:
                break
            if progress_every and (x - start) % progress_every == 0:
                print(f"  ... x={x}", flush=True)
            h = hasher(x)
            if h == target:
                return x
            # optional collision path not needed for preimage
    return None


def linear_scan(
    target: str,
    start: int,
    end: int,
    hasher: Callable[[int], str],
    step: int = 1,
) -> int | None:
    target = target.lower()
    for x in range(start, end + 1, step):
        if hasher(x) == target:
            return x
    return None


def calibrate(hasher: Callable[[int], str], n: int = 70) -> bool:
    from puzzle_keys_53125 import parse_53125

    d = parse_53125()[n].d
    tgt = hasher(d)
    lo = max(1, d - 50_000)
    hi = d + 50_000
    found = bsgs_preimage(tgt, lo, hi, hasher)
    ok = found == d
    print(f"calibrate P{n}: d={d} found={found} ok={ok}")
    return ok


def diagnose_target(target: str) -> None:
    from puzzle_keys_53125 import parse_53125

    print("=== target diagnosis ===")
    print(f"target: {target}")
    keys = parse_53125()
    for n in sorted(keys):
        d = keys[n].d
        px = keys[n].px
        for mode in ("dec", "hex", "hex64", "bytes"):
            if make_hasher(mode)(d) == target.lower():
                print(f"  HIT solved P{n} mode={mode} d={d}")
        for even in (False, True):
            if hash160_compressed(px, even) == target.lower():
                print(f"  HIT solved P{n} hash160 even_y={even}")

    px135 = 9210836494447108270027136741376870869791784014198948301625976867708124077590
    py135 = 46351506704828816385393879789131775975171267756561783641521771795450741674800
    for even in (py135 % 2 == 0,):
        h = hash160_compressed(px135, even)
        print(f"  P135 hash160: {h} match={h==target.lower()}")
    print(f"  P71 official: {DEFAULT_TARGET.lower()} match={target.lower()==DEFAULT_TARGET.lower()}")
    print(f"  old rmdbsgs typo: 20d45a6a... is P66 hash160")


def main() -> int:
    ap = argparse.ArgumentParser(description="RIPEMD160 band BSGS (fixed)")
    ap.add_argument("--target", default=DEFAULT_TARGET)
    ap.add_argument("--mode", default="dec", choices=["dec", "hex", "hex64", "bytes"])
    ap.add_argument("--puzzle", type=int, default=71, help="71 (default), 134, or 135 band")
    ap.add_argument("--sample", type=int, default=2_000_000, help="max values to scan (0=full band, infeasible)")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--diagnose", action="store_true")
    ap.add_argument("--lo", type=int, default=0)
    ap.add_argument("--hi", type=int, default=0)
    args = ap.parse_args()

    target = args.target.lower()
    hasher = make_hasher(args.mode)

    if args.diagnose:
        diagnose_target(target)
        return 0

    if args.calibrate:
        return 0 if calibrate(hasher) else 1

    if args.puzzle == 71:
        lo, hi = P71_LO, P71_HI
    elif args.puzzle == 134:
        lo, hi = P134_LO, P134_HI
    else:
        lo, hi = P135_LO, P135_HI
    if args.lo:
        lo = args.lo
    if args.hi:
        hi = args.hi
    if args.sample:
        hi = min(hi, lo + args.sample - 1)

    width = hi - lo + 1
    print(f"scan mode={args.mode} puzzle={args.puzzle} lo={lo} hi={hi} width={width}")
    print(f"target={target}")
    t0 = time.perf_counter()

    if width <= 5_000_000:
        hit = bsgs_preimage(target, lo, hi, hasher, progress_every=max(1, width // 10))
    else:
        print("width too large; use --sample")
        return 1

    elapsed = time.perf_counter() - t0
    if hit is not None:
        print(f"*** MATCH x={hit} hex={format(hit,'x')} ***")
        print(f"verify hash={hasher(hit)}")
        return 0
    print(f"no match elapsed={elapsed:.1f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
