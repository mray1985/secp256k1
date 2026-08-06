#!/usr/bin/env python3
"""
Fold from pubkey P toward floor (LO) and height (TOP) — NOT band midpoint.

We know P = (Px, Py). Three hinge projections of P, four fold directions
each (direct, height-mirror u, toward floor, toward top). BSGS on each anchor.

Band:
  LO    = 2^(n-1)           floor
  TOP   = 2^n - 1           height (ceiling)
  u     = d - LO
  u'    = (LO - 1) - u      height-mirror (d + C = TOP, not mid-mirror)

Fold magnitude from P: f_u = int({Delta_y} * LO) using live Py.
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from p135_common import G, N, P, load_target, save_hit, scalar_mult  # noqa: E402
from puzzle135_bucket_bsgs.ec_bsgs import bsgs_pubkey_range  # noqa: E402
from puzzle_keys_53125 import parse_53125

PN = P - N
REPORT = ROOT / "ARCHIVE" / "p135_fold_from_P.txt"


def frac(x: float) -> float:
    return x - math.floor(x)


def fsqrt_log2(v: int) -> float:
    getcontext().prec = 80
    v = int(v) % P
    ln = float(Decimal(v).sqrt().ln() / Decimal(2).ln())
    return ln - math.floor(ln)


def hinge_from_P(px: int, py: int) -> dict[str, float]:
    getcontext().prec = 80
    h = float(Decimal(PN).ln() / Decimal(2).ln())
    fh = frac(h)
    fx = fsqrt_log2(px)
    fy = fsqrt_log2(py)
    dy = h - 2 * fy  # log2 sqrt y = 2*fsqrt in half-log... wait

    # log2(sqrt(y)) = log2(y)/2
    ly = float((Decimal(py).sqrt().ln() / Decimal(2).ln()))
    dy_full = h - ly
    fdy = frac(dy_full)
    return {
        "H": h,
        "{H}": fh,
        "{sqrt_x}": fx,
        "{sqrt_y}": fy,
        "Delta_y": dy_full,
        "{Delta_y}": fdy,
        "E_x": fx - fh / 2,  # vs {H/2} shelf — approximate
        "E_y": fy - fh,
    }


def bf_from_fsqrt(f: float) -> float:
    return frac(2 * f)


def d_from_bf(n: int, bf: float, lo: int) -> int:
    d = int(round(2 ** ((n - 1) + bf)))
    return max(lo, d)


@dataclass
class FoldAnchor:
    name: str
    d: int
    proj: str
    direction: str


def fold_candidates_from_P(
    px: int,
    py: int,
    n: int,
    lo: int,
    top: int,
    hi: int,
) -> list[FoldAnchor]:
    """Three P-projections x four floor/height directions (ref LO/TOP, not mid)."""
    h = hinge_from_P(px, py)
    fold_bf = h["{Delta_y}"]

    keys = parse_53125()
    pk27 = keys[27]
    gz_xd = fsqrt_log2(pk27.px) - fsqrt_log2(pk27.d)
    gz_yd = fsqrt_log2(pk27.py) - fsqrt_log2(pk27.d)

    projections = {
        "P_x": bf_from_fsqrt(frac(fsqrt_log2(px) - gz_xd)),
        "P_y": bf_from_fsqrt(frac(fsqrt_log2(py) - gz_yd)),
        "P_Dy": bf_from_fsqrt(frac(fsqrt_log2(py) + h["{Delta_y}"])),
    }

    out: list[FoldAnchor] = []
    for proj, bf in projections.items():
        d0 = d_from_bf(n, bf, lo)
        u0 = d0 - lo
        u_mirror = (lo - 1) - u0
        folds = [
            ("direct", d0),
            ("height_mirror", lo + u_mirror),
            ("toward_floor", d_from_bf(n, frac(bf - fold_bf), lo)),
            ("toward_top", d_from_bf(n, frac(bf + fold_bf), lo)),
        ]
        for direction, d in folds:
            if lo <= d < hi:
                out.append(FoldAnchor(f"{proj}/{direction}", d, proj, direction))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Fold from pubkey P (floor/height, not mid)")
    ap.add_argument("--margin", type=int, default=5_000_000)
    ap.add_argument("--m", type=int, default=0)
    ap.add_argument("--list-only", action="store_true")
    args = ap.parse_args()

    px, py, _, _, _ = load_target()
    n = 135
    lo, hi, top = puzzle_band(n)
    h = hinge_from_P(px, py)
    anchors = fold_candidates_from_P(px, py, n, lo, top, hi)

    lines = [
        "FOLD FROM P — floor LO / height TOP (not band mid)",
        f"P x ...{str(px)[-12:]}  y ...{str(py)[-12:]}",
        f"LO (floor)=...{str(lo)[-8:]}  TOP (height)=...{str(top)[-8:]}",
        f"{{sqrt_x}}={h['{sqrt_x}']:.6f}  {{sqrt_y}}={h['{sqrt_y}']:.6f}  "
        f"{{Delta_y}}={h['{Delta_y}']:.6f}",
        f"fold_bf = {{Delta_y}} = {h['{Delta_y}']:.6f}  (band_frac shift toward LO/TOP)",
        f"anchors={len(anchors)}  BSGS margin=+/-{args.margin:,}",
        "",
    ]

    lines.append(f"target P known — BSGS: find d with d*G = P near each fold anchor")
    lines.append("")

    if args.list_only:
        for a in anchors:
            pos = 100 * (a.d - lo) / (hi - lo)
            lines.append(f"  {a.name:28s} d...{str(a.d)[-10:]}  pos={pos:.1f}%")
        text = "\n".join(lines)
        print(text)
        REPORT.write_text(text + "\n", encoding="utf-8")
        return 0

    m = args.m or None
    hit_d: int | None = None
    hit_name = ""
    t0 = time.perf_counter()

    for a in anchors:
        d_lo = max(lo, a.d - args.margin)
        d_hi = min(hi, a.d + args.margin + 1)
        lines.append(f"--- {a.name} d...{str(a.d)[-10:]} ---")
        print(f"BSGS {a.name} ...", flush=True)
        hit = bsgs_pubkey_range(px, py, d_lo, d_hi, m=m, progress=False)
        status = f"HIT d={hit}" if hit else "none"
        lines.append(f"  {status}")
        print(f"  {status}", flush=True)
        if hit:
            hit_d = hit
            hit_name = a.name
            break

    elapsed = time.perf_counter() - t0
    lines.extend(["", f"wall={elapsed:.1f}s  result={'SOLVED' if hit_d else 'not found'}"])
    print(f"\nwall={elapsed:.1f}s  result={'SOLVED' if hit_d else 'not found'}")

    if hit_d:
        save_hit(hit_d, source=f"p135_fold_from_P:{hit_name}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if hit_d else 1


if __name__ == "__main__":
    raise SystemExit(main())
