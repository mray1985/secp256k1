#!/usr/bin/env python3
"""
Flip P115 calibration onto surrounding puzzles — measure d proximity.

Transforms:
  same_frac      — P115 band fraction applied to neighbor band
  complement_frac— 1 - frac_115 on neighbor band
  mirror_msb     — bit-reflect P115 offset within band onto neighbor
  flip_decimal   — reverse decimal digits of P115 d, rescale to band
  schedule_p115_gp— k0 + P115_D * dk on neighbor RSZ -> d (P115 d as geom_pred)
  schedule_flip_gp— k0 + (band_top - P115_D) * dk on neighbor
  hinge_offset   — same_frac + HINGE offset
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    N,
    P115_D,
    P115_K,
    P115_R_TRUE_Y,
    p,
    pubkey_from_scalar,
    puzzle_band,
    y_roots,
)
from hashkeys_rsz import PUZZLE_RSZ, resolve_r_true_from_rsz  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

PIVOT_I99 = 198.95
PN = p - N
H2_FRAC = (math.log2(PN) / 2) - math.floor(math.log2(PN) / 2)
HINGE = int(2 ** (H2_FRAC * 134))

REPORT = ROOT / "ARCHIVE" / "p115_flip_surround.txt"
NEIGHBORS = list(range(100, 131, 5))


@dataclass
class FlipHit:
    target: int
    method: str
    d_est: int
    d_true: int
    abs_delta: int
    band_pct_err: float
    ec_hit: bool


def band_frac(d: int, n: int) -> float:
    lo, hi, _ = puzzle_band(n)
    return (d - lo) / (hi - lo)


def d_from_frac(frac: float, n: int) -> int:
    lo, hi, _ = puzzle_band(n)
    return lo + int(frac * (hi - lo - 1))


def mirror_offset_in_band(d_src: int, n_src: int, n_dst: int) -> int:
    lo_s, hi_s, top_s = puzzle_band(n_src)
    lo_d, hi_d, _ = puzzle_band(n_dst)
    off = d_src - lo_s
    width_s = hi_s - lo_s
    width_d = hi_d - lo_d
    # reflect offset about band midpoint
    off_mirror = width_s - 1 - off
    return lo_d + int(off_mirror * width_d / width_s)


def flip_decimal_rescale(d_src: int, n_dst: int) -> int:
    s = str(d_src)[::-1]
    lo, hi, _ = puzzle_band(n_dst)
    # map reversed decimal magnitude into band
    raw = int(s[: min(len(s), n_dst + 10)] or "0")
    return lo + (raw % (hi - lo))


def d_from_k(r: int, s: int, z: int, k: int) -> int:
    return (pow(r, -1, N) * (s * k - z)) % N


def ec_verify(d: int, px: int, py: int) -> bool:
    try:
        x, y = pubkey_from_scalar(d)
        return x == px and y == py
    except Exception:
        return False


def pivot_k_from_ry(ry: int, n: int) -> int:
    lsry = math.log2(ry) / 2.0
    lk = 2.0 * (PIVOT_I99 - lsry) - (256 - n)
    return int(2 ** max(0, lk))


def flip_candidates(n_dst: int, frac115: float, keys: dict) -> list[tuple[str, int]]:
    lo115, hi115, top115 = puzzle_band(115)
    lo_d, hi_d, top_d = puzzle_band(n_dst)
    out: list[tuple[str, int]] = []

    out.append(("same_frac", d_from_frac(frac115, n_dst)))
    out.append(("complement_frac", d_from_frac(1.0 - frac115, n_dst)))
    out.append(("mirror_msb", mirror_offset_in_band(P115_D, 115, n_dst)))
    out.append(("flip_decimal", flip_decimal_rescale(P115_D, n_dst)))
    out.append(("hinge+same_frac", d_from_frac(frac115, n_dst) + HINGE))
    out.append(("hinge-same_frac", d_from_frac(frac115, n_dst) - HINGE))

    # P115 complement height
    comp115 = top115 - P115_D
    out.append(("height_complement", lo_d + int((comp115 - lo115) * (hi_d - lo_d) / (hi115 - lo115))))

    rsz = PUZZLE_RSZ.get(n_dst)
    if rsz:
        k0 = (rsz.z * pow(rsz.s, -1, N)) % N
        dk = (rsz.r * pow(rsz.s, -1, N)) % N
        out.append(("schedule_p115_gp", d_from_k(rsz.r, rsz.s, rsz.z, (k0 + P115_D * dk) % N)))
        flip_gp = (top115 - P115_D) % N
        out.append(("schedule_flip_gp", d_from_k(rsz.r, rsz.s, rsz.z, (k0 + flip_gp * dk) % N)))

        # pivot k from neighbor R_y -> d
        rpt = resolve_r_true_from_rsz(n_dst)
        ry = rpt[1] if rpt else P115_R_TRUE_Y
        k_piv = pivot_k_from_ry(ry, n_dst)
        out.append(("pivot_ry_k", d_from_k(rsz.r, rsz.s, rsz.z, k_piv)))

        # flip: use P115 ry on neighbor sig
        k_piv115ry = pivot_k_from_ry(P115_R_TRUE_Y, n_dst)
        out.append(("pivot_P115_ry", d_from_k(rsz.r, rsz.s, rsz.z, k_piv115ry)))

    # linear delta from P115
    if n_dst != 115:
        delta_n = n_dst - 115
        out.append(("d115+2^delta", P115_D + (1 << abs(delta_n)) * (1 if delta_n > 0 else -1)))
        out.append(("d115*(1+delta/115)", int(P115_D * (1 + delta_n / 115))))

    return out


def main() -> int:
    keys = parse_53125()
    frac115 = band_frac(P115_D, 115)

    lines = [
        "P115 FLIP -> SURROUNDING PUZZLE d PROXIMITY",
        f"P115 d bits={P115_D.bit_length()} band_frac={frac115:.4f} ({100*frac115:.2f}%)",
        f"P115 d = {P115_D}",
        "",
        "Known neighbors:",
    ]
    for n in NEIGHBORS:
        if n in keys and keys[n].d:
            lines.append(f"  P{n} frac={band_frac(keys[n].d, n):.4f} d...{str(keys[n].d)[-12:]}")

    all_hits: list[FlipHit] = []

    for n in NEIGHBORS:
        if n == 115 or n not in keys or not keys[n].d:
            continue
        d_true = keys[n].d
        lo, hi, _ = puzzle_band(n)
        comp = PUZZLE_RSZ[n].pub_compressed
        px = int(comp[2:], 16)
        yp, yn = y_roots(px)
        py = yp if comp.startswith("02") else yn

        lines.append("")
        lines.append(f"=== P{n} (true frac={band_frac(d_true, n):.4f}) ===")

        best: FlipHit | None = None
        for method, d_est in flip_candidates(n, frac115, keys):
            d_est = d_est % N
            if not (lo <= d_est < hi):
                # still record if close
                pass
            delta = abs(d_est - d_true)
            pct = 100 * delta / (hi - lo)
            hit = ec_verify(d_est, px, py)
            row = FlipHit(n, method, d_est, d_true, delta, pct, hit)
            all_hits.append(row)
            if best is None or delta < best.abs_delta:
                best = row

        if best:
            lines.append(
                f"  BEST {best.method}: delta={best.abs_delta:.3e} band_err={best.band_pct_err:.4f}% "
                f"in_band={lo <= best.d_est < hi} ec={best.ec_hit}"
            )
            lines.append(f"    est ...{str(best.d_est)[-14:]}")
            lines.append(f"    tru ...{str(d_true)[-14:]}")

        # top 3 for this puzzle
        local = sorted([h for h in all_hits if h.target == n], key=lambda h: h.abs_delta)[:3]
        for h in local:
            lines.append(
                f"  {h.method:22s} delta_bits={h.abs_delta.bit_length():3d} "
                f"band_err={h.band_pct_err:8.4f}% ec={h.ec_hit}"
            )

    # Global best non-self
    lines.append("")
    lines.append("=== GLOBAL CLOSEST (any neighbor) ===")
    ext = [h for h in all_hits if h.target != 115]
    ext.sort(key=lambda h: h.abs_delta)
    for h in ext[:12]:
        lines.append(
            f"  P{h.target} {h.method:22s} delta={h.abs_delta:.3e} ({h.band_pct_err:.4f}% of band) ec={h.ec_hit}"
        )

    # Does any flip land on P135 if we include it?
    if 135 in PUZZLE_RSZ:
        lines.append("")
        lines.append("=== P135 (unsolved) flip estimates ===")
        for method, d_est in flip_candidates(135, frac115, keys):
            lo, hi, _ = puzzle_band(135)
            px = int(PUZZLE_RSZ[135].pub_compressed[2:], 16)
            yp, yn = y_roots(px)
            py = yp if PUZZLE_RSZ[135].pub_compressed.startswith("02") else yn
            d_est = d_est % N
            in_band = lo <= d_est < hi
            ec = ec_verify(d_est, px, py)
            if in_band or ec:
                lines.append(
                    f"  {method:22s} in_band={in_band} ec={ec} d...{str(d_est)[-12:]}"
                )

    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
