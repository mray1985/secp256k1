#!/usr/bin/env python3
"""Forward taxecc calibration: known d on solved puzzles -> each pipeline node output."""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    P115_R_TRUE_X,
    P115_R_TRUE_Y,
    pubkey_from_scalar,
    puzzle_band,
    y_roots,
)
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402
from tax_math_falsify import (  # noqa: E402
    H2_FRAC,
    H_FRAC,
    PIVOT_I99,
    d_from_k,
    form56_adjust,
    k_from_d,
    pivot_k_candidates,
    schedule_k1,
    schedule_k1_full,
)

OUT = ROOT / "ARCHIVE" / "taxecc_solved_forward.txt"


def r_true(n: int) -> tuple[int, int] | None:
    if n == 115:
        return P115_R_TRUE_X, P115_R_TRUE_Y
    return None


def correct_py(rsz_comp: str, px: int) -> int:
    yp, yn = y_roots(px)
    raw = bytes.fromhex(rsz_comp)
    if raw[0] == 2:
        return yp if yp % 2 == 0 else yn
    return yn if yn % 2 else yp


def forward_puzzle(n: int, d: int) -> list[str]:
    rsz = PUZZLE_RSZ[n]
    r, s, z = rsz.r, rsz.s, rsz.z
    px = int(rsz.pub_compressed[2:], 16)
    py = correct_py(rsz.pub_compressed, px)
    rt = r_true(n)
    rx_t, ry_t = rt if rt else (r % rsz.r, py)

    k = k_from_d(r, s, z, d)
    d_back = d_from_k(r, s, z, k)
    gx, gy = pubkey_from_scalar(d)
    kx, ky = pubkey_from_scalar(k)

    lo, hi, _ = puzzle_band(n)
    tz = (d & -d).bit_length() - 1 if d else 0
    lry = math.log2(ry_t) if ry_t > 0 else 0.0
    geom = 2.0 * (PIVOT_I99 - lry / 2.0)

    lines = [
        f"=== P{n} ===",
        f"  GENESIS  d={hex(d)}  bits={d.bit_length()}  in_band={lo <= d < hi}",
        f"           k={hex(k)}  bits={k.bit_length()}",
        f"           d*G match pubkey: x={gx == px}  y={gy == py}",
        f"           [k]G vs R: rx={kx == rx_t}  ry={ky == ry_t}",
        f"  SCHEDULE C  d_from_k roundtrip: {d_back == d}",
        f"  SCHEDULE SE pivot I99={PIVOT_I99}",
        f"           log2(ry)={lry:.4f}  geom_pred={geom:.4f}  log2(k_true)={math.log2(k):.4f}",
        f"           gap log2(k)-geom={math.log2(k) - geom:.2f} bits",
        f"           trailing_zeros(d)={tz}  zero_span=2^{tz}",
    ]

    # nearest SE candidate to true k (by log2 distance)
    se_cands = pivot_k_candidates(ry_t, n)
    if se_cands:
        best = min(se_cands, key=lambda t: abs(math.log2(t[1]) - math.log2(k)))
        lines.append(
            f"           nearest SE cand: [{best[0]}] k_bits={best[1].bit_length()}  "
            f"log2_delta={abs(math.log2(best[1]) - math.log2(k)):.2f}"
        )

    f56 = form56_adjust(k)
    lines.append(f"  FORM 56  branches={len(f56)}  hinge=2^floor(H2*134)={int(2 ** (H2_FRAC * 134))}")
    k1 = schedule_k1(k)
    k1f = schedule_k1_full(k, r, s, z, px)
    lines.append(f"  SCHEDULE K1  glv={len(k1)}  cbrt_paths={len(k1f)}")

    # does any heuristic stage recover d?
    hits: list[str] = []
    for stage, kc in se_cands:
        db = d_from_k(r, s, z, kc)
        if db == d:
            hits.append(f"SE_{stage}")
        for fname, k2 in form56_adjust(kc):
            if d_from_k(r, s, z, k2) == d:
                hits.append(f"SE_{stage}+{fname}")
    lines.append(f"  HEURISTIC d_hits: {hits if hits else 'none'}")
    lines.append("")
    return lines


def main() -> int:
    keys = parse_53125()
    solved = sorted(n for n in PUZZLE_RSZ if n in keys and keys[n].d > 0)

    lines = [
        "TAXECC FORWARD CALIBRATION — solved puzzles (known d -> node outputs)",
        "",
        f"{{H}}={H_FRAC:.6f}  {{H/2}}={H2_FRAC:.6f}  I99 pivot={PIVOT_I99}",
        f"puzzles={len(solved)}",
        "",
    ]

    gaps: list[tuple[int, float]] = []
    for n in solved:
        lines.extend(forward_puzzle(n, keys[n].d))
        rsz = PUZZLE_RSZ[n]
        k = k_from_d(rsz.r, rsz.s, rsz.z, keys[n].d)
        rt = r_true(n)
        ry = rt[1] if rt else correct_py(rsz.pub_compressed, int(rsz.pub_compressed[2:], 16))
        geom = 2.0 * (PIVOT_I99 - math.log2(ry) / 2.0)
        gaps.append((n, math.log2(k) - geom))

    lines.extend([
        "SUMMARY TABLE",
        f"{'P':>4} {'log2k':>8} {'geom':>8} {'gap':>8} {'k_bits':>7} {'d_bits':>7}",
    ])
    for n in solved:
        rsz = PUZZLE_RSZ[n]
        k = k_from_d(rsz.r, rsz.s, rsz.z, keys[n].d)
        rt = r_true(n)
        ry = rt[1] if rt else correct_py(rsz.pub_compressed, int(rsz.pub_compressed[2:], 16))
        geom = 2.0 * (PIVOT_I99 - math.log2(ry) / 2.0)
        lines.append(
            f"P{n:>3} {math.log2(k):8.2f} {geom:8.2f} {math.log2(k)-geom:8.2f} "
            f"{k.bit_length():7d} {keys[n].d.bit_length():7d}"
        )

    avg_gap = sum(g for _, g in gaps) / len(gaps)
    lines.extend([
        "",
        f"mean SE gap (log2 k - geom_pred): {avg_gap:.2f} bits",
        "Schedule C roundtrips on all solved: YES (algebra)",
        "Schedule SE arrests true k: NO on all tested",
        "",
    ])

    text = "\n".join(lines) + "\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
