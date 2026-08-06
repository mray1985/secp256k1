#!/usr/bin/env python3
"""Focused P135 hunt — notify on EC hit."""

from __future__ import annotations

import argparse
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
KANGA = ROOT / "135kanga_2p65_candidates.txt"
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "x_hunt.log"


def ec(d: int) -> bool:
    pt = d * G
    return pt.x() == PX and pt.y() == PY


def check(d: int) -> int | None:
    for cand in (d, N - d):
        if LO <= cand <= TOP and ec(cand):
            return cand
    return None


def load_kanga() -> list[int]:
    out: list[int] = []
    for line in KANGA.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("02"):
            continue
        try:
            d = int(line, 16)
        except ValueError:
            continue
        if LO <= d <= TOP:
            out.append(d)
    return out


def log(msg: str) -> None:
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def scroll(center: int, radius: int, step: int, label: str, tested: int, t0: float) -> tuple[int | None, int]:
    lo = max(LO, center - radius)
    hi = min(TOP, center + radius)
    d = lo
    while d <= hi:
        tested += 2
        hit = check(d)
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} [{label}] ***")
            return hit, tested
        if (d - lo) and (d - lo) % 500_000 == 0:
            log(f"  {label} d={d} rate={tested/(time.perf_counter()-t0):.0f}/s")
        d += step
    return None, tested


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shelf-radius", type=int, default=10_000_000)
    ap.add_argument("--kanga-radius", type=int, default=50_000)
    ap.add_argument("--step", type=int, default=1)
    args = ap.parse_args()

    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    tested = 0

    kanga = load_kanga()
    log(f"Phase 1: {len(kanga)} kanga direct EC")
    for i, d in enumerate(kanga):
        tested += 2
        hit = check(d)
        if hit:
            log(f"*** X MARKS THE SPOT d={hit} kanga[{i}] ***")
            return 0

    from p135_carry_remainder_report import build_p135_bridge

    shelf2 = build_p135_bridge(puzzle_row=2)["shelf2"]
    d0 = LO + (shelf2 % LO)
    log(f"Phase 2: shelf2 scroll center={d0} radius={args.shelf_radius:,}")
    hit, tested = scroll(d0, args.shelf_radius, args.step, "shelf2", tested, t0)
    if hit:
        return 0

    log(f"Phase 3: kanga local radius={args.kanga_radius:,} x {len(kanga)} seeds")
    for i, d in enumerate(kanga):
        hit, tested = scroll(d, args.kanga_radius, args.step, f"kanga[{i}]", tested, t0)
        if hit:
            return 0
        if i and i % 100 == 0:
            log(f"  kanga seed {i}/{len(kanga)} tested={tested}")

    elapsed = time.perf_counter() - t0
    log(f"DONE no hit tested={tested} elapsed={elapsed:.1f}s rate={tested/max(elapsed,1e-9):.0f}/s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
