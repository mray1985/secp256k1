#!/usr/bin/env python3
"""
P27 ground zero: canonical sqrt-fraction offsets anchor all puzzles.

At P27 (tightest |{sqrt x} - {sqrt d}| in dataset):
  GZ_xd = {sqrt x} - {sqrt d}  = -0.004510
  GZ_yd = {sqrt y} - {sqrt d}  = +0.481535
  GZ_yx = {sqrt y} - {sqrt x}  = +0.486045

For puzzle n with pubkey fractions fx, fy:
  pred {sqrt d} from x:  fx - GZ_xd
  pred {sqrt d} from y:  fy - GZ_yd
  band_frac(d) = {2 * pred sqrt d}  (puzzle band)
  d_pred = 2^((n-1) + band_frac)
"""

from __future__ import annotations

import math
import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from bucket_slice_search import verify_candidate  # noqa: E402
from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from p135_common import G, point_add, scalar_mult  # noqa: E402
from puzzle_keys_53125 import parse_53125

REPORT = ROOT / "ARCHIVE" / "p27_ground_zero_anchor.txt"


def frac(x: float) -> float:
    return x - math.floor(x)


def f2s(v: int) -> float:
    getcontext().prec = 80
    return float(Decimal(v).ln() / Decimal(2).ln()) / 2 - math.floor(
        float(Decimal(v).ln() / Decimal(2).ln()) / 2
    )


def band_frac_from_fsqrt(f: float) -> float:
    """band_frac = log2(d)-(n-1) when log2(sqrt d) = (n-1)/2 + f."""
    return frac(2 * f)


def d_from_band_frac(n: int, bf: float) -> int:
    return int(round(2 ** ((n - 1) + bf)))


def scan(d0: int, radius: int, lo: int, hi: int, px: int, py: int) -> int | None:
    d_start = max(lo, d0 - radius)
    d_end = min(hi - 1, d0 + radius)
    pt = scalar_mult(d_start, G)
    for i, d in enumerate(range(d_start, d_end + 1)):
        if pt and pt[0] == px and pt[1] == py and verify_candidate(d, px, py):
            return d
        if i + 1 <= d_end - d_start:
            pt = point_add(pt, G)
    return None


def main() -> int:
    keys = parse_53125()
    pk27 = keys[27]
    GZ_xd = f2s(pk27.px) - f2s(pk27.d)
    GZ_yd = f2s(pk27.py) - f2s(pk27.d)
    GZ_yx = f2s(pk27.py) - f2s(pk27.px)

    lines = [
        "P27 GROUND ZERO — canonical sqrt-fraction anchor",
        "",
        f"P27 d = {pk27.d}",
        f"  {{sqrt d}} = {f2s(pk27.d):.6f}",
        f"  {{sqrt x}} = {f2s(pk27.px):.6f}",
        f"  {{sqrt y}} = {f2s(pk27.py):.6f}",
        f"  band_frac = {math.log2(pk27.d) - 26:.6f}",
        "",
        "GROUND ZERO offsets (apply to any puzzle pubkey fractions):",
        f"  GZ_xd = {{sqrt x}} - {{sqrt d}} = {GZ_xd:+.6f}",
        f"  GZ_yd = {{sqrt y}} - {{sqrt d}} = {GZ_yd:+.6f}",
        f"  GZ_yx = {{sqrt y}} - {{sqrt x}} = {GZ_yx:+.6f}",
        "",
        "Predict:  {sqrt d} = {sqrt x} - GZ_xd  OR  {sqrt y} - GZ_yd",
        "          band_frac = {2 * sqrt d}",
        "",
    ]

    # validate on solved: how close is actual {sqrt d} to x-anchor prediction
    lines.append("=== solved: |actual - pred| from P27 x-anchor ===")
    errs_x = []
    errs_y = []
    for n, pk in sorted(keys.items()):
        if pk.d <= 0:
            continue
        fx, fy, fd = f2s(pk.px), f2s(pk.py), f2s(pk.d)
        px_pred = frac(fx - GZ_xd)
        py_pred = frac(fy - GZ_yd)
        ex = min(abs(fd - px_pred), abs(fd - px_pred + 1), abs(fd - px_pred - 1))
        ey = min(abs(fd - py_pred), abs(fd - py_pred + 1), abs(fd - py_pred - 1))
        errs_x.append(ex)
        errs_y.append(ey)
        if n <= 35 or n in (130, 135) or ex < 0.02:
            lines.append(
                f"  P{n:3d} err_x={ex:.4f} err_y={ey:.4f}  "
                f"actual_fd={fd:.4f} pred_x={px_pred:.4f} pred_y={py_pred:.4f}"
            )

    lines.append(
        f"\n  mean err x-anchor: {sum(errs_x)/len(errs_x):.4f}  "
        f"y-anchor: {sum(errs_y)/len(errs_y):.4f}  "
        f"count err_x<0.05: {sum(1 for e in errs_x if e<0.05)}/{len(errs_x)}"
    )

    # ladder up/down from 27: delta n vs error
    lines.extend(["", "=== distance from ground zero (puzzle n - 27) ==="])
    for n in [1, 10, 20, 27, 40, 60, 80, 100, 115, 130, 135]:
        if n == 135:
            continue
        if n not in keys or keys[n].d <= 0:
            continue
        pk = keys[n]
        fd = f2s(pk.d)
        px_pred = frac(f2s(pk.px) - GZ_xd)
        ex = min(abs(fd - px_pred), abs(fd - px_pred + 1), abs(fd - px_pred - 1))
        lines.append(f"  P{n:3d}  n-27={n-27:+4d}  err_x={ex:.4f}  band_frac={math.log2(pk.d)-(n-1):.4f}")

    # P135 projection
    lines.extend(["", "=== P135 projection from P27 ground zero ==="])
    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn
    fx, fy = f2s(px), f2s(py)
    fd_x = frac(fx - GZ_xd)
    fd_y = frac(fy - GZ_yd)
    bf_x = band_frac_from_fsqrt(fd_x)
    bf_y = band_frac_from_fsqrt(fd_y)
    lo, hi, _ = puzzle_band(135)
    d_x = d_from_band_frac(135, bf_x)
    d_y = d_from_band_frac(135, bf_y)
    lines.append(f"  {{sqrt x}}={fx:.6f}  {{sqrt y}}={fy:.6f}")
    lines.append(f"  pred {{sqrt d}} from x: {fd_x:.6f}  band_frac={bf_x:.6f}")
    lines.append(f"  pred {{sqrt d}} from y: {fd_y:.6f}  band_frac={bf_y:.6f}")
    lines.append(f"  d_x anchor tail ...{str(d_x)[-12:]}  frac_d={(d_x-lo)/lo:.4f}")
    lines.append(f"  d_y anchor tail ...{str(d_y)[-12:]}  frac_d={(d_y-lo)/lo:.4f}")
    lines.append(f"  x vs y anchor disagree by band_frac {abs(bf_x-bf_y):.4f}")

    # EC scan both anchors
    radius = 500_000
    lines.append(f"\n=== EC scan +/-{radius:,} around P27-anchored d (P135) ===")
    for name, d0 in (("x_anchor", d_x), ("y_anchor", d_y)):
        hit = scan(d0, radius, lo, hi, px, py)
        lines.append(f"  {name} center ...{str(d0)[-10:]}  hit={hit or 'none'}")

    # also scan from x-anchor with GZ_yx consistency: fx + GZ_yx should match fy
    chk = frac(fx + GZ_yx)
    lines.append(f"\n  check {{sqrt x}}+GZ_yx={chk:.6f} vs {{sqrt y}}={fy:.6f}  diff={abs(chk-fy):.6f}")

    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
