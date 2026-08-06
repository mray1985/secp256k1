#!/usr/bin/env python3
"""Calibrate 53125 digit-lift column maps on P130, apply to P135."""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ecdsa import SECP256k1
from puzzle_keys_53125 import parse_53125

G = SECP256k1.generator
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LO, TOP = 1 << 134, (1 << 135) - 1
PX135 = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY135 = 46351506704828816385393879789131775975171267756561783641521771795450741674800
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "hex_lift_hunt.log"

# pattern line, expected segment, use_x for 'x' markers
SEGMENTS = [
    ("33E7", "                                             33 E    7"),
    ("665", "                       6              6     5"),
    ("70", "  7                0"),
    ("53", "          5                                               3"),
    ("59F04F28B", "           5  9  F 0          4                    F 2   8B"),
    ("88C", "   8        8                C"),
    ("F97C03", "                         Fx9      7             C      x0  3"),
    ("C9", "        C                     9"),
]


def ec(d: int, px: int, py: int) -> bool:
    pt = d * G
    return pt.x() == px and pt.y() == py


def check135(d: int) -> int | None:
    for c in (d, N - d):
        if LO <= c <= TOP and ec(c, PX135, PY135):
            return c
    return None


def extract_segment(x: str, y: str, pattern: str, x_offset: int = 0, y_offset: int = 0) -> str:
    x = x.upper()
    y = y.upper()
    out: list[str] = []
    for i, ch in enumerate(pattern):
        if ch in " \t":
            continue
        xi = i + x_offset
        yi = i + y_offset
        if ch == "x":
            out.append(x[xi] if 0 <= xi < len(x) else "0")
        elif ch.lower() == "x" and i + 1 < len(pattern):
            # x9, x0: x from x string, digit from pattern
            out.append(x[xi] if 0 <= xi < len(x) else "0")
            nxt = pattern[i + 1]
            if nxt in "0123456789ABCDEFabcdef":
                out.append(nxt.upper())
        elif ch in "0123456789ABCDEFabcdef":
            if 0 <= yi < len(y) and y[yi] in "0123456789ABCDEF":
                out.append(y[yi])
            elif 0 <= xi < len(x):
                out.append(x[xi])
            else:
                out.append(ch.upper())
        elif ch == "F":
            out.append("F")
    return re.sub(r"[^0-9a-f]", "", "".join(out).lower())


def calibrate_segment(x: str, y: str, pattern: str, target: str) -> tuple[int, int]:
    best = (0, 0)
    best_score = -1
    tgt = target.lower()
    for xo in range(-20, 21):
        for yo in range(-20, 21):
            got = extract_segment(x, y, pattern, xo, yo)
            score = sum(a == b for a, b in zip(got, tgt))
            if score > best_score:
                best_score = score
                best = (xo, yo)
    return best


def lift_all(x: str, y: str, offsets: list[tuple[int, int]]) -> str:
    parts = []
    for (exp, pat), (xo, yo) in zip(SEGMENTS, offsets):
        parts.append(extract_segment(x, y, pat, xo, yo))
    return "".join(parts)


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    keys = parse_53125()
    k130 = keys[130]
    x130 = format(k130.px, "x")
    y130 = format(k130.py, "x")
    priv130 = format(k130.d, "x").lower().lstrip("0")

    # calibrate per-segment offsets
    offsets: list[tuple[int, int]] = []
    pos = 0
    log("=== P130 segment calibration ===")
    for exp, pat in SEGMENTS:
        elen = len(exp)
        seg = priv130[pos : pos + elen]
        xo, yo = calibrate_segment(x130, y130, pat, seg)
        got = extract_segment(x130, y130, pat, xo, yo)
        log(f"  {exp}: want={seg} got={got} xo={xo} yo={yo} ok={got==seg}")
        offsets.append((xo, yo))
        pos += elen

    lifted130 = lift_all(x130, y130, offsets)
    log(f"P130 full lifted={lifted130} match={lifted130==priv130}")

    # P135
    x135 = format(PX135, "x")
    y135 = format(PY135, "x")
    lifted135 = lift_all(x135, y135, offsets)
    log(f"P135 lifted hex={lifted135}")

    tested = 0
    for hx in [lifted135, lifted135.zfill(64), lifted135.zfill(34)]:
        try:
            d = int(hx, 16)
        except ValueError:
            continue
        if LO <= d <= TOP:
            tested += 2
            hit = check135(d)
            if hit:
                log(f"*** X MARKS THE SPOT d={hit} ***")
                return 0

    # blend template from 53125 line 226 with lifted
    template = "330766570535900402808800897060309"
    mask = "00e0000000000f00f00b00cf000c000c0"
    blend = list(template)
    lc = list(lifted135.zfill(len(template))[-len(template):])
    for i, m in enumerate(mask):
        if m != "0":
            blend[i] = lc[i]
    blend_hex = "".join(blend)
    log(f"P135 mask blend={blend_hex}")

    candidates: set[int] = set()
    for hx in [lifted135, blend_hex, template]:
        v = int(hx, 16)
        candidates.add(v)
        candidates.add(LO + (v % LO))
        candidates.add(LO + ((v * 2) % LO))
        candidates.add(LO + ((v ^ (int(x135[:16], 16))) % LO))

    # packed x||y substring windows (53125 line 229 style)
    pack = x135 + y135
    for start in range(0, len(pack) - 32):
        window = pack[start : start + 34]
        try:
            v = int(window, 16)
            candidates.add(LO + (v % LO))
        except ValueError:
            pass

    tested = 0
    for d in candidates:
        if LO <= d <= TOP:
            tested += 2
            hit = check135(d)
            if hit:
                log(f"*** X MARKS THE SPOT d={hit} ***")
                return 0

    # scroll top candidates
    for base in list(candidates)[:20]:
        if not (LO <= base <= TOP):
            base = LO + (base % LO)
        for delta in range(-50_000, 50_001, 1):
            d = base + delta
            if LO <= d <= TOP:
                tested += 2
                hit = check135(d)
                if hit:
                    log(f"*** X MARKS THE SPOT d={hit} scroll ***")
                    return 0

    log(f"DONE no hit tested={tested} elapsed={time.perf_counter()-t0:.1f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
