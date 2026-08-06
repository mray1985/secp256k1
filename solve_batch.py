#!/usr/bin/env python3
"""
Canonical solve runner — always hunts P135, P140, P145, P150, P155, P160.

Use this entry point (or p135_160_shelf2_offset_hunt.py) whenever attempting to
solve unsolved puzzles. Row-0 offset law applies to all six (n ≡ 0 mod 5).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from p135_160_shelf2_offset_hunt import hunt_one, log, predicted_offset_bits  # noqa: E402
import p135_160_shelf2_offset_hunt as shelf_hunt  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402
from unsolved_batch import UNSOLVED_PUZZLES  # noqa: E402

LOG = ROOT / "ARCHIVE" / "cloud_pages" / "solve_batch.log"
CSV = ROOT / "ARCHIVE" / "solve_batch.csv"


def main() -> int:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("", encoding="utf-8")
    shelf_hunt.LOG = LOG
    keys = parse_53125()
    all_results: list[dict] = []
    any_hit = False

    log("=== SOLVE BATCH (always P135–P160) ===")
    log(f"puzzles: {list(UNSOLVED_PUZZLES)}")
    log("offset_law_row=0 for all (n≡0 mod 5 cluster)")
    log("")

    for n in UNSOLVED_PUZZLES:
        pred = sorted(predicted_offset_bits(n, 0))
        log(f"--- P{n} predicted offset_bits (row 0): {pred} + gap±1 ---")
        all_results.extend(hunt_one(n, keys, offset_row=0))

    if all_results:
        with CSV.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(all_results[0].keys()))
            w.writeheader()
            w.writerows(all_results)

    log("=== SUMMARY ===")
    for n in UNSOLVED_PUZZLES:
        sub = [r for r in all_results if r["n"] == n]
        hits = [r for r in sub if r["ec_hit"]]
        log(f"P{n}: {len(sub)} candidates, {len(hits)} EC hit(s)")
        if hits:
            any_hit = True
            for h in hits:
                log(f"  *** SOLVED P{n} d={h['d_hex']} [{h['source']}] ***")

    log(f"csv -> {CSV}")
    log(f"log -> {LOG}")
    return 0 if any_hit else 1


if __name__ == "__main__":
    raise SystemExit(main())
