#!/usr/bin/env python3
"""
P160 massive power fuzz from RSZ pubkey: Px/Py ± k, (axis ± 2^n) ± k, n=1..158.

Target scale examples:
  --target-points 9.5e9   (default half-budget; fuzz ~7.5M per pubkey axis)
  --target-points 19e9    (full fuzz ~15M per axis)

One d*G == P hit solves Puzzle 160.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

CHECKPOINT = ROOT / "ARCHIVE" / "p160_power_fuzz_checkpoint.json"
REPORT = ROOT / "ARCHIVE" / "p160_power_fuzz_report.txt"


def _worker_check(batch: list[int], target_x: int, target_y: int) -> int | None:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "ECDLP"))
    from ecdlp_full_pipeline import pubkey_from_scalar  # noqa: WPS433

    for d in batch:
        pub_x, pub_y = pubkey_from_scalar(d)
        if pub_x == target_x and pub_y == target_y:
            return d
    return None


def in_band(d: int, lo: int, hi: int) -> bool:
    return lo <= d < hi


def lift(d: int, lo: int, hi: int) -> int:
    from ecdlp_full_pipeline import band_representative  # noqa: WPS433

    return band_representative(d, lo, hi)


from p160_pubkey_ladder import (  # noqa: E402
    fuzz_for_target,
    grid_width,
    iter_scalar_grid,
    load_pubkey_target,
    per_axis_count,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="P160 massive power fuzz")
    ap.add_argument("--fuzz", type=int, default=None, help="override linear fuzz half-width")
    ap.add_argument("--max-pow", type=int, default=158)
    ap.add_argument("--target-points", type=int, default=9_500_000_000, help="total point budget")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 1))
    ap.add_argument("--batch", type=int, default=2048)
    ap.add_argument("--progress", type=int, default=500_000)
    ap.add_argument("--export-only", action="store_true", help="estimate only, no EC (for 19T planning)")
    args = ap.parse_args()

    lo, hi, row, target_x, target_y, axes = load_pubkey_target()
    fuzz = args.fuzz
    if fuzz is None:
        fuzz = fuzz_for_target(int(args.target_points), len(axes), args.max_pow)

    per_a = per_axis_count(fuzz, args.max_pow)
    total_est = per_a * len(axes)

    lines = [
        "P160 PUBKEY LADDER POWER FUZZ",
        f"structure=pubkey ±k, (axis ± 2^n) ±k n=1..{args.max_pow}",
        f"target_points={args.target_points:,}",
        f"fuzz=±{fuzz:,}",
        f"max_pow={args.max_pow}",
        f"axes={[n for n, _ in axes]}",
        f"est_candidates={total_est:,}",
        f"workers={args.workers}",
        f"target Px row{row}: {target_x}",
        "",
    ]

    if args.target_points >= 1e12:
        lines += [
            "WARNING: 19T-class target is not practical on one CPU.",
            "This run uses the same grid formula but will take years unless sharded/GPU.",
            "Consider --export-only to plan shards, or lower --target-points to 19e9.",
            "",
        ]

    if args.export_only:
        rate = 2500 * args.workers
        hours = total_est / max(rate, 1) / 3600
        lines.append(f"ETA rough @ {rate:,}/s: {hours:,.1f} hours ({hours/24:,.1f} days)")
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 0

    print("\n".join(lines), flush=True)
    t0 = time.time()
    tested = 0
    solution: tuple[str, int] | None = None
    start_anchor = 0

    if CHECKPOINT.exists():
        try:
            ck = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
            start_anchor = int(ck.get("anchor_idx", 0))
            tested = int(ck.get("tested", 0))
            print(f"resume from anchor_idx={start_anchor} tested={tested:,}", flush=True)
        except Exception:
            pass

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for ai, (aname, anchor) in enumerate(axes):
            if ai < start_anchor or solution:
                continue
            print(f"pubkey axis [{aname}] ...", flush=True)
            batch: list[int] = []
            seen: set[int] = set()
            futures = []

            def flush_batch() -> None:
                nonlocal tested, solution, futures
                if not batch:
                    return
                chunk = batch[:]
                batch.clear()
                futures.append(pool.submit(_worker_check, chunk, target_x, target_y))

            for d, _n, _sign, _tag in iter_scalar_grid(anchor, lo, hi, fuzz, args.max_pow, in_band, lift):
                if d in seen:
                    continue
                seen.add(d)
                batch.append(d)
                if len(batch) >= args.batch:
                    flush_batch()

                if len(futures) >= args.workers * 4:
                    for fut in as_completed(futures):
                        hit_d = fut.result()
                        if hit_d is not None:
                            solution = (aname, hit_d)
                            break
                    futures = [f for f in futures if not f.done()]
                    if solution:
                        break

                tested += 1
                if tested % args.progress == 0:
                    rate = tested / max(time.time() - t0, 1e-9)
                    CHECKPOINT.write_text(
                        json.dumps({"anchor_idx": ai, "tested": tested, "fuzz": fuzz}),
                        encoding="utf-8",
                    )
                    print(f"  tested={tested:,} rate={rate:,.0f}/s", flush=True)

            flush_batch()
            for fut in as_completed(futures):
                hit_d = fut.result()
                if hit_d is not None:
                    solution = (aname, hit_d)
                    break
            if solution:
                break

    elapsed = time.time() - t0
    lines += [
        f"tested={tested:,}",
        f"elapsed={elapsed:.1f}s",
        f"rate={tested/max(elapsed,1e-9):,.0f}/s",
        "",
    ]
    if solution:
        aname, d = solution
        lines += ["*** SOLUTION ***", f"anchor={aname}", f"d={d}", f"hex={hex(d)}"]
        code = 0
    else:
        lines.append("NO HIT")
        code = 1

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"wrote {REPORT}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
