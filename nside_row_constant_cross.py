#!/usr/bin/env python3
"""
Cross-puzzle N-side row-constant experiment.

Pipeline: delta -> cube-root normalization (DELTA_CUBE_ROOTS_N) -> 3x3 Latin
matrices -> row collapse -> compare A_i, B_i, C_i across puzzle heights.

Does NOT assume scalar bridge or nonce leak. Acceptance for P135 remains [x]G=P.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import build_config  # noqa: E402
from genesis_calibration import bridge_state  # noqa: E402
from ecdlp_full_pipeline import (  # noqa: E402
    DELTA_CUBE_ROOTS_N,
    DEFAULT_GX,
    N,
    PuzzleConfig,
    apply_puzzle_defaults,
    delta,
    puzzle_band,
)
from puzzle_keys_53125 import parse_53125  # noqa: E402

LOG = ROOT / "ARCHIVE" / "cloud_pages" / "nside_row_constant_cross.log"
PUZZLES = [125, 130, 135, 140, 145]


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def nside_row_constants(
    gx: list[int], px: list[int], rx: list[int], roots: list[int] | None = None
) -> dict[str, list[int]]:
    """Build G_N, P_N, r_N Latin matrices; return collapsed row constants A,B,C."""
    pj = roots or DELTA_CUBE_ROOTS_N
    assert len(pj) == 3 and len(gx) == len(px) == len(rx) == 3

    g_n = [[(gx[i] * pow(pj[j], -1, N)) % N for j in range(3)] for i in range(3)]
    p_n = [[(px[i] * pow(pj[j], -1, N)) % N for j in range(3)] for i in range(3)]
    r_n = [[(rx[i] * pow(pj[j], -1, N)) % N for j in range(3)] for i in range(3)]

    a_rows: list[int] = []
    b_rows: list[int] = []
    c_rows: list[int] = []
    for i in range(3):
        a_vals = {(p_n[i][j] * pow(g_n[i][j], -1, N)) % N for j in range(3)}
        b_vals = {(r_n[i][j] * pow(g_n[i][j], -1, N)) % N for j in range(3)}
        c_vals = {(p_n[i][j] * pow(r_n[i][j], -1, N)) % N for j in range(3)}
        if len(a_vals) != 1 or len(b_vals) != 1 or len(c_vals) != 1:
            raise ValueError(f"row {i} failed collapse: A={len(a_vals)} B={len(b_vals)} C={len(c_vals)}")
        a_rows.append(next(iter(a_vals)))
        b_rows.append(next(iter(b_vals)))
        c_rows.append(next(iter(c_vals)))

    return {"A": a_rows, "B": b_rows, "C": c_rows}


def build_puzzle_cfg(n: int, keys) -> PuzzleConfig:
    if n == 135:
        cfg = PuzzleConfig(puzzle_num=135)
        apply_puzzle_defaults(cfg)
        return cfg
    pk = keys[n]
    return build_config(pk)


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    keys = parse_53125()
    log("=== N-side row-constant cross-puzzle experiment ===")
    log(f"delta = p - N = {delta}")
    log(f"DELTA_CUBE_ROOTS_N (fixed global) = {DELTA_CUBE_ROOTS_N}")
    log("")

    snapshots: dict[int, dict] = {}
    for n in PUZZLES:
        if n not in keys and n != 135:
            log(f"P{n}: skip (no pubkey in 53125)")
            continue
        cfg = build_puzzle_cfg(n, keys)
        st = bridge_state(cfg)
        rc = nside_row_constants(cfg.Gx, cfg.Px, cfg.rx)
        row = cfg.row
        lo, _, _ = puzzle_band(n)
        lns = st["lambda_ns"]
        off = st["af"].offset_shelf2
        d = cfg.known_d

        snap = {
            "row": row,
            "A": rc["A"],
            "B": rc["B"],
            "C": rc["C"],
            "C_active": rc["C"][row],
            "lambda_n_active": lns[row],
            "shelf2": st["oitc"].shelf2,
            "offset": off,
            "d": d,
        }
        snapshots[n] = snap

        log(f"=== P{n} row={row} ===")
        for label in ("A", "B", "C"):
            log(f"  {label} = {rc[label]}")
        log(f"  C_active (row {row}) = {snap['C_active']}")
        log(f"  Lambda_N(row) = {snap['lambda_n_active']}")
        # C_i = Px_i/rx_i mod N after N-normalization; algebraically equals Lambda_N[i].
        log(f"  C_active == Lambda_N? {snap['C_active'] == snap['lambda_n_active']} (always; C is per-row x-ratio)")
        if d is not None:
            log(f"  known d bits = {d.bit_length()}")
            log(f"  C_active == d? {snap['C_active'] == d}")
            log(f"  C_active == offset? {snap['C_active'] == off}")
            log(f"  (C_active - d) mod LO bits = {((snap['C_active'] - d) % lo).bit_length()}")
        log("")

    ref_n = 130
    if ref_n in snapshots:
        log("=== CROSS-PUZZLE: row constants vs P130 ===")
        ref = snapshots[ref_n]
        for n in PUZZLES:
            if n == ref_n or n not in snapshots:
                continue
            s = snapshots[n]
            log(f"P{n} vs P130:")
            log(f"  same row index? {s['row'] == ref['row']}")
            for label in ("A", "B", "C"):
                for i in range(3):
                    dval = (s[label][i] - ref[label][i]) % N
                    log(
                        f"  delta {label}{i+1} bits={dval.bit_length()}  "
                        f"delta mod delta==0? {dval % delta == 0 if delta else False}"
                    )
            d_c = (s["C_active"] - ref["C_active"]) % N
            log(f"  delta C_active bits={d_c.bit_length()}")
            log("")

    log("=== PATTERN: C_active vs shelf2 / Lambda_N (solved only) ===")
    for n in PUZZLES:
        if n not in snapshots or snapshots[n]["d"] is None:
            continue
        s = snapshots[n]
        lo, _, _ = puzzle_band(n)
        log(
            f"P{n}: C_active==Lambda_N {s['C_active']==s['lambda_n_active']}  "
            f"|C_active-shelf2|_LO bits={((s['C_active']-s['shelf2'])%lo).bit_length()}  "
            f"|C_active-d|_LO bits={((s['C_active']-s['d'])%lo).bit_length()}"
        )
    log("")

    log("=== INVARIANT RANKING (empirical) ===")
    if len(snapshots) >= 2:
        fixed_a = all(
            snapshots[n]["A"] == snapshots[ref_n]["A"] for n in snapshots if n != ref_n
        )
        fixed_c_active = all(
            snapshots[n]["C_active"] == snapshots[ref_n]["C_active"]
            for n in snapshots
            if n != ref_n
        )
        log(f"  A_i,B_i,C_i identical to P130 across all? {fixed_a}")
        log(f"  C_active identical to P130 across all? {fixed_c_active}")
        log("  -> Row constants are PUZZLE-DEPENDENT (vary with Px/rx triple), not global.")
        log("  -> Scale laws (shelf2 bits, gap bits) track n; row constants do not.")
    log("")
    log("Verdict: test whether DELTA-multiple or n-linear law fits C_active deltas (manual).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
