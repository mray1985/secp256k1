#!/usr/bin/env python3
"""
Catalog mathematical equivalences across all puzzles; notate which hold per puzzle.

Outputs:
  ARCHIVE/hinge_equivalence_catalog.txt   — full report + inverted index
  ARCHIVE/hinge_equivalence_catalog.csv   — per-puzzle equivalence flags
"""

from __future__ import annotations

import csv
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from compare_family_mirror_batch import build_config  # noqa: E402
from ecdlp_full_pipeline import N, all_cube_roots_mod_p, p, puzzle_band, y_roots  # noqa: E402
from genesis_calibration import bridge_state  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125

REPORT = ROOT / "ARCHIVE" / "hinge_equivalence_catalog.txt"
CSV_OUT = ROOT / "ARCHIVE" / "hinge_equivalence_catalog.csv"

PN = p - N
TIGHT = 0.05
VERY_TIGHT = 0.01


def frac(x: float) -> float:
    return x - math.floor(x)


def wrap_diff(a: float, b: float) -> float:
    d = a - b
    return min(abs(d), abs(d + 1), abs(d - 1))


def sgap(a: float, b: float) -> float:
    d = a - b
    if d > 0.5:
        d -= 1
    if d < -0.5:
        d += 1
    return d


def f2s(v: int) -> float:
    getcontext().prec = 80
    v = int(v) % p
    if v <= 0:
        return float("nan")
    ln = float(Decimal(v).ln() / Decimal(2).ln()) / 2
    return ln - math.floor(ln)


def l2(v: int) -> float:
    getcontext().prec = 80
    return float(Decimal(int(v)).ln() / Decimal(2).ln())


def band_frac(d: int, n: int) -> float:
    return frac(math.log2(d) - (n - 1))


def band_rep(c: int, lo: int) -> int:
    return lo + (c % lo)


@dataclass
class PuzzleRow:
    n: int
    solved: bool
    d: int
    px: int
    py: int
    true_slot: int


def load_puzzles() -> list[PuzzleRow]:
    keys = parse_53125()
    rows: list[PuzzleRow] = []
    seen: set[int] = set()

    for n, pk in sorted(keys.items()):
        if pk.px <= 0 or pk.py <= 0:
            continue
        tr = 0
        if pk.d > 0:
            try:
                tr = build_config(pk).row
            except Exception:
                tr = 0
        rows.append(PuzzleRow(n, pk.d > 0, pk.d, pk.px, pk.py, tr))
        seen.add(n)

    for n, rsz in sorted(PUZZLE_RSZ.items()):
        if n in seen or not rsz.pub_compressed:
            continue
        px = int(rsz.pub_compressed[2:], 16)
        yp, yn = y_roots(px)
        py = yp if yp % 2 == 0 else yn
        rows.append(PuzzleRow(n, False, 0, px, py, 0))

    return sorted(rows, key=lambda r: r.n)


def cube_slots(px: int, py: int) -> list[int]:
    res = (py * py - 7) % p
    roots = sorted(all_cube_roots_mod_p(res, witness=px))
    while len(roots) < 3:
        roots.append(roots[-1] if roots else px)
    return roots[:3]


def eval_equivalences(row: PuzzleRow, fh: float, fh2: float, gz_xd: float, gz_yd: float, gz_yx: float) -> dict[str, str]:
    """Return eq_id -> YES | NO | NA for one puzzle."""
    n, d, px, py = row.n, row.d, row.px, row.py
    yn = (p - py) % p
    yp, yn_roots = y_roots(px)
    neg_y = yn_roots if py == yp else yp

    fx, fy, fyn = f2s(px), f2s(py), f2s(neg_y)
    getcontext().prec = 80
    h = float(Decimal(PN).ln() / Decimal(2).ln())
    lsx = l2(px) / 2
    lsy = l2(py) / 2
    delta_x = h - lsx
    delta_y = h - lsy

    out: dict[str, str] = {}

    def yes_no(cond: bool, needs_d: bool = False) -> str:
        if needs_d and d <= 0:
            return "NA"
        return "YES" if cond else "NO"

    # --- Tier A: algebraic identities (always true when defined) ---
    out["ID01_H_minus_sqrt_y_eq_frac_Dy"] = yes_no(wrap_diff(frac(h) - frac(lsy), frac(delta_y)) < 1e-6)
    out["ID04_curve_y2_eq_x3_plus_7"] = yes_no((py * py - px * px * px - 7) % p == 0)
    if d > 0:
        out["ID05_neg_scalar_same_x"] = yes_no(px == scalar_x(N - d))
    else:
        out["ID05_neg_scalar_same_x"] = "NA"
    out["ID06_y_plus_neg_y_eq_p"] = yes_no((py + neg_y) % p == 0)

    if d > 0:
        fd = f2s(d)
        fnd = f2s(N - d)
        bf = band_frac(d, n)
        out["ID02_band_frac_eq_2_sqrt_d"] = yes_no(wrap_diff(bf, frac(2 * fd)) < 1e-6)
        out["ID03_band_frac_eq_log2d_minus_n1"] = yes_no(wrap_diff(bf, frac(math.log2(d) - (n - 1))) < 1e-6)
        lo, hi, _ = puzzle_band(n)
        out["S01_d_in_band"] = yes_no(lo <= d < hi)
        height = (1 << n) - 1
        out["S02_complement_eq_height_minus_d"] = yes_no((height - d) == ((1 << n) - 1 - d))
    else:
        for k in (
            "ID02_band_frac_eq_2_sqrt_d",
            "ID03_band_frac_eq_log2d_minus_n1",
            "S01_d_in_band",
            "S02_complement_eq_height_minus_d",
            "ID05_neg_scalar_same_x",
        ):
            if k not in out:
                out[k] = "NA"

    slots = cube_slots(px, py)
    out["S03_px_is_cube_root_slot"] = yes_no(px in slots)
    out["S04_true_slot_index"] = str(row.true_slot) if row.solved else "NA"

    # hinge errors
    ex = fx - fh2
    ey = fy - fh
    eyn = fyn - fh
    out["H06_y_closer_hinge_than_x"] = yes_no(delta_y < delta_x)
    out["H07_x_closer_hinge_than_y"] = yes_no(delta_x < delta_y)
    out["H01_tight_Ex"] = yes_no(abs(ex) < TIGHT)
    out["H02_tight_Ey_plus_y"] = yes_no(abs(ey) < TIGHT)
    out["H03_tight_Ey_minus_y"] = yes_no(abs(eyn) < TIGHT)
    out["H05_neg_y_beats_plus_y_on_Ey"] = yes_no(abs(eyn) < abs(ey))

    if d > 0:
        fd = f2s(d)
        g_xd = sgap(fx, fd)
        g_yd = sgap(fy, fd)
        g_yx = sgap(fy, fx)
        ed = fd - fh2
        out["H04_tight_Ex_minus_Ed"] = yes_no(abs(ex - ed) < TIGHT)
        out["GZ01_P27_x_offset"] = yes_no(wrap_diff(g_xd, gz_xd) < TIGHT)
        out["GZ02_P27_y_offset"] = yes_no(wrap_diff(g_yd, gz_yd) < TIGHT)
        out["GZ03_P27_yx_offset"] = yes_no(wrap_diff(g_yx, gz_yx) < TIGHT)
        out["GZ01_tight_001"] = yes_no(wrap_diff(g_xd, gz_xd) < VERY_TIGHT)
        out["T01_tightest_xd_in_dataset"] = "NA"  # filled globally

        s_l = g_xd + g_yd
        s_r = sgap(fx, fnd) + sgap(fyn, fnd)
        out["M01_mirror_sum_mod1"] = yes_no(wrap_diff(frac(s_l), frac(s_r)) < TIGHT)
        out["M03_mirror_sum_neg_mod1"] = yes_no(wrap_diff(frac(s_l), frac(-s_r)) < TIGHT)

        getcontext().prec = 80
        c_l = frac(float((Decimal(px) * Decimal(py) / (Decimal(d) * Decimal(d))).ln() / Decimal(2).ln()) / 2)
        nd = N - d
        c_r = frac(
            float((Decimal(px) * Decimal(neg_y) / (Decimal(nd) * Decimal(nd))).ln() / Decimal(2).ln()) / 2
        )
        out["M02_combined_mirror_ratio"] = yes_no(wrap_diff(c_l, c_r) < TIGHT)

        out["ALG01_yx_link"] = yes_no(wrap_diff(g_yd - g_xd, g_yx) < 1e-6)

        # lambda_band on true slot
        try:
            pk = parse_53125()[n]
            cfg = build_config(pk)
            st = bridge_state(cfg)
            lo, hi, _ = puzzle_band(n)
            lam_d = band_rep(st["lambda_ns"][row.true_slot], lo)
            eld = f2s(lam_d) - fh2
            out["L01_lambda_band_Ex_minus_Ed"] = yes_no(abs(ex - eld) < TIGHT)
        except Exception:
            out["L01_lambda_band_Ex_minus_Ed"] = "NA"
    else:
        for k in (
            "H04_tight_Ex_minus_Ed",
            "GZ01_P27_x_offset",
            "GZ02_P27_y_offset",
            "GZ03_P27_yx_offset",
            "GZ01_tight_001",
            "T01_tightest_xd_in_dataset",
            "M01_mirror_sum_mod1",
            "M02_combined_mirror_ratio",
            "M03_mirror_sum_neg_mod1",
            "ALG01_yx_link",
            "L01_lambda_band_Ex_minus_Ed",
        ):
            out[k] = "NA"

    return out


def scalar_x(scalar: int) -> int:
    from p135_common import G, scalar_mult  # noqa: WPS433

    pt = scalar_mult(scalar % N, G)
    return pt[0] if pt else -1


def main() -> int:
    getcontext().prec = 80
    fh = frac(float(Decimal(PN).ln() / Decimal(2).ln()))
    fh2 = frac(float(Decimal(PN).ln() / Decimal(2).ln()) / 2)

    keys = parse_53125()
    pk27 = keys[27]
    gz_xd = f2s(pk27.px) - f2s(pk27.d)
    gz_yd = f2s(pk27.py) - f2s(pk27.d)
    gz_yx = f2s(pk27.py) - f2s(pk27.px)

    puzzles = load_puzzles()
    catalog: list[dict[str, str]] = []
    for row in puzzles:
        rec = {"puzzle": str(row.n), "solved": "YES" if row.solved else "NO"}
        rec.update(eval_equivalences(row, fh, fh2, gz_xd, gz_yd, gz_yx))
        catalog.append(rec)

    # tightest |xd| marker
    if keys:
        xd_errs = []
        for row in puzzles:
            if not row.solved:
                continue
            pk = keys[row.n]
            err = abs(sgap(f2s(pk.px), f2s(pk.d)))
            xd_errs.append((err, row.n))
        if xd_errs:
            best_n = min(xd_errs)[1]
            for rec in catalog:
                if rec["puzzle"] == str(best_n):
                    rec["T01_tightest_xd_in_dataset"] = "YES"
                elif rec.get("T01_tightest_xd_in_dataset") == "NA":
                    rec["T01_tightest_xd_in_dataset"] = "NO"

    eq_ids = [k for k in catalog[0].keys() if k not in ("puzzle", "solved")]

    # inverted index
    by_eq: dict[str, list[int]] = defaultdict(list)
    for rec in catalog:
        pn = int(rec["puzzle"])
        for eid in eq_ids:
            if rec[eid] == "YES":
                by_eq[eid].append(pn)

    lines = [
        "HINGE EQUIVALENCE CATALOG — all puzzles",
        f"P27 ground zero: GZ_xd={gz_xd:+.6f}  GZ_yd={gz_yd:+.6f}  GZ_yx={gz_yx:+.6f}",
        f"Thresholds: TIGHT={TIGHT}  VERY_TIGHT={VERY_TIGHT}",
        f"Puzzles: {len(catalog)}  solved: {sum(1 for r in puzzles if r.solved)}",
        "",
        "=== EQUIVALENCE DEFINITIONS ===",
        "",
        "Tier A — algebraic identities (must hold when defined):",
        "  ID01  {H} - {sqrt y} = {Delta_y}           (fractional hinge gap on y)",
        "  ID02  band_frac(d) = {2 * sqrt d}",
        "  ID03  band_frac(d) = {log2(d) - (n-1)}",
        "  ID04  y^2 = x^3 + 7 (mod p)                (curve equation)",
        "  ID05  x(d*G) = x((N-d)*G)                    (negated point same x)",
        "  ID06  y + (-y) = p (mod p)",
        "",
        "Tier S — structural:",
        "  S01   d in puzzle band [2^(n-1), 2^n)",
        "  S02   complement = (2^n - 1) - d            (height mask)",
        "  S03   Px is one of 3 cube roots of (Py^2 - 7)",
        "  S04   true cube-root slot index (0/1/2)",
        "",
        "Tier H — hinge alignment (|error| < 0.05):",
        "  H01   |E_x| tight    E_x = {sqrt x} - {H/2}",
        "  H02   |E_y(+y)| tight",
        "  H03   |E_y(-y)| tight",
        "  H04   |E_x - E_d| tight",
        "  H05   -y beats +y on |E_y| (same x)",
        "  H06   Delta_y < Delta_x  (y closer to hinge in full log2 gap)",
        "  H07   Delta_x < Delta_y  (x closer)",
        "",
        "Tier GZ — P27 ground-zero transfer (|gap - P27 offset| < 0.05):",
        "  GZ01  {sqrt x}-{sqrt d} ~= GZ_xd",
        "  GZ02  {sqrt y}-{sqrt d} ~= GZ_yd",
        "  GZ03  {sqrt y}-{sqrt x} ~= GZ_yx",
        "  GZ01_tight_001  same with threshold 0.01",
        "",
        "Tier M — mirror pair (d,N-d) and (y,-y):",
        "  M01   (sqrt x - sqrt d)+(sqrt y - sqrt d) == (sqrt x - sqrt(N-d))+(sqrt(-y)-sqrt(N-d))  mod 1",
        "  M02   {sqrt(xy/d^2)} == {sqrt(x*(-y)/(N-d)^2)}  mod 1",
        "  M03   mirror sum S_L == -S_R  mod 1",
        "",
        "Tier ALG — exact per-puzzle links:",
        "  ALG01 ({sqrt y}-{sqrt d}) - ({sqrt x}-{sqrt d}) = {sqrt y}-{sqrt x}  (signed gaps)",
        "",
        "Tier L — lambda band:",
        "  L01   |E_x - E_d(lambda_band,true slot)| < 0.05",
        "",
        "Tier T — dataset records:",
        "  T01   tightest |{sqrt x}-{sqrt d}| in full solved set (P27)",
        "",
        "=== INVERTED INDEX: equivalence -> puzzles ===",
        "",
    ]

    for eid in eq_ids:
        lst = sorted(by_eq[eid])
        solved_only = [p for p in lst if any(r.n == p and r.solved for r in puzzles)]
        na_count = sum(1 for rec in catalog if rec[eid] == "NA")
        no_count = sum(1 for rec in catalog if rec[eid] == "NO")
        lines.append(f"{eid}")
        lines.append(f"  YES: {len(lst)}/{len(catalog)}  (solved YES: {len(solved_only)})  NA: {na_count}  NO: {no_count}")
        if len(lst) <= 90:
            lines.append(f"  puzzles: {lst}")
        else:
            lines.append(f"  puzzles: {lst[:40]} ... ({len(lst)} total)")
        lines.append("")

    lines.extend(["=== PER-PUZZLE EQUIVALENCE TAGS (YES only) ===", ""])
    for rec in catalog:
        pn = int(rec["puzzle"])
        tags = [eid for eid in eq_ids if rec[eid] == "YES"]
        lines.append(f"P{pn:3d} [{rec['solved']}] ({len(tags)} eq): {', '.join(tags)}")

    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["puzzle", "solved"] + eq_ids)
        w.writeheader()
        w.writerows(catalog)

    print(text[:12000])
    if len(text) > 12000:
        print(f"\n... [{len(text) - 12000} more chars in report]")
    print(f"\nwrote {REPORT}")
    print(f"wrote {CSV_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
