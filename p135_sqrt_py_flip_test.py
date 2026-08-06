#!/usr/bin/env python3
"""P135: d = m * sqrt(Py) for every in-band m, plus neighbor scan."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from bucket_slice_search import band_midpoint, verify_candidate  # noqa: E402
from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from p135_common import G, point_add, scalar_mult  # noqa: E402

PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
REPORT = ROOT / "ARCHIVE" / "p135_sqrt_py_flip_test.txt"


def isqrt(n: int) -> int:
    lo, hi = 1, n
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid * mid <= n:
            lo = mid
        else:
            hi = mid - 1
    return lo


def corridor(u: int) -> tuple[int, int]:
    lo, hi, _ = puzzle_band(135)
    top = hi - 1
    return (lo + u - 1) // u, top // u


def scan_neighbors(
    center: int,
    radius: int,
    lo: int,
    hi: int,
    px: int,
    py: int,
) -> int | None:
    d0 = max(lo, center - radius)
    d1 = min(hi - 1, center + radius)
    pt = scalar_mult(d0)
    for d in range(d0, d1 + 1):
        if pt and pt[0] == px and pt[1] == py:
            return d
        if d < d1:
            pt = point_add(pt, G)
    return None


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--radius", type=int, default=1 << 18)
    args = ap.parse_args()

    u = isqrt(PY)
    m_start, m_end = corridor(u)
    lo, hi, _ = puzzle_band(135)
    mid = band_midpoint(lo, hi)

    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn

    lines = [
        "P135 sqrt(Py) flip test",
        f"sqrt(Py) = {u}",
        f"sqrt(Py) dec ~ {u}.108267988633809884678...",
        f"m = {m_start} .. {m_end}  ({m_end - m_start + 1} candidates)",
        f"band midpoint frac=0.5 at d ...{str(mid)[-8:]}",
        "",
    ]

    hits = []
    for m in range(m_start, m_end + 1):
        d = m * u
        ok = verify_candidate(d, px, py)
        frac = (d - lo) / lo
        above = d >= mid
        flag = "EC_HIT" if ok else ""
        if ok:
            hits.append((m, d))
        lines.append(
            f"m={m:3d} d_tail...{str(d)[-8:]} frac={frac:.4f} upper={above} {flag}"
        )

    lines.append("")
    if not hits and args.radius:
        lines.append(f"neighbor scan +/-{args.radius} around each center ...")
        print("\n".join(lines[:6]), flush=True)
        for m in range(m_start, m_end + 1):
            found = scan_neighbors(m * u, args.radius, lo, hi, px, py)
            if found is not None:
                hits.append((m, found))
                lines.append(f"NEIGHBOR HIT near m={m} d={found}")
                break

    lines.append(f"EC hits: {len(hits)}")
    for m, d in hits:
        lines.append(f"  HIT m={m} d={d} hex={hex(d)}")

    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0 if hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
