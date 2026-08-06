#!/usr/bin/env python3
"""
P135: Px <-> r log-space combinations -> d candidates -> EC check.

Combines (3 log2(Px) + log2 7) and (3 log2(r) + log2 7) mod log2(N/p)
via difference, ratio, and cross-maps to private key band.
"""

from __future__ import annotations

import math
import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    DEFAULT_PX,
    N,
    P135_R_TRUE_X,
    p,
    primitive_cube_root_of_unity,
    pubkey_from_scalar,
    puzzle_band,
)
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "p135_log_px_r_combo_probe.txt"

PX = DEFAULT_PX[2]
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
PUZZLE = 135

getcontext().prec = 100


def d_log2(x: int) -> Decimal:
    return Decimal(x).ln() / Decimal(2).ln()


def log_mod(core: Decimal, mod: Decimal) -> Decimal:
    q = core // mod
    r = core - q * mod
    return r if r >= 0 else r + mod


def frac_part(x: Decimal) -> Decimal:
    return x - int(x) if x >= 0 else x - int(x) + 1


def cbrt_r(r: int) -> list[tuple[str, int]]:
    u0 = pow(r, (N + 2) // 9, N)
    w = primitive_cube_root_of_unity(N)
    if not w:
        return [("u0", u0)]
    return [(f"u{j}", u) for j, u in enumerate([u0, (u0 * w) % N, (u0 * w * w) % N])]


def ec_hit(d: int) -> bool:
    try:
        gx, gy = pubkey_from_scalar(d)
        return gx == PX and gy == PY
    except Exception:
        return False


def band_ok(d: int, lo: int, hi: int) -> bool:
    return lo <= d < hi


def emit_d(
    hits: list[str],
    lines: list[str],
    tag: str,
    d: int,
    lo: int,
    hi: int,
) -> None:
    if not band_ok(d, lo, hi):
        return
    ok = ec_hit(d)
    lines.append(f"  {tag}: d_bits={d.bit_length()} band=ok ec={ok} tail...{str(d)[-6:]}")
    if ok:
        hits.append(f"{tag} d={d}")


def maps_from_frac(
    hits: list[str],
    lines: list[str],
    tag: str,
    f: float,
    lo: int,
    hi: int,
) -> None:
    f = f % 1.0
    if f < 0:
        f += 1.0
    emit_d(hits, lines, f"{tag} lo*(1+f)", int(lo * (1 + f)), lo, hi)
    emit_d(hits, lines, f"{tag} lo+ f*lo", int(lo + f * lo), lo, hi)
    emit_d(hits, lines, f"{tag} lo*2^f", int(lo * (2**f)), lo, hi)
    emit_d(hits, lines, f"{tag} hi-2^f*lo", int(hi - lo * (2**f)), lo, hi)


def maps_from_log_residue(
    hits: list[str],
    lines: list[str],
    tag: str,
    v: float,
    ln: float,
    lo: int,
    hi: int,
    n: int,
) -> None:
    maps_from_frac(hits, lines, f"{tag} frac=v/LN", v / ln, lo, hi)
    maps_from_frac(hits, lines, f"{tag} frac=v mod1", v % 1.0, lo, hi)
    off = v - (n - 1)
    if 0 <= off < 2:
        emit_d(hits, lines, f"{tag} lo*2^off", int(lo * (2**off)), lo, hi)


def arrest_from_lam(lam: int, r: int, s: int, z: int) -> int | None:
    d = (s - r * lam) % N
    if d == 0:
        return None
    return (lam * z * pow(d, -1, N)) % N


def main() -> int:
    rsz = PUZZLE_RSZ[135]
    r_sig, s, z = rsz.r, rsz.s, rsz.z
    lo, hi, _ = puzzle_band(PUZZLE)
    ln = float(d_log2(N))
    lp = float(d_log2(p))
    l7 = float(d_log2(7))

    hits: list[str] = []
    lines = [
        "P135 LOG Px <-> r COMBINATION PROBE",
        f"Px tail ...{str(PX)[-3:]}  r tail ...{str(r_sig)[-3:]}",
        f"band [{lo}, {hi})",
        "",
    ]

    core_px = float(3 * d_log2(PX) + Decimal(str(l7)))
    core_r = float(3 * d_log2(r_sig) + Decimal(str(l7)))
    v_px_n = float(log_mod(Decimal(str(core_px)), Decimal(str(ln))))
    v_r_n = float(log_mod(Decimal(str(core_r)), Decimal(str(ln))))

    lines.append("=== cores ===")
    lines.append(f"  core(Px) mod log2(N) = {v_px_n:.10f}  frac={v_px_n/ln:.10f}")
    lines.append(f"  core(r) mod log2(N) = {v_r_n:.10f}  frac={v_r_n/ln:.10f}")
    lines.append("")

    # --- difference & ratio ---
    lines.append("=== A. difference (Px - r) in log space ===")
    delta = v_px_n - v_r_n
    delta_mod = delta % ln
    lines.append(f"  vPx - vr = {delta:.10f}  mod log2(N) = {delta_mod:.10f}  frac={delta_mod/ln:.10f}")
    maps_from_log_residue(hits, lines, "delta", delta_mod, ln, lo, hi, PUZZLE)
    maps_from_log_residue(hits, lines, "delta_raw", delta, ln, lo, hi, PUZZLE)

    lines.append("")
    lines.append("=== B. ratio log2(Px/r) combinations ===")
    log_ratio = math.log2(PX / r_sig)
    combos = [
        ("log2(Px/r)", log_ratio),
        ("3*log2(Px/r)", 3 * log_ratio),
        ("3*log2(Px/r)+log2(7)", 3 * log_ratio + l7),
        ("3*log2(Px/r) mod 1", (3 * log_ratio) % 1.0),
        ("(3*log2(Px/r)+log2(7)) mod 1", (3 * log_ratio + l7) % 1.0),
        ("log2(Px^3*7/r^3)", math.log2(PX**3 * 7 / r_sig**3)),
    ]
    for name, val in combos:
        vm = val % ln if abs(val) > ln else val
        lines.append(f"  {name} = {val:.10f}")
        maps_from_frac(hits, lines, name, val, lo, hi)
        if abs(val) > 1:
            maps_from_log_residue(hits, lines, name + "_modLN", vm % ln, ln, lo, hi, PUZZLE)

    lines.append("")
    lines.append("=== C. frac(Px) - frac(r) and product ===")
    f_px = v_px_n / ln
    f_r = v_r_n / ln
    f_diff = (f_px - f_r) % 1.0
    f_prod = (f_px * f_r) % 1.0
    f_sum = (f_px + f_r) % 1.0
    lines.append(f"  frac(Px)-frac(r) mod1 = {f_diff:.10f}")
    lines.append(f"  frac(Px)*frac(r) mod1 = {f_prod:.10f}")
    lines.append(f"  frac(Px)+frac(r) mod1 = {f_sum:.10f}")
    for name, f in [("f_diff", f_diff), ("f_prod", f_prod), ("f_sum", f_sum)]:
        maps_from_frac(hits, lines, name, f, lo, hi)

    lines.append("")
    lines.append("=== D. lambda from log combo -> arrest warrant ===")
    lam_candidates: list[tuple[str, int]] = []
    # integer lambda from field/scalar bridges already failed; try log-derived
    for name, val in [
        ("delta_mod_int", int(delta_mod)),
        ("delta_frac*lo", int(f_diff * lo)),
        ("core_diff_int", int(abs(core_px - core_r)) % N),
        ("Px/r mod N", (PX * pow(r_sig, -1, N)) % N),
        ("Px/r mod p lift", ((PX * pow(r_sig, -1, p)) % p) % N),
    ]:
        lam_candidates.append((name, val % N))

    for tag, u in cbrt_r(r_sig):
        lam_candidates.append((f"Px/{tag} N", (PX * pow(u, -1, N)) % N))

    # log-derived lambda: exp2((delta_mod/ln)*256) style
    lam_log = int(pow(2, int((delta_mod / ln) * 256)) % N)
    lam_candidates.append(("2^(256*frac(delta))", lam_log))

    for name, lam in lam_candidates:
        x = arrest_from_lam(lam, r_sig, s, z)
        if x is None:
            continue
        ok = ec_hit(x)
        ib = band_ok(x, lo, hi)
        if ok or ib:
            lines.append(f"  arrest {name}: x_bits={x.bit_length()} ec={ok} band={ib}")
        if ok:
            hits.append(f"arrest {name} x={x}")

    lines.append("")
    lines.append("=== E. cubic u branches vs Px difference ===")
    for tag, u in cbrt_r(r_sig):
        core_u = float(3 * d_log2(u) + Decimal(str(l7)))
        v_u = float(log_mod(Decimal(str(core_u)), Decimal(str(ln))))
        dlt = (v_px_n - v_u) % ln
        fd = ((v_px_n / ln) - (v_u / ln)) % 1.0
        lines.append(f"  {tag} vPx-vu mod LN = {dlt:.6f} frac_diff={fd:.6f}")
        maps_from_log_residue(hits, lines, f"Px-{tag}", dlt, ln, lo, hi, PUZZLE)
        maps_from_frac(hits, lines, f"fracPx-frac{tag}", fd, lo, hi)

    lines.append("")
    lines.append("=== F. solved P130 sanity (combo predicts d?) ===")
    from puzzle_keys_53125 import parse_53125  # noqa: E402

    pk = parse_53125().get(130)
    rsz130 = PUZZLE_RSZ.get(130)
    if pk and rsz130:
        px, d_true, r0 = pk.px, pk.d, rsz130.r
        lo130, hi130, _ = puzzle_band(130)
        cpx = float(3 * d_log2(px) + Decimal(str(l7)))
        cr = float(3 * d_log2(r0) + Decimal(str(l7)))
        vp = float(log_mod(Decimal(str(cpx)), Decimal(str(ln))))
        vr = float(log_mod(Decimal(str(cr)), Decimal(str(ln))))
        dm = (vp - vr) % ln
        fd = ((vp / ln) - (vr / ln)) % 1.0
        d_est = int(lo130 * (1 + fd))
        lines.append(f"  P130 frac_diff={fd:.6f} d_est bits={d_est.bit_length()} ec={ec_hit(d_est)} x==d {d_est==d_true}")

    lines.append("")
    lines.append("=== VERDICT ===")
    if hits:
        lines.append(f"  EC HITS: {len(hits)}")
        for h in hits:
            lines.append(f"    {h}")
    else:
        lines.append("  No EC hit from Px<->r log combinations.")

    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0 if hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
