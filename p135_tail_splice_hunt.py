#!/usr/bin/env python3
"""
P135 best shot: P130-verified tail splice + lane 0x68 + trailing-1 + tight scroll.
Skips broken F97C03 lift; uses ground-truth P130 tail on calibrated P135 head.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ecdsa import SECP256k1
from p135_p130_tail_calibrate import lift_all

OFFSETS_130 = [
    (-40, 0), (-40, 0), (-40, -40), (-40, -13),
    (-80, -80), (-80, -80), (-72, -59), (-80, -80),
]

G = SECP256k1.generator
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LO, TOP = 1 << 134, (1 << 135) - 1
PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
LANE68_LO = 0x6800000000000000000000000000000000
LANE68_HI = 0x6FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
SCROLL = 1_000_000
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_tail_splice_hunt.log"

P130_PRIV = "33e7665705359f04f28b88cf897c603c9"
P130_TAIL = P130_PRIV[23:]  # f897c603c9


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def in_lane68(d: int) -> bool:
    return LO <= d <= TOP and LANE68_LO <= d <= LANE68_HI


def ec_hit(d: int) -> int | None:
    for c in (d, N - d):
        if not in_lane68(c):
            continue
        pt = c * G
        if pt.x() == PX and pt.y() == PY:
            return c
    return None


def build_anchors() -> list[tuple[str, int]]:
    x135 = format(PX, "x")
    y135 = format(PY, "x")
    lift = lift_all(x135, y135, OFFSETS_130)
    head = lift[:23]  # through 88c (calibrated head)
    if len(head) < 23:
        head = (lift + P130_PRIV[:23])[:23]

    anchors: dict[int, str] = {}

    def add(name: str, sig: str) -> None:
        s = sig.lower().replace(" ", "")
        s = s[:34].ljust(34, "0")
        variants = [
            (name, s),
            (name + ".68", "68" + s[2:]),
        ]
        for label, hexs in variants:
            d = int(hexs, 16)
            if in_lane68(d):
                anchors[d] = label
            dec = str(d)
            for w in (9, 10, 11):
                if len(dec) > w:
                    tail = d % (10**w)
                    d2 = d - tail + tail * 10 + 1
                    if in_lane68(d2):
                        anchors[d2] = label + "+t1"

    add("head+tail", head + P130_TAIL)
    add("lift+f897", lift.replace("f097c603", "f897c603"))
    add("lift+f897", lift.replace("0979100", "897c603c9")[:33] + "9")
    # 53125 template tail blend on head
    template = "330766570535900462808800897060309"
    blend = head + template[len(head) :]
    add("template_blend", blend)
    # kanga splice to 68 with P130 tail length
    kanga_path = ROOT / "135kanga_2p65_candidates.txt"
    if kanga_path.exists():
        for line in kanga_path.read_text().splitlines()[:50]:
            line = line.strip().lower()
            if len(line) == 64:
                body = line[32:]  # keep kanga tail, force 68 prefix
                sig = "68" + body[:32]
                add("kanga68tail", sig[:34])

    return [(n, d) for d, n in sorted(anchors.items())]


def scroll(center: int) -> int | None:
    pt = center * G
    if pt.x() == PX and pt.y() == PY:
        return center
    p = pt
    for i in range(1, SCROLL + 1):
        d = center + i
        if d > LANE68_HI:
            break
        p = p + G
        hit = ec_hit(d)
        if hit:
            return hit
    p = pt
    for i in range(1, SCROLL + 1):
        d = center - i
        if d < LANE68_LO:
            break
        p = p + (-G)
        hit = ec_hit(d)
        if hit:
            return hit
    return None


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    log("P135 tail-splice + lane68 hunt")

    anchors = build_anchors()
    log(f"anchors={len(anchors)}")
    for name, d in anchors[:8]:
        log(f"  {name}: {format(d,'064x')}")

    for name, d in anchors:
        hit = ec_hit(d)
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} [{name}] ***")
            return 0

    ranked = sorted(anchors, key=lambda x: x[1])[:6]
    for i, (name, center) in enumerate(ranked):
        log(f"scroll {i+1}/6 {name}")
        hit = scroll(center)
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} scroll [{name}] ***")
            return 0

    log(f"DONE no hit elapsed={time.perf_counter()-t0:.1f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
