#!/usr/bin/env python3
"""
P135 unified long hunt — lane 68 (B~8) + P70 trailing-1 repair + lift/kanga.

Runs until hit or exhaustion. Checkpoints to ARCHIVE/cloud_pages/unified_lane68_hunt.log
"""

from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ecdsa import SECP256k1
from ecdsa.ellipticcurve import INFINITY

from p135_hex_lift_53125 import SEGMENTS, extract_segment, lift_all
from p135_lane68_smart_search import (
    calibrate_segment_b8,
    b8_variants,
    in_lane68,
    score_hex,
)
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
OUT = ROOT / "ARCHIVE" / "cloud_pages"
LOG = OUT / "unified_lane68_hunt.log"
CKPT = OUT / "unified_lane68_checkpoint.json"
SCROLL = 12_000_000
MAX_SCROLL_ANCHORS = 16


def log(msg: str) -> None:
    print(msg, flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


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


def sig_to_d(sig: str) -> int | None:
    sig = sig.lower()[:34].ljust(34, "0")
    d = int(sig, 16)
    return d if in_lane68(d) else None


def trailing_one_repairs(d: int) -> set[int]:
    """P70 pattern: last decimal chunk *10+1; hex tail + '1'; segment tail repair."""
    out: set[int] = set()
    if not in_lane68(d):
        return out
    out.add(d)

    h = format(d, "064x").lstrip("0")
    # hex append 1 (trim to 135-bit window)
    for extra in ("1", "01"):
        sig = (h + extra)[-34:]
        d2 = int(sig, 16)
        if in_lane68(d2):
            out.add(d2)

    dec = str(d)
    # P70: last prime 1111390773 -> 11113907731 (10-digit tail *10+1)
    for width in (9, 10, 11, 12):
        if len(dec) <= width:
            continue
        base = 10**width
        tail = d % base
        head = d - tail
        d2 = head + tail * 10 + 1
        if in_lane68(d2):
            out.add(d2)

    # last lift segment (C9) style: 2-hex nibble pair *16+1
    tail2 = d & 0xFF
    d3 = (d & ~0xFF) + tail2 * 16 + 1
    if in_lane68(d3):
        out.add(d3)

    return out


def build_lift_offsets() -> list[tuple[int, int]]:
    k130 = parse_53125()[130]
    x130, y130 = format(k130.px, "x"), format(k130.py, "x")
    priv = format(k130.d, "x").lower().lstrip("0")
    offsets: list[tuple[int, int]] = []
    pos = 0
    for exp, pat in SEGMENTS:
        seg = priv[pos : pos + len(exp)]
        offsets.append(calibrate_segment_b8(x130, y130, pat, seg))
        pos += len(exp)
    return offsets


def collect_anchors() -> list[tuple[str, int]]:
    anchors: dict[int, str] = {}

    def add(name: str, d: int) -> None:
        if in_lane68(d) and d not in anchors:
            anchors[d] = name

    # kanga splice 64/65 -> 68
    for line in KANGA.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip().lower()
        if len(line) == 64 and line.startswith("0" * 30 + "6"):
            h68 = line[:30] + "68" + line[32:]
            add("kanga-splice68", int(h68, 16))

    offsets = build_lift_offsets()
    x135 = format(PX, "x")
    y135 = format(PY, "x")
    lift = lift_all(x135, y135, offsets)
    log(f"lift135={lift}")

    # 68 + lift tail, B/8 variants
    tail = lift[2:]
    for tv in b8_variants(tail, max_flips=5):
        sig = ("68" + tv)[:34]
        d = sig_to_d(sig)
        if d is not None:
            add("lift68", d)

    # mask blend
    template = "330766570535900402808800897060309"
    mask = "00e0000000000f00f00b00cf000c000c0"
    blend = list(template)
    lc = list(lift.zfill(len(template))[-len(template) :])
    for i, m in enumerate(mask):
        if m != "0":
            blend[i] = lc[i]
    blend_hex = "".join(blend)
    for tv in b8_variants(blend_hex[2:], max_flips=4):
        d = sig_to_d(("68" + tv)[:34])
        if d is not None:
            add("mask68", d)

    # trailing-1 repairs on all anchors so far
    base = list(anchors.items())
    for d, _name in base:
        for d2 in trailing_one_repairs(d):
            add("trail1", d2)

    ranked = sorted(anchors.items(), key=lambda kv: kv[0])
    log(f"anchors total={len(ranked)}")
    return [(name, d) for d, name in ranked]


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


def save_ckpt(data: dict) -> None:
    CKPT.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    tested = 0
    log("=== P135 unified lane68 + trailing-1 hunt ===")

    anchors = collect_anchors()

    # Phase A: direct
    for name, d in anchors:
        tested += 1
        hit = try_scalar(d)
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} [{name}] hex={format(hit,'064x')} ***")
            save_ckpt({"hit": hit, "name": name})
            return 0

    log(f"Phase A: {len(anchors)} direct checks, 0 hits")

    # Phase B: scroll top anchors near median
    ds = [d for _, d in anchors]
    med = ds[len(ds) // 2]
    ranked = sorted(anchors, key=lambda kv: abs(kv[1] - med))[:MAX_SCROLL_ANCHORS]
    log(f"Phase B: scroll +/-{SCROLL:,} on {len(ranked)} anchors")

    for idx, (name, center) in enumerate(ranked):
        hit = scroll(center, SCROLL)
        tested += 2 * SCROLL
        save_ckpt(
            {
                "phase": "scroll",
                "anchor_idx": idx,
                "center": hex(center),
                "tested": tested,
                "elapsed": time.perf_counter() - t0,
            }
        )
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} scroll [{name}] center={hex(center)} ***")
            log(f"  hex={format(hit,'064x')}")
            save_ckpt({"hit": hit, "name": name, "center": hex(center)})
            return 0
        log(f"  anchor {idx+1}/{len(ranked)} {name} {hex(center)[:18]}... done")

    elapsed = time.perf_counter() - t0
    log(f"DONE no hit tested~{tested} elapsed={elapsed:.1f}s")
    save_ckpt({"hit": None, "tested": tested, "elapsed": elapsed})
    return 1


if __name__ == "__main__":
    sys.exit(main())
