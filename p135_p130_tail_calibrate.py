#!/usr/bin/env python3
"""
P130 tail lift calibration + P135 apply (lane 68 / trailing-1).

Left-align model (see puzzle_stack_align.py):
  Strip leading zeros, put MSD in column 0; puzzle n grows to the RIGHT.
  Puzzle 1's '1' and P130's '3' share the same left column; width = bit_length(d).
"""

from __future__ import annotations

import itertools
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
LANE68_LO = 0x6800000000000000000000000000000000
LANE68_HI = 0x6FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p130_tail_calibrate.log"

# (label, pattern, target slice from priv — None = sequential by label len)
SEGMENTS = [
    ("33E7", "                                             33 E    7", 4),
    ("665", "                       6              6     5", 3),
    ("70", "  7                0", 2),
    ("53", "          5                                               3", 2),
    ("59F04F28B", "           5  9  F 0          4                    F 2   8B", 9),
    ("88C", "   8        8                C", 3),
    ("F97C03", "                    F                   x9                   7    C     x0                               3", 8),
    ("C9", "        C                     9", 2),  # c9
]


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def extract_segment(x: str, y: str, pattern: str, x_offset: int = 0, y_offset: int = 0) -> str:
    x = x.upper()
    y = y.upper()
    out: list[str] = []
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch in " \t":
            i += 1
            continue
        xi = i + x_offset
        yi = i + y_offset
        if ch == "F" and i + 1 < len(pattern) and pattern[i + 1].lower() == "x":
            out.append("F")
            i += 1
            continue
        if ch.lower() == "x":
            out.append(x[xi] if 0 <= xi < len(x) else "0")
            if i + 1 < len(pattern) and pattern[i + 1] in "0123456789ABCDEFabcdef":
                out.append(pattern[i + 1].upper())
                i += 2
                continue
            i += 1
            continue
        if ch in "0123456789ABCDEFabcdef":
            if 0 <= yi < len(y) and y[yi] in "0123456789ABCDEF":
                out.append(y[yi])
            elif 0 <= xi < len(x) and x[xi] in "0123456789ABCDEF":
                out.append(x[xi])
            else:
                out.append(ch.upper())
        elif ch == "F":
            out.append("F")
        i += 1
    return re.sub(r"[^0-9a-f]", "", "".join(out).lower())


def score_hex(got: str, tgt: str) -> int:
    g, t = got.lower(), tgt.lower()
    s = 0
    for a, b in zip(g, t):
        if a == b:
            s += 2
        elif a in "8b" and b in "8b":
            s += 1
    return s + max(0, min(len(g), len(t)) - abs(len(g) - len(t)))


def calibrate(x: str, y: str, pattern: str, target: str, span: int = 80) -> tuple[int, int, str, int]:
    best = (0, 0)
    best_score = -1
    best_got = ""
    tgt = target.lower()
    for xo in range(-span, span + 1):
        for yo in range(-span, span + 1):
            got = extract_segment(x, y, pattern, xo, yo)
            sc = score_hex(got, tgt)
            if sc > best_score:
                best_score = sc
                best = (xo, yo)
                best_got = got
    return best[0], best[1], best_got, best_score


def priv_targets(priv: str) -> list[str]:
    """Slice priv hex using corrected tail lengths."""
    targets: list[str] = []
    pos = 0
    for label, _pat, n in SEGMENTS:
        if label == "C9":
            targets.append(priv[-2:])
        elif label == "F97C03":
            targets.append(priv[-10:-2])  # f897c603
        else:
            targets.append(priv[pos : pos + n])
            pos += n
    return targets


def lift_all(x: str, y: str, offsets: list[tuple[int, int]]) -> str:
    return "".join(
        extract_segment(x, y, pat, xo, yo) for (_, pat, _), (xo, yo) in zip(SEGMENTS, offsets)
    )


def ec_hit(d: int) -> int | None:
    for c in (d, N - d):
        if not (LO <= c <= TOP):
            continue
        pt = c * G
        if pt.x() == PX135 and pt.y() == PY135:
            return c
    return None


def lane68_candidates(lift: str) -> list[int]:
    out: set[int] = set()
    tail = lift.lstrip("0")
    if tail and tail[0] in "23456789abcdef":
        tail = lift[1:] if lift[0] in "23" else lift[2:]
    bases = [lift, "68" + lift[2:], "68" + lift[2:].replace("b", "8")]
    for b in bases:
        for extra in ("", "1", "c9"):
            sig = (b + extra)[:34].ljust(34, "0")
            d = int(sig, 16)
            if LANE68_LO <= d <= LANE68_HI:
                out.add(d)
            # P70 trailing-1 decimal repair
            dec = str(d)
            for w in (9, 10, 11):
                if len(dec) > w:
                    tail_d = d % (10**w)
                    head = d - tail_d
                    d2 = head + tail_d * 10 + 1
                    if LANE68_LO <= d2 <= LANE68_HI:
                        out.add(d2)
    return sorted(out)


def show_left_align(keys: dict, lo: int, hi: int) -> None:
    log("")
    log("=== LEFT-ALIGN (MSD column 0): puzzle 1 vs 130 ===")
    for n in [1, 2, 3, 10, 70, 130]:
        if n not in keys:
            continue
        sig = format(keys[n].d, "x")
        log(f"  P{n:3d} MSD-col0: {sig}")
    log("  P1's '1' and P130's '3' share column 0; each puzzle adds digits to the RIGHT.")
    log("  In 64-hex pad: zeros on the left shrink ~1 nibble per 4 puzzle heights.")
    log("  Binary in 135-bit frame: leftmost-1 marches left (P135 expects col 0).")


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    keys = parse_53125()
    k130 = keys[130]
    x130, y130 = format(k130.px, "x"), format(k130.py, "x")
    priv130 = format(k130.d, "x").lower().lstrip("0")
    targets = priv_targets(priv130)

    show_left_align(keys, LO, TOP)

    log("")
    log("=== P130 tail calibration (wide search) ===")
    log(f"priv130={priv130}")
    offsets: list[tuple[int, int]] = []
    for (label, pat, _n), tgt in zip(SEGMENTS, targets):
        span = 80 if label in ("59F04F28B", "88C", "F97C03", "C9") else 40
        xo, yo, got, sc = calibrate(x130, y130, pat, tgt, span=span)
        ok = got == tgt
        log(f"  {label}: want={tgt} got={got} xo={xo} yo={yo} score={sc} ok={ok}")
        offsets.append((xo, yo))

    lifted130 = lift_all(x130, y130, offsets)
    log(f"P130 lifted={lifted130}")
    log(f"P130 match={lifted130 == priv130}")

    x135, y135 = format(PX135, "x"), format(PY135, "x")
    lift135 = lift_all(x135, y135, offsets)
    log(f"P135 lifted={lift135}")

    tested = 0
    cands = lane68_candidates(lift135)
    log(f"P135 lane68 candidates={len(cands)}")
    for d in cands:
        tested += 1
        hit = ec_hit(d)
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} hex={format(hit,'064x')} ***")
            return 0

    # tight scroll on best 3 (±100k)
    for center in cands[:3]:
        pt = center * G
        p = pt
        for i in range(1, 100_001):
            d = center + i
            if d > LANE68_HI:
                break
            p = p + G
            tested += 1
            hit = ec_hit(d)
            if hit:
                log(f"*** X MARKS THE SPOT d={hit} scroll +{i} ***")
                return 0
        p = pt
        for i in range(1, 100_001):
            d = center - i
            if d < LANE68_LO:
                break
            p = p + (-G)
            tested += 1
            hit = ec_hit(d)
            if hit:
                log(f"*** X MARKS THE SPOT d={hit} scroll -{i} ***")
                return 0

    log(f"DONE no hit tested={tested} elapsed={time.perf_counter()-t0:.1f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
