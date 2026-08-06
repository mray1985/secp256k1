#!/usr/bin/env python3
"""Run full bridge + hunt for Puzzle 140."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from genesis_calibration import bridge_state  # noqa: E402
from ecdlp_full_pipeline import (  # noqa: E402
    N,
    apply_puzzle_defaults,
    build_alignment_candidates,
    build_d_candidates,
    carry,
    compute_alignment_frame,
    compute_order_in_the_court,
    compute_shelf_iteration_matrix,
    delta,
    oitc_notebook_d_cong,
    p,
    puzzle_band,
    pubkey_from_scalar,
    run_bridge_regression,
    verify_d_candidates,
)
from hashkeys_rsz import PUZZLE_RSZ, recover_r_point_from_sig, y_roots_from_x  # noqa: E402
from p135_160_shelf2_offset_hunt import (  # noqa: E402
    ROW_DELTA,
    build_cfg,
    hunt_one,
    predicted_offset_bits,
)
from puzzle_keys_53125 import parse_53125  # noqa: E402

LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p140_pipeline_run.log"


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def r_candidates(r_sig: int) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    xs: list[int] = []
    for x in (r_sig % N, (r_sig % N) + N):
        if 0 < x < p and x not in xs:
            xs.append(x)
    for x in xs:
        y_sq = (pow(x, 3, p) + 7) % p
        if pow(y_sq, (p - 1) // 2, p) != 1:
            continue
        y_pos, y_neg = y_roots_from_x(x)
        for y in (y_pos, y_neg):
            out.append((x, y, "y_even" if y % 2 == 0 else "y_odd"))
    return out


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    n = 140
    keys = parse_53125()
    pk = keys.get(n)
    cfg = build_cfg(n, keys)
    lo, hi, top = puzzle_band(n)

    log(f"=== Puzzle {n} pipeline run ===")
    log("")
    log("TARGET (53125 pubkey)")
    if pk:
        log(f"  Px = {pk.px}")
        log(f"  Py = {pk.py}")
        log(f"  d known = {'yes' if pk.d else 'no'}")
    log("")
    log("CONFIG")
    log(f"  row = {cfg.row}  (Px slot index)")
    log(f"  Px[row] = {cfg.Px[cfg.row]}")
    log(f"  Py = {cfg.Py}")
    log(f"  band LO..HI = [2^139, 2^140)")
    log("")

    reg_ok, reg_msgs = run_bridge_regression(cfg)
    log(f"Bridge regression: {'PASS' if reg_ok else 'FAIL'}")
    for m in reg_msgs:
        log(f"  {m}")

    st = bridge_state(cfg)
    oitc = st["oitc"]
    af = st["af"]
    lns = st["lambda_ns"]
    row = cfg.row
    gap = st["gap"]
    gap_lo = gap % lo
    pred = sorted(predicted_offset_bits(n, row))

    log("")
    log("SHELF / OFFSET SHELL (no known d)")
    log(f"  shelf2 = {oitc.shelf2} ({oitc.shelf2.bit_length()} bits)")
    log(f"  shelf2 mod LO bits = {(oitc.shelf2 % lo).bit_length()}")
    log(f"  gap mod LO = {gap_lo} ({gap_lo.bit_length()} bits)")
    log(f"  row = {row}")
    log(f"  predicted offset_bits (row law): {pred}")
    log(f"  H-10 baseline (n-10): {n - 10}")
    log(f"  C_floor = {oitc.c_floor}")

    rsz = PUZZLE_RSZ.get(n)
    if rsz:
        log("")
        log("RSZ (hashkeys spend tx)")
        log(f"  r = {rsz.r}")
        log(f"  s = {rsz.s}")
        log(f"  z = {rsz.z}")
        log(f"  published k = {rsz.nonce_hex or 'none'}")
        rc = r_candidates(rsz.r)
        log(f"  R lift candidates: {len(rc)}")
        for x, y, lab in rc:
            log(f"    {lab}: x={x}")
        r_pref = recover_r_point_from_sig(rsz.r)
        log(f"  prefer_even_y R = {r_pref}")
        log("  k not solvable without d (one ECDSA equation, two unknowns)")

    log("")
    log("PHASE 17 — d*G candidate scan (no known d injected)")
    lam_p = (cfg.Px[row] * pow(cfg.rx[row], -1, p)) % p
    lam_ns = lns
    lam_y_n = (cfg.Py * pow(cfg.ry, -1, N)) % N
    qx = [(x * delta) % N for x in cfg.rx]
    qx_s = [(x * delta) % N for x in cfg.Px]
    oitc2 = compute_order_in_the_court(
        lo=lo,
        qx=qx,
        qy=(cfg.ry * delta) % N,
        qx_scaled=qx_s,
        qy_scaled=(cfg.Py * delta) % N,
        lambda_ns=lam_ns,
        lam_y_n=lam_y_n,
    )
    sim = compute_shelf_iteration_matrix(lo, [oitc2.shelf2, oitc2.shelf3, oitc2.shelf_y])
    af2 = compute_alignment_frame(oitc=oitc2, sim=sim, lo=lo, hi=hi, known_d=None)
    b_x_own: list[int | None] = []
    for i in range(3):
        ok, _, b = carry(lam_ns[i] * qx[i] - qx_s[i], N)
        b_x_own.append(b if ok else None)
    candidates = build_d_candidates(
        lo=lo,
        hi=hi,
        lambda_p=lam_p,
        lambda_ns=lam_ns,
        lam_y_n=lam_y_n,
        lambda_n_target=lam_ns[row],
        b_x_own=b_x_own,
    )
    for track, d_cong in oitc_notebook_d_cong(oitc2):
        if d_cong not in {c[1] for c in candidates}:
            candidates.append((track, d_cong, d_cong))
    align = build_alignment_candidates(
        af=af2,
        oitc=oitc2,
        sim=sim,
        lambda_ns=lam_ns,
        gap=gap,
        lambda_p=lam_p,
        lambda_n_target=lam_ns[row],
    )
    seen = {c[1] for c in candidates}
    for name, d, raw in align:
        if d not in seen:
            candidates.append((name, d, raw))
            seen.add(d)
    px_target, py_target = cfg.Px[row], cfg.Py
    results, any_hit = verify_d_candidates(candidates, cfg.Px, py_target, lo, hi)
    hits = [r for r in results if r.hit]
    in_band_hits = [r for r in hits if r.in_band]
    log(f"  candidates tested: {len(candidates)}")
    log(f"  EC hits (any): {len(hits)}")
    log(f"  EC hits in-band: {len(in_band_hits)}")
    for r in in_band_hits[:12]:
        log(f"    HIT in-band: {r.name}  d={r.d} ({r.d.bit_length()}b) row={r.matched_row}")
    if len(in_band_hits) > 12:
        log(f"    ... +{len(in_band_hits) - 12} more in-band hits")

    verified = []
    for r in in_band_hits:
        pub_x, pub_y = pubkey_from_scalar(r.d)
        if pub_x == px_target and pub_y == py_target:
            verified.append(r)
    log(f"  hits matching target Px/Py row: {len(verified)}")
    for r in verified:
        log(f"    *** VERIFIED P140 d = {r.d} [{r.name}] ***")

    log("")
    log("SHELF2+OFFSET HUNT (row-calibrated bit filter + EC gate)")
    hunt_rows = hunt_one(n, keys)
    ec_hits = [r for r in hunt_rows if r.get("ec_hit")]
    log(f"  filtered candidates: {len(hunt_rows)}")
    log(f"  EC hits: {len(ec_hits)}")
    for r in ec_hits:
        log(f"    *** HIT d={r['d']} offset_bits={r['offset_bits']} [{r['source']}] ***")
    if not ec_hits:
        log("  no EC hit in hunt window")
        if hunt_rows:
            log("  closest filtered (by offset_bits vs pred):")
            for r in sorted(hunt_rows, key=lambda x: min(abs(x["offset_bits"] - t) for t in pred))[:5]:
                log(
                    f"    d_bits={r['d'].bit_length()} off_bits={r['offset_bits']} "
                    f"gap={r['gap_bits']} src={r['source'][:50]}"
                )

    log("")
    if verified or ec_hits:
        log("RESULT: P140 SOLVED")
    else:
        log("RESULT: P140 OPEN — bridge closed, d not recovered")
    log(f"log -> {LOG}")
    return 0 if (verified or ec_hits) else 1


if __name__ == "__main__":
    raise SystemExit(main())
