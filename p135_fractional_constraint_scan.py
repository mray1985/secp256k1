#!/usr/bin/env python3
"""
P135 fractional constraint scan.

Targets (band_frac = log2(d) - 134):
  1. upper_half mid     band_frac ~ 0.584963
  2. frac(lsy) - frac(dy) ~ 0.333450  from {H}-{lsy} = {dy} ~ 0.006126
  3. frac(H)            band_frac ~ 0.345702
  4. mid*2^(dy-1) lane  band_frac ~ 0.506
  5. band_frac - frac(lsy) ~ 0.245 (upper-mid minus y frac)

For each anchor: neighbor EC scan +/- radius.
Also reports fractional residuals for every tested d.
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from bucket_slice_search import band_midpoint, verify_candidate  # noqa: E402
from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from p135_common import G, point_add, scalar_mult  # noqa: E402

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
PN = P - N
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800

H = Decimal(PN).ln() / Decimal(2).ln()
getcontext().prec = 80
LSY = float((Decimal(PY).ln() / Decimal(2).ln()) / 2)
DY = float(H) - LSY

FRAC_H = float(H) - math.floor(float(H))
FRAC_LSY = LSY - math.floor(LSY)
FRAC_DY = DY - math.floor(DY)

REPORT = ROOT / "ARCHIVE" / "p135_fractional_constraint_scan.txt"


def frac(x: float) -> float:
    return x - math.floor(x)


def band_frac(d: int) -> float:
    return math.log2(d) - 134


def d_at_band_frac(bf: float) -> int:
    return int(round(2 ** (134 + bf)))


def fractional_metrics(d: int) -> dict:
    bf = band_frac(d)
    f_log2d = frac(math.log2(d))
    res_y = FRAC_LSY - f_log2d
    res_h = FRAC_H - FRAC_LSY  # exact P135 hinge fractional gap on y
    return {
        "d": d,
        "bf": bf,
        "frac_log2d": f_log2d,
        "res_lsy_minus_log2d": res_y,
        "res_h_minus_lsy": FRAC_H - FRAC_LSY,
        "bf_minus_lsy": bf - FRAC_LSY,
    }


def scan_neighbors(
    center: int,
    radius: int,
    lo: int,
    hi: int,
    px: int,
    py: int,
) -> tuple[int | None, int]:
    d0 = max(lo, center - radius)
    d1 = min(hi - 1, center + radius)
    tested = d1 - d0 + 1
    pt = scalar_mult(d0, G)
    for i, d in enumerate(range(d0, d1 + 1)):
        if pt and pt[0] == px and pt[1] == py:
            if verify_candidate(d, px, py):
                return d, tested
        if i + 1 <= d1 - d0:
            pt = point_add(pt, G)
    return None, tested


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--radius", type=int, default=500_000)
    ap.add_argument("--wide", type=int, default=0, help="extra wide scan radius for anchor 1")
    args = ap.parse_args()

    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn

    lo, hi, _ = puzzle_band(135)
    mid = band_midpoint(lo, hi)

    anchors = [
        ("upper_half_mid", 0.584963),
        ("frac_lsy_minus_frac_dy", FRAC_LSY - FRAC_DY),
        ("frac_H", FRAC_H),
        ("dy_minus1_lane", math.log2(mid * (2 ** (DY - 1))) - 134),
        ("bf_minus_lsy_0245", FRAC_LSY + 0.245450),  # ~0.585 - 0.340
    ]

    lines = [
        "P135 fractional constraint scan",
        f"H={float(H):.12f}  frac(H)={FRAC_H:.6f}",
        f"log2(sqrt Py)={LSY:.12f}  frac={FRAC_LSY:.6f}",
        f"Delta_y={DY:.6f}  frac(Dy)={FRAC_DY:.6f}",
        f"identity frac(H)-frac(lsy)={FRAC_H - FRAC_LSY:.6f}  (expect frac(Dy)={FRAC_DY:.6f})",
        f"band [{lo}, {hi})  mid bf={math.log2(mid)-134:.6f}",
        f"radius +/- {args.radius:,}",
        "",
        "=== anchors ===",
    ]

    total_tested = 0
    hits: list[tuple[str, int]] = []
    t0 = time.perf_counter()

    for name, bf in anchors:
        center = d_at_band_frac(bf)
        center = max(lo, min(hi - 1, center))
        m = fractional_metrics(center)
        rad = args.wide if name == "upper_half_mid" and args.wide else args.radius
        hit, tested = scan_neighbors(center, rad, lo, hi, px, py)
        total_tested += tested
        lines.append(f"{name}:")
        lines.append(f"  target bf={bf:.6f}  center d tail ...{str(center)[-10:]}")
        lines.append(
            f"  actual bf={m['bf']:.6f}  frac_log2d={m['frac_log2d']:.6f}  "
            f"frac(lsy)-frac(log2d)={m['res_lsy_minus_log2d']:.6f}  "
            f"bf-frac(lsy)={m['bf_minus_lsy']:.6f}"
        )
        lines.append(f"  scan +/-{rad:,} tested={tested:,} hit={'YES d='+str(hit) if hit else 'no'}")
        if hit:
            hits.append((name, hit))
        lines.append("")

    # Combined tight window: bf within eps of 0.585 AND |frac(lsy)-frac(log2d) - 0.006| small
    # These are incompatible at same d; report separately
    lines.append("=== note: simultaneous bf~0.585 AND frac(lsy)-frac(log2d)~0.006 impossible ===")
    lines.append(f"  at bf=0.585: frac(lsy)-frac(log2d) = {FRAC_LSY - frac(math.log2(d_at_band_frac(0.585))):.6f}")
    lines.append(f"  at frac diff 0.006: bf = {band_frac(d_at_band_frac(FRAC_LSY - FRAC_DY)):.6f}")
    lines.append("")

    # Dense micro-scan around upper_half if small enough
    eps = 0.002
    d_lo = int(2 ** (134 + 0.584963 - eps))
    d_hi = int(2 ** (134 + 0.584963 + eps))
    d_lo = max(lo, d_lo)
    d_hi = min(hi - 1, d_hi)
    micro_count = d_hi - d_lo + 1
    lines.append(f"=== micro corridor bf in [0.583,0.587]: {micro_count:,} keys ===")
    if micro_count <= 5_000_000:
        pt = scalar_mult(d_lo, G)
        micro_hit = None
        best_frac = None
        best_d = None
        for i, d in enumerate(range(d_lo, d_hi + 1)):
            if pt and pt[0] == px and pt[1] == py and verify_candidate(d, px, py):
                micro_hit = d
                break
            r = FRAC_LSY - frac(math.log2(d))
            if best_frac is None or abs(r - FRAC_DY) < abs(best_frac - FRAC_DY):
                best_frac = r
                best_d = d
            if i + 1 <= d_hi - d_lo:
                pt = point_add(pt, G)
        total_tested += micro_count
        lines.append(f"  tested {micro_count:,}  hit={micro_hit or 'none'}")
        if best_d:
            lines.append(
                f"  closest frac(lsy)-frac(log2d) to {FRAC_DY:.6f}: d tail ...{str(best_d)[-10:]} "
                f"val={best_frac:.6f} bf={band_frac(best_d):.6f}"
            )
    else:
        lines.append(f"  skip full micro (>{micro_count:,} keys); use --radius on anchor")

    elapsed = time.perf_counter() - t0
    lines.extend([
        "",
        f"total EC keys tested: {total_tested:,}",
        f"elapsed: {elapsed:.1f}s",
        f"hits: {len(hits)}",
    ])
    for name, d in hits:
        lines.append(f"  HIT {name} d={d} hex={hex(d)}")

    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {REPORT}")
    return 0 if hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
