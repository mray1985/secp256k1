#!/usr/bin/env python3
"""
P135 cubic-root lambda arrest warrant.

For each cubic branch u_i (u_i^3 ≡ r mod N, or Wolfram r^3 roots):
  lambda_i = Px * u_i^-1 mod N   (and field-lift variant)
  D_i = s - r*lambda_i mod N
  k_i = z * D_i^-1 mod N
  x_i = lambda_i * k_i mod N

Check band [2^134, 2^135) and x_i*G == P135.
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
    P135_R_TRUE_X,
    p,
    primitive_cube_root_of_unity,
    pubkey_from_scalar,
    puzzle_band,
)
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "p135_cubic_arrest_warrant_report.txt"

PX = DEFAULT_PX[2]
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800

# Wolfram screenshot 2026-06-26: cube roots of r_sig^3 mod N
WOLFRAM_R3_ROOTS = [
    4295241207732992648834070171909958737418321088245693014740872866482121928576,
    20843592559837250438751770916128405230237688095804012051917246139229375937393,
    90653255469745952335985143920649543885181555095025199315947044135806663628368,
]


def cube_roots_of_r(r: int) -> list[tuple[str, int]]:
    """Return labeled u branches: primary (N+2)/9, unity rotations, Wolfram r^3 roots."""
    out: list[tuple[str, int]] = []
    r %= N
    if pow(r, (N - 1) // 3, N) != 1:
        out.append(("non-residue", r))
        return out

    u0 = pow(r, (N + 2) // 9, N)
    if pow(u0, 3, N) == r:
        w = primitive_cube_root_of_unity(N)
        if w:
            for j, u in enumerate([u0, (u0 * w) % N, (u0 * w * w) % N]):
                out.append((f"cbrt_r_j{j}", u))
        else:
            out.append(("cbrt_r_j0", u0))
    else:
        out.append(("cbrt_r_fail", u0))

    for j, u in enumerate(WOLFRAM_R3_ROOTS):
        tag = "wolfram_r3_j%d" % j
        if pow(u, 3, N) == pow(r, 3, N):
            out.append((tag, u))

    # direct signature x as branch
    if P135_R_TRUE_X not in [u for _, u in out]:
        out.append(("r_sig_direct", P135_R_TRUE_X))

    return out


def lambda_candidates(u: int) -> list[tuple[str, int]]:
    lam_n = (PX * pow(u, -1, N)) % N
    lam_field = (PX * pow(u % p, -1, p)) % p
    lam_lift = lam_field % N
    return [
        ("Px/u mod N", lam_n),
        ("Px/u mod p lifted", lam_lift),
    ]


def arrest_x(lam: int, r: int, s: int, z: int) -> tuple[int | None, int | None, int | None]:
    d = (s - r * lam) % N
    if d == 0:
        return None, None, None
    k = (z * pow(d, -1, N)) % N
    x = (lam * k) % N
    return d, k, x


def ec_ok(x: int) -> bool:
    try:
        px, py = pubkey_from_scalar(x)
        return px == PX and py == PY
    except Exception:
        return False


def run_puzzle135() -> list[str]:
    rsz = PUZZLE_RSZ[135]
    r, s, z = rsz.r, rsz.s, rsz.z
    lo, hi, _ = puzzle_band(135)
    lines = [
        "P135 CUBIC ARREST WARRANT",
        "",
        f"Px tail ...{str(PX)[-3:]}",
        f"RSZ r tail ...{str(r)[-3:]}  r_true tail ...{str(P135_R_TRUE_X)[-3:]}  match={r == P135_R_TRUE_X}",
        f"N mod 9 = {N % 9}  (use (N+2)/9 root when N==7 mod 9)",
        f"band [{lo}, {hi})",
        "",
    ]

    branches = cube_roots_of_r(r)
    lines.append(f"u branches ({len(branches)}):")
    for tag, u in branches:
        ok_r = pow(u, 3, N) == r
        ok_r3 = pow(u, 3, N) == pow(r, 3, N)
        lines.append(
            f"  {tag:14s} u...{str(u)[-3:]}  u^3==r {ok_r}  u^3==r^3 {ok_r3}"
        )
    lines.append("")

    any_hit = False
    for tag, u in branches:
        lines.append(f"--- branch {tag} ---")
        for lname, lam in lambda_candidates(u):
            d, k, x = arrest_x(lam, r, s, z)
            if x is None:
                lines.append(f"  {lname}: D=0 skip")
                continue
            in_band = lo <= x < hi
            hit = ec_ok(x)
            any_hit = any_hit or hit
            lines.append(
                f"  {lname}: x bits={x.bit_length()} in_band={in_band} ec_hit={hit} "
                f"D bits={d.bit_length()} k bits={k.bit_length()}"
            )
            if in_band or hit:
                lines.append(f"    x = {x}")
                lines.append(f"    x hex = {format(x, 'x')}")
        lines.append("")

    # Control: standard ECDSA x = r^-1 (s*k - z) not applicable without k
    # Control: if lambda = Px/r mod N directly (old path)
    lam_old = (PX * pow(r, -1, N)) % N
    d, k, x = arrest_x(lam_old, r, s, z)
    lines.append("--- control: lambda = Px/r (no cube root) ---")
    if x is not None:
        lines.append(
            f"  x bits={x.bit_length()} in_band={lo <= x < hi} ec_hit={ec_ok(x)}"
        )
        lines.append(f"  x tail ...{str(x)[-6:]}")
    lines.append("")
    lines.append(f"ANY EC HIT: {any_hit}")
    return lines


def run_p130_control() -> list[str]:
    """P130 has known d in 53125 — reverse-check arrest formula."""
    from puzzle_keys_53125 import parse_53125

    keys = parse_53125()
    pk = keys.get(130)
    rsz = PUZZLE_RSZ.get(130)
    if not pk or not rsz or not pk.d:
        return ["P130 control: missing data", ""]

    d_known = pk.d
    px = pk.px
    r, s, z = rsz.r, rsz.s, rsz.z
    # implied lambda from x = lambda * z / (s - r*lambda) is messy; check forward:
    k = (pow(s, -1, N) * (z + r * d_known)) % N
    lam_implied = (d_known * pow(k, -1, N)) % N
    lam_geo = (px * pow(r, -1, N)) % N
    lines = [
        "P130 CONTROL (known d)",
        f"  d bits={d_known.bit_length()}",
        f"  k from ECDSA bits={k.bit_length()}",
        f"  implied lambda = d/k mod N tail ...{str(lam_implied)[-3:]}",
        f"  Px/r mod N tail ...{str(lam_geo)[-3:]}  match={lam_implied == lam_geo}",
        "",
    ]
    # arrest forward with lam_geo
    d2, k2, x2 = arrest_x(lam_geo, r, s, z)
    if x2 is not None:
        lines.append(
            f"  arrest with Px/r: x==d_known {x2 == d_known} ec={ec_ok(x2)}"
        )
    return lines


def main() -> int:
    lines = run_puzzle135() + run_p130_control()
    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
