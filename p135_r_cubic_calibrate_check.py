#!/usr/bin/env python3
"""
Check P135 N-side cubic calibration: nine lambda ratios vs bridge lambda_ns,
shelf2 offset law, and solved-neighbor P130 ground truth.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    DEFAULT_PX,
    DEFAULT_RX,
    DEFAULT_RY,
    N,
    P135_R_TRUE_X,
    PuzzleConfig,
    apply_puzzle_defaults,
    delta,
    p,
    primitive_cube_root_of_unity,
    pubkey_from_scalar,
    puzzle_band,
)
from gap_tier_common import observed_offset  # noqa: E402
from genesis_calibration import bridge_state  # noqa: E402
from p135_160_shelf2_offset_hunt import (  # noqa: E402
    build_cfg,
    ec_hit,
    offset_bits_ok,
    predicted_offset_bits,
)
from puzzle_keys_53125 import parse_53125  # noqa: E402
from unsolved_batch import offset_law_row  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "p135_r_cubic_calibrate_check.txt"

BETA = 55594575648329892869085402983802832744385952214688224221778511981742606582254


def head(v: int, k: int) -> str:
    s = str(v)
    return s[:k] if len(s) >= k else s


def n_gap(rx: int) -> int:
    return ((pow(DEFAULT_RY, 2, N) - 3) - (pow(rx, 3, N) + 4)) % N


def lam_n(px: int, r: int) -> int:
    return (px * pow(r, -1, N)) % N


def lam_p(px: int, r: int) -> int:
    return (px * pow(r, -1, p)) % p


def check_puzzle(n: int, keys: dict, lines: list[str], *, use_true_r: bool) -> None:
    cfg = build_cfg(n, keys) if n != 135 else PuzzleConfig(puzzle_num=135)
    if n == 135:
        apply_puzzle_defaults(cfg)
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(n)
    oitc = st["oitc"]
    lns = st["lambda_ns"]
    gap_val = st["gap"]
    gap_lo = gap_val % lo
    gap_bits = gap_lo.bit_length()
    law_row = offset_law_row(n, cfg.row)
    pred = sorted(predicted_offset_bits(n, law_row))
    pk = keys.get(n)
    px_t = pk.px if pk else cfg.Px[cfg.row]
    py_t = pk.py if pk else cfg.Py

    r_wrong = cfg.rx[cfg.row]
    r_true = P135_R_TRUE_X if n == 135 else None
    w = primitive_cube_root_of_unity(N)

    lines.append(f"=== P{n} use_true_r={use_true_r} row={cfg.row} ===")
    lines.append(f"  shelf2 bits={oitc.shelf2.bit_length()}  offset_bits law {pred}")
    if pk and pk.d:
        off = observed_offset(pk.d, oitc.shelf2, lo)
        lines.append(
            f"  known d bits={pk.d.bit_length()} offset_bits={off.bit_length()} "
            f"offset_ok={offset_bits_ok(off, n, law_row, gap_bits)}"
        )

    # Bridge lambda_ns uses cfg.rx (wrong slot for P135 if row!=1)
    for k in range(3):
        lines.append(
            f"  bridge lambda_ns[{k}] tail ...{str(lns[k])[-3:]}  "
            f"(from rx[{k}] tail ...{str(cfg.rx[k])[-3:]})"
        )

    if n != 135:
        lines.append("")
        return

    lines.append(f"  wrong r=rx[{cfg.row}] ...{str(r_wrong)[-3:]} gap h2={head(n_gap(r_wrong),2)}")
    lines.append(f"  true r_sig       ...{str(r_true)[-3:]} gap h2={head(n_gap(r_true),2)}")
    lines.append("")

    # 9 N ratios: Px[k] / (w^j * r_true)
    lines.append("  --- nine N lambdas lambda[k,j] = Px[k] / (w^j * r_true) ---")
    best = []
    for j in range(3):
        rj = (pow(w, j, N) * r_true) % N if w else r_true
        for k in range(3):
            lam = lam_n(DEFAULT_PX[k], rj)
            match_bridge = lam == lns[k]
            # d candidate from shelf2 + (lam mod lo) style?
            off_cand = lam % lo
            d_cand = (oitc.shelf2 + off_cand) % hi
            if d_cand < lo:
                d_cand = lo + (d_cand % (hi - lo))
            ob = observed_offset(d_cand, oitc.shelf2, lo)
            ob_ok = offset_bits_ok(ob, n, law_row, gap_bits)
            hit = ec_hit(d_cand, px_t, py_t) if ob_ok else False
            gm = head(n_gap(rj), 2) == "14"
            lines.append(
                f"    j={j} k={k} r...{str(rj)[-3:]} lam...{str(lam)[-3:]} "
                f"match_lns[{k}]={match_bridge} gap_row2={gm} off_bits={ob.bit_length()} "
                f"off_ok={ob_ok} ec={hit}"
            )
            best.append((match_bridge, ob_ok, hit, j, k, lam))

    # 9 field ratios with row-2 R_eff only
    lines.append("  --- field Lambdas at row-2 R_eff (tail 368) ---")
    row2_pairs = [(1, 0), (0, 1), (2, 2)]
    for i, j in row2_pairs:
        rf = (pow(BETA, i, p) * DEFAULT_RX[j]) % p
        lp = lam_p(DEFAULT_PX[2], rf)
        ln = lam_n(DEFAULT_PX[2], rf if rf < N else rf)
        lines.append(
            f"    field i={i} j={j} Lambda_p bits={lp.bit_length()} "
            f"lambda_N bits={ln.bit_length()} lam_N tail ...{str(ln)[-3:]}"
        )

    # Corrected cfg: force rx[1]=true r for bridge_state
    lines.append("  --- bridge_state with rx[1]=r_sig (calibrated) ---")
    cfg2 = PuzzleConfig(puzzle_num=135)
    apply_puzzle_defaults(cfg2)
    cfg2.rx = list(cfg2.rx)
    cfg2.rx[1] = r_true
    cfg2.row = 1
    st2 = bridge_state(cfg2)
    for k in range(3):
        lam = lam_n(DEFAULT_PX[k], r_true)
        lines.append(
            f"    k={k} recomputed Px/r_true ...{str(lam)[-3:]} "
            f"bridge lns[{k}] ...{str(st2['lambda_ns'][k])[-3:]} "
            f"match={lam == st2['lambda_ns'][k]}"
        )
    lines.append(f"  calibrated shelf2 bits={st2['oitc'].shelf2.bit_length()}")
    lines.append(f"  original  shelf2 bits={oitc.shelf2.bit_length()}")
    lines.append(f"  shelf2 delta bits={(st2['oitc'].shelf2 - oitc.shelf2).bit_length() if st2['oitc'].shelf2 != oitc.shelf2 else 0}")
    lines.append("")


def main() -> int:
    keys = parse_53125()
    lines = [
        "P135 R CUBIC CALIBRATION CHECK",
        "",
        "Tests:",
        "  1. nine N lambdas Px[k]/(w^j*r_true) vs bridge lambda_ns",
        "  2. row-2 gap + offset-bit law on shelf2+lambda mod LO candidates",
        "  3. bridge_state with rx[1]=r_sig vs default row=2",
        "  4. P130 solved neighbor sanity",
        "",
    ]

    check_puzzle(130, keys, lines, use_true_r=False)
    check_puzzle(135, keys, lines, use_true_r=True)

    # Which j branch for P135 matches lambda_ns[2] (pubkey row)?
    w = primitive_cube_root_of_unity(N)
    cfg = build_cfg(135, keys)
    st = bridge_state(cfg)
    px_row = 2
    target = st["lambda_ns"][px_row]
    lines.append("=== branch select: which j gives Px[2]/r_j == lambda_ns[2]? ===")
    for j in range(3):
        rj = (pow(w, j, N) * P135_R_TRUE_X) % N
        lam = lam_n(DEFAULT_PX[px_row], rj)
        lines.append(
            f"  j={j} r...{str(rj)[-3:]} lam match row2 lns: {lam == target} "
            f"lam...{str(lam)[-6:]} target...{str(target)[-6:]}"
        )
    lines.append("")

    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
