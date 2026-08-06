#!/usr/bin/env python3
"""
Strict Schedule E -> D -> L -> O -> C -> P execution pipeline.

P115 locks calibration. P70-P125 blind (known_k masked). P135 last.
Only generated_k wins count (score == 5). No known_k_direct victories.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
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

REPORT = ROOT / "ARCHIVE" / "schedule_pipeline.txt"


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
    d: int = 0


# --- Schedules ---

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


def geom_pred_index(ry: int, n: int, mode: str) -> int:
    """142-bit invariant as correction index (not k)."""
    if ry <= 0:
        return CORR_142
    lsry = math.log2(ry) / 2.0
    lk = 2.0 * (PIVOT_I99 - lsry)
    if mode == "2p142":
        return CORR_142
    if mode == "geom_round":
        return max(1, int(round(2 ** max(0.0, lk - (256 - n)))))
    if mode == "geom_floor":
        return max(1, int(2 ** math.floor(max(0.0, lk - (256 - n)))))
    if mode == "n_bits":
        return max(1, 1 << (n - 1))
    return CORR_142


def schedule_E(
    k0: int,
    dk: int,
    pivot: int,
    r_base: int,
    geom_pred: int,
    *,
    c_range: range = range(-2, 3),
) -> Iterator[Candidate]:
    gp = geom_pred % N
    piv = pivot % N
    rb = r_base % N
    forms = [
        ("k0+gp*dk", schedule_O(k0 + gp * dk)),
        ("pivot+gp", schedule_O(piv + gp)),
        ("pivot-gp", schedule_O(piv - gp)),
        ("N-pivot+gp", schedule_O(N - piv + gp)),
        ("N-pivot-gp", schedule_O(N - piv - gp)),
    ]
    for label, k in forms:
        if k > 0:
            yield Candidate(label, k)
    step = CORR_142 % N
    for c in c_range:
        k = schedule_O(rb + c * step)
        if k > 0:
            yield Candidate(f"Rbase+{c}*2^142", k)


def score_candidate(ctx: PuzzleCtx, cand: Candidate) -> ScoreRow:
    if ctx.masked_k is not None and cand.k == ctx.masked_k:
        return ScoreRow(ctx.n, cand.label, cand.k, False, False, False, False, False, False)

    R = schedule_D(cand.k)
    rx_match = (R[0] % N) == (ctx.rx % N)
    ry_match = R[1] == ctx.ry or R[1] == ((-ctx.ry) % p)
    on_curve = schedule_L(R)
    r_inv = pow(ctx.r, -1, N)
    d = schedule_C(ctx.s * cand.k, ctx.z, r_inv)
    pub = schedule_P(d)
    pubkey_match = pub[0] == ctx.px and pub[1] == ctx.py
    d_in_range = ctx.lo <= d < ctx.hi
    full = rx_match and ry_match and on_curve and pubkey_match and d_in_range
    return ScoreRow(ctx.n, cand.label, cand.k, rx_match, ry_match, on_curve, pubkey_match, d_in_range, full, d)


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
    known_k = None
    if rsz.k is not None:
        known_k = rsz.k
    elif known_d:
        known_k = rsz.recover_k_from_d(known_d)

    masked_k = known_k if blind else None
    return PuzzleCtx(n, rsz.r, rsz.s, rsz.z, px, py, rx, ry, lo, hi, known_d, known_k, masked_k)


def p115_lock(ctx: PuzzleCtx) -> list[str]:
    lines = ["=== P115 CALIBRATION LOCK ==="]
    k0 = (ctx.z * pow(ctx.s, -1, N)) % N
    dk = (ctx.r * pow(ctx.s, -1, N)) % N
    k_rec = (k0 + P115_D * dk) % N
    R = schedule_D(P115_K)
    lines.append(f"ry_source == R_true: {ctx.ry == P115_R_TRUE_Y}")
    lines.append(f"rx_match: {(R[0] % N) == (ctx.rx % N)}")
    lines.append(f"ry_match: {R[1] == P115_R_TRUE_Y}")
    lines.append(f"k0 + d*dk == k: {k_rec == P115_K % N}")
    lines.append(f"known d bits={P115_D.bit_length()}  k bits={P115_K.bit_length()}")
    return lines


def run_puzzle(ctx: PuzzleCtx, gp_mode: str) -> tuple[list[ScoreRow], list[str]]:
    k0 = (ctx.z * pow(ctx.s, -1, N)) % N
    dk = (ctx.r * pow(ctx.s, -1, N)) % N
    gp = geom_pred_index(ctx.ry, ctx.n, gp_mode)
    cands = list(schedule_E(k0, dk, PIVOT_INT, ctx.rx, gp))
    rows = [score_candidate(ctx, c) for c in cands]
    full = [r for r in rows if r.full]
    best = max(rows, key=lambda r: sum([r.rx_match, r.ry_match, r.on_curve, r.pubkey_match, r.d_in_range]))
    lines = [
        f"P{ctx.n} gp_mode={gp_mode} gp_bits={gp.bit_length()} candidates={len(cands)} full_wins={len(full)}",
        f"  best={best.label} score={sum([best.rx_match,best.ry_match,best.on_curve,best.pubkey_match,best.d_in_range])}/5",
    ]
    for r in full[:3]:
        lines.append(f"  FULL WIN {r.label} d_bits={r.d.bit_length()}")
    return rows, lines


def main() -> int:
    keys = parse_53125()
    lines = [
        "SCHEDULE PIPELINE (strict generated_k only)",
        f"PIVOT_I99={PIVOT_I99}  CORR_142=2^142",
        "",
    ]

    ctx115 = load_ctx(115, keys, blind=False)
    if not ctx115:
        print("P115 missing")
        return 1
    lines.extend(p115_lock(ctx115))
    lines.append("")

    gp_modes = ["2p142", "geom_round", "geom_floor", "n_bits"]
    blind_puzzles = [n for n in range(70, 131, 5) if n in PUZZLE_RSZ and n in keys and keys[n].d]

    # P115 calibration: all gp modes + all formulas
    lines.append("=== P115 SCHEDULE E SWEEP (calibration — wins expected only if algebra aligns) ===")
    p115_full: list[ScoreRow] = []
    for mode in gp_modes:
        rows, detail = run_puzzle(ctx115, mode)
        p115_full.extend([r for r in rows if r.full])
        lines.extend(detail)
    lines.append("")

    # Blind funnel P70-P125
    lines.append("=== BLIND P70-P125 (known_k masked) ===")
    blind_full: dict[str, list[int]] = {}
    for n in blind_puzzles:
        ctx = load_ctx(n, keys, blind=True)
        if not ctx:
            continue
        for mode in gp_modes:
            rows, detail = run_puzzle(ctx, mode)
            for r in rows:
                if r.full:
                    blind_full.setdefault(r.label, []).append(n)
            if any(r.full for r in rows):
                lines.extend(detail)

    if blind_full:
        for label, ps in sorted(blind_full.items(), key=lambda x: -len(x[1])):
            lines.append(f"  BLIND WIN {label}: P{ps}")
    else:
        lines.append("  no blind full-score wins on P70-P125")

    lines.append("")
    lines.append("=== P135 (last — not scored as win without ground truth) ===")
    ctx135 = load_ctx(135, keys, blind=True)
    if ctx135:
        for mode in gp_modes:
            rows, detail = run_puzzle(ctx135, mode)
            lines.extend(detail)
            top = sorted(rows, key=lambda r: sum([r.rx_match, r.ry_match, r.pubkey_match, r.d_in_range]), reverse=True)[:2]
            for r in top:
                lines.append(
                    f"    top {r.label} rx={r.rx_match} ry={r.ry_match} pub={r.pubkey_match} band={r.d_in_range}"
                )

    lines.extend([
        "",
        "RECOMMENDATION — feed Schedule E first on P115:",
        "  1. k0 + (2^142) * dk     — linear bridge with fixed 142-bit correction index",
        "  2. R_base + c * 2^142    — sweep c in {-2,-1,0,1,2} from arrested R_x",
        "  3. pivot + 2^142         — I99 pivot + correction scaffold",
        "  Algebra lock: k0 + d*dk is the identity (geom_pred=d); blind path uses 2^142 not d.",
    ])

    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
