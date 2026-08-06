#!/usr/bin/env python3
"""Verify email 'arrest' formulas against solved puzzles and P135."""

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
from puzzle_keys_53125 import parse_53125

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
PN = P - N

getcontext().prec = 120


def sqrt_dec(v: int) -> Decimal:
    return Decimal(v).sqrt()


def frac_dec(d: Decimal) -> Decimal:
    return d - d.to_integral_value(rounding="ROUND_FLOOR")


def log2_dec(d: Decimal) -> Decimal:
    return (d.ln() / Decimal(2).ln())


def fsqrt_log2(v: int) -> float:
    if v <= 0:
        return float("nan")
    return float(log2_dec(sqrt_dec(v))) - math.floor(float(log2_dec(sqrt_dec(v))))


def arrest_v1(k: int = 71) -> int:
    """x = floor(frac(sqrt(N)) * sqrt(p-N) * 2^k)"""
    sn = sqrt_dec(N)
    spn = sqrt_dec(PN)
    tail = frac_dec(sn)
    val = tail * spn * (Decimal(2) ** k)
    return int(val.to_integral_value(rounding="ROUND_FLOOR"))


def arrest_v2(k: int = 71) -> int:
    """x = floor((p-N) * frac(sqrt(N)) * 2^k) mod N — email boxed form."""
    sn = sqrt_dec(N)
    tail = frac_dec(sn)
    val = Decimal(PN) * tail * (Decimal(2) ** k)
    return int(val.to_integral_value(rounding="ROUND_FLOOR")) % N


def arrest_v3(k: int = 71) -> int:
    """x = floor(frac(sqrt(N)) * 2^k) * sqrt(p-N) approx — alternate grouping."""
    sn = sqrt_dec(N)
    tail = frac_dec(sn)
    spn = sqrt_dec(PN)
    val = tail * (Decimal(2) ** k) * spn
    return int(val.to_integral_value(rounding="ROUND_FLOOR"))


def arrest_v4(py: int, k_half: float = 0.172851) -> int:
    """x ~ sqrt(y) * 2^{H/2} / tail — structural ratio (not integer formula)."""
    sy = sqrt_dec(py)
    spn = sqrt_dec(PN)
    tail = frac_dec(sqrt_dec(N))
    # scale to 135-bit band via 2^134
    val = sy * (Decimal(2) ** Decimal(str(k_half))) / tail
    return int(val.to_integral_value(rounding="ROUND_FLOOR"))


def geom_mean_arrest() -> int:
    """Integer part of geometric mean of gap and coordinate tail (email sec 4)."""
    spn = float(sqrt_dec(PN))
    tail = float(frac_dec(sqrt_dec(N)))
    # sqrt(gap * tail) scaled — email says x_int log2 ~ 96.3
    gm = math.sqrt(PN * tail)  # wrong dims; try sqrt(PN) * sqrt(tail)
    return int(gm * (2 ** 71))


def main() -> int:
    sn = sqrt_dec(N)
    sp = sqrt_dec(P)
    spn = sqrt_dec(PN)
    h = float(log2_dec(Decimal(PN)))
    fh = h - math.floor(h)
    fh2 = (h / 2) - math.floor(h / 2)

    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn
    lo, hi, _ = puzzle_band(135)

    lines = [
        "ARREST FORMULA VERIFICATION",
        "",
        "=== constants ===",
        f"floor(sqrt(N)) = {int(sn.to_integral_value(rounding='ROUND_FLOOR'))}",
        f"floor(sqrt(p)) = {int(sp.to_integral_value(rounding='ROUND_FLOOR'))}",
        f"frac(sqrt(N)) decimal tail = {frac_dec(sn)}",
        f"sqrt(p-N) = {spn}",
        f"log2(p-N) = {h:.10f}  {{H}} = {fh:.6f}  {{H/2}} = {fh2:.6f}",
        f"log2 sqrt(Np/(p-N)) = {float(log2_dec((sqrt_dec(N)*sqrt_dec(P))/spn)):.6f}",
        f"P135 band [{lo}, {hi})",
        "",
        "=== email formulas at k=71 ===",
    ]

    for name, fn in [
        ("v1 frac(sqrtN)*sqrt(pN)*2^k", lambda: arrest_v1(71)),
        ("v2 (pN)*frac(sqrtN)*2^k mod N", lambda: arrest_v2(71)),
        ("v3 frac(sqrtN)*2^k*sqrt(pN)", lambda: arrest_v3(71)),
        ("v4 sqrt(y)*2^H2/tail", lambda: arrest_v4(py)),
        ("geom_mean*2^71", geom_mean_arrest),
    ]:
        d = fn()
        in_band = lo <= d < hi
        hit = verify_candidate(d, px, py) if in_band else False
        lines.append(
            f"  {name}: d...{str(d)[-12:]}  bits={d.bit_length()}  "
            f"in_band={in_band}  EC={hit}"
        )

    # k sweep around 71
    lines.extend(["", "=== k sweep v1 (frac*sqrt(pN)*2^k) ==="])
    for k in range(65, 78):
        d = arrest_v1(k)
        ib = lo <= d < hi
        ec = verify_candidate(d, px, py) if ib else False
        if ib or k in (69, 70, 71, 72, 73):
            lines.append(f"  k={k:2d} bits={d.bit_length():3d} in_band={ib} EC={ec} tail...{str(d)[-10:]}")

    # calibration on solved puzzles: what k would v1 need?
    lines.extend(["", "=== solved calibration: k such that v1(d) ~ true d ==="])
    keys = parse_53125()
    errs = []
    for n in [27, 64, 70, 100, 115, 130]:
        if n not in keys:
            continue
        d_true = keys[n].d
        # binary search k
        best_k, best_err = None, None
        for k in range(0, 80):
            pred = arrest_v1(k)
            err = abs(pred - d_true)
            if best_err is None or err < best_err:
                best_err = err
                best_k = k
        rel = best_err / d_true if d_true else 0
        errs.append(rel)
        lines.append(f"  P{n:3d} best_k={best_k} rel_err={rel:.4f}  d_true_bits={d_true.bit_length()}")

    lines.append(f"  mean rel err across sample: {sum(errs)/len(errs):.4f}")

    # 10^29 / 2^96.3 check
    lines.extend([
        "",
        "=== 10^29 / log bridge ===",
        f"10^29 bits ~ {Decimal(10)**29:.2E}  log2 ~ {math.log2(10**29):.3f}",
        f"191.827/2 = {191.827/2:.3f}  (email half-log claim)",
    ])

    text = "\n".join(lines)
    out = ROOT / "ARCHIVE" / "arrest_formula_verify.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
