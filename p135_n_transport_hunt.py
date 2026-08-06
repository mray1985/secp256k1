#!/usr/bin/env python3
"""
P135 hunt using N-side transport gap from P135 true rx + bridge ry.

Law (splits the +7 curve constant):
  px^3 + 4 == py^2 - 3   (mod p: always for on-curve pubkeys)

N displacement gap:
  gap(px,py) = (py^2 - 3) - (px^3 + 4)  mod N
             = (py^2 - px^3 - 7)         mod N

Hunt P135 d where pubkey gap matches anchor gap from (P135_R_TRUE_X, DEFAULT_RY).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import build_config  # noqa: E402
from ecdlp_full_pipeline import (  # noqa: E402
    DEFAULT_RY,
    N,
    P135_R_TRUE_X,
    puzzle_band,
    pubkey_from_scalar,
)
from genesis_calibration import bridge_state  # noqa: E402
from gap_tier_common import gap_interval, sample_offsets_in_interval  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

P135 = 135
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_n_transport_hunt.log"


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def n_gap(px: int, py: int) -> int:
    return ((pow(py, 2, N) - 3) - (pow(px, 3, N) + 4)) % N


def head_dec(value: int, digits: int) -> str:
    s = str(value)
    return s[:digits] if len(s) >= digits else s


def main() -> int:
    ap = argparse.ArgumentParser(description="P135 N-gap transport hunt")
    ap.add_argument("--samples", type=int, default=200_000, help="offsets sampled each sign")
    ap.add_argument("--head", type=int, default=0, help="if >0, match only first N decimal digits of gap")
    args = ap.parse_args()

    LOG.write_text("", encoding="utf-8")
    lo, hi, _top = puzzle_band(P135)
    keys = parse_53125()

    rx = P135_R_TRUE_X
    ry = DEFAULT_RY
    anchor_gap = n_gap(rx, ry)
    lhs_n = (pow(rx, 3, N) + 4) % N
    rhs_n = (pow(ry, 2, N) - 3) % N

    log("=== P135 N-GAP TRANSPORT HUNT ===")
    log("law: px^3 + 4 == py^2 - 3  (mod p)")
    log(f"N gap = (py^2 - 3) - (px^3 + 4) mod N")
    log(f"anchor rx tail ...{str(rx)[-3:]}  bridge ry tail ...{str(ry)[-3:]}")
    log(f"lhs (x^3+4) mod N tail ...{str(lhs_n)[-3:]}")
    log(f"rhs (y^2-3) mod N tail ...{str(rhs_n)[-3:]}")
    log(f"anchor gap tail ...{str(anchor_gap)[-3:]}")
    log(f"anchor gap head2 {head_dec(anchor_gap, 2)} head3 {head_dec(anchor_gap, 3)}")
    log(f"band: [{lo}, {hi})")
    log("")

    solved_same = [n for n, k in keys.items() if k.d > 0 and n_gap(k.px, k.py) == anchor_gap]
    log(f"solved puzzles with exact anchor gap: {len(solved_same)}")
    if args.head > 0:
        solved_head = [
            n
            for n, k in keys.items()
            if k.d > 0 and head_dec(n_gap(k.px, k.py), args.head) == head_dec(anchor_gap, args.head)
        ]
        log(f"solved puzzles with gap head{args.head} match: {len(solved_head)}")
    log("")

    ref = 134 if 134 in keys else 130
    shelf2 = bridge_state(build_config(keys[ref]))["oitc"].shelf2
    _, o_lo, o_hi = gap_interval(P135, 1)
    log(f"shelf2 from P{ref}: {shelf2}")
    log(f"offset window ob135: [{o_lo}, {o_hi})")
    log(f"samples/sign: {args.samples}")
    log("")

    def gap_match(g: int) -> bool:
        if args.head > 0:
            return head_dec(g, args.head) == head_dec(anchor_gap, args.head)
        return g == anchor_gap

    tested = 0
    passed = 0
    for off in sample_offsets_in_interval(o_lo, o_hi, args.samples):
        for sign in (+1, -1):
            d = shelf2 + sign * off
            if not (lo <= d < hi):
                continue
            tested += 1
            x, y = pubkey_from_scalar(d)
            g = n_gap(x, y)
            if not gap_match(g):
                continue
            passed += 1
            log(
                f"PASS d={d} off={sign * off} "
                f"gap_tail={str(g)[-3:]} px_tail={str(x)[-3:]} py_tail={str(y)[-3:]}"
            )
            if passed >= 50:
                break
        if passed >= 50:
            break

    log("")
    log(f"tested={tested} passed_filter={passed}")
    if passed == 0:
        log("no exact gap hits — try --head 2 or --head 3 for weaker fingerprint match")
    log(f"log -> {LOG}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
