#!/usr/bin/env python3
"""
Exhaustive u-flip corridor search for P135.

Every in-band d = m * U for m in [M_START, M_END] is checked via BSGS on m
(equivalent to brute-forcing all ~2^51 lattice points, feasible in ~2^25 work).

Manifest: P135_u_flip_full_range_manifest.txt
  U = 20962014851359949581252061
  m = 1038930257294765 .. 2077860514589528  (1038930257294764 rows)
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from bucket_slice_search import band_midpoint  # noqa: E402
from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from p135_common import (  # noqa: E402
    G,
    N,
    load_target,
    point_add,
    point_neg,
    save_hit,
    scalar_mult,
    verify_candidate,
)

U = 20962014851359949581252061
M_START = 1038930257294765
M_END = 2077860514589528
REPORT = ROOT / "ARCHIVE" / "p135_u_flip_exhaustive.txt"


def bsgs_u_flip_corridor(
    px: int,
    py: int,
    *,
    m_start: int = M_START,
    m_end: int = M_END,
    u: int = U,
    upper_half_only: bool = False,
    progress: bool = True,
) -> tuple[int, int] | None:
    """Return (m, d) if found else None. Covers every m in [m_start, m_end]."""
    lo, hi, _ = puzzle_band(135)
    if upper_half_only:
        mid = band_midpoint(lo, hi)
        m_min = (mid + u - 1) // u
        m_start = max(m_start, m_min)

    width = m_end - m_start + 1
    if width <= 0:
        return None

    m_step = int(math.isqrt(width)) + 1
    target = (px, py)

    # P(m) = (m*u)*G = P0 + r*UG,  m = m_start + r + j*m_step
    p0 = scalar_mult((m_start * u) % N, G)
    ug = scalar_mult(u % N, G)
    if p0 is None or ug is None:
        return None

    if progress:
        print(f"corridor m=[{m_start},{m_end}] width={width} (~2^{width.bit_length()})")
        print(f"BSGS m_step={m_step} (~2^{m_step.bit_length()})")

    baby: dict[int, int] = {}
    t0 = time.perf_counter()
    pt = p0
    for r in range(m_step):
        if pt is not None:
            x = pt[0]
            if x not in baby:
                baby[x] = r
        if r + 1 < m_step:
            pt = point_add(pt, ug)
        if progress and r and r % max(1, m_step // 10) == 0:
            print(f"  baby {r}/{m_step}", flush=True)

    if progress:
        print(f"  baby table {len(baby):,} in {time.perf_counter()-t0:.1f}s", flush=True)

    neg_mug = point_neg(scalar_mult(m_step, ug))
    q = point_add(target, point_neg(p0))
    t1 = time.perf_counter()

    for j in range(m_step):
        m_base = m_start + j * m_step
        if m_base > m_end:
            break
        if q is not None:
            r = baby.get(q[0])
            if r is not None:
                m_abs = m_base + r
                if m_start <= m_abs <= m_end:
                    d = m_abs * u
                    if lo <= d < hi and verify_candidate(d, px, py):
                        return m_abs, d
        q = point_add(q, neg_mug) if q is not None else None
        if progress and j and j % max(1, m_step // 10) == 0:
            print(f"  giant j={j}/{m_step}", flush=True)

    if progress:
        print(f"  giant done in {time.perf_counter()-t1:.1f}s", flush=True)
    return None


def linear_scan_chunk(
    px: int,
    py: int,
    m_from: int,
    m_to: int,
    *,
    u: int = U,
    emit_every: int = 5_000_000,
) -> tuple[int, int] | None:
    """Literal every-m scan for a chunk (checkpoint-friendly)."""
    lo, hi, _ = puzzle_band(135)
    ug = scalar_mult(u, G)
    p0 = scalar_mult((m_from * u) % N, G)
    if ug is None or p0 is None:
        return None
    pt = p0
    t0 = time.perf_counter()
    for i, m in enumerate(range(m_from, m_to + 1)):
        if i:
            pt = point_add(pt, ug)
        if pt and pt[0] == px and pt[1] == py:
            d = m * u
            if lo <= d < hi:
                return m, d
        if emit_every and i and i % emit_every == 0:
            rate = i / max(time.perf_counter() - t0, 1e-9)
            print(f"  m={m} {rate:,.0f}/s", flush=True)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Exhaustive P135 u-flip corridor")
    ap.add_argument("--mode", choices=("bsgs", "linear"), default="bsgs")
    ap.add_argument("--upper-half", action="store_true")
    ap.add_argument("--m-from", type=int, default=M_START)
    ap.add_argument("--m-to", type=int, default=M_END)
    args = ap.parse_args()

    px, py, _, _, _ = load_target()
    lines = [
        "P135 u-flip exhaustive corridor",
        f"U={U}",
        f"m=[{args.m_from}, {args.m_to}]",
        f"mode={args.mode} upper_half={args.upper_half}",
        "",
    ]

    if args.mode == "bsgs":
        hit = bsgs_u_flip_corridor(px, py, m_start=args.m_from, m_end=args.m_to, upper_half_only=args.upper_half)
    else:
        hit = linear_scan_chunk(px, py, args.m_from, args.m_to)

    if hit:
        m, d = hit
        lines.append(f"HIT m={m} d={d} hex={hex(d)}")
        save_hit(d, source="u_flip_exhaustive")
        print("\n".join(lines))
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 0

    lines.append("no hit (entire requested corridor covered)")
    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
