#!/usr/bin/env python3
"""
P160 power fuzz from RSZ pubkey: Px/Py ± k, (axis ± 2^n) ± k for n=1..158.
One d*G == P hit solves the puzzle.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import band_representative, pubkey_from_scalar  # noqa: E402
from p160_pubkey_ladder import fuzz_for_target, load_pubkey_target, per_axis_count  # noqa: E402


def in_band(d: int, lo: int, hi: int) -> bool:
    return lo <= d < hi


def lift(d: int, lo: int, hi: int) -> int:
    return band_representative(d, lo, hi)


def iter_candidates(anchor: int, lo: int, hi: int, fuzz: int, max_pow: int):
    seen: set[int] = set()

    def emit(tag: str, raw: int):
        d = raw if in_band(raw, lo, hi) else lift(raw, lo, hi)
        if d in seen:
            return
        seen.add(d)
        yield tag, d

    for k in range(-fuzz, fuzz + 1):
        yield from emit(f"base{k:+d}", anchor + k)

    for n in range(1, max_pow + 1):
        step = 1 << n
        for sign_name, base in (("p", anchor + step), ("m", anchor - step)):
            for k in range(-fuzz, fuzz + 1):
                yield from emit(f"{sign_name}2^{n}{k:+d}", base + k)


def main() -> int:
    ap = argparse.ArgumentParser(description="P160 pubkey ladder power fuzz EC scan")
    ap.add_argument("--fuzz", type=int, default=None)
    ap.add_argument("--target-points", type=int, default=9_500_000_000)
    ap.add_argument("--max-pow", type=int, default=158)
    ap.add_argument("--progress", type=int, default=100_000)
    args = ap.parse_args()

    lo, hi, row, target_x, target_y, axes = load_pubkey_target()
    fuzz = args.fuzz
    if fuzz is None:
        fuzz = fuzz_for_target(args.target_points, len(axes), args.max_pow)

    per_axis = per_axis_count(fuzz, args.max_pow)
    print("P160 PUBKEY LADDER — 1 hit = solution")
    print(f"structure: pubkey ±k, (axis ± 2^n) ±k  n=1..{args.max_pow}")
    print(f"fuzz=±{fuzz:,}  ~{per_axis:,} candidates/axis")
    print(f"target row{row} Px={target_x}")
    print()

    t0 = time.time()
    tested = 0
    hit: tuple[str, str, int] | None = None

    for aname, anchor in axes:
        if hit:
            break
        print(f"pubkey axis {aname} ...", flush=True)
        for tag, d in iter_candidates(anchor, lo, hi, fuzz, args.max_pow):
            tested += 1
            pub_x, pub_y = pubkey_from_scalar(d)
            if pub_x == target_x and pub_y == target_y:
                hit = (aname, tag, d)
                break
            if tested % args.progress == 0:
                rate = tested / max(time.time() - t0, 1e-9)
                print(f"  tested={tested:,}  rate={rate:,.0f}/s", flush=True)

    elapsed = time.time() - t0
    lines = [
        "P160 PUBKEY LADDER SCAN",
        f"fuzz=±{fuzz}  max_pow={args.max_pow}",
        f"tested={tested:,}  elapsed={elapsed:.1f}s  rate={tested/max(elapsed,1e-9):,.0f}/s",
        "",
    ]

    if hit:
        aname, tag, d = hit
        lines += [
            "*** SOLUTION ***",
            f"anchor={aname}  tag={tag}",
            f"d={d}",
            f"hex={hex(d)}",
        ]
    else:
        lines.append("NO HIT")

    text = "\n".join(lines) + "\n"
    out = ROOT / "ARCHIVE" / "p160_power_fuzz_report.txt"
    out.write_text(text, encoding="utf-8")
    print()
    print(text)
    print(f"wrote {out}")
    return 0 if hit else 1


if __name__ == "__main__":
    raise SystemExit(main())
