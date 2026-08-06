#!/usr/bin/env python3
"""P135 EC search with known leading form: 30 hex zeros then nibble in 4567."""

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

PREFIX = "0" * 30  # 30 leading zero hex digits in 64-char padded form
VALID_FIRST = "4567"
KANGA = ROOT / "135kanga_2p65_candidates.txt"
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "prefix30_hunt.log"


def matches_prefix30(d: int) -> bool:
    h = format(d, "064x")
    if not h.startswith(PREFIX):
        return False
    n = h[30]
    return n in VALID_FIRST


def ec(d: int) -> bool:
    pt = d * G
    return pt.x() == PX and pt.y() == PY


def try_d(d: int) -> int | None:
    if not matches_prefix30(d) or not (LO <= d <= TOP):
        return None
    for c in (d, N - d):
        if LO <= c <= TOP and matches_prefix30(c) and ec(c):
            return c
    return None


def log(msg: str) -> None:
    print(msg, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def load_kanga() -> list[int]:
    out: list[int] = []
    for line in KANGA.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip().lower()
        if not line or line.startswith("02") or len(line) < 64:
            continue
        if not line.startswith(PREFIX) or line[30] not in VALID_FIRST:
            continue
        d = int(line, 16)
        if LO <= d <= TOP:
            out.append(d)
    return out


def band_from_prefix(first: str, tail_hex: str) -> int | None:
    """Build d = 0x{first}{tail} in 135-bit band (34 sig hex digits after 30 zeros)."""
    sig = first + tail_hex.lower()
    if len(sig) > 34:
        sig = sig[:34]
    sig = sig.zfill(34)  # 135 bits max width in hex
    d = int(sig, 16)
    if LO <= d <= TOP:
        return d
    return None


def main() -> int:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    tested = 0

    log("P135 prefix constraint: 30 hex zeros + first nibble in 4567")
    log(f"  LO={LO} HI={TOP}")
    log(f"  LO hex sig: {format(LO,'064x').lstrip('0')}")
    log(f"  HI hex sig: {format(TOP,'064x').lstrip('0')}")

    # Phase 1: kanga file
    kanga = load_kanga()
    log(f"Phase 1: {len(kanga)} kanga match prefix30+4567")
    for i, d in enumerate(kanga):
        tested += 1
        hit = try_d(d)
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} kanga[{i}] ***")
            return 0

    # Phase 2: hex lift from 53125 (if available)
    try:
        from p135_hex_lift_53125 import lift_all, SEGMENTS, calibrate_segment, extract_segment
        from puzzle_keys_53125 import parse_53125

        k130 = parse_53125()[130]
        x130, y130 = format(k130.px, "x"), format(k130.py, "x")
        priv130 = format(k130.d, "x").lower().lstrip("0")
        offsets = []
        pos = 0
        for exp, pat in SEGMENTS:
            elen = len(exp)
            seg = priv130[pos : pos + elen]
            offsets.append(calibrate_segment(x130, y130, pat, seg))
            pos += elen
        x135 = format(PX, "x")
        y135 = format(PY, "x")
        lifted = lift_all(x135, y135, offsets)
        log(f"Phase 2: lifted135={lifted}")
        for first in VALID_FIRST:
            d = band_from_prefix(first, lifted)
            if d is None:
                continue
            tested += 1
            hit = try_d(d)
            if hit:
                log(f"*** X MARKS THE SPOT d={hit} lift first={first} ***")
                return 0
    except Exception as e:
        log(f"Phase 2 skip: {e}")

    # Phase 3: scroll each first-nibble lane (4,5,6,7) near kanga cluster
    log("Phase 3: lane scroll ±200k around kanga centroid per nibble")
    from collections import defaultdict

    lanes: dict[str, list[int]] = defaultdict(list)
    for d in kanga:
        lanes[format(d, "064x")[30]].append(d)
    for nib, vals in lanes.items():
        center = sum(vals) // len(vals)
        log(f"  lane {nib}: {len(vals)} seeds center~{center}")
        for delta in range(-200_000, 200_001):
            d = center + delta
            if not (LO <= d <= TOP) or not matches_prefix30(d):
                continue
            tested += 1
            hit = try_d(d)
            if hit:
                log(f"*** X MARKS THE SPOT d={hit} lane{nib} delta={delta} ***")
                return 0

    elapsed = time.perf_counter() - t0
    log(f"DONE no hit tested={tested} elapsed={elapsed:.1f}s rate={tested/max(elapsed,1e-9):.0f}/s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
