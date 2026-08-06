#!/usr/bin/env python3
"""
Falsify the Tax Math pipeline on solved puzzles + report P135.

Schedule SE  -> 199-bit pivot arrests k from ry
Form 56      -> {H/2} hinge adjustment (p-N field gap)
Schedule K1  -> GLV lambda + cubic-root branches
Schedule C   -> d = (s*k - z) * r^-1 mod N

Pass criteria (per puzzle with known d):
  [k]G matches R (rx, ry)  AND  d_rec == d_known  AND  d_rec*G == P
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path

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
    primitive_cube_root_of_unity,
    pubkey_from_scalar,
    puzzle_band,
    y_roots,
)
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

getcontext().prec = 80

# secp256k1 GLV eigenvalue (scalar endomorphism)
LAMBDA_GLV = 0x5363AD4CC05C30E0A5261C028812645A122E22EA20816678DF02967C1B23BD72

PN = p - N
PIVOT_I99 = 198.95
H_FRAC = math.log2(PN) - math.floor(math.log2(PN))  # {H}
H2_FRAC = (math.log2(PN) / 2) - math.floor(math.log2(PN) / 2)  # {H/2}

REPORT = ROOT / "ARCHIVE" / "tax_math_falsify.txt"


@dataclass
class Trial:
    puzzle: int
    stage: str
    k: int
    d: int
    rx_match: bool
    ry_match: bool
    d_match: bool
    ec_d: bool
    in_band: bool


def k_from_d(r: int, s: int, z: int, d: int) -> int:
    return (pow(s, -1, N) * (z + r * d)) % N


def d_from_k(r: int, s: int, z: int, k: int) -> int:
    return (pow(r, -1, N) * (s * k - z)) % N


def point_from_k(k: int) -> tuple[int, int]:
    return pubkey_from_scalar(k % N)


def pivot_k_candidates(ry: int, n: int) -> list[tuple[str, int]]:
    """Schedule SE: geometric pivot -> integer k guesses."""
    if ry <= 0:
        return []
    lry = math.log2(ry)
    lsry = lry / 2.0
    out: list[tuple[str, int]] = []

    for pivot in (PIVOT_I99, 199.0, 198.0):
        lsk = pivot - lsry
        lk = 2.0 * lsk
        for shift_name, lk_adj in [
            ("raw", lk),
            ("minus8", lk - 8),
            ("minus_n_gap", lk - (256 - n)),
            ("to_n_bits", float(n)),
        ]:
            if lk_adj <= 0:
                continue
            k_int = int(round(2**lk_adj))
            if k_int > 0:
                out.append((f"pivot{pivot}_{shift_name}", k_int))
            # floor/ceil variants
            k_lo = int(2 ** math.floor(lk_adj))
            k_hi = int(2 ** math.ceil(lk_adj))
            if k_lo > 0:
                out.append((f"pivot{pivot}_{shift_name}_floor", k_lo))
            if k_hi > 0 and k_hi != k_lo:
                out.append((f"pivot{pivot}_{shift_name}_ceil", k_hi))
    return out


def form56_adjust(k: int) -> list[tuple[str, int]]:
    """Form 56: hinge phase adjustments on k."""
    h2 = Decimal(str(H2_FRAC))
    spn = Decimal(PN).sqrt()
    tail = Decimal(N).sqrt() - Decimal(N).sqrt().to_integral_value()
    out: list[tuple[str, int]] = []
    scales = [
        ("identity", 1.0),
        ("mul_2^H2", float(2**H2_FRAC)),
        ("div_2^H2", float(2 ** (-H2_FRAC))),
        ("mul_sqrt_pN_frac", float(spn * tail) / float(2**64)),
    ]
    for name, scale in scales:
        if scale <= 0:
            continue
        k2 = int(k * scale) % N
        if k2 > 0:
            out.append((f"form56_{name}", k2))
    # integer hinge: k +/- 2^floor(H2*134)
    hinge = int(2 ** (H2_FRAC * 134))
    out.append(("form56_k_plus_hinge", (k + hinge) % N))
    out.append(("form56_k_minus_hinge", (k - hinge) % N))
    return out


def schedule_k1(k: int) -> list[tuple[str, int]]:
    """Schedule K1: GLV paths on k."""
    out: list[tuple[str, int]] = []
    for i, mult in enumerate([1, LAMBDA_GLV, (LAMBDA_GLV * LAMBDA_GLV) % N]):
        out.append((f"glv_{i}", (k * mult) % N))
    return out


def schedule_k1_full(k: int, r: int, s: int, z: int, px: int) -> list[tuple[str, int]]:
    out = schedule_k1(k)
    r %= N
    if pow(r, (N - 1) // 3, N) == 1:
        u0 = pow(r, (N + 2) // 9, N)
        w = primitive_cube_root_of_unity(N)
        branches = [u0]
        if w:
            branches = [u0, (u0 * w) % N, (u0 * w * w) % N]
        for j, u in enumerate(branches):
            lam = (px * pow(u, -1, N)) % N
            denom = (s - r * lam) % N
            if denom == 0:
                continue
            k_arrest = (z * pow(denom, -1, N)) % N
            out.append((f"k1_cbrt_j{j}", k_arrest))
    return out


def evaluate(
    n: int,
    stage: str,
    k: int,
    r: int,
    s: int,
    z: int,
    px: int,
    py: int,
    d_known: int | None,
    rx_true: int | None,
    ry_true: int | None,
) -> Trial:
    lo, hi, _ = puzzle_band(n)
    d = d_from_k(r, s, z, k)
    try:
        kx, ky = point_from_k(k)
    except Exception:
        kx, ky = -1, -1
    rx = r % N  # signature r
    rx_match = kx == rx or (rx_true is not None and kx == rx_true)
    ry_match = ry_true is not None and ky == ry_true
    d_match = d_known is not None and d == d_known
    try:
        dx, dy = pubkey_from_scalar(d)
        ec_d = dx == px and dy == py
    except Exception:
        ec_d = False
    return Trial(n, stage, k, d, rx_match, ry_match, d_match, ec_d, lo <= d < hi)


def hunt_puzzle(
    n: int,
    d_known: int | None,
    rx_true: int | None,
    ry_true: int | None,
) -> tuple[list[Trial], list[str]]:
    rsz = PUZZLE_RSZ.get(n)
    if not rsz:
        return [], [f"P{n}: no RSZ"]
    r, s, z = rsz.r, rsz.s, rsz.z
    comp = rsz.pub_compressed
    px = int(comp[2:], 16)
    yp, yn = y_roots(px)
    py = yp if comp.startswith("02") else yn

    ry_use = ry_true if ry_true is not None else py
    lines = [f"P{n}  known_d={d_known is not None}  ry_source={'R_true' if ry_true else 'pub_y'}"]

    if d_known:
        k_true = k_from_d(r, s, z, d_known)
        try:
            kx, ky = point_from_k(k_true)
            lines.append(
                f"  k_true bits={k_true.bit_length()}  [k]G rx_match={kx == rx_true or kx == r}  "
                f"ry_match={ry_true is not None and ky == ry_true}"
            )
            lines.append(
                f"  pivot log2(k)={math.log2(k_true):.4f}  "
                f"geom_pred={2*(PIVOT_I99 - math.log2(ry_use)/2):.4f}"
            )
        except Exception as ex:
            lines.append(f"  k_true error: {ex}")

    trials: list[Trial] = []
    seen: set[tuple[str, int]] = set()

    def add(stage: str, k: int) -> None:
        key = (stage, k)
        if key in seen or k <= 0:
            return
        seen.add(key)
        trials.append(evaluate(n, stage, k, r, s, z, px, py, d_known, rx_true, ry_true))

    # Schedule SE
    for name, k in pivot_k_candidates(ry_use, n):
        add(f"SE_{name}", k)
        for fname, k2 in form56_adjust(k):
            add(f"SE_{name}+{fname}", k2)
        for kname, k3 in schedule_k1_full(k, r, s, z, px):
            add(f"SE_{name}+{kname}", k3)

    # If known k, test direct Schedule C only
    if d_known:
        k_true = k_from_d(r, s, z, d_known)
        add("known_k_direct", k_true)

    wins = [t for t in trials if t.ec_d and t.d_match]
    rx_wins = [t for t in trials if t.rx_match and t.ry_match]
    lines.append(f"  trials={len(trials)}  full_wins(ec+d)={len(wins)}  R_point_wins={len(rx_wins)}")
    for t in wins[:5]:
        lines.append(f"    WIN {t.stage} k_bits={t.k.bit_length()} d_bits={t.d.bit_length()}")
    return trials, lines


def main() -> int:
    keys = parse_53125()
    lines = [
        "TAX MATH FALSIFICATION REPORT",
        "",
        f"I99 pivot = {PIVOT_I99}",
        f"{{H}} = {H_FRAC:.6f}  {{H/2}} = {H2_FRAC:.6f}",
        "",
    ]

    all_trials: list[Trial] = []
    solved_with_d = sorted(n for n in PUZZLE_RSZ if n in keys and keys[n].d > 0)

    for n in solved_with_d:
        rx_true = ry_true = None
        if n == 115:
            rx_true, ry_true = P115_R_TRUE_X, P115_R_TRUE_Y
        trials, detail = hunt_puzzle(n, keys[n].d, rx_true, ry_true)
        all_trials.extend(trials)
        lines.extend(detail)
        lines.append("")

    # P135 unsolved
    trials135, detail135 = hunt_puzzle(135, None, P135_R_TRUE_X, P135_R_TRUE_Y)
    all_trials.extend(trials135)
    lines.extend(["=== P135 (unsolved) ==="])
    lines.extend(detail135)
    band_hits = [t for t in trials135 if t.in_band and t.ec_d]
    lines.append(f"  P135 ec+band hits: {len(band_hits)}")
    for t in band_hits[:10]:
        lines.append(f"    {t.stage} d={t.d}")

    # Summary
    full_wins = [t for t in all_trials if t.d_match and t.ec_d]
    lines.extend([
        "",
        "SUMMARY",
        f"  solved puzzles tested: {len(solved_with_d)}",
        f"  total trials: {len(all_trials)}",
        f"  full wins (d_match AND ec_d) on solved: {len(full_wins)}",
    ])
    if full_wins:
        for t in full_wins[:20]:
            lines.append(f"    P{t.puzzle} {t.stage}")
    else:
        lines.append("  VERDICT: Tax Math pipeline does NOT recover known d on solved puzzles.")
        lines.append("  Schedule C is correct algebra; Schedule SE pivot does not arrest true k.")

    # P115 explicit calibration
    lines.extend([
        "",
        "P115 CALIBRATION (ground truth)",
        f"  d_known bits={P115_D.bit_length()}",
        f"  k_known bits={P115_K.bit_length()}",
        f"  k0+d*dk==k: {( (int(PUZZLE_RSZ[115].z) * pow(int(PUZZLE_RSZ[115].s),-1,N) + P115_D * (int(PUZZLE_RSZ[115].r)*pow(int(PUZZLE_RSZ[115].s),-1,N))%N) % N) == P115_K % N}",
    ])

    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
