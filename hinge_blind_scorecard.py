#!/usr/bin/env python3
"""
Blind predictive scorecard — hinge invariants must pick unknown branches
without oracle access.

Tests:
  T1  Blind x-slot tournament (argmin |E_x| over 3 cube-root slots)
  T2  Blind y-leg at true x (+y vs -y by |E_y|)
  T3  Blind 6-way joint (3 slots x 2 y legs)
  T4  Blind d from P27 x-offset -> band_frac -> EC scan (no true d)
  T5  Prefix + leave-one-out GZ calibration (no answer leakage)

Outputs:
  ARCHIVE/hinge_blind_scorecard.txt
  ARCHIVE/hinge_blind_scorecard.csv
"""

from __future__ import annotations

import csv
import math
import sys
from dataclasses import dataclass, field
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from bucket_slice_search import verify_candidate  # noqa: E402
from compare_family_mirror_batch import build_config  # noqa: E402
from ecdlp_full_pipeline import all_cube_roots_mod_p, p, puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from p135_common import G, point_add, scalar_mult  # noqa: E402
from puzzle_keys_53125 import parse_53125

REPORT = ROOT / "ARCHIVE" / "hinge_blind_scorecard.txt"
CSV_OUT = ROOT / "ARCHIVE" / "hinge_blind_scorecard.csv"

PN = p - 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
EC_SCAN_RADIUS = 50_000  # per unsolved / T4 verification window


def frac(x: float) -> float:
    return x - math.floor(x)


def wrap_diff(a: float, b: float) -> float:
    d = a - b
    return min(abs(d), abs(d + 1), abs(d - 1))


def f2s(v: int) -> float:
    getcontext().prec = 80
    v = int(v) % p
    if v <= 0:
        return float("nan")
    ln = float(Decimal(v).ln() / Decimal(2).ln()) / 2
    return ln - math.floor(ln)


def hinge_shelves() -> tuple[float, float]:
    getcontext().prec = 80
    h = float(Decimal(PN).ln() / Decimal(2).ln())
    return frac(h), frac(h / 2)


def cube_slots(px: int, py: int) -> list[int]:
    res = (py * py - 7) % p
    roots = sorted(all_cube_roots_mod_p(res, witness=px))
    while len(roots) < 3:
        roots.append(roots[-1] if roots else px)
    return roots[:3]


def true_slot_index(px: int, py: int) -> int:
    slots = cube_slots(px, py)
    for i, xi in enumerate(slots):
        if xi == px:
            return i
    return 0


def true_y_label(px: int, py: int, slot: int) -> str:
    yp, yn = y_roots(cube_slots(px, py)[slot])
    return "y" if py == yp else "-y"


@dataclass
class Branch:
    slot: int
    y_label: str
    xi: int
    yi: int
    ex: float
    ey: float

    @property
    def abs_ex(self) -> float:
        return abs(self.ex)

    @property
    def abs_ey(self) -> float:
        return abs(self.ey)


@dataclass
class PuzzleScore:
    n: int
    solved: bool
    true_slot: int
    true_y: str
    pick_slot_ex: int
    pick_y_at_true_x: str
    pick_joint_ex: tuple[int, str]
    pick_joint_ey: tuple[int, str]
    pick_joint_sum: tuple[int, str]
    t1_ok: bool
    t2_ok: bool
    t3_ex_ok: bool
    t3_ey_ok: bool
    t3_sum_ok: bool
    t4_d_pred_bf: float | None = None
    t4_d_pred: int | None = None
    t4_ec_hit: str = "NA"
    t4_bf_err: float | None = None
    t5_prefix_err: float | None = None
    t5_loo_err: float | None = None
    notes: list[str] = field(default_factory=list)


def branches_for_pubkey(px: int, py: int, fh: float, fh2: float) -> list[Branch]:
    out: list[Branch] = []
    for i, xi in enumerate(cube_slots(px, py)):
        yp, yn = y_roots(xi)
        for yl, yi in (("y", yp), ("-y", yn)):
            out.append(
                Branch(
                    slot=i,
                    y_label=yl,
                    xi=xi,
                    yi=yi,
                    ex=f2s(xi) - fh2,
                    ey=f2s(yi) - fh,
                )
            )
    return out


def ec_scan(d0: int, radius: int, lo: int, hi: int, px: int, py: int) -> int | None:
    d_start = max(lo, d0 - radius)
    d_end = min(hi - 1, d0 + radius)
    pt = scalar_mult(d_start, G)
    for i, d in enumerate(range(d_start, d_end + 1)):
        if pt and pt[0] == px and pt[1] == py and verify_candidate(d, px, py):
            return d
        if i + 1 <= d_end - d_start:
            pt = point_add(pt, G)
    return None


def gz_xd_from_keys(keys: dict, include: set[int]) -> float | None:
    gaps = []
    for pn, pk in keys.items():
        if pn not in include or pk.d <= 0:
            continue
        gaps.append(sgap(f2s(pk.px), f2s(pk.d)))
    if not gaps:
        return None
    return sum(gaps) / len(gaps)


def sgap(a: float, b: float) -> float:
    d = a - b
    if d > 0.5:
        d -= 1
    if d < -0.5:
        d += 1
    return d


def load_pubkey_rows() -> list[tuple[int, bool, int, int, int]]:
    keys = parse_53125()
    rows: list[tuple[int, bool, int, int, int]] = []
    seen: set[int] = set()
    for n, pk in sorted(keys.items()):
        if pk.px <= 0 or pk.py <= 0:
            continue
        rows.append((n, pk.d > 0, pk.px, pk.py, pk.d))
        seen.add(n)
    for n, rsz in sorted(PUZZLE_RSZ.items()):
        if n in seen or not rsz.pub_compressed:
            continue
        px = int(rsz.pub_compressed[2:], 16)
        yp, yn = y_roots(px)
        py = yp if yp % 2 == 0 else yn
        rows.append((n, False, px, py, 0))
    return sorted(rows, key=lambda r: r[0])


def score_puzzle(
    n: int,
    solved: bool,
    px: int,
    py: int,
    d_true: int,
    fh: float,
    fh2: float,
    gz_fixed: float,
    keys: dict,
) -> PuzzleScore:
    ts = true_slot_index(px, py)
    ty = true_y_label(px, py, ts)
    br = branches_for_pubkey(px, py, fh, fh2)

    pick_slot = min(br, key=lambda b: b.abs_ex).slot
    at_true_x = [b for b in br if b.slot == ts]
    pick_y = min(at_true_x, key=lambda b: b.abs_ey).y_label
    pick_jex = min(br, key=lambda b: b.abs_ex)
    pick_jey = min(br, key=lambda b: b.abs_ey)
    pick_jsum = min(br, key=lambda b: b.abs_ex + b.abs_ey)

    ps = PuzzleScore(
        n=n,
        solved=solved,
        true_slot=ts,
        true_y=ty,
        pick_slot_ex=pick_slot,
        pick_y_at_true_x=pick_y,
        pick_joint_ex=(pick_jex.slot, pick_jex.y_label),
        pick_joint_ey=(pick_jey.slot, pick_jey.y_label),
        pick_joint_sum=(pick_jsum.slot, pick_jsum.y_label),
        t1_ok=pick_slot == ts,
        t2_ok=pick_y == ty,
        t3_ex_ok=(pick_jex.slot, pick_jex.y_label) == (ts, ty),
        t3_ey_ok=(pick_jey.slot, pick_jey.y_label) == (ts, ty),
        t3_sum_ok=(pick_jsum.slot, pick_jsum.y_label) == (ts, ty),
    )

    # T4: blind d from fixed P27 GZ_xd (calibrated once on full set — separate from T5)
    fd_pred = frac(f2s(px) - gz_fixed)
    bf = frac(2 * fd_pred)
    d_pred = int(round(2 ** ((n - 1) + bf)))
    ps.t4_d_pred_bf = bf
    ps.t4_d_pred = d_pred
    if solved and d_true > 0:
        ps.t4_bf_err = wrap_diff(bf, frac(math.log2(d_true) - (n - 1)))
        lo, hi, _ = puzzle_band(n)
        if lo <= d_true < hi:
            if abs(d_pred - d_true) <= EC_SCAN_RADIUS:
                ps.t4_ec_hit = str(d_true)
                ps.notes.append("T4_true_d_in_window")
            else:
                ps.t4_ec_hit = "none"
    elif not solved:
        lo, hi, _ = puzzle_band(n)
        hit = ec_scan(d_pred, EC_SCAN_RADIUS, lo, hi, px, py)
        ps.t4_ec_hit = str(hit) if hit else "none"
        if hit:
            ps.notes.append("T4_UNSOLVED_HIT")

    # T5 prefix + LOO
    prefix = {pn for pn in keys if pn < n and keys[pn].d > 0}
    loo = {pn for pn in keys if keys[pn].d > 0 and pn != n}
    for label, include, attr in (
        ("prefix", prefix, "t5_prefix_err"),
        ("loo", loo, "t5_loo_err"),
    ):
        gz = gz_xd_from_keys(keys, include)
        if gz is None or not solved or d_true <= 0:
            setattr(ps, attr, None)
            continue
        pred_fd = frac(f2s(px) - gz)
        err = wrap_diff(pred_fd, f2s(d_true))
        setattr(ps, attr, err)

    return ps


def pct(num: int, den: int) -> str:
    return f"{num}/{den} ({100 * num / den:.1f}%)" if den else "0/0"


def main() -> int:
    fh, fh2 = hinge_shelves()
    keys = parse_53125()
    pk27 = keys[27]
    gz_fixed = f2s(pk27.px) - f2s(pk27.d)

    rows_in = load_pubkey_rows()
    scores: list[PuzzleScore] = []
    for n, solved, px, py, d in rows_in:
        scores.append(score_puzzle(n, solved, px, py, d, fh, fh2, gz_fixed, keys))

    solved_scores = [s for s in scores if s.solved]
    unsolved = [s for s in scores if not s.solved]

    lines = [
        "HINGE BLIND PREDICTIVE SCORECARD",
        f"{{H}}={fh:.6f}  {{H/2}}={fh2:.6f}",
        f"P27 fixed GZ_xd={gz_fixed:+.6f}  (T4 only; T5 uses prefix/LOO)",
        f"EC scan radius +/-{EC_SCAN_RADIUS:,} around predicted d",
        f"Puzzles: {len(scores)}  solved: {len(solved_scores)}  unsolved: {len(unsolved)}",
        f"Random baseline 6-way joint: 1/6 = 16.7%",
        "",
        "=== T1 Blind x-slot (argmin |E_x|, y ignored) ===",
        f"  correct: {pct(sum(1 for s in solved_scores if s.t1_ok), len(solved_scores))}",
        "",
        "=== T2 Blind y-leg at TRUE x (argmin |E_y|, slot given) ===",
        f"  correct: {pct(sum(1 for s in solved_scores if s.t2_ok), len(solved_scores))}",
        "  (oracle slot — upper bound on y discrimination)",
        "",
        "=== T3 Blind 6-way joint (3 slots x 2 y) ===",
        f"  argmin |E_x|:     {pct(sum(1 for s in solved_scores if s.t3_ex_ok), len(solved_scores))}",
        f"  argmin |E_y|:     {pct(sum(1 for s in solved_scores if s.t3_ey_ok), len(solved_scores))}",
        f"  argmin |Ex|+|Ey|: {pct(sum(1 for s in solved_scores if s.t3_sum_ok), len(solved_scores))}",
        "",
        "=== T4 Blind d from P27 GZ_xd (pubkey x only) ===",
    ]

    t4_bf = [s.t4_bf_err for s in solved_scores if s.t4_bf_err is not None]
    t4_ec = [s for s in solved_scores if s.t4_ec_hit not in ("NA", "none")]
    lines.append(f"  mean |band_frac err|: {sum(t4_bf)/len(t4_bf):.4f}" if t4_bf else "  no bf data")
    lines.append(f"  bf err < 0.05: {sum(1 for e in t4_bf if e < 0.05)}/{len(t4_bf)}")
    lines.append(f"  true d within +/-{EC_SCAN_RADIUS:,} of pred: {sum(1 for s in solved_scores if s.t4_ec_hit not in ('NA', 'none'))}/{len(solved_scores)} solved")
    for s in unsolved:
        lines.append(f"  P{s.n} unsolved EC: {s.t4_ec_hit}  pred_bf={s.t4_d_pred_bf:.6f}  d~...{str(s.t4_d_pred)[-10:]}")

    lines.extend(["", "=== T5 Calibration without answer leakage ==="])
    t5p = [s.t5_prefix_err for s in solved_scores if s.t5_prefix_err is not None]
    t5l = [s.t5_loo_err for s in solved_scores if s.t5_loo_err is not None]
    lines.append("  Prefix (GZ_xd = mean of puzzles < n):")
    lines.append(f"    mean err {{sqrt d}}: {sum(t5p)/len(t5p):.4f}  <0.05: {sum(1 for e in t5p if e<0.05)}/{len(t5p)}")
    lines.append("  Leave-one-out (mean over all other solved):")
    lines.append(f"    mean err {{sqrt d}}: {sum(t5l)/len(t5l):.4f}  <0.05: {sum(1 for e in t5l if e<0.05)}/{len(t5l)}")
    lines.extend(["", "=== P135 blind detail ==="])
    p135 = next((s for s in scores if s.n == 135), None)
    if p135:
        br = branches_for_pubkey(
            next(r[2] for r in rows_in if r[0] == 135),
            next(r[3] for r in rows_in if r[0] == 135),
            fh,
            fh2,
        )
        lines.append(f"  true slot={p135.true_slot}  pick_slot(T1)={p135.pick_slot_ex}  T1={'YES' if p135.t1_ok else 'NO'}")
        lines.append(f"  true y={p135.true_y}  pick_y(T2)={p135.pick_y_at_true_x}  T2={'YES' if p135.t2_ok else 'NO'}")
        lines.append(f"  joint Ex pick={p135.pick_joint_ex}")
        lines.append(f"  joint Ey pick={p135.pick_joint_ey}")
        lines.append(f"  T4 pred_bf={p135.t4_d_pred_bf:.6f}  EC={p135.t4_ec_hit}")
        lines.append("  branch table:")
        for b in sorted(br, key=lambda x: (x.slot, x.y_label)):
            mark = ""
            if b.slot == p135.true_slot and b.y_label == p135.true_y:
                mark = " <-- live"
            lines.append(
                f"    slot{b.slot} {b.y_label:>2}  Ex={b.ex:+.6f} Ey={b.ey:+.6f}  |Ex|={b.abs_ex:.4f} |Ey|={b.abs_ey:.4f}{mark}"
            )

    lines.extend(["", "=== Per-puzzle (solved, mispredictions only) ==="])
    for s in solved_scores:
        if s.t1_ok and s.t2_ok and s.t3_ex_ok:
            continue
        lines.append(
            f"  P{s.n:3d} true=slot{s.true_slot}/{s.true_y}  "
            f"T1->slot{s.pick_slot_ex}  T2->{s.pick_y_at_true_x}  "
            f"T3Ex->({s.pick_joint_ex[0]},{s.pick_joint_ex[1]})  "
            f"T5p={(f'{s.t5_prefix_err:.3f}' if s.t5_prefix_err is not None else 'NA')}"
        )

    lines.extend(["", "=== ID01 tautology note ==="])
    lines.append("  {H}-{sqrt y}={Delta_y} is definitional when Delta_y=H-log2(sqrt y).")
    lines.append("  These tests do NOT use ID01; they use E_x,E_y branch picks and d projection.")

    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "puzzle",
                "solved",
                "true_slot",
                "true_y",
                "T1_slot_ok",
                "T2_y_ok",
                "T3_joint_ex_ok",
                "T3_joint_ey_ok",
                "T3_joint_sum_ok",
                "T4_pred_bf",
                "T4_bf_err",
                "T4_ec_hit",
                "T5_prefix_err",
                "T5_loo_err",
            ]
        )
        for s in scores:
            w.writerow(
                [
                    s.n,
                    s.solved,
                    s.true_slot,
                    s.true_y,
                    s.t1_ok,
                    s.t2_ok,
                    s.t3_ex_ok,
                    s.t3_ey_ok,
                    s.t3_sum_ok,
                    f"{s.t4_d_pred_bf:.6f}" if s.t4_d_pred_bf is not None else "",
                    f"{s.t4_bf_err:.6f}" if s.t4_bf_err is not None else "",
                    s.t4_ec_hit,
                    f"{s.t5_prefix_err:.6f}" if s.t5_prefix_err is not None else "",
                    f"{s.t5_loo_err:.6f}" if s.t5_loo_err is not None else "",
                ]
            )

    print(text)
    print(f"\nwrote {REPORT}")
    print(f"wrote {CSV_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
