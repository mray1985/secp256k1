#!/usr/bin/env python3
"""
Run every analyzed solve/bridge system on unsolved P135–P160.

Systems (EC-gated where applicable):
  1. bridge_regression     — structural laws
  2. lambda_laws           — LAW-P / LAW-N / LAW-X
  3. shelf2_align_hunt     — alignment + bridge terms (row-0 offset law)
  4. phase17_candidates    — full pipeline congruence-class pool
  5. pair_term_regress     — solved-puzzle pair formulas → shelf2+offset
  6. gap_tier_bridge       — bridge terms in gap-1/gap-2 offset intervals
  7. shift_combo_carry     — carry-shift combos (row-calibrated pattern)
  8. carry_band_reps       — carry shift band representatives
  9. tangent_ec_probes     — tangent / chord scalar lifts
 10. bridge_direct_terms   — shelf2 ± each bridge term (row-0 filter)
"""

from __future__ import annotations

import csv
import itertools
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import build_config  # noqa: E402
from ecdlp_full_pipeline import (  # noqa: E402
    N,
    band_representative,
    build_alignment_candidates,
    build_bridge_offset_terms,
    build_d_candidates,
    carry,
    compute_alignment_frame,
    compute_order_in_the_court,
    compute_shelf_iteration_matrix,
    delta,
    oitc_notebook_d_cong,
    p,
    pubkey_from_scalar,
    puzzle_band,
    run_bridge_regression,
    verify_core_lambda_laws,
    verify_d_candidates,
)
from gap_tier_common import (  # noqa: E402
    d_candidates_from_offset,
    gap_interval,
    observed_offset,
)
from genesis_calibration import bridge_state  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ, recover_r_point_from_sig  # noqa: E402
from p135_160_shelf2_offset_hunt import (  # noqa: E402
    ROW_DELTA,
    build_cfg,
    hunt_one,
    offset_bits_ok,
    predicted_offset_bits,
)
from p135_carry_joint import bridge_ints  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402
from shift_diagnostic import exact_carry_solutions  # noqa: E402
from tangent_uniformizer_analysis import tangent_at, with_r_point  # noqa: E402
from unsolved_batch import UNSOLVED_PUZZLES, offset_law_row  # noqa: E402

LOG = ROOT / "ARCHIVE" / "cloud_pages" / "all_systems_batch.log"
CSV = ROOT / "ARCHIVE" / "all_systems_batch.csv"


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


@dataclass
class SystemResult:
    system: str
    n: int
    ok: bool
    candidates: int = 0
    ec_hits: int = 0
    hit_d: str = ""
    hit_source: str = ""
    detail: str = ""


@dataclass
class PuzzleCtx:
    n: int
    cfg: object
    st: dict
    lo: int
    hi: int
    px: int
    py: int
    px_slot: int
    law_row: int
    shelf2: int
    gap_bits: int
    term_map: dict[str, int] = field(default_factory=dict)


def ec_hit(d: int, px: int, py: int) -> bool:
    try:
        x, y = pubkey_from_scalar(d)
        return x == px and y == py
    except Exception:
        return False


def ec_try(d: int, px: int, py: int) -> tuple[bool, int | None]:
    for cand in (d, (N - d) % N):
        if ec_hit(cand, px, py):
            return True, cand
    return False, None


def make_ctx(n: int, keys: dict) -> PuzzleCtx | None:
    pk = keys.get(n)
    if not pk or not pk.px or not pk.py:
        return None
    cfg = build_cfg(n, keys)
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(n)
    px_slot = cfg.row
    law_row = offset_law_row(n, px_slot)
    gap_bits = (st["gap"] % lo).bit_length()
    lam_p = (cfg.Px[px_slot] * pow(cfg.rx[px_slot], -1, p)) % p
    terms = build_bridge_offset_terms(
        oitc=st["oitc"],
        sim=st["sim"],
        lambda_ns=st["lambda_ns"],
        lo=lo,
        hi=hi,
        gap=st["gap"],
        lambda_p=lam_p,
        lambda_n_target=lam_p,
    )
    return PuzzleCtx(
        n=n,
        cfg=cfg,
        st=st,
        lo=lo,
        hi=hi,
        px=pk.px,
        py=pk.py,
        px_slot=px_slot,
        law_row=law_row,
        shelf2=st["oitc"].shelf2,
        gap_bits=gap_bits,
        term_map=dict(terms),
    )


def run_bridge_regression_sys(ctx: PuzzleCtx) -> SystemResult:
    ok, msgs = run_bridge_regression(ctx.cfg)
    return SystemResult("bridge_regression", ctx.n, ok, detail="; ".join(msgs[:3]))


def run_lambda_laws(ctx: PuzzleCtx) -> SystemResult:
    row = ctx.px_slot
    px, rx = ctx.cfg.Px[row], ctx.cfg.rx[row]
    py, ry = ctx.cfg.Py, ctx.cfg.ry
    laws = verify_core_lambda_laws(
        px=px, rx=rx, py=py, ry=ry, row=row,
        px_triple=ctx.cfg.Px, rx_triple=ctx.cfg.rx,
    )
    ok = laws.p_curve_law and laws.n_law
    return SystemResult(
        "lambda_laws", ctx.n, ok,
        detail=f"LAW-P={laws.p_curve_law} LAW-N={laws.n_law}",
    )


def run_shelf2_align_hunt(ctx: PuzzleCtx, keys: dict) -> SystemResult:
    rows = hunt_one(ctx.n, keys, offset_row=ctx.law_row)
    hits = [r for r in rows if r["ec_hit"]]
    r = SystemResult("shelf2_align_hunt", ctx.n, True, len(rows), len(hits))
    if hits:
        h = hits[0]
        r.hit_d = h["d_hex"]
        r.hit_source = h["source"]
    return r


def run_phase17(ctx: PuzzleCtx) -> SystemResult:
    cfg = ctx.cfg
    row = ctx.px_slot
    px, rx, py, ry = cfg.Px, cfg.rx, cfg.Py, cfg.ry
    lo, hi = ctx.lo, ctx.hi
    lam_p = (px[row] * pow(rx[row], -1, p)) % p
    lam_ns = [(px[i] * pow(rx[i], -1, N)) % N for i in range(3)]
    lam_y_n = (py * pow(ry, -1, N)) % N
    gap = (lam_ns[row] - lam_p) % N
    qx = [(x * delta) % N for x in rx]
    qx_s = [(x * delta) % N for x in px]
    oitc = compute_order_in_the_court(
        lo=lo, qx=qx, qy=(ry * delta) % N, qx_scaled=qx_s,
        qy_scaled=(py * delta) % N, lambda_ns=lam_ns, lam_y_n=lam_y_n,
    )
    sim = compute_shelf_iteration_matrix(lo, [oitc.shelf2, oitc.shelf3, oitc.shelf_y])
    af = compute_alignment_frame(oitc=oitc, sim=sim, lo=lo, hi=hi, known_d=None)
    b_x_own: list[int | None] = []
    for i in range(3):
        ok, _, b = carry(lam_ns[i] * qx[i] - qx_s[i], N)
        b_x_own.append(b if ok else None)
    candidates = build_d_candidates(
        lo=lo, hi=hi, lambda_p=lam_p, lambda_ns=lam_ns, lam_y_n=lam_y_n,
        lambda_n_target=lam_ns[row], b_x_own=b_x_own,
    )
    for track, d_cong in oitc_notebook_d_cong(oitc):
        if d_cong not in {c[1] for c in candidates}:
            candidates.append((track, d_cong, d_cong))
    for name, d, raw in build_alignment_candidates(
        af=af, oitc=oitc, sim=sim, lambda_ns=lam_ns, gap=gap,
        lambda_p=lam_p, lambda_n_target=lam_ns[row],
    ):
        if d not in {c[1] for c in candidates}:
            candidates.append((name, d, raw))
    results, _ = verify_d_candidates(candidates, px, py, lo, hi)
    in_band = [r for r in results if r.hit and r.in_band and r.pub_x == ctx.px and r.pub_y == ctx.py]
    r = SystemResult("phase17_candidates", ctx.n, True, len(candidates), len(in_band))
    if in_band:
        r.hit_d = f"{in_band[0].d:064x}"
        r.hit_source = in_band[0].name
    return r


def regress_formulas(keys: dict) -> dict[int, list[str]]:
    """Pair/single bridge formulas that recover solved d, grouped by offset-law row."""
    row_hits: dict[int, dict[str, int]] = {0: {}, 1: {}, 2: {}}
    row_total: dict[int, int] = {0: 0, 1: 0, 2: 0}

    for n in sorted(keys):
        pk = keys[n]
        if pk.d == 0 or n < 70:
            continue
        try:
            cfg = build_config(pk)
            st = bridge_state(cfg)
        except Exception:
            continue
        lo, hi, _ = puzzle_band(n)
        lam_p = (cfg.Px[cfg.row] * pow(cfg.rx[cfg.row], -1, p)) % p
        terms = dict(build_bridge_offset_terms(
            oitc=st["oitc"], sim=st["sim"], lambda_ns=st["lambda_ns"],
            lo=lo, hi=hi, gap=st["gap"], lambda_p=lam_p, lambda_n_target=lam_p,
        ))
        shelf2 = st["oitc"].shelf2
        law_r = offset_law_row(n, cfg.row)
        row_total[law_r] = row_total.get(law_r, 0) + 1
        items = list(terms.items())
        for (na, va), (nb, vb) in itertools.combinations(items, 2):
            for op_name, off in (
                (f"{na}+{nb}", (va + vb) % lo),
                (f"{na}-{nb}", (va - vb) % lo),
                (f"{nb}-{na}", (vb - va) % lo),
            ):
                for d in (shelf2 + off, shelf2 - off, shelf2 + off - lo, shelf2 - off + lo):
                    if lo <= d < hi and d == pk.d:
                        row_hits[law_r][op_name] = row_hits[law_r].get(op_name, 0) + 1
        for name, off in terms.items():
            for d in (shelf2 + off, shelf2 - off, shelf2 + off - lo, shelf2 - off + lo):
                if lo <= d < hi and d == pk.d:
                    key = f"single:{name}"
                    row_hits[law_r][key] = row_hits[law_r].get(key, 0) + 1

    out: dict[int, list[str]] = {}
    for row in (0, 1, 2):
        ranked = sorted(row_hits[row].items(), key=lambda x: -x[1])
        # row 0 cluster: keep any hit; others require ≥2 for stability
        min_hits = 1 if row == 0 else 2
        out[row] = [name for name, cnt in ranked if cnt >= min_hits]
    return out


def formulas_for_puzzle(ctx: PuzzleCtx, formulas: dict[int, list[str]]) -> list[str]:
    """Merge offset-law row formulas with px-slot row fallback."""
    seen: set[str] = set()
    out: list[str] = []
    for row in (ctx.law_row, ctx.px_slot):
        for name in formulas.get(row, []):
            if name not in seen:
                seen.add(name)
                out.append(name)
    return out


def run_pair_regress(ctx: PuzzleCtx, formula_list: list[str]) -> SystemResult:
    lo, hi = ctx.lo, ctx.hi
    shelf2 = ctx.shelf2
    tm = ctx.term_map
    seen: set[int] = set()
    hits = 0
    hit_d = ""
    hit_src = ""

    def test_d(name: str, d: int) -> None:
        nonlocal hits, hit_d, hit_src
        if d in seen or not (lo <= d < hi):
            return
        seen.add(d)
        ok, got = ec_try(d, ctx.px, ctx.py)
        if ok and got is not None:
            hits += 1
            hit_d = f"{got:064x}"
            hit_src = name

    for formula in formula_list[:50]:
        if formula.startswith("single:"):
            off = tm.get(formula[7:])
            if off is None:
                continue
            if not offset_bits_ok(off, ctx.n, ctx.law_row, ctx.gap_bits):
                continue
            for d, _ in d_candidates_from_offset(shelf2, off, lo, hi):
                test_d(formula, d)
        elif "+" in formula:
            na, nb = formula.split("+", 1)
            if na not in tm or nb not in tm:
                continue
            off = (tm[na] + tm[nb]) % lo
            if not offset_bits_ok(off, ctx.n, ctx.law_row, ctx.gap_bits):
                continue
            for d, _ in d_candidates_from_offset(shelf2, off, lo, hi):
                test_d(formula, d)
        elif "-" in formula:
            na, nb = formula.split("-", 1)
            if na not in tm or nb not in tm:
                continue
            off = (tm[na] - tm[nb]) % lo
            if not offset_bits_ok(off, ctx.n, ctx.law_row, ctx.gap_bits):
                continue
            for d, _ in d_candidates_from_offset(shelf2, off, lo, hi):
                test_d(formula, d)

    return SystemResult(
        "pair_term_regress", ctx.n, True, len(seen), hits,
        hit_d, hit_src, detail=f"formulas={len(formula_list)}",
    )


def run_gap_tier_bridge(ctx: PuzzleCtx) -> SystemResult:
    lo, hi = ctx.lo, ctx.hi
    shelf2 = ctx.shelf2
    seen: set[int] = set()
    hits = 0
    hit_d = ""
    hit_src = ""

    for gap in (1, 2):
        _, o_lo, o_hi = gap_interval(ctx.n, gap)
        for name, off in ctx.term_map.items():
            if not (o_lo <= off < o_hi):
                continue
            for d, dr in d_candidates_from_offset(shelf2, off, lo, hi):
                if d in seen:
                    continue
                seen.add(d)
                ok, got = ec_try(d, ctx.px, ctx.py)
                if ok and got is not None:
                    hits += 1
                    hit_d = f"{got:064x}"
                    hit_src = f"gap{gap}:{name}:{dr}"

    return SystemResult("gap_tier_bridge", ctx.n, True, len(seen), hits, hit_d, hit_src)


def shifts_mod_lo(ctx: PuzzleCtx) -> list[int]:
    lo = ctx.lo
    row = ctx.px_slot
    px, rx = ctx.cfg.Px, ctx.cfg.rx
    lam = (px[row] * pow(rx[row], -1, N)) % N
    Qx = [(x * delta) % N for x in px]
    qx = [(x * delta) % N for x in rx]
    out: list[int] = []
    for i in range(3):
        sols = exact_carry_solutions(lam, qx[i], Qx[i])
        if sols:
            out.append(sols[0][0] % lo)
        else:
            out.append(0)
    return out


def run_shift_combo(ctx: PuzzleCtx) -> SystemResult:
    lo, hi = ctx.lo, ctx.hi
    shelf2 = ctx.shelf2
    sm = shifts_mod_lo(ctx)
    s1, s2m, s3 = sm
    lns = ctx.st["lambda_ns"]
    lam_p = (ctx.cfg.Px[ctx.px_slot] * pow(ctx.cfg.rx[ctx.px_slot], -1, p)) % p
    offs = {
        "s1": s1, "s2": s2m, "s3": s3,
        "s1+s2": (s1 + s2m) % lo,
        "s1-s2": (s1 - s2m) % lo,
        "s2-s1": (s2m - s1) % lo,
        "s1+s2+s3": (s1 + s2m + s3) % lo,
        "gap_row": (lns[ctx.px_slot] - lam_p) % lo,
        "gap_lo": ctx.st["gap"] % lo,
    }
    hits = 0
    hit_d = ""
    hit_src = ""
    for name, off in offs.items():
        if not offset_bits_ok(off, ctx.n, ctx.law_row, ctx.gap_bits):
            continue
        for d, dr in d_candidates_from_offset(shelf2, off, lo, hi):
            ok, got = ec_try(d, ctx.px, ctx.py)
            if ok and got is not None:
                hits += 1
                hit_d = f"{got:064x}"
                hit_src = f"{name}:{dr}"
    return SystemResult("shift_combo_carry", ctx.n, True, len(offs), hits, hit_d, hit_src)


def run_carry_band(ctx: PuzzleCtx) -> SystemResult:
    lo, hi = ctx.lo, ctx.hi
    b = bridge_ints(ctx.cfg)
    hits = 0
    hit_d = ""
    hit_src = ""
    tested = 0
    for i in range(3):
        sh = b["shifts"][i]
        if not sh:
            continue
        d = band_representative(sh[0], lo, hi)
        tested += 1
        ok, got = ec_try(d, ctx.px, ctx.py)
        if ok and got is not None:
            hits += 1
            hit_d = f"{got:064x}"
            hit_src = f"carry_row{i+1}"
    return SystemResult("carry_band_reps", ctx.n, True, tested, hits, hit_d, hit_src)


def run_tangent_probes(ctx: PuzzleCtx) -> SystemResult:
    lo, hi = ctx.lo, ctx.hi
    shelf2 = ctx.shelf2
    td = tangent_at(ctx.px, ctx.py)
    rx_w, ry_w = ctx.cfg.rx[ctx.px_slot], ctx.cfg.ry
    rsz = PUZZLE_RSZ.get(ctx.n)
    if rsz:
        rpt = recover_r_point_from_sig(rsz.r)
        if rpt:
            rx_w, ry_w = rpt
    td = with_r_point(td, rx_w, ry_w)
    m_gap = (td.slope_m - td.chord_to_rx) % p if td.chord_to_rx is not None else 0
    lam = td.lam_p or 1
    m_ratio = (td.slope_m * pow(lam, -1, p)) % p
    raw = [
        ("m mod N", td.slope_m % N),
        ("m-chord mod N", m_gap % N),
        ("m/Lambda mod N", m_ratio % N),
        ("shelf2+(m mod LO)", shelf2 + (td.slope_m % lo)),
        ("shelf2+(m-chord mod LO)", shelf2 + (m_gap % lo)),
        ("shelf2+(m/Lambda mod LO)", shelf2 + (m_ratio % lo)),
    ]
    hits = 0
    hit_d = ""
    hit_src = ""
    for name, d in raw:
        d %= N
        if not (lo <= d < hi):
            continue
        ok, got = ec_try(d, ctx.px, ctx.py)
        if ok and got is not None:
            hits += 1
            hit_d = f"{got:064x}"
            hit_src = name
    return SystemResult("tangent_ec_probes", ctx.n, True, len(raw), hits, hit_d, hit_src)


def run_bridge_direct(ctx: PuzzleCtx) -> SystemResult:
    lo, hi = ctx.lo, ctx.hi
    shelf2 = ctx.shelf2
    seen: set[int] = set()
    hits = 0
    hit_d = ""
    hit_src = ""
    for name, off in ctx.term_map.items():
        if not offset_bits_ok(off, ctx.n, ctx.law_row, ctx.gap_bits):
            continue
        for d, dr in d_candidates_from_offset(shelf2, off, lo, hi):
            if d in seen:
                continue
            seen.add(d)
            ok, got = ec_try(d, ctx.px, ctx.py)
            if ok and got is not None:
                hits += 1
                hit_d = f"{got:064x}"
                hit_src = f"{name}:{dr}"
    return SystemResult("bridge_direct_terms", ctx.n, True, len(seen), hits, hit_d, hit_src)


def main() -> int:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("", encoding="utf-8")
    keys = parse_53125()
    t0 = time.time()

    log("=== ALL SYSTEMS BATCH — P135 P140 P145 P150 P155 P160 ===")
    log(f"puzzles: {list(UNSOLVED_PUZZLES)}")
    log("offset_law_row=0 for all (n≡0 mod 5)")
    log("")

    formulas = regress_formulas(keys)
    log(f"Pair-term regression formulas (≥2 hits on solved): row0={len(formulas[0])} row1={len(formulas[1])} row2={len(formulas[2])}")
    log("")

    all_results: list[SystemResult] = []
    any_solve = False

    import p135_160_shelf2_offset_hunt as shelf_mod
    shelf_mod.LOG = LOG

    for n in UNSOLVED_PUZZLES:
        ctx = make_ctx(n, keys)
        if ctx is None:
            log(f"P{n}: missing pubkey in 53125 — skip")
            continue
        pred = sorted(predicted_offset_bits(n, ctx.law_row))
        log(f"--- P{n} px_slot={ctx.px_slot} law_row={ctx.law_row} pred_off={pred} gap_bits={ctx.gap_bits} ---")

        systems = [
            run_bridge_regression_sys(ctx),
            run_lambda_laws(ctx),
            run_phase17(ctx),
            run_pair_regress(ctx, formulas_for_puzzle(ctx, formulas)),
            run_gap_tier_bridge(ctx),
            run_shift_combo(ctx),
            run_carry_band(ctx),
            run_tangent_probes(ctx),
            run_bridge_direct(ctx),
            run_shelf2_align_hunt(ctx, keys),
        ]
        for sr in systems:
            all_results.append(sr)
            flag = " *** SOLVED ***" if sr.ec_hits else ""
            if sr.ec_hits:
                any_solve = True
            if sr.system in ("bridge_regression", "lambda_laws"):
                log(f"  {sr.system:22s} {'PASS' if sr.ok else 'FAIL'}  {sr.detail}{flag}")
            else:
                log(
                    f"  {sr.system:22s} cand={sr.candidates:4d} hits={sr.ec_hits}{flag}"
                    + (f"  d={sr.hit_d} [{sr.hit_source}]" if sr.ec_hits else "")
                )
        log("")

    with CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["system", "n", "ok", "candidates", "ec_hits", "hit_d", "hit_source", "detail"],
        )
        w.writeheader()
        for sr in all_results:
            w.writerow({
                "system": sr.system,
                "n": sr.n,
                "ok": sr.ok,
                "candidates": sr.candidates,
                "ec_hits": sr.ec_hits,
                "hit_d": sr.hit_d,
                "hit_source": sr.hit_source,
                "detail": sr.detail,
            })

    log("=== MATRIX (ec_hits per system x puzzle) ===")
    systems = sorted({r.system for r in all_results})
    log(f"{'system':22s} " + " ".join(f"P{n:>3}" for n in UNSOLVED_PUZZLES))
    for sys_name in systems:
        row = f"{sys_name:22s} "
        for n in UNSOLVED_PUZZLES:
            sub = [r for r in all_results if r.system == sys_name and r.n == n]
            if not sub:
                row += "  - "
            elif sys_name in ("bridge_regression", "lambda_laws"):
                row += "  P " if sub[0].ok else "  F "
            else:
                row += f"{sub[0].ec_hits:4d} "
        log(row)

    elapsed = time.time() - t0
    log("")
    log(f"elapsed={elapsed:.1f}s")
    log(f"csv -> {CSV}")
    log(f"log -> {LOG}")
    log("RESULT: SOLVED" if any_solve else "RESULT: all six still OPEN")
    return 0 if any_solve else 1


if __name__ == "__main__":
    raise SystemExit(main())
