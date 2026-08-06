#!/usr/bin/env python3
"""
P135: cross-puzzle F97 nibble deltas + tight lane-68 scroll on best lifts.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ecdsa import SECP256k1
from puzzle_keys_53125 import parse_53125
from p135_f97_nibble_lift import (
    calibrate_f97_nibbles,
    calibrate_segment_offsets,
    ec_hit,
    f97_pattern,
    in_lane68,
    lane68_variants,
    lift_with_f97_nibbles,
)
from p135_p130_tail_calibrate import extract_segment, score_hex

G = SECP256k1.generator
LANE68_HI = 0x6FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
LANE68_LO = 0x6800000000000000000000000000000000
PX135 = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY135 = 46351506704828816385393879789131775975171267756561783641521771795450741674800
SCROLL = 500_000
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_f97_nibble_scroll.log"
F97_TEMPLATE = "f897c603"  # P130 tail shape (structural, not assumed exact for P135)


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def calibrate_f97_cross_delta(
    x135: str,
    y135: str,
    pattern: str,
    p130_nib_offs: list[tuple[int, int]],
    base: tuple[int, int] = (-72, -59),
    delta_radius: int = 35,
) -> tuple[list[tuple[int, int]], str]:
    """
    Apply P130 per-nibble deltas to P135 base offset; local search without fixed P135 target.
    Nibble 1: prefer 8/b (lane 6B). Others: maximize soft match to P130 tail template.
    """
    maj = p130_nib_offs[0]  # reference for delta (use first nibble's block offset)
    # deltas vs P130 majority offset (-72,-59) on nibble 0
    p130_maj = (-72, -59)
    deltas = [(xo - p130_maj[0], yo - p130_maj[1]) for xo, yo in p130_nib_offs]

    nib_offs: list[tuple[int, int]] = []
    stitched: list[str] = []
    for ni, (dx0, dy0) in enumerate(deltas):
        best_off = base
        best_score = -1
        best_ch = "0"
        center_x = base[0] + dx0
        center_y = base[1] + dy0
        for dx in range(-delta_radius, delta_radius + 1):
            for dy in range(-delta_radius, delta_radius + 1):
                xo, yo = center_x + dx, center_y + dy
                got = extract_segment(x135, y135, pattern, xo, yo)
                if ni >= len(got):
                    continue
                ch = got[ni]
                if ni == 1 and ch not in "8b":
                    continue
                sc = score_hex(got, F97_TEMPLATE)
                if ni == 1 and ch in "8b":
                    sc += 4
                if sc > best_score:
                    best_score = sc
                    best_off = (xo, yo)
                    best_ch = ch
        if best_score < 0:
            # fallback: no 8/b at nibble 1, use best template score
            for dx in range(-delta_radius, delta_radius + 1):
                for dy in range(-delta_radius, delta_radius + 1):
                    xo, yo = center_x + dx, center_y + dy
                    got = extract_segment(x135, y135, pattern, xo, yo)
                    if ni >= len(got):
                        continue
                    sc = score_hex(got, F97_TEMPLATE)
                    if sc > best_score:
                        best_score = sc
                        best_off = (xo, yo)
                        best_ch = got[ni]
        nib_offs.append(best_off)
        stitched.append(best_ch)
    return nib_offs, "".join(stitched)


def scroll(center: int, label: str) -> int | None:
    pt = center * G
    if pt.x() == PX135 and pt.y() == PY135:
        log(f"*** HIT d={center} direct [{label}] ***")
        return center
    p = pt
    for i in range(1, SCROLL + 1):
        d = center + i
        if d > LANE68_HI:
            break
        p = p + G
        hit = ec_hit(d)
        if hit:
            log(f"*** HIT d={hit} scroll +{i} [{label}] ***")
            return hit
    p = pt
    for i in range(1, SCROLL + 1):
        d = center - i
        if d < LANE68_LO:
            break
        p = p + (-G)
        hit = ec_hit(d)
        if hit:
            log(f"*** HIT d={hit} scroll -{i} [{label}] ***")
            return hit
    return None


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    keys = parse_53125()
    k130 = keys[130]
    x130, y130 = format(k130.px, "x"), format(k130.py, "x")
    priv130 = format(k130.d, "x").lower().lstrip("0")
    f97_pat = f97_pattern()
    f97_tgt = priv130[-10:-2]
    x135, y135 = format(PX135, "x"), format(PY135, "x")

    seg_offsets = calibrate_segment_offsets(x130, y130, priv130)
    p130_nib_offs, _ = calibrate_f97_nibbles(x130, y130, f97_pat, f97_tgt)

    log("=== cross-delta F97 on P135 (no fixed P135 target) ===")
    cross_offs, cross_f97 = calibrate_f97_cross_delta(x135, y135, f97_pat, p130_nib_offs)
    for i, (xo, yo) in enumerate(cross_offs):
        log(f"  nibble {i}: offset=({xo},{yo})")
    log(f"cross F97 stitched={cross_f97}")
    lift_cross = lift_with_f97_nibbles(x135, y135, seg_offsets, f97_pat, cross_offs)
    log(f"cross full lift={lift_cross}")

    offs_f897, _ = calibrate_f97_nibbles(x135, y135, f97_pat, F97_TEMPLATE)
    lift_f897 = lift_with_f97_nibbles(x135, y135, seg_offsets, f97_pat, offs_f897)
    log(f"f897 lift={lift_f897}")

    anchors: dict[int, str] = {}
    for lift_name, lift in [("f897", lift_f897), ("cross", lift_cross)]:
        for name, d in lane68_variants(lift):
            if d not in anchors:
                anchors[d] = f"{lift_name}/{name}"

    # priority: f897 68 variants first
    priority_hex = [
        "68805bb705259f04f28b88cf897c603c9",
        "6880588705259f04f28888cf897c603c9",
    ]
    ranked: list[tuple[str, int]] = []
    for hx in priority_hex:
        d = int(hx, 16)
        if in_lane68(d):
            ranked.append((anchors.get(d, "priority"), d))
    for d, name in sorted(anchors.items()):
        if (name, d) not in ranked and (anchors.get(d, name), d) not in ranked:
            ranked.append((name, d))

    log(f"anchors={len(ranked)} scroll=±{SCROLL}")
    for name, d in ranked[:6]:
        log(f"  {name}: {format(d,'064x')}")

    tested = 0
    for name, d in ranked:
        tested += 2
        hit = ec_hit(d)
        if hit:
            log(f"*** HIT d={hit} [{name}] ***")
            return 0

    for i, (name, center) in enumerate(ranked[:4]):
        log(f"scroll {i+1}/4 {name}")
        hit = scroll(center, name)
        if hit:
            return 0
        tested += SCROLL * 2

    log(f"DONE no hit tested~{tested} elapsed={time.perf_counter()-t0:.1f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
