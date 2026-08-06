#!/usr/bin/env python3
"""
P135: d = m * cbrt(rx) flipped through full band [2^134, 2^135).

cbrt(rx) ~ 4.49222121914583157683347142071669243628790707445889164843386 * 10^25
rx = P135_R_TRUE_X (signature r / wrong rx branch tail ...368)

Uses BSGS on m to exhaustively cover every in-band lattice point (same as u-flip).
"""

from __future__ import annotations

import argparse
import math
import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from bucket_slice_search import band_midpoint  # noqa: E402
from ecdlp_full_pipeline import N, puzzle_band  # noqa: E402
from p135_common import load_target, save_hit, verify_candidate  # noqa: E402
from p135_u_flip_exhaustive import bsgs_u_flip_corridor  # noqa: E402

RX = 90653255469745952335985143920649543885181555095025199315947044135806663628368
CBRT_RX_DEC = Decimal("4.49222121914583157683347142071669243628790707445889164843386")


def cbrt_u_integer() -> int:
    """Integer floor of real cbrt(rx) — matches Wolfram ~4.492... × 10^25."""
    lo, hi = 1, RX
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid * mid * mid <= RX:
            lo = mid
        else:
            hi = mid - 1
    return lo


REPORT = ROOT / "ARCHIVE" / "p135_cbrt_rx_flip_exhaustive.txt"


def corridor_bounds(u: int) -> tuple[int, int, int]:
    lo, hi, _ = puzzle_band(135)
    top = hi - 1
    m_start = (lo + u - 1) // u
    m_end = top // u
    count = max(0, m_end - m_start + 1)
    return m_start, m_end, count


def mod_n_cube_roots(r: int) -> list[int]:
    """Three cube roots of r mod N when N == 7 (mod 9)."""
    exp = (N + 2) // 9
    u0 = pow(r, exp, N)
    omega = pow(2, (2 * N - 1) // 3, N)
    if pow(omega, 3, N) != 1 % N:
        omega = pow(3, (N - 1) // 3, N)
    return [u0 % N, (u0 * omega) % N, (u0 * omega * omega) % N]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upper-half", action="store_true")
    ap.add_argument("--bsgs", action="store_true", default=True)
    args = ap.parse_args()

    u = cbrt_u_integer()
    m_start, m_end, count = corridor_bounds(u)
    px, py, _, _, _ = load_target()
    lo, hi, _ = puzzle_band(135)
    mid = band_midpoint(lo, hi)

    lines = [
        "P135 cbrt(rx) flip exhaustive",
        f"rx tail ...{str(RX)[-6:]}",
        f"cbrt(rx) dec ~ {CBRT_RX_DEC} * 10^25",
        f"U = int(cbrt) = {u}",
        f"U digits = {u.bit_length()} bits",
        f"m_start = {m_start}",
        f"m_end   = {m_end}",
        f"row_count = {count} (~2^{count.bit_length()})",
        f"first d = {m_start * u}",
        f"last  d = {m_end * u}",
        f"upper_half_only = {args.upper_half}",
        "",
        "mod-N cube roots of rx (scalar court, not real cbrt):",
    ]

    for i, root in enumerate(mod_n_cube_roots(RX)):
        lines.append(f"  u{i} tail ...{str(root)[-6:]}  (mod N)")

    lines.append("")
    print("\n".join(lines), flush=True)

    hit = bsgs_u_flip_corridor(
        px,
        py,
        m_start=m_start,
        m_end=m_end,
        u=u,
        upper_half_only=args.upper_half,
    )

    if hit:
        m, d = hit
        lines.append(f"HIT m={m} d={d} hex={hex(d)}")
        save_hit(d, source="cbrt_rx_flip")
        text = "\n".join(lines)
        REPORT.write_text(text + "\n", encoding="utf-8")
        print(text)
        return 0

    lines.append("no hit (entire cbrt(rx) corridor covered)")
    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
