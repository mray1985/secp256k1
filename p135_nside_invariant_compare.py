#!/usr/bin/env python3
"""Cross-puzzle N-side invariant comparison (P130, P135, P140, P145)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from genesis_calibration import bridge_state
from ecdlp_full_pipeline import (
    DELTA_CUBE_ROOTS_N,
    DEFAULT_GX,
    DEFAULT_RX,
    DEFAULT_RY,
    N,
    PuzzleConfig,
    all_cube_roots_mod_p,
    apply_puzzle_defaults,
    delta,
    p,
    puzzle_band,
)
from puzzle_keys_53125 import parse_53125

LOG = ROOT / "ARCHIVE" / "cloud_pages" / "nside_invariant_compare.log"
PUZZLES = [130, 135, 140, 145]


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def build_cfg(n: int, pk) -> PuzzleConfig:
    if n == 135:
        cfg = PuzzleConfig(puzzle_num=135)
        apply_puzzle_defaults(cfg)
        return cfg
    cfg = PuzzleConfig(puzzle_num=n, known_d=pk.d)
    apply_puzzle_defaults(cfg)
    px_roots = sorted(all_cube_roots_mod_p((pk.py * pk.py - 7) % p, witness=pk.px))
    cfg.Px = px_roots
    cfg.rx = list(DEFAULT_RX)  # r-family from defaults unless RSZ
    cfg.Py = pk.py
    cfg.ry = DEFAULT_RY
    cfg.Gx = list(DEFAULT_GX)
    cfg.row = px_roots.index(pk.px)
    return cfg


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    keys = parse_53125()
    log("=== delta = p - N (global) ===")
    log(f"delta = {delta}")
    log(f"delta cube roots N (fixed): {DELTA_CUBE_ROOTS_N}")
    log("")

    snapshots: dict[int, dict] = {}
    for n in PUZZLES:
        if n not in keys and n != 135:
            log(f"P{n}: missing from 53125")
            continue
        pk = keys.get(n)
        cfg = build_cfg(n, pk) if pk else PuzzleConfig(puzzle_num=135)
        if n != 135:
            apply_puzzle_defaults(cfg)
        st = bridge_state(cfg)
        af = st["af"]
        lns = st["lambda_ns"]
        lam_p = (cfg.Px[cfg.row] * pow(cfg.rx[cfg.row], -1, p)) % p
        fam = (lns[0] * lns[1] * lns[2]) % N
        lo, _, top = puzzle_band(n)
        snap = {
            "row": cfg.row,
            "lambda_ns": lns,
            "lambda_p": lam_p,
            "family_prod": fam,
            "gap_row_mod_lo": (lns[cfg.row] - lam_p) % lo,
            "defect_lo": (delta + lo) % N,
            "defect_hi": (delta + top) % N,
            "shelf2": st["oitc"].shelf2,
            "offset": af.offset_shelf2,
            "gap": st["gap"],
        }
        snapshots[n] = snap
        log(f"=== P{n} row={cfg.row} ===")
        log(f"  lambda_ns = {lns}")
        log(f"  lambda_p(row) = {lam_p}")
        log(f"  family_prod = {fam}")
        log(f"  gap (bridge_state) = {st['gap']}")
        log(f"  gap_row mod LO = {snap['gap_row_mod_lo']} ({snap['gap_row_mod_lo'].bit_length()} bits)")
        log(f"  defect+LO bits={snap['defect_lo'].bit_length()} defect+TOP bits={snap['defect_hi'].bit_length()}")
        log(f"  shelf2 bits={snap['shelf2'].bit_length()}")
        if pk and pk.d:
            log(f"  known d bits={pk.d.bit_length()}")
        log("")

    if len(snapshots) >= 2:
        log("=== CROSS-PUZZLE INVARIANT CHECK ===")
        ref = snapshots.get(130)
        if ref:
            for n in (135, 140, 145):
                if n not in snapshots:
                    continue
                s = snapshots[n]
                log(f"P{n} vs P130:")
                log(f"  same row? {s['row'] == ref['row']}")
                log(f"  family_prod match? {s['family_prod'] == ref['family_prod']}")
                log(f"  lambda_ns equal? {s['lambda_ns'] == ref['lambda_ns']}")
                d_fam = (s['family_prod'] - ref['family_prod']) % N
                log(f"  delta_family bits={d_fam.bit_length()}")
                log("")

    return 0


if __name__ == "__main__":
    sys.exit(main())
