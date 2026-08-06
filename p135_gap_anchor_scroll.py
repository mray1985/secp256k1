#!/usr/bin/env python3
"""Scroll ±2M on top structural P135 anchors (gap_lo, gap_row, lift68)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdsa import SECP256k1
from ecdlp_full_pipeline import N, PuzzleConfig, apply_puzzle_defaults, delta, p, puzzle_band
from gap_tier_common import d_candidates_from_offset
from genesis_calibration import bridge_state
from shift_diagnostic import exact_carry_solutions

G = SECP256k1.generator
PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
SCROLL = 2_000_000
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_gap_anchor_scroll.log"


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def scroll(center: int, lo: int, hi: int, label: str) -> int | None:
    pt = center * G
    if pt.x() == PX and pt.y() == PY:
        log(f"*** HIT d={center} [{label}] ***")
        return center
    p_fwd = pt
    for i in range(1, SCROLL + 1):
        d = center + i
        if d >= hi:
            break
        p_fwd = p_fwd + G
        if p_fwd.x() == PX and p_fwd.y() == PY:
            log(f"*** HIT d={d} [{label}] +{i} ***")
            return d
    p_bwd = pt
    for i in range(1, SCROLL + 1):
        d = center - i
        if d < lo:
            break
        p_bwd = p_bwd + (-G)
        if p_bwd.x() == PX and p_bwd.y() == PY:
            log(f"*** HIT d={d} [{label}] -{i} ***")
            return d
    return None


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    cfg = PuzzleConfig(135)
    apply_puzzle_defaults(cfg)
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(135)
    s2 = st["oitc"].shelf2
    row = cfg.row
    lns = st["lambda_ns"]
    lam_p = (cfg.Px[row] * pow(cfg.rx[row], -1, p)) % p
    lam = (cfg.Px[row] * pow(cfg.rx[row], -1, N)) % N
    Qx = [(x * delta) % N for x in cfg.Px]
    qx = [(x * delta) % N for x in cfg.rx]
    gap_lo = st["gap"] % lo
    gap_row = (lns[row] - lam_p) % lo
    anchors = []
    for name, off in [
        ("gap_lo", gap_lo),
        ("gap_row", gap_row),
        ("s2_shift", exact_carry_solutions(lam, qx[1], Qx[1])[0][0] % lo),
    ]:
        for d, dr in d_candidates_from_offset(s2, off, lo, hi):
            if dr == "+":
                anchors.append((name, d))
    anchors.append(("lift68", int("68805bb705259f04f28b88cf897c603c9", 16)))
    log(f"P135 gap-anchor scroll: {len(anchors)} centers ±{SCROLL}")
    for name, d in anchors:
        hit = scroll(d, lo, hi, name)
        if hit:
            return 0
    log("no hit")
    return 1


if __name__ == "__main__":
    sys.exit(main())
