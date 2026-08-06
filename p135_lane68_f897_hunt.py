#!/usr/bin/env python3
"""P135: F97C03 0->8 repair + lane 0x68 anchors, tight EC only."""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ecdsa import SECP256k1
from ecdsa.ellipticcurve import INFINITY

from p135_p130_tail_calibrate import lift_all
from puzzle_keys_53125 import parse_53125

G = SECP256k1.generator
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LO, TOP = 1 << 134, (1 << 135) - 1
PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
LANE68_LO = 0x6800000000000000000000000000000000
LANE68_HI = 0x6FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
SCROLL = 2_000_000
# cached from p130_tail_calibrate.log (wide search)
OFFSETS_130 = [
    (-40, 0),
    (-40, 0),
    (-40, -40),
    (-40, -13),
    (-80, -80),
    (-80, -80),
    (-72, -59),
    (-80, -80),
]
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "lane68_f897_hunt.log"


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


def b8_variants(s: str) -> set[str]:
    idx = [i for i, ch in enumerate(s.lower()) if ch in "8b"]
    out = {s.lower()}
    for r in range(1, min(4, len(idx)) + 1):
        for combo in itertools.combinations(idx, r):
            chars = list(s.lower())
            for i in combo:
                chars[i] = "8" if chars[i] == "b" else "b"
            out.add("".join(chars))
    return out


def repair_f97_segment(lift: str, priv130: str) -> list[str]:
    """Force F97C03 tail using P130 ground truth + single-nibble repairs."""
    # head = first 23 hex chars (through 88c)
    head = priv130[:23]
    tail_true = priv130[23:]  # f897c603c9
    out = set()
    # apply calibrated head from lift if head matches
    lift_head = lift[:23]
    for h in {head, lift_head}:
        for t in b8_variants(tail_true):
            out.add(h + t)
    # direct lift repairs at f097 -> f897
    for v in b8_variants(lift):
        out.add(v.replace("f097c603", "f897c603"))
        out.add(v.replace("f097", "f897", 1))
    return sorted(out)


def to_lane68_d(sig_hex: str) -> int | None:
    for prefix in ("68", ""):
        if prefix:
            s = ("68" + sig_hex[2:]) if sig_hex.startswith(("2", "3")) else ("68" + sig_hex)
        else:
            s = sig_hex
        s = s[:34].ljust(34, "0")
        d = int(s, 16)
        if in_lane68(d):
            return d
    return None


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
    log("P135 lane68 f897 repair hunt")

    keys = parse_53125()
    k130 = keys[130]
    priv130 = format(k130.d, "x").lower().lstrip("0")
    x135 = format(PX, "x")
    y135 = format(PY, "x")
    lift135 = lift_all(x135, y135, OFFSETS_130)
    log(f"lift135 raw={lift135}")

    lifts = repair_f97_segment(lift135, priv130)
    log(f"repaired lift variants={len(lifts)}")
    for L in lifts[:5]:
        log(f"  sample: {L}")

    tested = 0
    anchors: list[int] = []
    for L in lifts:
        for extra in ("", "1"):
            sig = (L + extra)[:34]
            d = to_lane68_d(sig)
            if d is None:
                continue
            anchors.append(d)
            tested += 1
            hit = ec_hit(d)
            if hit:
                log(f"*** X MARKS THE SPOT d={hit} hex={format(hit,'064x')} ***")
                return 0

    uniq = sorted(set(anchors))
    log(f"direct: {len(uniq)} lane68 anchors, 0 hits")

    for i, center in enumerate(uniq[:8]):
        log(f"scroll {i+1}/8 center={format(center,'064x')}")
        hit = scroll(center)
        tested += 2 * SCROLL
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} scroll anchor#{i} ***")
            return 0

    log(f"DONE no hit tested~{tested}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
