#!/usr/bin/env python3
"""
P135 dual-anchor scan: +d only (y leg), plus N-d mirror report (-y leg).

Anchors:
  hinge_frac  band_frac ~ 0.333  ({log2 sqrt y} - {log2 d} = {Delta_y})
  upper_half  band_frac ~ 0.585  (mid / upper-half lane)
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

from bucket_slice_search import verify_candidate  # noqa: E402
from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from p135_common import G, point_add, scalar_mult  # noqa: E402

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
PN = P - N
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
PYN = P - PY

getcontext().prec = 80
H = float(Decimal(PN).ln() / Decimal(2).ln())
LSY = float((Decimal(PY).ln() / Decimal(2).ln()) / 2)
LSY_NEG = float((Decimal(PYN).ln() / Decimal(2).ln()) / 2)
DY = H - LSY
DY_NEG = H - LSY_NEG

FRAC_H = H - math.floor(H)
FRAC_LSY = LSY - math.floor(LSY)
FRAC_LSY_NEG = LSY_NEG - math.floor(LSY_NEG)
FRAC_DY = DY - math.floor(DY)

ANCHORS = [
    ("hinge_frac", FRAC_LSY - FRAC_DY),  # ~0.333450
    ("upper_half", 0.584963),
]

REPORT = ROOT / "ARCHIVE" / "p135_dual_anchor_plus_d_scan.txt"


def frac(x: float) -> float:
    return x - math.floor(x)


def band_frac(d: int) -> float:
    return math.log2(d) - 134


def d_at_bf(bf: float) -> int:
    return int(round(2 ** (134 + bf)))


def scan_plus_d(
    center: int,
    radius: int,
    lo: int,
    hi: int,
    px: int,
    py: int,
) -> tuple[int | None, int]:
    d0 = max(lo, center - radius)
    d1 = min(hi - 1, center + radius)
    n = d1 - d0 + 1
    pt = scalar_mult(d0, G)
    for i, d in enumerate(range(d0, d1 + 1)):
        if pt and pt[0] == px and pt[1] == py and verify_candidate(d, px, py):
            return d, n
        if i + 1 <= d1 - d0:
            pt = point_add(pt, G)
    return None, n


def mirror_report(d: int, mlo: int, mhi: int) -> dict:
    dm = N - d
    l2 = math.log2(dm)
    return {
        "N_minus_d": dm,
        "log2_frac": frac(l2),
        "mirror_log_off": l2 - math.log2(mlo),
        "in_mirror_band": mlo <= dm <= mhi,
        "frac_lsy_minus_log2": FRAC_LSY - frac(l2),
        "frac_lsy_neg_minus_log2": FRAC_LSY_NEG - frac(l2),
        "dy_neg": DY_NEG,
        "frac_dy_neg": frac(DY_NEG),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--radius", type=int, default=2_000_000)
    args = ap.parse_args()

    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn

    lo, hi, _ = puzzle_band(135)
    mlo, mhi = N - hi, N - lo

    lines = [
        "P135 dual-anchor scan: +d only (y leg) + N-d mirror report (-y leg)",
        "",
        f"H={H:.12f}  frac(H)={FRAC_H:.6f}",
        f"y:  log2(sqrt)={LSY:.6f}  frac={FRAC_LSY:.6f}  Dy={DY:.6f}  frac(Dy)={FRAC_DY:.6f}",
        f"-y: log2(sqrt)={LSY_NEG:.6f}  frac={FRAC_LSY_NEG:.6f}  Dy={DY_NEG:.6f}  frac(Dy)={frac(DY_NEG):.6f}",
        f"identity frac(H)-frac(lsy)={FRAC_H - FRAC_LSY:.6f}",
        f"+d band [{lo}, {hi})   mirror [{mlo}, {mhi}]",
        f"EC scan radius +/- {args.radius:,} on +d only",
        "",
    ]

    total = 0
    hits: list[tuple[str, int]] = []
    t0 = time.perf_counter()

    for name, bf_target in ANCHORS:
        d0 = max(lo, min(hi - 1, d_at_bf(bf_target)))
        bf = band_frac(d0)
        hit, n = scan_plus_d(d0, args.radius, lo, hi, px, py)
        total += n
        mir = mirror_report(d0, mlo, mhi)

        lines.extend([
            f"=== {name} (target bf={bf_target:.6f}) ===",
            "  +d (y leg — EC tested):",
            f"    d center tail ...{str(d0)[-12:]}",
            f"    band_frac={bf:.6f}",
            f"    frac(lsy)-frac(log2 d)={FRAC_LSY - frac(math.log2(d0)):.6f}  (target {FRAC_DY:.6f} for hinge)",
            f"    EC +/-{args.radius:,} tested={n:,}  hit={hit if hit else 'none'}",
            "  N-d (mirror — -y leg, NOT EC for P135):",
            f"    N-d tail ...{str(mir['N_minus_d'])[-12:]}",
            f"    in mirror band: {mir['in_mirror_band']}",
            f"    frac(log2(N-d))={mir['log2_frac']:.6f}  mirror_log_off={mir['mirror_log_off']:.6f}",
            f"    frac(lsy)-frac(log2 N-d)={mir['frac_lsy_minus_log2']:.6f}  (= frac(lsy) if log2 frac~0)",
            f"    frac(lsy_neg)-frac(log2 N-d)={mir['frac_lsy_neg_minus_log2']:.6f}  (= frac(lsy_neg) if log2 frac~0)",
            f"    predicts -y hinge Dy={mir['dy_neg']:.6f}  frac(Dy)={mir['frac_dy_neg']:.6f}",
            "",
        ])
        if hit:
            hits.append((name, hit))

    lines.extend([
        "=== read ===",
        "  hinge_frac +d: y-side 0.006 residue at bf~0.333",
        "  upper_half +d: y-side upper lane at bf~0.585 (frac diff -0.245)",
        "  N-d mirror: log2 frac~0, picks up full y frac (0.340) or -y frac (0.631)",
        "  P135 pubkey needs +d with even y — N-d gives (x,-y), wrong address",
        "",
        f"total +d EC keys: {total:,}",
        f"elapsed: {time.perf_counter()-t0:.1f}s",
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
