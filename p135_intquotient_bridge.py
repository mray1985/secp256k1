#!/usr/bin/env python3
"""
Theorem B search — binary-step scroll (not decimal +1 blind walk).

Anchors in decimal; scroll by 2^b offsets around d0, EC verify survivors only.
You see bit-level jumps; decimal +1 hides which bits move the pubkey prefix.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from bucket_slice_search import verify_candidate  # noqa: E402
from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from p135_common import G, N, save_hit, scalar_mult  # noqa: E402

REPORT = ROOT / "ARCHIVE" / "p135_intquotient_bridge.txt"


def iq_bits(z: int, r: int, s: int, d: int) -> int:
    n = z + r * d
    return 0 if n <= 0 else (n // s).bit_length()


def d_anchor(s: int, z: int, r: int, n: int) -> int:
    return (s * (1 << n) - z) // r


def verify_hit(d: int, r: int, s: int, z: int, px: int, py: int) -> bool:
    pt = scalar_mult(d, G)
    return (
        pt is not None
        and pt[0] == px
        and pt[1] == py
        and verify_candidate(d, px, py)
    )


def binary_offsets(max_bit: int, radius_steps: int) -> list[int]:
    """All d0 + sign*2^b for b in [0,max_bit], |sign|*2^b <= radius cap."""
    offs: set[int] = {0}
    cap = radius_steps
    for b in range(max_bit + 1):
        step = 1 << b
        if step > cap:
            break
        offs.add(step)
        offs.add(-step)
        for k in range(2, cap // step + 1):
            if k * step <= cap:
                offs.add(k * step)
                offs.add(-k * step)
    return sorted(offs)


def main() -> int:
    ap = argparse.ArgumentParser(description="P135 intquotient + binary-step search")
    ap.add_argument("--target-bits", type=int, default=135)
    ap.add_argument("--bit-window", type=int, default=8)
    ap.add_argument("--max-bit", type=int, default=40, help="highest 2^b offset from d0")
    ap.add_argument("--radius", type=int, default=1_000_000, help="max |offset| from d0")
    args = ap.parse_args()

    rsz = PUZZLE_RSZ[135]
    r, s, z = int(rsz.r), int(rsz.s), int(rsz.z)
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn
    lo, hi, _ = puzzle_band(135)

    lines = [
        "P135 INTQUOTIENT + BINARY-STEP (decimal d, bit-offset scroll)",
        f"target iq bits ~ {args.target_bits}",
        f"offsets: d0 + k*2^b  b=0..{args.max_bit}  |k*2^b| <= {args.radius}",
        "",
    ]
    print("\n".join(lines), flush=True)

    hit_d: int | None = None
    t0 = time.perf_counter()
    checked = 0

    for n in range(args.target_bits - args.bit_window, args.target_bits + args.bit_window + 1):
        d0 = max(lo, min(hi - 1, d_anchor(s, z, r, n)))
        offsets = binary_offsets(args.max_bit, args.radius)
        best_iq = best_d = -1
        survivors = 0
        for off in offsets:
            d = d0 + off
            if not (lo <= d < hi):
                continue
            checked += 1
            bits = iq_bits(z, r, s, d)
            if abs(bits - args.target_bits) <= 1:
                survivors += 1
                if verify_hit(d, r, s, z, px, py):
                    hit_d = d
                    lines.append(f"HIT n={n} d={d} d0={d0} off={off} iq_bits={bits}")
                    print(lines[-1], flush=True)
                    break
            if best_iq < 0 or abs(bits - args.target_bits) < abs(best_iq - args.target_bits):
                best_iq = bits
                best_d = d
        line = (
            f"n={n:3d} d0={d0}  iq@d0={iq_bits(z,r,s,d0)}  "
            f"offsets={len(offsets)} checked={checked} survivors={survivors}  "
            f"best_d={best_d} best_iq={best_iq}"
        )
        lines.append(line)
        print(line, flush=True)
        if hit_d:
            break

    elapsed = time.perf_counter() - t0
    summary = f"checked={checked:,} wall={elapsed:.1f}s result={'SOLVED' if hit_d else 'not found'}"
    lines.extend(["", summary])
    print(summary, flush=True)
    if hit_d:
        save_hit(hit_d, source="intquotient_binary_step")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if hit_d else 1


if __name__ == "__main__":
    raise SystemExit(main())
