#!/usr/bin/env python3
"""Continue P135 lane-68 hunt: correct anchors + wider scroll."""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ecdsa import SECP256k1
from p135_f97_nibble_lift import (
    calibrate_f97_nibbles,
    calibrate_segment_offsets,
    ec_hit,
    f97_pattern,
    in_lane68,
    lift_with_f97_nibbles,
)
from puzzle_keys_53125 import parse_53125

G = SECP256k1.generator
LANE68_LO = 0x6800000000000000000000000000000000
LANE68_HI = 0x6FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
SCROLL = 2_000_000
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_continue_hunt.log"

BEST_LIFTS = [
    ("f897c603", "20805bb705259f04f28b88cf897c603c9"),
    ("f897c60d", "20805bb705259f04f28b88cf897c60dc9"),
    ("f0979100", "20805bb705259f04f28b88cf0979100c9"),
    ("f8979100", "20805bb705259f04f28b88cf8979100c9"),
]


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def sig_lane68(lift33: str) -> str:
    s = lift33.lower()[:33]
    return ("68" + s[2:])[:34].ljust(34, "0")


def anchors_from_lift(name: str, lift: str) -> list[tuple[str, int]]:
    out: dict[int, str] = {}
    for label, sig in [
        ("68", sig_lane68(lift)),
        ("68-b8", sig_lane68(lift.replace("b", "8"))),
    ]:
        d = int(sig, 16)
        if in_lane68(d):
            out[d] = f"{name}/{label}"
        dec = str(d)
        for w in (9, 10, 11):
            if len(dec) > w:
                tail = d % (10**w)
                d2 = d - tail + tail * 10 + 1
                if in_lane68(d2):
                    out[d2] = f"{name}/{label}+t1"
    return sorted((n, d) for d, n in out.items())


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
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"\n--- continue {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")

    t0 = time.perf_counter()
    keys = parse_53125()
    k130 = keys[130]
    x130, y130 = format(k130.px, "x"), format(k130.py, "x")
    priv130 = format(k130.d, "x").lower().lstrip("0")
    f97_pat = f97_pattern()
    seg_offs = calibrate_segment_offsets(x130, y130, priv130)
    offs_f897, _ = calibrate_f97_nibbles(
        format(PX, "x"), format(PY, "x"), f97_pat, "f897c603"
    )
    lift_live = lift_with_f97_nibbles(
        format(PX, "x"), format(PY, "x"), seg_offs, f97_pat, offs_f897
    )
    log(f"live f897 lift={lift_live}")

    ranked: list[tuple[str, int]] = []
    seen: set[int] = set()
    priority = [
        int(sig_lane68("20805bb705259f04f28b88cf897c603c9"), 16),
        int(sig_lane68("20805bb705259f04f28b88cf897c60dc9"), 16),
    ]
    for d in priority:
        if in_lane68(d) and d not in seen:
            seen.add(d)
            ranked.append(("priority/68", d))

    for name, lift in BEST_LIFTS:
        for label, d in anchors_from_lift(name, lift):
            if d not in seen:
                seen.add(d)
                ranked.append((label, d))

    log(f"anchors={len(ranked)} scroll=+/-{SCROLL}")
    for label, d in ranked[:10]:
        log(f"  {label}: {format(d,'064x')}")

    tested = 0
    for label, d in ranked:
        tested += 2
        hit = ec_hit(d)
        if hit:
            log(f"*** HIT d={hit} direct [{label}] ***")
            return 0

    scroll_list = ranked[:6]
    for i, (label, center) in enumerate(scroll_list):
        log(f"scroll {i+1}/{len(scroll_list)} {label}")
        hit = scroll(center, label)
        if hit:
            return 0
        tested += SCROLL * 2

    log(f"DONE no hit tested~{tested} elapsed={time.perf_counter()-t0:.1f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
