#!/usr/bin/env python3
"""
Per-nibble F97C03 calibration on P130, apply to P135, direct EC (lane 0x68).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ecdsa import SECP256k1
from puzzle_keys_53125 import parse_53125
from p135_p130_tail_calibrate import (
    SEGMENTS,
    calibrate,
    extract_segment,
    priv_targets,
    score_hex,
)

G = SECP256k1.generator
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LO, TOP = 1 << 134, (1 << 135) - 1
PX135 = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY135 = 46351506704828816385393879789131775975171267756561783641521771795450741674800
LANE68_LO = 0x6800000000000000000000000000000000
LANE68_HI = 0x6FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_f97_nibble_lift.log"

F97_LABEL = "F97C03"
F97_SPAN = 120


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def f97_pattern() -> str:
    for label, pat, _ in SEGMENTS:
        if label == F97_LABEL:
            return pat
    raise KeyError(F97_LABEL)


def calibrate_f97_nibbles(
    x: str, y: str, pattern: str, target: str, span: int = F97_SPAN
) -> tuple[list[tuple[int, int]], str]:
    """Per-nibble offsets: for each position pick slide where that nibble matches."""
    tgt = target.lower()
    nib_offsets: list[tuple[int, int]] = []
    stitched: list[str] = []
    for ni in range(len(tgt)):
        best_off = (0, 0)
        best_score = -1
        best_ch = "0"
        for xo in range(-span, span + 1):
            for yo in range(-span, span + 1):
                got = extract_segment(x, y, pattern, xo, yo)
                if ni >= len(got) or got[ni] != tgt[ni]:
                    continue
                sc = score_hex(got, tgt)
                if sc > best_score:
                    best_score = sc
                    best_off = (xo, yo)
                    best_ch = got[ni]
        nib_offsets.append(best_off)
        stitched.append(best_ch)
    return nib_offsets, "".join(stitched)


def extract_f97_nibbles(
    x: str, y: str, pattern: str, nib_offsets: list[tuple[int, int]]
) -> str:
    out: list[str] = []
    for ni, (xo, yo) in enumerate(nib_offsets):
        got = extract_segment(x, y, pattern, xo, yo)
        out.append(got[ni] if ni < len(got) else "0")
    return "".join(out)


def calibrate_segment_offsets(x: str, y: str, priv: str) -> list[tuple[int, int]]:
    targets = priv_targets(priv)
    offsets: list[tuple[int, int]] = []
    for (label, pat, _n), tgt in zip(SEGMENTS, targets):
        if label == F97_LABEL:
            offsets.append((0, 0))  # replaced by per-nibble table
            continue
        span = 80 if label in ("59F04F28B", "88C", "C9") else 40
        xo, yo, _, _ = calibrate(x, y, pat, tgt, span=span)
        offsets.append((xo, yo))
    return offsets


def lift_with_f97_nibbles(
    x: str,
    y: str,
    seg_offsets: list[tuple[int, int]],
    f97_pat: str,
    f97_nib_offsets: list[tuple[int, int]],
) -> str:
    parts: list[str] = []
    for (label, pat, _n), (xo, yo) in zip(SEGMENTS, seg_offsets):
        if label == F97_LABEL:
            parts.append(extract_f97_nibbles(x, y, f97_pat, f97_nib_offsets))
        else:
            parts.append(extract_segment(x, y, pat, xo, yo))
    return "".join(parts)


def in_lane68(d: int) -> bool:
    return LO <= d <= TOP and LANE68_LO <= d <= LANE68_HI


def ec_hit(d: int) -> int | None:
    for c in (d, N - d):
        if not in_lane68(c):
            continue
        pt = c * G
        if pt.x() == PX135 and pt.y() == PY135:
            return c
    return None


def lane68_variants(lift: str) -> list[tuple[str, int]]:
    out: dict[int, str] = {}
    bases = [
        ("lift", lift),
        ("68", ("68" + lift[2:])[:34].ljust(34, "0")),
        ("68-b8", ("68" + lift[2:].replace("b", "8"))[:34].ljust(34, "0")),
    ]
    for name, sig in bases:
        d = int(sig, 16)
        if in_lane68(d):
            out[d] = name
        dec = str(d)
        for w in (9, 10, 11):
            if len(dec) > w:
                tail = d % (10**w)
                d2 = d - tail + tail * 10 + 1
                if in_lane68(d2):
                    out[d2] = name + "+t1"
    return [(n, d) for d, n in sorted(out.items())]


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    keys = parse_53125()
    k130 = keys[130]
    x130, y130 = format(k130.px, "x"), format(k130.py, "x")
    priv130 = format(k130.d, "x").lower().lstrip("0")
    f97_pat = f97_pattern()
    f97_tgt = priv130[-10:-2]

    log("=== P130 segment offsets (except F97C03) ===")
    seg_offsets = calibrate_segment_offsets(x130, y130, priv130)
    for (label, _, _), off in zip(SEGMENTS, seg_offsets):
        if label != F97_LABEL:
            log(f"  {label}: offset={off}")

    log("")
    log("=== P130 F97C03 per-nibble calibration ===")
    log(f"target={f97_tgt}")
    f97_nib_offs, f97_stitched = calibrate_f97_nibbles(x130, y130, f97_pat, f97_tgt)
    for i, (xo, yo) in enumerate(f97_nib_offs):
        log(f"  nibble {i} '{f97_tgt[i]}': offset=({xo},{yo})")
    log(f"stitched F97={f97_stitched} ok={f97_stitched == f97_tgt}")

    lifted130 = lift_with_f97_nibbles(x130, y130, seg_offsets, f97_pat, f97_nib_offs)
    log(f"P130 full lift={lifted130}")
    log(f"P130 match={lifted130 == priv130}")

    log("")
    log("=== P135 apply (per-nibble F97 offsets from P130) ===")
    x135, y135 = format(PX135, "x"), format(PY135, "x")
    lift135_p130offs = lift_with_f97_nibbles(x135, y135, seg_offsets, f97_pat, f97_nib_offs)
    log(f"P135 lift (P130 nib offsets)={lift135_p130offs}")

    # P135 coords differ: re-calibrate F97 per-nibble with repaired tail target
    f97_hypotheses = [
        ("f897c603", "f897c603"),  # P130 ground-truth tail shape
        ("f0979100", "f0979100"),  # raw segment at (-72,-59)
        ("f8979100", "f8979100"),  # nibble1 only 0->8 on raw
    ]
    lifts135: list[tuple[str, str]] = [("p130offs", lift135_p130offs)]

    for hname, htgt in f97_hypotheses:
        offs135, stitched = calibrate_f97_nibbles(x135, y135, f97_pat, htgt)
        log(f"P135 F97 target {hname}: stitched={stitched}")
        for i, (xo, yo) in enumerate(offs135):
            log(f"  nibble {i} '{htgt[i]}': offset=({xo},{yo})")
        lift = lift_with_f97_nibbles(x135, y135, seg_offsets, f97_pat, offs135)
        lifts135.append((hname, lift))
        log(f"  full lift={lift}")

    tested = 0
    seen: set[int] = set()
    for lift_name, lift135 in lifts135:
        log(f"--- EC lane68 [{lift_name}] ---")
        cands = lane68_variants(lift135)
        log(f"lane68 candidates={len(cands)}")
        for name, d in cands:
            if d in seen:
                continue
            seen.add(d)
            log(f"  {name}: {format(d,'064x')}")
            tested += 2
            hit = ec_hit(d)
            if hit:
                log(f"*** X MARKS THE SPOT d={hit} [{lift_name}/{name}] ***")
                return 0

    log(f"DONE no hit tested={tested} elapsed={time.perf_counter()-t0:.1f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
