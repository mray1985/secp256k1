#!/usr/bin/env python3
"""
P135 — three-bridge arrest: field, scalar, cubic (object not shadow).

Suspect 1: lambda_p = (Px * r^-1 mod p) mod N
Suspect 2: lambda_N = Px * r^-1 mod N
Suspect 3: u_i^3 == r mod N; lambda_i = Px * u_i^-1 mod N

For each: x = lambda * z * (s - r*lambda)^-1 mod N
Verdict: [x]G == P135 and x in [2^134, 2^135)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    DEFAULT_PX,
    N,
    p,
    primitive_cube_root_of_unity,
    pubkey_from_scalar,
    puzzle_band,
)
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "p135_three_bridge_arrest.txt"

PX = DEFAULT_PX[2]
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800


def cbrt_r_mod_n(r: int) -> list[int]:
    r %= N
    u0 = pow(r, (N + 2) // 9, N)
    w = primitive_cube_root_of_unity(N)
    if w is None:
        return [u0]
    return [u0, (u0 * w) % N, (u0 * w * w) % N]


def arrest(lam: int, r: int, s: int, z: int) -> tuple[int, int, int] | None:
    d = (s - r * lam) % N
    if d == 0:
        return None
    k = (z * pow(d, -1, N)) % N
    x = (lam * k) % N
    return d, k, x


def ec_hit(x: int) -> bool:
    gx, gy = pubkey_from_scalar(x)
    return gx == PX and gy == PY


from dataclasses import dataclass


@dataclass
class TrialResult:
    summary: str
    ec: bool
    band: bool


def trial_result(name: str, lam: int, r: int, s: int, z: int, lo: int, hi: int) -> TrialResult:
    res = arrest(lam, r, s, z)
    if res is None:
        return TrialResult(f"  {name}: D=0 (skip)", False, False)
    d, k, x = res
    ec = ec_hit(x)
    band = lo <= x < hi
    cuff = "CUFFED" if ec else "cleared"
    band_s = "IN_BAND" if band else "out"
    return TrialResult(
        f"  {name}: lam...{str(lam)[-5:]}  D_bits={d.bit_length()}  k_bits={k.bit_length()}  "
        f"x_bits={x.bit_length()}  {band_s}  ec={ec}  [{cuff}]",
        ec,
        band,
    )


def main() -> int:
    rsz = PUZZLE_RSZ[135]
    r, s, z = rsz.r, rsz.s, rsz.z
    lo, hi, _ = puzzle_band(135)

    lam_p = ((PX * pow(r, -1, p)) % p) % N
    lam_n = (PX * pow(r, -1, N)) % N

    lines = [
        "P135 THREE-BRIDGE ARREST",
        f"Px tail ...{str(PX)[-3:]}  r tail ...{str(r)[-3:]}",
        f"band [{lo}, {hi})",
        "",
        "=== SUSPECT 1: FIELD BRIDGE (mod p, then mod N) ===",
        f"  lambda_p = (Px * r^-1 mod p) mod N  tail ...{str(lam_p)[-5:]}",
    ]

    results = []
    results.append(trial_result("field bridge", lam_p, r, s, z, lo, hi))
    lines.append(results[-1].summary)

    lines += [
        "",
        "=== SUSPECT 2: SCALAR BRIDGE (mod N) ===",
        f"  lambda_N = Px * r^-1 mod N  tail ...{str(lam_n)[-5:]}",
        f"  lambda_p != lambda_N: {(lam_p != lam_n)}  delta tail ...{str((lam_n - lam_p) % N)[-5:]}",
    ]
    results.append(trial_result("scalar bridge", lam_n, r, s, z, lo, hi))
    lines.append(results[-1].summary)

    lines += ["", "=== SUSPECT 3: CUBIC BRIDGE (object u, not shadow r) ==="]
    for j, u in enumerate(cbrt_r_mod_n(r)):
        ok = pow(u, 3, N) == r
        lam_i = (PX * pow(u, -1, N)) % N
        lines.append(f"  u{j} tail ...{str(u)[-3:]}  u^3==r {ok}")
        lines.append(f"  lambda_{j} = Px * u{j}^-1 mod N  tail ...{str(lam_i)[-5:]}")
        results.append(trial_result(f"cubic u{j}", lam_i, r, s, z, lo, hi))
        lines.append(results[-1].summary)
        lines.append("")

    ec_any = any(r.ec for r in results)
    band_any = any(r.band for r in results)
    wed = "One suspect cuffed." if ec_any else "Three suspects. All cleared."
    lines += [
        "=== VERDICT ===",
        f"  EC hits (P135 pubkey): {sum(r.ec for r in results)}",
        f"  Band hits [2^134,2^135): {sum(r.band for r in results)}",
        f"  Any suspect cuffed: {ec_any}",
        "",
        f"Wednesday: Field bridge, scalar bridge, cubic bridge. {wed}",
    ]

    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0 if ec_any else 1


if __name__ == "__main__":
    raise SystemExit(main())
