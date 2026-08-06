#!/usr/bin/env python3
"""
Strict Schedule E -> D -> L -> O -> C -> P execution pipeline (v2).

Adds:
  - hinge-adjusted geom_pred ({H/2} on 2^142 scaffold)
  - wider R_base + c * 2^142 sweep
  - P115 algebra control (gp=d, not counted as blind win)
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    N,
    P115_D,
    P115_K,
    P115_R_TRUE_X,
    P115_R_TRUE_Y,
    P135_R_TRUE_X,
    P135_R_TRUE_Y,
    p,
    pubkey_from_scalar,
    puzzle_band,
    y_roots,
)
from hashkeys_rsz import PUZZLE_RSZ, resolve_r_true_from_rsz  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

PIVOT_I99 = 198.95
PIVOT_INT = int(2**PIVOT_I99) % N
CORR_142 = 1 << 142
PN = p - N
LOG2_PN = math.log2(PN)
H_FRAC = LOG2_PN - math.floor(LOG2_PN)
H2_FRAC = (LOG2_PN / 2) - math.floor(LOG2_PN / 2)
HINGE = int(2 ** (H2_FRAC * 134))

REPORT = ROOT / "ARCHIVE" / "schedule_pipeline_v2.txt"


@dataclass
class PuzzleCtx:
    n: int
    r: int
    s: int
    z: int
    px: int
    py: int
    rx: int
    ry: int
    lo: int
    hi: int
    known_d: int | None = None
    known_k: int | None = None
    masked_k: int | None = None


@dataclass
class Candidate:
    label: str
    k: int
    control: bool = False


@dataclass
class ScoreRow:
    puzzle: int
    label: str
    k: int
    rx_match: bool
    ry_match: bool
    on_curve: bool
    pubkey_match: bool
    d_in_range: bool
    full: bool
    control: bool = False
    d: int = 0


def schedule_O(val: int) -> int:
    return val % N


def schedule_D(k: int) -> tuple[int, int]:
    return pubkey_from_scalar(schedule_O(k))


def schedule_L(R: tuple[int, int]) -> bool:
    x, y = R
    return (y * y) % p == (pow(x, 3, p) + 7) % p


def schedule_C(sk: int, z: int, r_inv: int) -> int:
    return schedule_O((sk - z) * r_inv)


def schedule_P(d: int) -> tuple[int, int]:
    return schedule_D(d)


def _base_geom(ry: int, n: int, mode: str) -> int:
    if mode == "2p142":
        return CORR_142
    if mode == "n_bits":
        return max(1, 1 << (n - 1))
    if ry <= 0:
        return CORR_142
    lsry = math.log2(ry) / 2.0
    lk = 2.0 * (PIVOT_I99 - lsry)
    shift = max(0.0, lk - (256 - n))
    if mode == "geom_round":
        return max(1, int(round(2**shift)))
    if mode == "geom_floor":
        return max(1, int(2 ** math.floor(shift)))
    if mode == "geom_ceil":
        return max(1, int(2 ** math.ceil(shift)))
    return CORR_142


def geom_pred_variants(ry: int, n: int, d_known: int | None) -> list[tuple[str, int, bool]]:
    """Return (label, geom_pred, is_algebra_control)."""
    out: list[tuple[str, int, bool]] = []
    bases = ["2p142", "geom_round", "geom_floor", "geom_ceil", "n_bits"]
    for bm in bases:
        gp = _base_geom(ry, n, bm)
        out.append((f"{bm}", gp, False))
        out.append((f"{bm}+hinge", schedule_O(gp + HINGE), False))
        out.append((f"{bm}-hinge", schedule_O(gp - HINGE), False))
        out.append((f"{bm}*2^H2", schedule_O(int(gp * (2**H2_FRAC))), False))
        out.append((f"{bm}//2^H2", schedule_O(int(gp / (2**H2_FRAC))), False))
        out.append((f"{bm}+2^H2n", schedule_O(gp + int(2 ** (H2_FRAC * n))), False))
    if d_known:
        out.append(("algebra_d", d_known % N, True))
    return out


def pivot_variants() -> list[tuple[str, int]]:
    piv = PIVOT_INT
    return [
        ("pivot", piv),
        ("pivot+hinge", schedule_O(piv + HINGE)),
        ("pivot-hinge", schedule_O(piv - HINGE)),
        ("pivot*2^H2", schedule_O(int(piv * (2**H2_FRAC)))),
        ("N-pivot", schedule_O(N - piv)),
    ]


def schedule_E(
    k0: int,
    dk: int,
    r_base: int,
    geom_pred: int,
    gp_label: str,
    *,
    c_range: range,
    control: bool = False,
) -> Iterator[Candidate]:
    gp = geom_pred % N
    rb = r_base % N
    step = CORR_142 % N

    # Priority formulas (user order)
    yield Candidate(f"{gp_label}|k0+gp*dk", schedule_O(k0 + gp * dk), control)
    for c in c_range:
        k = schedule_O(rb + c * step)
        if k > 0:
            yield Candidate(f"{gp_label}|Rbase+{c}*2^142", k, control)

    for plabel, piv in pivot_variants():
        for op, val in [("+gp", schedule_O(piv + gp)), ("-gp", schedule_O(piv - gp))]:
            k = val
            if k > 0:
                yield Candidate(f"{gp_label}|{plabel}{op}", k, control)

    # hinge on k0 bridge directly
    for hname, hgp in [
        ("hinge", HINGE),
        ("2^H2n", int(2 ** (H2_FRAC * 135))),
    ]:
        yield Candidate(
            f"{gp_label}|k0+(gp+{hname})*dk",
            schedule_O(k0 + schedule_O(gp + hgp) * dk),
            control,
        )
        yield Candidate(
            f"{gp_label}|k0+(gp-{hname})*dk",
            schedule_O(k0 + schedule_O(gp - hgp) * dk),
            control,
        )


def score_candidate(ctx: PuzzleCtx, cand: Candidate) -> ScoreRow:
    if not cand.control and ctx.masked_k is not None and cand.k == ctx.masked_k:
        return ScoreRow(ctx.n, cand.label, cand.k, False, False, False, False, False, False, cand.control)

    R = schedule_D(cand.k)
    rx_match = (R[0] % N) == (ctx.rx % N)
    ry_match = R[1] == ctx.ry or R[1] == ((-ctx.ry) % p)
    on_curve = schedule_L(R)
    r_inv = pow(ctx.r, -1, N)
    d = schedule_C(ctx.s * cand.k, ctx.z, r_inv)
    if d <= 0:
        return ScoreRow(
            ctx.n, cand.label, cand.k, rx_match, ry_match, on_curve,
            False, False, False, cand.control, d,
        )
    pub = schedule_P(d)
    pubkey_match = pub[0] == ctx.px and pub[1] == ctx.py
    d_in_range = ctx.lo <= d < ctx.hi
    full = rx_match and ry_match and on_curve and pubkey_match and d_in_range
    return ScoreRow(
        ctx.n, cand.label, cand.k, rx_match, ry_match, on_curve,
        pubkey_match, d_in_range, full, cand.control, d,
    )


def load_ctx(n: int, keys: dict, *, blind: bool) -> PuzzleCtx | None:
    rsz = PUZZLE_RSZ.get(n)
    if not rsz:
        return None
    comp = rsz.pub_compressed
    px = int(comp[2:], 16)
    yp, yn = y_roots(px)
    py = yp if comp.startswith("02") else yn

    if n == 115:
        rx, ry = P115_R_TRUE_X, P115_R_TRUE_Y
    elif n == 135:
        rx, ry = P135_R_TRUE_X, P135_R_TRUE_Y
    else:
        rpt = resolve_r_true_from_rsz(n)
        if not rpt:
            return None
        rx, ry = rpt[0], rpt[1]

    lo, hi, _ = puzzle_band(n)
    known_d = keys[n].d if n in keys and keys[n].d else None
    known_k = rsz.k if rsz.k is not None else None
    if known_k is None and known_d:
        known_k = rsz.recover_k_from_d(known_d)
    masked_k = known_k if blind else None
    return PuzzleCtx(n, rsz.r, rsz.s, rsz.z, px, py, rx, ry, lo, hi, known_d, known_k, masked_k)


def p115_lock(ctx: PuzzleCtx) -> list[str]:
    k0 = (ctx.z * pow(ctx.s, -1, N)) % N
    dk = (ctx.r * pow(ctx.s, -1, N)) % N
    k_rec = (k0 + P115_D * dk) % N
    R = schedule_D(P115_K)
    return [
        "=== P115 CALIBRATION LOCK ===",
        f"ry_source == R_true: {ctx.ry == P115_R_TRUE_Y}",
        f"rx_match: {(R[0] % N) == (ctx.rx % N)}",
        f"ry_match: {R[1] == P115_R_TRUE_Y}",
        f"k0 + d*dk == k: {k_rec == P115_K % N}",
        f"HINGE bits={HINGE.bit_length()}  {{H/2}}={H2_FRAC:.6f}",
        "",
    ]


def run_puzzle(ctx: PuzzleCtx, c_range: range) -> tuple[list[ScoreRow], list[str]]:
    k0 = (ctx.z * pow(ctx.s, -1, N)) % N
    dk = (ctx.r * pow(ctx.s, -1, N)) % N
    variants = geom_pred_variants(ctx.ry, ctx.n, ctx.known_d if not ctx.masked_k else None)

    cands: list[Candidate] = []
    for glabel, gp, control in variants:
        cands.extend(
            schedule_E(k0, dk, ctx.rx, gp, glabel, c_range=c_range, control=control)
        )

    rows = [score_candidate(ctx, c) for c in cands]
    generated = [r for r in rows if not r.control]
    full_gen = [r for r in generated if r.full]
    full_ctrl = [r for r in rows if r.control and r.full]

    def score_sum(r: ScoreRow) -> int:
        return sum([r.rx_match, r.ry_match, r.on_curve, r.pubkey_match, r.d_in_range])

    best = max(generated, key=score_sum) if generated else None
    lines = [
        f"P{ctx.n} candidates={len(cands)} gen_full={len(full_gen)} ctrl_full={len(full_ctrl)}",
    ]
    if best:
        lines.append(f"  best_gen={best.label} score={score_sum(best)}/5")
    for r in full_gen[:5]:
        lines.append(f"  GEN WIN {r.label} d_bits={r.d.bit_length()}")
    for r in full_ctrl[:2]:
        lines.append(f"  CTRL OK {r.label} (algebra d)")
    return rows, lines


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--c-min", type=int, default=-32)
    ap.add_argument("--c-max", type=int, default=32)
    ap.add_argument("--skip-p135", action="store_true")
    args = ap.parse_args()
    c_range = range(args.c_min, args.c_max + 1)

    keys = parse_53125()
    lines = [
        "SCHEDULE PIPELINE V2 (hinge + wide R_base sweep)",
        f"PIVOT_I99={PIVOT_I99}  CORR_142=2^142  c in [{args.c_min},{args.c_max}]",
        f"HINGE={HINGE.bit_length()} bits  {{H/2}}={H2_FRAC:.6f}",
        "",
    ]

    ctx115 = load_ctx(115, keys, blind=False)
    if not ctx115:
        print("P115 missing")
        return 1
    lines.extend(p115_lock(ctx115))

    lines.append("=== P115 EXPANDED SWEEP ===")
    _, p115_detail = run_puzzle(ctx115, c_range)
    lines.extend(p115_detail)
    lines.append("")

    blind_puzzles = [n for n in range(70, 131, 5) if n in PUZZLE_RSZ and n in keys and keys[n].d]
    lines.append("=== BLIND P70-P125 ===")
    blind_wins: dict[str, list[int]] = {}
    for n in blind_puzzles:
        ctx = load_ctx(n, keys, blind=True)
        if not ctx:
            continue
        rows, detail = run_puzzle(ctx, c_range)
        full = [r for r in rows if r.full and not r.control]
        if full:
            lines.extend(detail)
            for r in full:
                blind_wins.setdefault(r.label, []).append(n)

    if blind_wins:
        for label, ps in sorted(blind_wins.items(), key=lambda x: -len(x[1]))[:15]:
            lines.append(f"  BLIND WIN {label}: P{ps}")
    else:
        lines.append("  no blind full-score wins")

    # Near-miss leaderboard across blind set
    lines.append("")
    lines.append("=== BLIND NEAR-MISS (score 4/5) ===")
    near: dict[str, list[int]] = {}
    for n in blind_puzzles:
        ctx = load_ctx(n, keys, blind=True)
        if not ctx:
            continue
        rows, _ = run_puzzle(ctx, c_range)
        for r in rows:
            if r.control:
                continue
            s = sum([r.rx_match, r.ry_match, r.on_curve, r.pubkey_match, r.d_in_range])
            if s == 4:
                near.setdefault(r.label, []).append(n)
    if near:
        for label, ps in sorted(near.items(), key=lambda x: -len(x[1]))[:10]:
            lines.append(f"  4/5 {label}: P{ps}")
    else:
        lines.append("  none")

    if not args.skip_p135:
        lines.append("")
        lines.append("=== P135 (generated only, no ground truth) ===")
        ctx135 = load_ctx(135, keys, blind=True)
        if ctx135:
            rows, detail = run_puzzle(ctx135, c_range)
            lines.extend(detail)
            top = sorted(
                [r for r in rows if not r.control],
                key=lambda r: sum([r.rx_match, r.ry_match, r.pubkey_match, r.d_in_range]),
                reverse=True,
            )[:5]
            lines.append("  top generated:")
            for r in top:
                s = sum([r.rx_match, r.ry_match, r.on_curve, r.pubkey_match, r.d_in_range])
                lines.append(
                    f"    {s}/5 {r.label} rx={r.rx_match} ry={r.ry_match} "
                    f"pub={r.pubkey_match} band={r.d_in_range}"
                )

    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
