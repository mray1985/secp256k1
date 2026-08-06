#!/usr/bin/env python3
"""
Phase 10c + quotient layer: m = d*k^-1 vs bridge objects; (b1,b2,b3) integer lifts.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import PUZZLE_LIST, build_config  # noqa: E402
from ecdlp_full_pipeline import (  # noqa: E402
    N,
    compare_bridge_to_scalar_frame,
    compute_scalar_frame,
    concat_point_xy,
    delta,
    p as FIELD_P,
    puzzle_band,
    pubkey_from_scalar,
)
from genesis_calibration import bridge_state  # noqa: E402
from gap_tier_common import observed_offset  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ, recover_r_point_from_sig  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402


def own_row_quotients(cfg) -> tuple[int, int, int]:
    px, rx = cfg.Px, cfg.rx
    Qx = [(x * delta) % N for x in px]
    qx = [(x * delta) % N for x in rx]
    out = []
    for i in range(3):
        lam = (px[i] * pow(rx[i], -1, N)) % N
        num = lam * qx[i] - Qx[i]
        if num % N != 0:
            out.append(0)
        else:
            out.append(num // N)
    return out[0], out[1], out[2]


def bridge_candidates(cfg, st) -> dict[str, int]:
    row = cfg.row
    px, rx = cfg.Px, cfg.rx
    py, ry = cfg.Py, cfg.ry
    lam_p = (px[row] * pow(rx[row], -1, FIELD_P)) % FIELD_P
    lns = st["lambda_ns"]
    oitc = st["oitc"]
    gap = st["gap"]
    cands: dict[str, int] = {
        "Lambda_p": lam_p,
        "Lambda_N_eps": lns[row],
        "Lambda_1": lns[0],
        "Lambda_2": lns[1],
        "Lambda_3": lns[2],
        "Lambda_family": (lns[0] * lns[1] * lns[2]) % N,
        "lambda_yN": (py * pow(ry, -1, N)) % N if py and ry else 0,
        "GAP": gap,
        "shelf2": oitc.shelf2,
        "C_floor": oitc.c_floor,
    }
    b1, b2, b3 = own_row_quotients(cfg)
    cands["b1_own"] = b1
    cands["b2_own"] = b2
    cands["b3_own"] = b3
    cands["b_sum"] = b1 + b2 + b3
    if py and ry:
        pc = concat_point_xy(px[row], py)
        rsz = PUZZLE_RSZ.get(cfg.puzzle_num)
        if rsz:
            rpt = recover_r_point_from_sig(rsz.r)
            if rpt:
                rc = concat_point_xy(rpt[0], rpt[1])
                cands["P_concat_mod_N"] = pc % N
                cands["R_concat_mod_N"] = rc % N
                if rc % N:
                    cands["P_over_R_pack_mod_N"] = (pc * pow(rc % N, -1, N)) % N
    return cands


def analyze_puzzle(n: int, keys: dict) -> list[str]:
    if n not in keys or keys[n].d == 0:
        return []
    pk = keys[n]
    rsz = PUZZLE_RSZ.get(n)
    if rsz is None:
        return [f"P{n}: no RSZ — skip m-frame"]
    k = rsz.k
    if k is None:
        k = rsz.recover_k_from_d(pk.d)
    if not rsz.verify_ecdsa(pk.d) and rsz.k is not None:
        pass  # still run with recovered k

    cfg = build_config(pk)
    st = bridge_state(cfg)
    lo, _, _ = puzzle_band(n)
    frame = compute_scalar_frame(pk.d, k)
    cands = bridge_candidates(cfg, st)
    cands["d"] = pk.d
    cands["k"] = k
    cands["m"] = frame.m
    cands["m_inv"] = frame.m_inv
    rows = compare_bridge_to_scalar_frame(frame=frame, lo=lo, candidates=cands)

    lines = [
        f"P{n}  d_bits={pk.d.bit_length()}  k_bits={k.bit_length()}  "
        f"m_bits={frame.m.bit_length()}  m_inv_bits={frame.m_inv.bit_length()}",
    ]
    for label in ("m", "m_inv", "d", "k"):
        lines.append(f"  exact == {label}: " + ", ".join(r.label for r in rows if getattr(r, f"eq_{label}")))

    closest = sorted(rows, key=lambda r: min(r.diff_m_mod_lo, r.diff_m_inv_mod_lo))[:5]
    lines.append("  closest mod LO to m/m_inv:")
    for r in closest:
        side = "m" if r.diff_m_mod_lo <= r.diff_m_inv_mod_lo else "m_inv"
        dist = min(r.diff_m_mod_lo, r.diff_m_inv_mod_lo)
        lines.append(f"    {r.label}: nearest={side} dist_LO_bits={dist.bit_length()}")

    b1, b2, b3 = cands["b1_own"], cands["b2_own"], cands["b3_own"]
    o = observed_offset(pk.d, st["oitc"].shelf2, lo)
    tests = {
        "b_sum == d": b1 + b2 + b3 == pk.d,
        "b_sum mod LO == o": (b1 + b2 + b3) % lo == o,
        "b_sum == C_floor": b1 + b2 + b3 == st["oitc"].c_floor,
        "b_sum == m": (b1 + b2 + b3) % N == frame.m,
        "b_sum == m_inv": (b1 + b2 + b3) % N == frame.m_inv,
        "b3 == d": b3 == pk.d,
    }
    hits = [k for k, v in tests.items() if v]
    lines.append(f"  quotient tuple: b_bits=({b1.bit_length()},{b2.bit_length()},{b3.bit_length()})  hits={hits or 'none'}")
    lines.append("")
    return lines


def p135_section() -> list[str]:
    from ecdlp_full_pipeline import PuzzleConfig, apply_puzzle_defaults, carry

    lines = ["P135 (no known d/k — structural only)", ""]
    c = PuzzleConfig(puzzle_num=135, row=2)
    apply_puzzle_defaults(c)
    st = bridge_state(c)
    lo, hi, _ = puzzle_band(135)
    lns = st["lambda_ns"]
    row = c.row
    px, rx = c.Px, c.rx
    Qx = [(x * delta) % N for x in px]
    qx = [(x * delta) % N for x in rx]
    lam = lns[row]

    lines.append("  Shift identity (eps row=3):")
    for i in range(3):
        dlam = (lns[i] - lam) % N
        lines.append(f"    s_{i+1} = Λ_{i+1}-Λ_ε  bits={dlam.bit_length()}")

    b1, b2, b3 = own_row_quotients(c)
    lines.append(
        f"  Own-row quotients b_i bits: ({b1.bit_length()}, {b2.bit_length()}, {b3.bit_length()})"
    )
    lines.append(f"  b_sum bits={ (b1+b2+b3).bit_length() }  C_floor bits={st['oitc'].c_floor.bit_length()}")

    rsz = PUZZLE_RSZ[135]
    rpt = recover_r_point_from_sig(rsz.r)
    if rpt and c.Py:
        pc = concat_point_xy(px[row], c.Py)
        rc = concat_point_xy(rpt[0], rpt[1])
        m_pack = (pc * pow(rc % N, -1, N)) % N if rc % N else 0
        lines.append(f"  (P||Py)/(R||Ry) mod N bits={m_pack.bit_length()}  [NOT EC m without k]")
        lines.append(f"  P_concat mod LO bits={(pc % lo).bit_length()}  R_concat mod LO bits={(rc % lo).bit_length()}")

    lines.append("")
    lines.append("  ECDLP gate: d*G==P still OPEN (254 congruence classes tested in pipeline).")
    lines.append("")
    return lines


def main() -> None:
    keys = parse_53125()
    lines = [
        "M-BRIDGE + QUOTIENT LAYER REPORT",
        "Test bridge objects against m=d*k^-1 and m_inv=k*d^-1 (not d alone).",
        "Integer quotients b_i = (Λ_i*qx_i - Qx_i)/N per own-row Λ.",
        "",
    ]

    m_hits = 0
    m_inv_hits = 0
    n_tests = 0
    for n in PUZZLE_LIST:
        if n not in keys or keys[n].d == 0:
            continue
        rsz = PUZZLE_RSZ.get(n)
        if rsz is None:
            continue
        k = rsz.k or rsz.recover_k_from_d(keys[n].d)
        cfg = build_config(keys[n])
        st = bridge_state(cfg)
        lo, _, _ = puzzle_band(n)
        frame = compute_scalar_frame(keys[n].d, k)
        cands = bridge_candidates(cfg, st)
        cands["d"] = keys[n].d
        cands["k"] = k
        cands["m"] = frame.m
        cands["m_inv"] = frame.m_inv
        rows = compare_bridge_to_scalar_frame(
            frame=frame, lo=lo, candidates=cands
        )
        n_tests += 1
        if any(r.eq_m for r in rows):
            m_hits += 1
        if any(r.eq_m_inv for r in rows):
            m_inv_hits += 1
        lines += analyze_puzzle(n, keys)

    lines += [
        f"SUMMARY: puzzles with RSZ+d: {n_tests}",
        f"  any bridge object == m: {m_hits}/{n_tests}",
        f"  any bridge object == m_inv: {m_inv_hits}/{n_tests}",
        "",
        "Note: P115 shows m and m_inv hit exactly as objects; Lambda/Cq/b_i do not.",
        "Shift s_i = Λ_i - Λ_ε is bookkeeping (78/78); not m or d.",
        "",
    ]
    lines += p135_section()

    report = "\n".join(lines)
    print(report)
    out = ROOT / "ARCHIVE" / "m_bridge_quotient_report.txt"
    out.write_text(report + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
