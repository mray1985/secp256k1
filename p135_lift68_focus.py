#!/usr/bin/env python3
"""Focused P135 hunt: calibrated lift + F897 tail repair + lane 0x68 only."""

from __future__ import annotations

import itertools
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ecdsa import SECP256k1
from p135_p130_tail_calibrate import lift_all

G = SECP256k1.generator
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LO, TOP = 1 << 134, (1 << 135) - 1
PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
LANE68_LO = 0x6800000000000000000000000000000000
LANE68_HI = 0x6FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
SCROLL = 500_000
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_lift68_focus.log"

OFFSETS_130 = [
    (-40, 0), (-40, 0), (-40, -40), (-40, -13),
    (-80, -80), (-80, -80), (-72, -59), (-80, -80),
]
P130_TAIL = "f897c603c9"


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def in_band_lane68(d: int) -> bool:
    return LO <= d <= TOP and LANE68_LO <= d <= LANE68_HI


def ec_match(d: int) -> int | None:
    for c in (d, N - d):
        if not in_band_lane68(c):
            continue
        pt = c * G
        if pt.x() == PX and pt.y() == PY:
            return c
    return None


def sig68(base: str) -> str:
    b = base.lower()[:34].ljust(34, "0")
    return ("68" + b[2:])[:34].ljust(34, "0")


def variants(lift: str) -> list[tuple[str, str]]:
    head = lift[:23]
    reps = [
        ("lift", lift),
        ("f897", lift.replace("f0979100", "f897c603")),
        ("head+tail", head + P130_TAIL),
        ("f897+68", sig68(lift.replace("f0979100", "f897c603"))),
        ("head+tail+68", sig68(head + P130_TAIL)),
    ]
    # B→8 at each 'b' position (prophecy lane 6B)
    for i, ch in enumerate(lift):
        if ch == "b":
            v = lift[:i] + "8" + lift[i + 1 :]
            reps.append((f"b8@{i}", sig68(v.replace("f0979100", "f897c603"))))
    # 0→8 on F97 segment nibble
    reps.append(("097-to-897", sig68(lift.replace("f097", "f897"))))
    reps.append(("9100-to-c603", sig68(lift.replace("9100", "c603"))))
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name, s in reps:
        s = s[:34].ljust(34, "0")
        if s not in seen:
            seen.add(s)
            out.append((name, s))
    return out


def scroll(center: int, label: str) -> int | None:
    pt = center * G
    if pt.x() == PX and pt.y() == PY:
        return center
    p = pt
    for i in range(1, SCROLL + 1):
        d = center + i
        if d > LANE68_HI:
            break
        p = p + G
        hit = ec_match(d)
        if hit:
            return hit
    p = pt
    for i in range(1, SCROLL + 1):
        d = center - i
        if d < LANE68_LO:
            break
        p = p + (-G)
        hit = ec_match(d)
        if hit:
            return hit
    return None


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    x, y = format(PX, "x"), format(PY, "x")
    lift = lift_all(x, y, OFFSETS_130)
    log(f"lift={lift} ({len(lift)} chars)")

    anchors: list[tuple[str, int]] = []
    for name, sig in variants(lift):
        d = int(sig, 16)
        if in_band_lane68(d):
            anchors.append((name, d))
            log(f"  {name}: {format(d,'064x')}")

    for name, d in anchors:
        hit = ec_match(d)
        if hit:
            log(f"*** HIT d={hit} [{name}] ***")
            return 0

    # scroll top lift-derived only (not kanga)
    priority = ["head+tail+68", "f897+68", "097-to-897", "head+tail", "f897"]
    ranked = []
    for p in priority:
        for name, d in anchors:
            if name == p:
                ranked.append((name, d))
    for name, d in anchors:
        if (name, d) not in ranked:
            ranked.append((name, d))

    for i, (name, center) in enumerate(ranked[:4]):
        log(f"scroll {i+1}/4 {name} ±{SCROLL}")
        hit = scroll(center, name)
        if hit:
            log(f"*** HIT d={hit} scroll [{name}] ***")
            return 0

    log(f"DONE no hit elapsed={time.perf_counter()-t0:.1f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
