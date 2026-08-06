#!/usr/bin/env python3
"""
BSGS displacement from formula rails — we know pubkey P.

For anchor d0 (near-miss formula):
  find d in [d0 - margin, d0 + margin]  with  d*G = P
  i.e.  P0 + delta*G = P   solved by EC BSGS in O(sqrt(width)).

Not linear scan: baby table on r*G, giant walk on P - (d_lo + j*m)*G.
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from harvester_endless_scroll import three_rail_anchors  # noqa: E402
from p135_common import G, load_target, save_hit, scalar_mult  # noqa: E402
from puzzle135_bucket_bsgs.ec_bsgs import bsgs_pubkey_range  # noqa: E402

REPORT = ROOT / "ARCHIVE" / "rail_anchor_bsgs.txt"


def bsgs_from_anchor(
    px: int,
    py: int,
    d0: int,
    margin: int,
    m: int | None = None,
    lo: int | None = None,
    hi: int | None = None,
) -> tuple[int | None, int, int]:
    """BSGS window around d0; return (d_hit, d_lo, d_hi)."""
    d_lo = d0 - margin
    d_hi = d0 + margin + 1
    if lo is not None:
        d_lo = max(lo, d_lo)
    if hi is not None:
        d_hi = min(hi, d_hi)
    width = d_hi - d_lo
    if width <= 0:
        return None, d_lo, d_hi
    hit = bsgs_pubkey_range(px, py, d_lo, d_hi, m=m, progress=True)
    return hit, d_lo, d_hi


def calibrate_puzzle(n: int, margin: int) -> bool:
    from puzzle_keys_53125 import parse_53125

    pk = parse_53125()[n]
    lo, hi, _ = puzzle_band(n)
    anchors = three_rail_anchors(pk.px, pk.py, n)
    print(f"=== calibrate P{n} true d ...{str(pk.d)[-10:]} margin +/-{margin:,} ===")
    ok = False
    for anc in anchors:
        t0 = time.perf_counter()
        hit, d_lo, d_hi = bsgs_from_anchor(pk.px, pk.py, anc.d, margin, lo=lo, hi=hi)
        dt = time.perf_counter() - t0
        delta = hit - anc.d if hit is not None else None
        match = hit == pk.d
        ok = ok or match
        print(
            f"  {anc.name:22s} d0...{str(anc.d)[-8:]}  "
            f"hit={('...'+str(hit)[-8:]) if hit else 'none'}  "
            f"delta={delta}  match={match}  {dt:.1f}s"
        )
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="BSGS from formula rails (known pubkey)")
    ap.add_argument("--margin", type=int, default=10_000_000, help="+/- window around each anchor d0")
    ap.add_argument("--m", type=int, default=0, help="baby step size (0 = sqrt(width))")
    ap.add_argument("--calibrate", type=int, default=0, metavar="N", help="test on solved puzzle N")
    args = ap.parse_args()

    m = args.m or None

    if args.calibrate:
        ok = calibrate_puzzle(args.calibrate, args.margin)
        return 0 if ok else 1

    px, py, _, _, _ = load_target()
    lo, hi, _ = puzzle_band(135)
    anchors = three_rail_anchors(px, py, 135)

    # sanity: anchor points vs target
    lines = [
        "RAIL ANCHOR BSGS — Puzzle 135 (known pubkey)",
        f"target Px ...{str(px)[-12:]}",
        f"band [{lo}, {hi})  margin=+/-{args.margin:,}",
        f"m = {m or 'auto sqrt(width)'}",
        "",
    ]
    print(f"target pubkey known — BSGS displacement from each rail anchor\n")

    hit_d: int | None = None
    hit_rail = ""
    t_all = time.perf_counter()

    for anc in anchors:
        lines.append(f"--- {anc.name} ---")
        lines.append(f"  d0 ...{str(anc.d)[-12:]}  band_pos={100*(anc.d-lo)/(hi-lo):.1f}%")
        p0 = scalar_mult(anc.d, G)
        if p0:
            lines.append(f"  P0 x ...{str(p0[0])[-12:]}  x_eq_target={p0[0]==px}")
        t0 = time.perf_counter()
        hit, d_lo, d_hi = bsgs_from_anchor(px, py, anc.d, args.margin, m=m, lo=lo, hi=hi)
        dt = time.perf_counter() - t0
        width = d_hi - d_lo
        est_m = m or int(math.isqrt(width)) + 1
        status = f"SOLVED d={hit} delta={hit-anc.d}" if hit else "none"
        line = (
            f"  width={width:,} (~2^{width.bit_length()-1})  m~2^{est_m.bit_length()-1}  "
            f"{dt:.1f}s  {status}"
        )
        lines.append(line)
        print(f"{anc.name}: {line}", flush=True)
        if hit:
            hit_d = hit
            hit_rail = anc.name
            break

    elapsed = time.perf_counter() - t_all
    lines.extend(["", f"wall={elapsed:.1f}s  result={'SOLVED' if hit_d else 'not found'}"])
    print(f"\nwall={elapsed:.1f}s  result={'SOLVED' if hit_d else 'not found'}")

    if hit_d:
        save_hit(hit_d, source=f"rail_anchor_bsgs:{hit_rail}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if hit_d else 1


if __name__ == "__main__":
    raise SystemExit(main())
