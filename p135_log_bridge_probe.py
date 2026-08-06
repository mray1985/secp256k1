#!/usr/bin/env python3
"""
High-precision log-bridge probe for P135:

  core(x) = 3*log2(x) + log2(7)
  vN = core mod log2(N)
  vP = core mod log2(p)

Sweep x in {Px[k], rx[j], r_sig, u_i, R_eff row-2}.
Derive d candidates from normalized fraction; EC-check P135.
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
    DEFAULT_RX,
    N,
    P135_R_TRUE_X,
    p,
    primitive_cube_root_of_unity,
    pubkey_from_scalar,
    puzzle_band,
)
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "p135_log_bridge_probe.txt"

BETA = 55594575648329892869085402983802832744385952214688224221778511981742606582254
PX_TARGET = DEFAULT_PX[2]
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
PUZZLE = 135

getcontext().prec = 100


def d_log2(x: int) -> Decimal:
    return Decimal(x).ln() / Decimal(2).ln()


def log_mod(core: Decimal, mod: Decimal) -> Decimal:
    if core < 0:
        core = core % mod
    q = core // mod
    r = core - q * mod
    if r < 0:
        r += mod
    return r


def cbrt_r(r: int) -> list[tuple[str, int]]:
    u0 = pow(r, (N + 2) // 9, N)
    w = primitive_cube_root_of_unity(N)
    if not w:
        return [("u0", u0)]
    return [(f"u{j}", u) for j, u in enumerate([u0, (u0 * w) % N, (u0 * w * w) % N])]


def ec_hit(d: int) -> bool:
    try:
        gx, gy = pubkey_from_scalar(d)
        return gx == PX_TARGET and gy == PY
    except Exception:
        return False


def d_candidates(v: Decimal, ln: Decimal, lo: int, hi: int, n: int) -> list[tuple[str, int]]:
    """Several maps from log residue to scalar d in band."""
    out: list[tuple[str, int]] = []
    frac = v / ln
    frac1 = frac - int(frac)  # fractional part
    if frac1 < 0:
        frac1 += 1

    maps = [
        ("lo*(1+frac1)", int(lo * (1 + float(frac1)))),
        ("lo+frac1*lo", int(lo + float(frac1) * lo)),
        ("lo*2^frac1", int(lo * (2 ** float(frac1)))),
        ("int(lo*frac)", int(lo * float(frac))),
    ]
    # bit-offset: v - (n-1) as fractional exponent above LO
    v_f = float(v)
    off = v_f - (n - 1)
    if 0 <= off < 1:
        maps.append(("lo*2^off", int(lo * (2**off))))

    seen: set[int] = set()
    for name, d in maps:
        if d in seen:
            continue
        seen.add(d)
        if lo <= d < hi:
            out.append((name, d))
    return out


def collect_x_values() -> list[tuple[str, int]]:
    vals: list[tuple[str, int]] = []
    for k, px in enumerate(DEFAULT_PX):
        vals.append((f"Px[{k}]", px))
    for j, rx in enumerate(DEFAULT_RX):
        vals.append((f"rx[{j}]", rx))
    vals.append(("r_sig", P135_R_TRUE_X))
    for tag, u in cbrt_r(P135_R_TRUE_X):
        vals.append((tag, u))
    for i, j in [(1, 0), (0, 1), (2, 2)]:
        rf = (pow(BETA, i, p) * DEFAULT_RX[j]) % p
        vals.append((f"R_eff i={i}j={j}", rf))
    rsz = PUZZLE_RSZ[135]
    vals.append(("r_RSZ", rsz.r))
    return vals


def main() -> int:
    ln = d_log2(N)
    lp = d_log2(p)
    log2_7 = d_log2(7)
    delta = lp - ln

    lo, hi, _ = puzzle_band(PUZZLE)
    lines = [
        "P135 LOG BRIDGE PROBE (high precision)",
        "",
        f"log2(N) = {ln}",
        f"log2(p) = {lp}",
        f"log2(p) - log2(N) = {delta}",
        f"log2(7) = {log2_7}",
        "",
    ]

    hits: list[str] = []
    lines.append("=== per witness x ===")
    lines.append(
        f"{'label':16s}  {'tail':>5s}  {'vN':>14s}  {'vP':>14s}  {'dN-dP':>12s}  {'fracN':>10s}"
    )

    for label, x in collect_x_values():
        if x <= 0:
            continue
        core = 3 * d_log2(x) + log2_7
        vN = log_mod(core, ln)
        vP = log_mod(core, lp)
        d_diff = vP - vN
        fracN = vN / ln
        frac1 = fracN - int(fracN)
        lines.append(
            f"{label:16s}  ...{str(x)[-3:]:>5s}  {float(vN):14.8f}  {float(vP):14.8f}  "
            f"{float(d_diff):12.6e}  {float(frac1):10.8f}"
        )

        for mod_name, v, lbase in (("N", vN, ln), ("P", vP, lp)):
            for map_name, d in d_candidates(v, lbase, lo, hi, PUZZLE):
                ok = ec_hit(d)
                row = f"  -> d via {mod_name}/{map_name}: bits={d.bit_length()} ec={ok}"
                lines.append(row)
                if ok:
                    hits.append(f"{label} {mod_name} {map_name} d={d}")

    lines.append("")
    lines.append("=== solved puzzle correlation (Px vs log2(d)) ===")
    keys = parse_53125()
    err_n: list[float] = []
    err_p: list[float] = []
    err_split: list[float] = []
    for n, pk in sorted(keys.items()):
        if pk.d <= 0 or n < 10:
            continue
        lo_n, _, _ = puzzle_band(n)
        if not (lo_n <= pk.d < puzzle_band(n)[1]):
            continue
        core = 3 * d_log2(pk.px) + log2_7
        vN = log_mod(core, ln)
        vP = log_mod(core, lp)
        target = float(d_log2(pk.d))
        # compare mod residue to log2(d) mod log2(N)
        tN = float(log_mod(Decimal(str(target)), ln))
        tP = float(log_mod(Decimal(str(target)), lp))
        err_n.append(abs(float(vN) - tN))
        err_p.append(abs(float(vP) - tP))
        err_split.append(abs(float(vN) - tP))

    lines.append(f"  puzzles: {len(err_n)}")
    lines.append(f"  mean |vN - log2(d) mod log2(N)|: {sum(err_n)/len(err_n):.6f}")
    lines.append(f"  mean |vP - log2(d) mod log2(p)|: {sum(err_p)/len(err_p):.6f}")
    lines.append(f"  mean |vN - log2(d) mod log2(p)| (cross): {sum(err_split)/len(err_split):.6f}")

    # rx instead of Px on solved
    lines.append("")
    lines.append("=== same on r from RSZ where available ===")
    rsz_err = []
    for n in sorted(PUZZLE_RSZ.keys()):
        if n > 130:
            break
        pk = keys.get(n)
        rsz = PUZZLE_RSZ[n]
        if not pk or not pk.d:
            continue
        core = 3 * d_log2(rsz.r) + log2_7
        vN = float(log_mod(core, ln))
        tN = float(log_mod(d_log2(pk.d), ln))
        rsz_err.append(abs(vN - tN))
    if rsz_err:
        lines.append(f"  RSZ r puzzles: {len(rsz_err)} mean err vs log2(d) mod log2(N): {sum(rsz_err)/len(rsz_err):.6f}")

    lines.append("")
    lines.append("=== VERDICT ===")
    if hits:
        lines.append(f"  EC HITS: {len(hits)}")
        for h in hits:
            lines.append(f"    {h}")
    else:
        lines.append("  No EC hit from log-bridge d candidates on P135.")

    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0 if hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
