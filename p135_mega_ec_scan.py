#!/usr/bin/env python3
"""Random EC-gated scan: d = shelf2 ± o in gap-1/gap-2 offset intervals (P135)."""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import PuzzleConfig, apply_puzzle_defaults, pubkey_from_scalar, puzzle_band
from gap_tier_common import d_candidates_from_offset, gap_interval
from genesis_calibration import bridge_state

H = 135


def ec_hit(d: int, px: int, py: int) -> bool:
    x, y = pubkey_from_scalar(d)
    return x == px and y == py


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=2_000_000)
    ap.add_argument("--seed", type=int, default=135)
    ap.add_argument("--report-every", type=int, default=250_000)
    args = ap.parse_args()

    random.seed(args.seed)
    cfg = PuzzleConfig(puzzle_num=H, row=2)
    apply_puzzle_defaults(cfg)
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(H)
    shelf2 = st["oitc"].shelf2
    px, py = cfg.Px[cfg.row], cfg.Py
    assert py is not None

    tiers = []
    for gap in (1, 2):
        ob, o_lo, o_hi = gap_interval(H, gap)
        tiers.append((gap, ob, o_lo, o_hi))

    lines = [
        "P135 MEGA GAP-TIER EC SCAN",
        f"trials={args.trials:,}  shelf2 bits={shelf2.bit_length()}",
        f"target Px row={cfg.row + 1}",
        "",
    ]
    for gap, ob, o_lo, o_hi in tiers:
        lines.append(f"  gap={gap}  offset_bits={ob}  o in [{o_lo}, {o_hi})")

    t0 = time.time()
    tested = 0
    hits: list[tuple[int, int, str, int]] = []

    for i in range(1, args.trials + 1):
        gap, _, o_lo, o_hi = random.choice(tiers)
        o = random.randrange(o_lo, o_hi)
        cands = d_candidates_from_offset(shelf2, o, lo, hi)
        if not cands:
            continue
        d, direction = random.choice(cands)
        tested += 1
        if ec_hit(d, px, py):
            hits.append((d, gap, direction, o))
            break
        if i % args.report_every == 0:
            elapsed = time.time() - t0
            rate = tested / max(elapsed, 1e-9)
            print(f"  ... {i:,}/{args.trials:,}  tested={tested:,}  {rate:,.0f}/s", flush=True)

    elapsed = time.time() - t0
    lines.append("")
    lines.append(f"tested={tested:,}  elapsed={elapsed:.1f}s  rate={tested/max(elapsed,1e-9):,.0f}/s")
    lines.append(f"EC hits: {len(hits)}")
    for d, gap, direction, o in hits:
        lines.append(f"  HIT d={d}  gap={gap}  dir={direction}  o_bits={o.bit_length()}")

    report = "\n".join(lines) + "\n"
    print(report)
    out = ROOT / "ARCHIVE" / "p135_mega_ec_scan_report.txt"
    out.write_text(report, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
