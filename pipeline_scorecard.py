#!/usr/bin/env python3
"""Score how many puzzles pass each stage of the built pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import PUZZLE_LIST, build_config  # noqa: E402
from genesis_calibration import bridge_state  # noqa: E402
from ecdlp_full_pipeline import (  # noqa: E402
    N,
    PuzzleConfig,
    _HAS_ECDSA,
    add_c_bracket_candidates,
    add_matrix_candidates,
    add_scalar_frame_candidates,
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
    run_bridge_regression,
    verify_d_candidates,
    verify_family_bridge,
    verify_n_side_balance,
    verify_n_y_compression,
)
from hashkeys_rsz import PUZZLE_RSZ, y_roots_from_x  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402


def full_d_test(cfg: PuzzleConfig) -> dict:
    lo, hi, _ = puzzle_band(cfg.puzzle_num)
    py, ry = cfg.Py, cfg.ry
    row = cfg.row
    px, rx = cfg.Px, cfg.rx
    lam_p = (px[row] * pow(rx[row], -1, p)) % p
    lam_n = (px[row] * pow(rx[row], -1, N)) % N
    lam_ns = [(px[i] * pow(rx[i], -1, N)) % N for i in range(3)]
    lam_y_n = (py * pow(ry, -1, N)) % N
    gap = (lam_ns[row] - lam_p) % N
    qx = [(x * delta) % N for x in rx]
    qx_s = [(x * delta) % N for x in px]
    oitc = compute_order_in_the_court(
        lo=lo,
        qx=qx,
        qy=(ry * delta) % N,
        qx_scaled=qx_s,
        qy_scaled=(py * delta) % N,
        lambda_ns=lam_ns,
        lam_y_n=lam_y_n,
    )
    sim = compute_shelf_iteration_matrix(lo, [oitc.shelf2, oitc.shelf3, oitc.shelf_y])
    af = compute_alignment_frame(oitc=oitc, sim=sim, lo=lo, hi=hi, known_d=cfg.known_d)
    n_yc = verify_n_y_compression(px_triple=px, rx_triple=rx, py=py, ry=ry)
    nb = verify_n_side_balance(
        px_triple=px,
        rx_triple=rx,
        gx_triple=cfg.Gx,
        py=py,
        ry=ry,
        ip_mod_p=1,
        ir_mod_p=1,
    )
    lambda_p0 = (px[0] * pow(rx[0], -1, p)) % p
    fb = verify_family_bridge(
        px_triple=px,
        rx_triple=rx,
        py=py,
        ry=ry,
        qx_scaled=qx_s,
        qr_scaled=qx,
        lambda_p=lambda_p0,
        n_balance=nb,
        n_y_compress=n_yc,
        lambda_n_target=lam_n,
    )
    b_x_own: list[int | None] = []
    for i in range(3):
        num_own = lam_ns[i] * qx[i] - qx_s[i]
        ok_own, _, b_own = carry(num_own, N)
        b_x_own.append(b_own if ok_own else None)
    candidates = build_d_candidates(
        lo=lo,
        hi=hi,
        lambda_p=lam_p,
        lambda_ns=lam_ns,
        lam_y_n=lam_y_n,
        lambda_n_target=lam_n,
        b_x_own=b_x_own,
    )
    add_c_bracket_candidates(candidates, oitc.c_floor, oitc.c_plus1, oitc.c_minus1, oitc.c_minus2)
    for track, d_cong in oitc_notebook_d_cong(oitc):
        if d_cong not in {c[1] for c in candidates}:
            candidates.append((f"d congruent ({track})", d_cong, d_cong))
    add_matrix_candidates(candidates, sim)
    add_scalar_frame_candidates(
        candidates, known_d=cfg.known_d, known_k=cfg.known_k, concat_frame=None
    )
    align_cands = build_alignment_candidates(
        af=af,
        oitc=oitc,
        sim=sim,
        lambda_ns=lam_ns,
        gap=gap,
        lambda_p=lam_p,
        lambda_n_target=lam_n,
    )
    seen = {c[1] for c in candidates}
    for name, d, raw in align_cands:
        if d not in seen:
            candidates.append((f"align: {name}", d, raw))
            seen.add(d)
    if cfg.known_d is not None:
        kd = cfg.known_d % N
        if kd not in seen:
            candidates.insert(0, ("known d", kd, kd))
    results, any_hit = verify_d_candidates(candidates, px, py, lo, hi)
    known_hit = any(
        r.hit and r.d % N == (cfg.known_d % N) for r in results
    ) if cfg.known_d else False
    return {
        "known_d_hit": known_hit,
        "any_d_hit": any_hit,
        "n_candidates": len(candidates),
        "n_hits": sum(1 for r in results if r.hit),
    }


def kG_matches_r_both_branches(n: int, k: int, r_sig: int, p: int) -> bool:
    kG = None
    from ecdsa import SECP256k1, SigningKey

    sk = SigningKey.from_secret_exponent(k % N, curve=SECP256k1)
    pt = sk.get_verifying_key().pubkey.point
    kG = (int(pt.x()), int(pt.y()))
    xs: list[int] = []
    for x in (r_sig % N, (r_sig % N) + N):
        if 0 < x < p and x not in xs:
            xs.append(x)
    for x in xs:
        y_sq = (pow(x, 3, p) + 7) % p
        if pow(y_sq, (p - 1) // 2, p) != 1:
            continue
        y_pos, y_neg = y_roots_from_x(x)
        if kG in ((x, y_pos), (x, y_neg)):
            return True
    return False


def main() -> int:
    keys = parse_53125()
    rows: list[dict] = []

    for n in PUZZLE_LIST:
        if n == 135 or n not in keys or keys[n].d == 0:
            if n == 135:
                cfg = PuzzleConfig(puzzle_num=135)
                apply_puzzle_defaults(cfg)
                reg_ok, _ = run_bridge_regression(cfg)
                rows.append(
                    {
                        "n": 135,
                        "d_known": False,
                        "bridge_reg": reg_ok,
                        "shelf2_plus_offset": None,
                        "known_d_hit": None,
                        "k_solvable": None,
                        "has_rsz": n in PUZZLE_RSZ,
                    }
                )
            continue

        pk = keys[n]
        cfg = build_config(pk)
        reg_ok, _ = run_bridge_regression(cfg)
        st = bridge_state(cfg)
        af = st["af"]
        shelf2_ok = (
            (af.shelf2 + af.offset_shelf2) % N == pk.d
            if af.offset_shelf2 is not None
            else False
        )
        dt = full_d_test(cfg) if _HAS_ECDSA else {}
        k_ok = None
        rsz = PUZZLE_RSZ.get(n)
        if rsz is not None:
            k = (pow(rsz.s, -1, N) * (rsz.z + rsz.r * pk.d)) % N
            k_ok = kG_matches_r_both_branches(n, k, rsz.r, p)

        rows.append(
            {
                "n": n,
                "d_known": True,
                "bridge_reg": reg_ok,
                "shelf2_plus_offset": shelf2_ok,
                "known_d_hit": dt.get("known_d_hit"),
                "any_d_hit": dt.get("any_d_hit"),
                "n_hits": dt.get("n_hits"),
                "k_solvable": k_ok,
                "has_rsz": rsz is not None,
            }
        )

    solved = [r for r in rows if r.get("d_known")]
    rsz_solved = [r for r in solved if r.get("has_rsz")]

    lines = [
        "PIPELINE SCORECARD — PUZZLE_LIST (step 5, P5..P135)",
        f"puzzles in batch: {len(rows)}  solved d: {len(solved)}  unsolved: {len(rows) - len(solved)}",
        "",
        "Layer 1 — structural bridge (lambda laws + regression):",
        f"  bridge regression PASS: {sum(1 for r in rows if r['bridge_reg'])}/{len(rows)}",
        "",
        "Layer 2 — shelf alignment frame (needs known d for offset):",
        f"  shelf2 + offset == d: {sum(1 for r in solved if r['shelf2_plus_offset'])}/{len(solved)}",
        "",
        "Layer 3 — EC gate d*G == P from pipeline candidates:",
        f"  true d hits among candidates: {sum(1 for r in solved if r.get('known_d_hit'))}/{len(solved)}",
        f"  any spurious d hits: {sum(1 for r in solved if r.get('any_d_hit'))}/{len(solved)}",
        "",
        "Layer 4 — ECDSA k from solved d (RSZ subset):",
        f"  k*G == R (both y branches): {sum(1 for r in rsz_solved if r.get('k_solvable'))}/{len(rsz_solved)}",
        "",
        f"{'n':>4} {'reg':>3} {'s2+o':>4} {'dG':>3} {'kG':>3} {'RSZ':>3}",
        "-" * 28,
    ]
    for r in rows:
        kG = "Y" if r.get("k_solvable") else ("N" if r.get("k_solvable") is False else "-")
        s2 = "Y" if r.get("shelf2_plus_offset") else ("N" if r.get("d_known") else "-")
        dG = "Y" if r.get("known_d_hit") else ("N" if r.get("d_known") else "-")
        lines.append(
            f"{r['n']:4d} {'Y' if r['bridge_reg'] else 'N':>3} {s2:>4} {dG:>3} {kG:>3} "
            f"{'Y' if r.get('has_rsz') else 'N':>3}"
        )

    text = "\n".join(lines) + "\n"
    print(text)
    out = ROOT / "ARCHIVE" / "pipeline_scorecard.txt"
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
