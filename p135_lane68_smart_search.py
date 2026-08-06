#!/usr/bin/env python3
"""
P135 lane 68 smart hunt:
  1) kanga 6A -> 68 splice (prophecy B~8)
  2) calibrated lift + B/8 variants
  3) wide incremental scroll on ranked anchors
"""

from __future__ import annotations

import itertools
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ecdsa import SECP256k1
from ecdsa.ellipticcurve import INFINITY

from p135_hex_lift_53125 import SEGMENTS, calibrate_segment, extract_segment, lift_all
from puzzle_keys_53125 import parse_53125

G = SECP256k1.generator
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LO = 1 << 134
TOP = (1 << 135) - 1
PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
LANE68_LO = 0x6800000000000000000000000000000000
LANE68_HI = 0x6FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
KANGA = ROOT / "135kanga_2p65_candidates.txt"
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "lane68_smart_hunt.log"
SCROLL = 5_000_000


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def score_hex(got: str, tgt: str) -> int:
    g, t = got.lower(), tgt.lower()
    s = 0
    for a, b in zip(g, t):
        if a == b:
            s += 2
        elif a in "8b" and b in "8b":
            s += 1
    return s


def calibrate_segment_b8(x: str, y: str, pattern: str, target: str) -> tuple[int, int]:
    best = (0, 0)
    best_score = -1
    for xo in range(-40, 41):
        for yo in range(-40, 41):
            got = extract_segment(x, y, pattern, xo, yo)
            sc = score_hex(got, target)
            if sc > best_score:
                best_score = sc
                best = (xo, yo)
    return best


def b8_variants(hexstr: str, max_flips: int = 3) -> set[str]:
    """All b<->8 single/double swaps up to max_flips positions."""
    s = hexstr.lower()
    idx = [i for i, c in enumerate(s) if c in "8b"]
    out = {s}
    for r in range(1, min(max_flips, len(idx)) + 1):
        for combo in itertools.combinations(idx, r):
            chars = list(s)
            for i in combo:
                chars[i] = "8" if chars[i] == "b" else "b"
            out.add("".join(chars))
    return out


def in_lane68(d: int) -> bool:
    return LO <= d <= TOP and LANE68_LO <= d <= LANE68_HI


def point_ok(pt) -> bool:
    return pt is not INFINITY and pt.x() == PX and pt.y() == PY


def try_scalar(d: int) -> int | None:
    if not in_lane68(d):
        return None
    if point_ok(d * G):
        return d
    c = N - d
    if in_lane68(c) and point_ok(c * G):
        return c
    return None


def scroll(center: int, radius: int) -> int | None:
    pt = center * G
    if point_ok(pt):
        return center
    p = pt
    for i in range(1, radius + 1):
        d = center + i
        if d > LANE68_HI:
            break
        p = p + G
        if point_ok(p):
            return d
    p = pt
    for i in range(1, radius + 1):
        d = center - i
        if d < LANE68_LO:
            break
        p = p + (-G)
        if point_ok(p):
            return d
    return None


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    tested = 0
    log("P135 lane68 smart hunt")

    # --- Phase 1: kanga splice 65/64 -> 68 ---
    splice_hits = 0
    scroll_centers: list[int] = []
    for line in KANGA.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip().lower()
        if len(line) != 64 or not line.startswith("0" * 30 + "6"):
            continue
        h68 = line[:30] + "68" + line[32:]
        d = int(h68, 16)
        if not in_lane68(d):
            continue
        tested += 1
        hit = try_scalar(d)
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} kanga-splice68 ***")
            return 0
        splice_hits += 1
        scroll_centers.append(d)
    log(f"Phase 1: {splice_hits} splice68 direct checks, 0 hits")

    # --- Phase 2: lift anchors with B/8 variants ---
    keys = parse_53125()
    k130 = keys[130]
    x130, y130 = format(k130.px, "x"), format(k130.py, "x")
    priv130 = format(k130.d, "x").lower().lstrip("0")
    offsets: list[tuple[int, int]] = []
    pos = 0
    for exp, pat in SEGMENTS:
        seg = priv130[pos : pos + len(exp)]
        offsets.append(calibrate_segment_b8(x130, y130, pat, seg))
        pos += len(exp)
    lifted130 = lift_all(x130, y130, offsets)
    log(f"P130 lift score={score_hex(lifted130,priv130)}/{len(priv130)*2} match={lifted130==priv130}")

    x135 = format(PX, "x")
    y135 = format(PY, "x")
    lift135 = lift_all(x135, y135, offsets)
    tail = lift135[2:]  # drop leading 2 -> replace with 68
    lift_anchors: set[int] = set()
    for tv in b8_variants(tail, max_flips=4):
        sig = ("68" + tv)[:34].ljust(34, "0")
        d = int(sig, 16)
        if in_lane68(d):
            lift_anchors.add(d)
    log(f"Phase 2: {len(lift_anchors)} lift68 B/8 variants")
    for d in lift_anchors:
        tested += 1
        hit = try_scalar(d)
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} lift68 ***")
            return 0
        scroll_centers.append(d)

    # mask blend -> 68
    template = "330766570535900402808800897060309"
    mask = "00e0000000000f00f00b00cf000c000c0"
    blend = list(template)
    lc = list(lift135.zfill(len(template))[-len(template) :])
    for i, m in enumerate(mask):
        if m != "0":
            blend[i] = lc[i]
    blend_hex = "".join(blend)
    for tv in b8_variants(blend_hex[2:], max_flips=3):
        sig = ("68" + tv)[:34].ljust(34, "0")
        d = int(sig, 16)
        if in_lane68(d):
            scroll_centers.append(d)

    # dedupe scroll centers, rank by closeness to median splice
    uniq = sorted(set(scroll_centers))
    if uniq:
        med = uniq[len(uniq) // 2]
    else:
        med = int(("68" + lift135[2:])[:34].ljust(34, "0"), 16)
    ranked = sorted(uniq, key=lambda d: abs(d - med))[:8]
    log(f"Phase 3: scroll +/-{SCROLL:,} on {len(ranked)} anchors (med={hex(med)})")

    for i, center in enumerate(ranked):
        hit = scroll(center, SCROLL)
        tested += 2 * SCROLL
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} scroll anchor#{i} center={hex(center)} ***")
            return 0
        if (i + 1) % 4 == 0:
            log(f"  ... {i+1}/{len(ranked)} anchors done")

    log(f"DONE no hit tested~{tested} elapsed={time.perf_counter()-t0:.1f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
