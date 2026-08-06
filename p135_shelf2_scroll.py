#!/usr/bin/env python3
"""Tight ±scroll on P135 shelf2-hunt anchors (row=2, offset-calibrated)."""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import N, puzzle_band
from puzzle_keys_53125 import parse_53125

from ecdsa import SECP256k1

PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
G = SECP256k1.generator
SCROLL = 500_000
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_shelf2_scroll.log"
CSV_IN = ROOT / "ARCHIVE" / "p135_160_shelf2_offset_hunt.csv"
MAX_ANCHORS = 8


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def ec_hit_pt(d: int, pt) -> bool:
    x, y = pt.x(), pt.y()
    return x == PX and y == PY


def pick_anchors() -> list[tuple[str, int]]:
    anchors: list[tuple[str, int]] = []
    seen: set[int] = set()

    def add(label: str, d: int) -> None:
        lo, hi, _ = puzzle_band(135)
        if not (lo <= d < hi) or d in seen:
            return
        seen.add(d)
        anchors.append((label, d))

    add("lift68", int("68805bb705259f04f28b88cf897c603c9", 16))
    rows: list[dict] = []
    if CSV_IN.is_file():
        with CSV_IN.open(encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r.get("n") == "135"]
    rows.sort(key=lambda r: (r["source"] != "lift68", r["offset_bits"] != "134", r["source"]))
    for row in rows:
        add(row["source"], int(row["d"]))
    return anchors[:MAX_ANCHORS]


def scroll(center: int, label: str) -> int | None:
    lo, hi, _ = puzzle_band(135)
    pt = center * G
    if ec_hit_pt(center, pt):
        log(f"*** HIT d={center} [{label}] direct ***")
        return center
    p = pt
    for i in range(1, SCROLL + 1):
        d = center + i
        if d >= hi:
            break
        p = p + G
        if ec_hit_pt(d, p):
            log(f"*** HIT d={d} {label} +{i} ***")
            return d
    p = pt
    for i in range(1, SCROLL + 1):
        d = center - i
        if d < lo:
            break
        p = p + (-G)
        if ec_hit_pt(d, p):
            log(f"*** HIT d={d} {label} -{i} ***")
            return d
    return None


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    anchors = pick_anchors()
    log(f"P135 shelf2 scroll: {len(anchors)} anchors, ±{SCROLL}")
    checked = 0
    for label, d in anchors:
        checked += 1 + 2 * SCROLL
        hit = scroll(d, label)
        if hit:
            mirror = (N - hit) % N
            log(f"mirror N-d = {mirror}")
            return 0
    log(f"no hit ({checked:,} checks, {time.perf_counter() - t0:.1f}s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
