#!/usr/bin/env python3
"""Arrest formula using Delta_y instead of frac(sqrt N)."""

from __future__ import annotations

import math
import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from bucket_slice_search import verify_candidate  # noqa: E402
from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from p135_common import G, point_add, scalar_mult  # noqa: E402
from puzzle_keys_53125 import parse_53125

getcontext().prec = 120

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
PN = P - N
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800


def log2d(v: int | Decimal) -> float:
    return float((Decimal(v).ln() / Decimal(2).ln()))


def arrest(mult: float, k: int, spn: Decimal) -> int:
    return int((Decimal(str(mult)) * spn * (Decimal(2) ** k)).to_integral_value(rounding="ROUND_FLOOR"))


def scan(d0: int, radius: int, lo: int, hi: int, px: int, py: int) -> int | None:
    d0 = max(lo, min(hi - 1, d0))
    ds, de = max(lo, d0 - radius), min(hi - 1, d0 + radius)
    pt = scalar_mult(ds, G)
    for i, d in enumerate(range(ds, de + 1)):
        if pt and pt[0] == px and pt[1] == py and verify_candidate(d, px, py):
            return d
        if i + 1 <= de - ds:
            pt = point_add(pt, G)
    return None


def main() -> int:
    spn = Decimal(PN).sqrt()
    sn = Decimal(N).sqrt()
    frac_sn = float(sn - sn.to_integral_value(rounding="ROUND_FLOOR"))

    h = log2d(PN)
    fh = h - math.floor(h)
    ly = log2d(Decimal(PY).sqrt())
    fsy = ly - math.floor(ly)
    dy = h - ly
    fdy = dy - math.floor(dy)

    lo, hi, _ = puzzle_band(135)
    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn

    forms = [
        ("{Delta_y}", fdy),
        ("Delta_y full", dy),
        ("|E_y|", abs(fsy - fh)),
    ]

    lines = [
        "ARREST WITH Delta_y (not frac sqrt N)",
        "",
        f"H = {h:.10f}   {{H}} = {fh:.6f}",
        f"log2 sqrt(y) = {ly:.10f}   {{sqrt y}} = {fsy:.6f}",
        f"Delta_y = {dy:.10f}   {{Delta_y}} = {fdy:.6f}",
        f"frac(sqrt N) = {frac_sn:.6f}  (old multiplier)",
        f"P135 band [{lo}, {hi})",
        "",
        "Formula: d = floor( mult * sqrt(p-N) * 2^k )",
        "",
    ]

    for fname, mult in forms:
        lines.append(f"=== {fname} = {mult:.10f} ===")
        in_band = []
        for k in range(60, 95):
            d = arrest(mult, k, spn)
            ib = lo <= d < hi
            if ib:
                ec = verify_candidate(d, px, py)
                pos = 100 * (d - lo) / (hi - lo)
                in_band.append((k, d, pos, ec))
                lines.append(
                    f"  k={k:2d} pos={pos:5.2f}% bits={d.bit_length()} EC={ec} ...{str(d)[-12:]}"
                )
        if not in_band:
            lines.append("  (no k in 60..94 lands in band)")
        lines.append("")

    # compare email k=71/72 with old vs new
    lines.append("=== head-to-head at k=71,72 ===")
    for k in (71, 72):
        d_old = arrest(frac_sn, k, spn)
        d_new = arrest(fdy, k, spn)
        lines.append(f"k={k}:")
        lines.append(f"  frac(sqrtN): bits={d_old.bit_length()} in={lo<=d_old<hi} ...{str(d_old)[-12:]}")
        lines.append(f"  {{Delta_y}}:  bits={d_new.bit_length()} in={lo<=d_new<hi} ...{str(d_new)[-12:]}")
    lines.append("")

    # find k that puts {Delta_y} in band for P135
    best_k = next(k for k in range(90) if lo <= arrest(fdy, k, spn) < hi)
    d_star = arrest(fdy, best_k, spn)
    lines.append(f"P135 in-band: k={best_k}  d...{str(d_star)[-12:]}  pos={100*(d_star-lo)/(hi-lo):.2f}%")

    hit = scan(d_star, 100_000, lo, hi, px, py)
    lines.append(f"EC scan +/-100k: {hit or 'none'}")

    # solved calibration
    lines.append("")
    lines.append("=== solved calibration (best k, {{Delta_y}}) ===")
    keys = parse_53125()
    for n in [64, 70, 100, 115, 130]:
        dt = keys[n].d
        lo_n = 1 << (n - 1)
        hi_n = 1 << n
        best = None
        for k in range(95):
            d = arrest(fdy, k, spn)
            if lo_n <= d < hi_n:
                err = abs(d - dt)
                if best is None or err < best[0]:
                    best = (err, k, d)
        if best:
            lines.append(f"P{n} best_k={best[1]} rel_err={best[0]/dt:.4f} bits={best[2].bit_length()}")

    text = "\n".join(lines)
    out = ROOT / "ARCHIVE" / "arrest_delta_y.txt"
    out.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
