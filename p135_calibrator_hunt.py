#!/usr/bin/env python3
"""
P135 hunt using calibrator puzzles 41, 35, 15, 16, 29, 9.

Maps each to a head segment offset (calibrated on that puzzle), tail from P130.
Also tries direct (xo,yo) tuples: (41,35), (15,16), (29,9) and permutations.
"""

from __future__ import annotations

import itertools
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
    f97_pattern,
    lane68_variants,
    lift_with_f97_nibbles,
)
from p135_p130_tail_calibrate import (
    SEGMENTS,
    calibrate,
    ec_hit,
    extract_segment,
    lane68_candidates,
    lift_all,
    priv_targets,
)

G = SECP256k1.generator
CALIBRATORS = [41, 35, 15, 16, 29, 9]
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_calibrator_hunt.log"
SCROLL = 500_000


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def calibrate_puzzle(pk) -> list[tuple[int, int]]:
    x = format(pk.px, "x")
    y = format(pk.py, "x")
    priv = format(pk.d, "x").lower().lstrip("0")
    targets = priv_targets(priv)
    offsets: list[tuple[int, int]] = []
    for (label, pat, _n), tgt in zip(SEGMENTS, targets):
        span = 80 if label in ("59F04F28B", "88C", "C9", "F97C03") else 50
        xo, yo, _, _ = calibrate(x, y, pat, tgt, span=span)
        offsets.append((xo, yo))
    return offsets


def seg_offsets_from_calibrators(keys: dict) -> list[tuple[int, int]]:
    """First 6 segments use per-puzzle calibrator; F97+C9 from P130."""
    out: list[tuple[int, int]] = []
    for i, n in enumerate(CALIBRATORS):
        pk = keys[n]
        full = calibrate_puzzle(pk)
        out.append(full[i])
    p130 = calibrate_segment_offsets(
        format(keys[130].px, "x"),
        format(keys[130].py, "x"),
        format(keys[130].d, "x").lower().lstrip("0"),
    )
    out.append(p130[6])  # F97 placeholder
    out.append(p130[7])  # C9
    return out


def try_lift(name: str, lift: str, seen: set[int]) -> int | None:
    cands: list[tuple[str, int]] = []
    for d in lane68_candidates(lift):
        if d not in seen:
            seen.add(d)
            cands.append(("lane68", d))
    for item in lane68_variants(lift):
        d = item[1] if isinstance(item, tuple) else item
        if d not in seen:
            seen.add(d)
            cands.append(("var", d))
    for cname, d in cands:
        hit = ec_hit(d)
        if hit:
            log(f"*** HIT d={hit} [{name}/{cname}] lift={lift} ***")
            return hit
    return None


def scroll_lane68(center: int, label: str) -> int | None:
    from p135_f97_nibble_lift import LANE68_HI, LANE68_LO

    pt = center * G
    if pt.x() == 9210836494447108270027136741376870869791784014198948301625976867708124077590:
        log(f"*** HIT d={center} [{label}] ***")
        return center
    p = pt
    for i in range(1, SCROLL + 1):
        d = center + i
        if d > LANE68_HI:
            break
        p = p + G
        if ec_hit(d):
            log(f"*** HIT d={ec_hit(d)} [{label}] +{i} ***")
            return ec_hit(d)
    p = pt
    for i in range(1, SCROLL + 1):
        d = center - i
        if d < LANE68_LO:
            break
        p = p + (-G)
        h = ec_hit(d)
        if h:
            log(f"*** HIT d={h} [{label}] -{i} ***")
            return h
    return None


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    keys = parse_53125()
    x135 = format(keys[135].px, "x")
    y135 = format(keys[135].py, "x")
    k130 = keys[130]
    priv130 = format(k130.d, "x").lower().lstrip("0")
    seg130 = calibrate_segment_offsets(
        format(k130.px, "x"), format(k130.py, "x"), priv130
    )
    f97_offs, _ = calibrate_f97_nibbles(
        x135, y135, f97_pattern(), "f897c603"
    )

    seen: set[int] = set()
    log(f"P135 calibrator hunt: {CALIBRATORS}")

    # 1) Per-segment calibrator map
    mixed = seg_offsets_from_calibrators(keys)
    lift = lift_with_f97_nibbles(x135, y135, mixed, f97_pattern(), f97_offs)
    log(f"mixed_calibrators lift={lift}")
    log(f"  offsets={mixed}")
    if try_lift("mixed_calibrators", lift, seen):
        return 0

    # 2) Each calibrator's full offset table on P135
    for n in CALIBRATORS:
        pk = keys[n]
        offs = calibrate_puzzle(pk)
        lift = lift_with_f97_nibbles(x135, y135, offs, f97_pattern(), f97_offs)
        log(f"P{n} full table lift={lift[:40]}...")
        if try_lift(f"P{n}_full", lift, seen):
            return 0

    # 3) Direct numeric pairs as segment offsets (first 3 segs)
    direct_triples = [
        [(41, 35), (15, 16), (29, 9)],
        [(35, 41), (16, 15), (9, 29)],
        [(41, 35), (29, 9), (15, 16)],
    ]
    for ti, head in enumerate(direct_triples):
        offs = head + list(seg130[3:])
        lift = lift_all(x135, y135, offs)
        log(f"direct_triple_{ti} lift={lift}")
        if try_lift(f"direct_{ti}", lift, seen):
            return 0

    # 4) Six numbers as x-only offsets for segs 0-5
    for yo in [0, 9, 16, 29, 35, 41]:
        offs = [(CALIBRATORS[i], yo) for i in range(6)] + list(seg130[6:])
        lift = lift_all(x135, y135, offs)
        if try_lift(f"x_cal_yo{yo}", lift, seen):
            return 0

    # 5) Delta: calibrator offset - P130 offset applied to P135
    p130_full = calibrate_puzzle(k130)
    for n in CALIBRATORS:
        pk = keys[n]
        cal = calibrate_puzzle(pk)
        delta_offs = [
            (cal[i][0] - p130_full[i][0], cal[i][1] - p130_full[i][1])
            for i in range(8)
        ]
        applied = [
            (seg130[i][0] + delta_offs[i][0], seg130[i][1] + delta_offs[i][1])
            for i in range(8)
        ]
        lift = lift_with_f97_nibbles(x135, y135, applied, f97_pattern(), f97_offs)
        if try_lift(f"delta_P{n}", lift, seen):
            return 0

    # 6) Scroll best lane68 from mixed lift
    for d in lane68_candidates(lift):
        if scroll_lane68(d, "mixed_scroll"):
            return 0

    log(f"DONE no hit ({len(seen)} candidates, {time.perf_counter()-t0:.1f}s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
