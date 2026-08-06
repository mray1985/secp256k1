#!/usr/bin/env python3
"""CPU-only local scroll around Phase 17c shelf anchors (no GPU, no full kangaroo).

Pollard kangaroo on a W-bit interval costs ~2^(W/2) group ops.  A ~125-bit offset
(H=135, P115 pattern) implies ~2^62 steps — not practical on CPU.  This script
only checks d = seed ± radius around bridge-derived seeds (seconds–minutes).

Usage:
  python align_cpu_scroll.py --puzzle 135 --radius 500000
  python align_cpu_scroll.py --puzzle 115 --radius 0   # sanity (known d at shelf2+offset)
"""

from __future__ import annotations

import argparse
import math
import sys
import time

from ecdlp_full_pipeline import (
    N,
    P115_HEIGHT_MINUS_OFFSET_BITS,
    PuzzleConfig,
    apply_puzzle_defaults,
    band_representative,
    compute_alignment_frame,
    compute_order_in_the_court,
    compute_shelf_iteration_matrix,
    build_bridge_offset_terms,
    delta,
    p,
    pubkey_from_scalar,
    verify_n_y_compression,
    y_even,
)


def pubkey_hit(d: int, px: int, py: int) -> bool:
    x, y = pubkey_from_scalar(d)
    return x == px and y == py


def build_seeds(cfg: PuzzleConfig) -> tuple[int, int, int, list[tuple[str, int]]]:
    """Return LO, HI, shelf2, and priority scalar seeds in puzzle band."""
    lo, hi = cfg.lo, cfg.hi
    row = cfg.row
    px, rx, py = cfg.Px, cfg.rx, cfg.Py
    assert py is not None and cfg.ry is not None

    qx = [(rx[i] * delta) % N for i in range(3)]
    qx_scaled = [(px[i] * delta) % N for i in range(3)]
    lambda_ns = [(qx_scaled[i] * pow(qx[i], -1, N)) % N for i in range(3)]
    lambda_p = (px[row] * pow(rx[row], -1, p)) % p
    lambda_n = lambda_ns[row]
    gap = (lambda_n - lambda_p) % N

    n_yc = verify_n_y_compression(px_triple=px, rx_triple=rx, py=py, ry=cfg.ry)
    py1 = y_even(px[0])
    ry1 = y_even(rx[0])
    oitc = compute_order_in_the_court(
        lo=lo,
        qx=qx,
        qy=(ry1 * delta) % N,
        qx_scaled=qx_scaled,
        qy_scaled=(py1 * delta) % N,
        lambda_ns=lambda_ns,
        lam_y_n=n_yc.lambda_y_n,
    )
    sim = compute_shelf_iteration_matrix(
        lo, [oitc.shelf2, oitc.shelf3, oitc.shelf_y], ["d2", "d3", "dy"]
    )
    af = compute_alignment_frame(
        oitc=oitc, sim=sim, lo=lo, hi=hi, known_d=cfg.known_d
    )
    offsets = build_bridge_offset_terms(
        oitc=oitc,
        sim=sim,
        lambda_ns=lambda_ns,
        lo=lo,
        hi=hi,
        gap=gap,
        lambda_p=lambda_p,
        lambda_n_target=lambda_n,
        calibrated_offset=af.offset_shelf2,
    )

    seeds: list[tuple[str, int]] = [("shelf2", af.shelf2)]
    for name, off in offsets:
        seeds.append((f"shelf2+{name}", af.shelf2 + off))
    # Dedupe by band representative
    seen: set[int] = set()
    unique: list[tuple[str, int]] = []
    for name, raw in seeds:
        d = raw % N
        if not (lo <= d < hi):
            d = band_representative(raw, lo, hi)
        if d in seen:
            continue
        seen.add(d)
        unique.append((name, d))
    return lo, hi, af.shelf2, unique


def kangaroo_feasible_bits(max_seconds: float = 86_400.0, ops_per_sec: float = 50_000.0) -> int:
    """Rough max interval bits for Pollard kangaroo in one CPU-day at ops_per_sec."""
    max_ops = max_seconds * ops_per_sec
    # sqrt(2^W) <= max_ops  =>  W <= 2*log2(max_ops)
    if max_ops <= 1:
        return 0
    return int(2 * math.log2(max_ops))


def main() -> int:
    ap = argparse.ArgumentParser(description="CPU local scroll around shelf2 bridge seeds")
    ap.add_argument("--puzzle", type=int, default=135)
    ap.add_argument("--radius", type=int, default=500_000, help="±window per seed (default 500k)")
    ap.add_argument("--max-seeds", type=int, default=24, help="cap seeds tested (priority order)")
    ap.add_argument("--step", type=int, default=1, help="stride inside window (1=every scalar)")
    args = ap.parse_args()

    cfg = PuzzleConfig(puzzle_num=args.puzzle)
    apply_puzzle_defaults(cfg)
    lo, hi, shelf2, seeds = build_seeds(cfg)
    px0, py = cfg.Px[cfg.row], cfg.Py
    assert py is not None

    h = cfg.puzzle_num
    expect_off_bits = max(1, cfg.puzzle_num - P115_HEIGHT_MINUS_OFFSET_BITS)
    cpu_kangaroo_bits = kangaroo_feasible_bits()

    print("=" * 72)
    print(f"  CPU align scroll — Puzzle {h}  band [2^{h - 1}, 2^{h})")
    print(f"  shelf2 anchor: {shelf2}")
    print(f"  P115 pattern: offset ~ H-{P115_HEIGHT_MINUS_OFFSET_BITS} => ~{expect_off_bits} bits here")
    print(f"  Pollard kangaroo on {expect_off_bits}-bit offset: ~2^{expect_off_bits // 2} ops (needs GPU/cluster)")
    print(f"  CPU kangaroo ~1 day @ 50k ops/s: feasible only if interval <= ~{cpu_kangaroo_bits} bits")
    print(f"  This script: ±{args.radius:,} around each of up to {args.max_seeds} seeds")
    print("=" * 72)

    seeds = seeds[: args.max_seeds]
    t0 = time.time()
    tested = 0
    solution: tuple[str, int] | None = None

    for name, center in seeds:
        start = max(lo, center - args.radius)
        end = min(hi - 1, center + args.radius)
        if start > end:
            continue
        width = end - start + 1
        print(f"  seed [{name}] center={center}  window [{start}, {end}]  width={width:,}")
        d = start
        while d <= end:
            tested += 1
            if pubkey_hit(d, px0, py):
                solution = (name, d)
                break
            d += args.step
        if solution:
            break

    elapsed = time.time() - t0
    print()
    print(f"  tested={tested:,}  elapsed={elapsed:.2f}s  rate={tested / max(elapsed, 1e-9):,.0f}/s")
    if solution:
        name, d = solution
        print(f"  *** HIT [{name}]  d={d}  hex={hex(d)}")
        if cfg.known_d and d != cfg.known_d:
            print(f"  (note: known_d={cfg.known_d} — unexpected mismatch)")
        return 0
    print("  no hit in scroll windows — offset is not within ±radius of tested seeds")
    print("  next: derive tighter bridge offset, or export range for GPU keyhunt (see puzzle160_keyhunt_bsgs/)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
