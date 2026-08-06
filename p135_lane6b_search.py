#!/usr/bin/env python3
"""P135 search focused on lane 6B: upper half of nibble-6 band [0x68.., 0x6f..]."""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ecdsa import SECP256k1

G = SECP256k1.generator
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LO = 1 << 134
TOP = (1 << 135) - 1
PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800

LANE6_LO = 6 << 132
LANE6_HI = (7 << 132) - 1
LANE6B_LO = 0x6800000000000000000000000000000000
LANE6B_HI = LANE6_HI
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "lane6b_hunt.log"


def ec(d: int) -> bool:
    pt = d * G
    return pt.x() == PX and pt.y() == PY


def try_d(d: int) -> int | None:
    if not (LANE6B_LO <= d <= LANE6B_HI and LO <= d <= TOP):
        return None
    for c in (d, N - d):
        if LANE6B_LO <= c <= LANE6B_HI and LO <= c <= TOP and ec(c):
            return c
    return None


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def mirror_6a_to_6b(d: int) -> int:
    """Reflect offset within lane 6: 6A seeds -> symmetric 6B position."""
    lane6_mid = (LANE6_LO + LANE6_HI) // 2
    return d + (lane6_mid - d) + (lane6_mid - LANE6_LO + 1)
    # simpler: off = d - LANE6_LO; return LANE6B_LO + off


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    tested = 0

    log("P135 lane 6B hunt")
    log(f"  6B range: {hex(LANE6B_LO)} .. {hex(LANE6B_HI)}")

    # Phase 1: hex-lift variants with 6b prefix
    lift = "20805bb7052b604261808815abccecd65"
    anchors: list[int] = []
    for head in ("6b", "68", "69", "6a", "6c", "6d", "6e", "6f"):
        tail = lift[2:] if head == "6b" else lift[1:]
        sig = (head + tail)[:34].ljust(34, "0")
        d = int(sig, 16)
        if LANE6B_LO <= d <= LANE6B_HI:
            anchors.append(d)
    log(f"Phase 1: {len(anchors)} lift anchors")
    for d in anchors:
        tested += 1
        hit = try_d(d)
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} lift anchor ***")
            return 0

    # Phase 2: mirror kanga 6A -> 6B (1612 reflections)
    kanga_path = ROOT / "135kanga_2p65_candidates.txt"
    kanga = [int(l.strip(), 16) for l in kanga_path.read_text().splitlines() if len(l.strip()) == 64]
    lane6_mid = (LANE6_LO + LANE6_HI) // 2
    mirrored: list[int] = []
    for d in kanga:
        off = d - LANE6_LO
        m = LANE6B_LO + off
        if LANE6B_LO <= m <= LANE6B_HI:
            mirrored.append(m)
    log(f"Phase 2: {len(mirrored)} kanga mirrors into 6B")
    for d in mirrored:
        tested += 1
        hit = try_d(d)
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} kanga-mirror ***")
            return 0

    # Phase 3: scroll ±500k around lift 6b anchor + barcode spliced
    center = int(("6b" + lift[2:])[:34].ljust(34, "0"), 16)
    if not (LANE6B_LO <= center <= LANE6B_HI):
        center = (LANE6B_LO + LANE6B_HI) // 2
    log(f"Phase 3: scroll center {hex(center)} +/-500k")
    for delta in range(-500_000, 500_001):
        d = center + delta
        if not (LANE6B_LO <= d <= LANE6B_HI):
            continue
        tested += 1
        hit = try_d(d)
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} scroll delta={delta} ***")
            return 0

    elapsed = time.perf_counter() - t0
    log(f"DONE no hit tested={tested} elapsed={elapsed:.1f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
