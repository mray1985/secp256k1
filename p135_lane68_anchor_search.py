#!/usr/bin/env python3
"""P135 tight hunt: 0x68 anchor (B~8) + 53125 lift tail, local scroll in lane 6B."""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ecdsa import SECP256k1
from ecdsa.ellipticcurve import INFINITY

G = SECP256k1.generator
CURVE = SECP256k1.curve
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LO = 1 << 134
TOP = (1 << 135) - 1
PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800

LANE6B_LO = 0x6800000000000000000000000000000000
LANE6B_HI = (7 << 132) - 1
LIFT = "20805bb7052b604261808815abccecd65"
SCROLL = 3_000_000
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "lane68_anchor_hunt.log"


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def build_anchors() -> list[tuple[str, int]]:
    anchors: list[tuple[str, int]] = []
    base = "68" + LIFT[2:32]
    anchors.append(("68+lift", int(base.ljust(34, "0"), 16)))
    # B->8 throughout tail
    t8 = LIFT[2:].replace("b", "8")
    anchors.append(("68+lift_b8", int(("68" + t8)[:34].ljust(34, "0"), 16)))
    # only first b in lift (805bb -> 8058b)
    t1 = LIFT[2:].replace("bb", "8b", 1)
    anchors.append(("68+lift_bb8b", int(("68" + t1)[:34].ljust(34, "0"), 16)))
    # 53125 mask blend from prior session
    mask_blend = "338766570535900462808815897c60369"
    anchors.append(("68+mask_blend", int(("68" + mask_blend[2:])[:34].ljust(34, "0"), 16)))
    # dedupe
    seen: set[int] = set()
    out: list[tuple[str, int]] = []
    for name, d in anchors:
        if d not in seen and LANE6B_LO <= d <= LANE6B_HI:
            seen.add(d)
            out.append((name, d))
    return out


def point_matches(pt) -> bool:
    if pt is INFINITY:
        return False
    return pt.x() == PX and pt.y() == PY


def scroll_anchor(name: str, center: int) -> int | None:
    """Incremental +G / -G scroll around center."""
    tested = 0
    pt = center * G
    if point_matches(pt):
        return center

    p = pt
    for i in range(1, SCROLL + 1):
        d = center + i
        if d > LANE6B_HI or d > TOP:
            break
        p = p + G
        tested += 1
        if point_matches(p):
            log(f"*** HIT forward {name} d={d} delta=+{i} tested={tested} ***")
            return d

    # backward
    p = pt
    for i in range(1, SCROLL + 1):
        d = center - i
        if d < LANE6B_LO or d < LO:
            break
        p = p + (-G)
        tested += 1
        if point_matches(p):
            log(f"*** HIT backward {name} d={d} delta=-{i} tested={tested} ***")
            return d

    log(f"  {name} center={hex(center)} scroll done tested={tested}")
    return None


def try_complement(d: int) -> int | None:
    c = N - d
    if LO <= c <= TOP and LANE6B_LO <= c <= LANE6B_HI:
        pt = c * G
        if point_matches(pt):
            return c
    return None


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    log("P135 lane 68 anchor hunt (B~8 reading)")
    log(f"  6B band {hex(LANE6B_LO)} .. {hex(LANE6B_HI)}")
    log(f"  scroll +/- {SCROLL:,} per anchor")

    anchors = build_anchors()
    log(f"anchors ({len(anchors)}):")
    for name, d in anchors:
        log(f"  {name}: {format(d, '064x')}")

    for name, d in anchors:
        hit = scroll_anchor(name, d)
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} ({name}) ***")
            log(f"  hex={format(hit, '064x')}")
            return 0
        alt = try_complement(d)
        if alt:
            log(f"*** X MARKS THE SPOT N-d={alt} ({name}) ***")
            return 0

    elapsed = time.perf_counter() - t0
    log(f"DONE no hit elapsed={elapsed:.1f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
