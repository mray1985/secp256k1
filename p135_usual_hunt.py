#!/usr/bin/env python3
"""Usual P135 pass: per-nibble F97 lift -> lane 68 -> direct EC -> tight scroll."""

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

G = SECP256k1.generator
LANE68_LO = 0x6800000000000000000000000000000000
LANE68_HI = 0x6FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
SCROLL = 1_000_000
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_usual_hunt.log"
F97_TARGET = "f897c603"


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def scroll(center: int, label: str) -> int | None:
    pt = center * G
    if pt.x() == PX and pt.y() == PY:
        log(f"*** HIT d={center} [{label}] ***")
        return center
    p = pt
    for i in range(1, SCROLL + 1):
        d = center + i
        if d > LANE68_HI:
            break
        p = p + G
        hit = ec_hit(d)
        if hit:
            log(f"*** HIT d={hit} +{i} [{label}] ***")
            return hit
    p = pt
    for i in range(1, SCROLL + 1):
        d = center - i
        if d < LANE68_LO:
            break
        p = p + (-G)
        hit = ec_hit(d)
        if hit:
            log(f"*** HIT d={hit} -{i} [{label}] ***")
            return hit
    return None


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    keys = parse_53125()
    k130 = keys[130]
    x130, y130 = format(k130.px, "x"), format(k130.py, "x")
    priv130 = format(k130.d, "x").lower().lstrip("0")
    x135, y135 = format(PX, "x"), format(PY, "x")
    f97_pat = f97_pattern()

    seg_offs = calibrate_segment_offsets(x130, y130, priv130)
    f97_offs, f97 = calibrate_f97_nibbles(x135, y135, f97_pat, F97_TARGET)
    lift = lift_with_f97_nibbles(x135, y135, seg_offs, f97_pat, f97_offs)
    log(f"P135 lift={lift} F97={f97}")

    seen: set[int] = set()
    for name, d in lane68_variants(lift):
        if d in seen:
            continue
        seen.add(d)
        hit = ec_hit(d)
        if hit:
            log(f"*** HIT d={hit} direct [{name}] ***")
            return 0

    scroll_centers = [
        ("68", int(("68" + lift[2:])[:34].ljust(34, "0"), 16)),
        ("68-b8", int(("68" + lift[2:].replace("b", "8"))[:34].ljust(34, "0"), 16)),
    ]
    for label, center in scroll_centers:
        if not in_lane68(center):
            continue
        log(f"scroll +/-{SCROLL} {label} {format(center,'064x')}")
        hit = scroll(center, label)
        if hit:
            return 0

    log(f"DONE no hit elapsed={time.perf_counter()-t0:.1f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
