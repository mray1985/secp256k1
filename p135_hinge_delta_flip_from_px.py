#!/usr/bin/env python3
"""
Step away from P135 Px using hinge gap Delta, flipped through the band.

H = log2(p-N)
Delta_x = H - log2(sqrt(Px)),  Delta_y = H - log2(sqrt(Py))

Flip lattice: d = m * U  for m in corridor [2^134, 2^135).

U variants:
  - coord / 2^Delta  (flip away from hinge in log-sqrt space)
  - coord * 2^Delta  (toward hinge)
  - (p-N) / coord scaled
  - 2^Delta, 2^(Delta-1) as raw step units from Px-derived anchors
"""

from __future__ import annotations

import math
import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from bucket_slice_search import band_midpoint, verify_candidate  # noqa: E402
from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
PN = P - N
PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
REPORT = ROOT / "ARCHIVE" / "p135_hinge_delta_flip_from_px.txt"


def isqrt(n: int) -> int:
    lo, hi = 1, max(1, n)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid * mid <= n:
            lo = mid
        else:
            hi = mid - 1
    return lo


def log2_dec(n: int) -> Decimal:
    getcontext().prec = 80
    return Decimal(n).ln() / Decimal(2).ln()


def hinge_deltas(px: int, py: int) -> tuple[Decimal, Decimal, Decimal]:
    getcontext().prec = 80
    h = log2_dec(PN)
    dx = h - log2_dec(px) / 2
    dy = h - log2_dec(py) / 2
    return h, dx, dy


def corridor(u: int, lo: int, top: int) -> tuple[int, int, int]:
    if u <= 0:
        return 0, -1, 0
    ms = (lo + u - 1) // u
    me = top // u
    return ms, me, max(0, me - ms + 1)


def scan_corridor(u: int, lo: int, top: int, px: int, py: int, mirror: bool = False) -> list[int]:
    ms, me, _ = corridor(u, lo, top)
    hits = []
    for m in range(ms, me + 1):
        d = m * u
        if mirror:
            d = N - d
        if lo <= d < top + 1 or (mirror and lo <= d <= top):
            if lo <= d < lo + (top - lo + 1):
                pass
        if lo <= d < top + 1:
            if verify_candidate(d, px, py):
                hits.append(d)
        elif mirror:
            d2 = N - d
            if lo <= d2 < top + 1 and verify_candidate(d2, px, py):
                hits.append(d2)
    return hits


def scale_int(v: int, exp: float, div: bool) -> int:
    """v * 2^exp or v / 2^exp as integer."""
    if div:
        return int(v / (2**exp))
    return int(v * (2**exp))


def main() -> int:
    getcontext().prec = 80
    lo, hi, _ = puzzle_band(135)
    top = hi - 1
    mid = band_midpoint(lo, hi)

    rsz = PUZZLE_RSZ[135]
    tpx = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(tpx)
    tpy = yp if yp % 2 == 0 else yn

    h, dx, dy = hinge_deltas(PX, PY)
    sqrt_x = isqrt(PX)
    sqrt_y = isqrt(PY)
    sqrt_pn = isqrt(PN)

    dx_f = float(dx)
    dy_f = float(dy)

    lines = [
        "P135 hinge-delta flip from Px",
        f"H = log2(p-N) = {float(h)}",
        f"Delta_x = {dx_f:.6f}  Delta_y = {dy_f:.6f}",
        f"sqrt(Px) bits={sqrt_x.bit_length()} sqrt(Py) bits={sqrt_y.bit_length()}",
        f"2^Delta_x = {2**dx_f:.6f}  2^Delta_y = {2**dy_f:.6f}",
        f"2^(Delta_x-1) = {2**(dx_f-1):.6f}  2^(Delta_y-1) = {2**(dy_f-1):.6f}",
        "",
        "Interpretation: sqrt(p-N)/sqrt(coord) = 2^Delta",
        f"  check y: ratio={sqrt_pn/sqrt_y:.6f} 2^Dy={2**dy_f:.6f}",
        f"  check x: ratio={sqrt_pn/sqrt_x:.6f} 2^Dx={2**dx_f:.6f}",
        "",
        "=== flip corridors d = m*U (and mirror N-d) ===",
    ]

    # Build U candidates
    candidates: list[tuple[str, int]] = []

    for side, coord, delta in (("x", sqrt_x, dx_f), ("y", sqrt_y, dy_f)):
        for tag, div in (("flip_div", True), ("toward_mul", False)):
            for use_delta in (delta, delta - 1, 1.0):
                if use_delta <= 0:
                    continue
                u = scale_int(coord, use_delta, div)
                name = f"{side}_{tag}_d{use_delta:.4f}"
                candidates.append((name, u))

    # ratio anchors: U = (p-N) / coord  flipped
    candidates.append(("pn_div_sqrt_y", PN // sqrt_y if sqrt_y else 0))
    candidates.append(("pn_div_sqrt_x", PN // sqrt_x if sqrt_x else 0))
    candidates.append(("sqrt_y_div_2dy", scale_int(sqrt_y, dy_f, True)))
    candidates.append(("sqrt_x_div_2dx", scale_int(sqrt_x, dx_f, True)))
    candidates.append(("sqrt_y_mul_2dy", scale_int(sqrt_y, dy_f, False)))
    candidates.append(("Px_div_2dx2", scale_int(PX, 2 * dx_f, True)))
    candidates.append(("Py_div_2dy2", scale_int(PY, 2 * dy_f, True)))
    candidates.append(("raw_2^Dy", int(2**dy_f)))
    candidates.append(("raw_2^Dx", int(2**dx_f)))
    candidates.append(("raw_2^(Dy-1)", int(2 ** (dy_f - 1))))
    candidates.append(("Px_step_flip", scale_int(PX, dy_f, True)))  # step scalar-ish from Px coord

    # d anchors from log (from prior analysis)
    for tag, d in [
        ("LO*2^(Dy-1)", int(lo * (2 ** (dy_f - 1)))),
        ("mid*2^(Dy-1)", int(mid * (2 ** (dy_f - 1)))),
        ("LO*(1+Dy-1)", int(lo * (1 + (dy_f - 1)))),
        ("LO*Dy/256", int(lo * dy_f / 256)),
        ("mid*Dy/256", int(mid * dy_f / 256)),
    ]:
        candidates.append((tag, d))

    seen_u: set[int] = set()
    total_tested = 0
    all_hits: list[tuple[str, int]] = []

    for name, u in candidates:
        if u <= 0 or u in seen_u:
            continue
        seen_u.add(u)
        ms, me, cnt = corridor(u, lo, top)
        if cnt == 0 or cnt > 10_000_000:
            lines.append(f"  {name}: U={u} ({u.bit_length()}b) m=[{ms},{me}] count={cnt} SKIP")
            continue
        hits = scan_corridor(u, lo, top, tpx, tpy, mirror=False)
        total_tested += cnt
        line = f"  {name}: U={u} ({u.bit_length()}b) count={cnt} hits={len(hits)}"
        if cnt <= 200:
            for m in range(ms, me + 1):
                d = m * u
                frac = (d - lo) / lo
                lp = math.log2(d) - 134
                line += f"\n    m={m} d_tail={str(d)[-8:]} frac={frac:.4f} log_pos={lp:.4f}"
        lines.append(line)
        for d in hits:
            all_hits.append((name, d))
        # mirror pass on same U
        hits_m = []
        for m in range(ms, me + 1):
            d = N - m * u
            if lo <= d <= top and verify_candidate(d, tpx, tpy):
                hits_m.append(d)
        if hits_m:
            lines.append(f"    mirror hits={hits_m}")
            for d in hits_m:
                all_hits.append((name + "_mirror", d))

    lines.extend([
        "",
        f"total lattice points tested: {total_tested}",
        f"EC hits: {len(all_hits)}",
    ])
    for name, d in all_hits:
        lines.append(f"  HIT {name} d={d} hex={hex(d)}")

    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {REPORT}")
    return 0 if all_hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
