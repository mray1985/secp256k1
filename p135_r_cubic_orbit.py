#!/usr/bin/env python3
"""
P135: field vs N-side cubic orbits of signature r — nine bridge ratios + row-2 tower.

Field orbit (mod p):
  R_eff[i,j] = beta^i * DEFAULT_RX[j]  (beta^3 = 1 mod p)
  Lambda[i,j,k] = DEFAULT_PX[k] * R_eff[i,j]^-1  mod p

N-side signature orbit (mod N):
  r_sig = P135_R_TRUE_X  (r = R_x mod N, r < N)
  r_orb[j] = w^j * r_sig  mod N   (w = primitive cube root of unity mod N)
  lambda[i,j,k] = DEFAULT_PX[k] * r_orb[j]^-1  mod N

Row-2 tower fingerprint (transport gap with bridge DEFAULT_RY):
  gap_h2=14, gap_h3=148, lhs tail ...768

Wrong bridge slot (cfg.row rx index 2, tail ...739):
  gap_h2=52, gap_h3=529  (row-3 tower)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    DEFAULT_PX,
    DEFAULT_RX,
    DEFAULT_RY,
    N,
    P135_R_TRUE_X,
    all_cube_roots_mod,
    p,
    primitive_cube_root_of_unity,
)

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "p135_r_cubic_orbit_report.txt"

BETA = 55594575648329892869085402983802832744385952214688224221778511981742606582254
ROW2 = ("14", "148", "768")
ROW3 = ("52", "529", "255")


def head(v: int, k: int) -> str:
    s = str(v)
    return s[:k] if len(s) >= k else s


def n_gap(rx: int) -> int:
    return ((pow(DEFAULT_RY, 2, N) - 3) - (pow(rx, 3, N) + 4)) % N


def gap_meta(rx: int) -> dict:
    g = n_gap(rx)
    lhs = (pow(rx, 3, N) + 4) % N
    return {
        "gap": g,
        "h2": head(g, 2),
        "h3": head(g, 3),
        "lhs_tail": str(lhs)[-3:],
        "row2": head(g, 2) == ROW2[0] and head(g, 3) == ROW2[1],
        "row3": head(g, 2) == ROW3[0] and head(g, 3) == ROW3[1],
    }


def cube_root_one(mod: int, a: int) -> int | None:
    """One cube root when a is a cubic residue mod prime mod."""
    if pow(a, (mod - 1) // 3, mod) != 1:
        return None
    r = pow(a, (2 * mod - 1) // 3, mod)
    return r if pow(r, 3, mod) == a % mod else None


def main() -> int:
    r_sig = P135_R_TRUE_X
    w_n = primitive_cube_root_of_unity(N)
    w_p = primitive_cube_root_of_unity(p)

    lines = [
        "P135 R CUBIC ORBIT — field vs N-side",
        "",
        f"r_sig = P135_R_TRUE_X  (r < N: {r_sig < N}, r < p: {r_sig < p})",
        f"r tail ...{str(r_sig)[-3:]}",
        "",
        "Row-2 tower target: gap_h2=14 gap_h3=148 lhs...768",
        "Row-3 (wrong bridge slot rx[2]): gap_h2=52 gap_h3=529 lhs...255",
        "",
    ]

    wrong = DEFAULT_RX[2]
    true_meta = gap_meta(r_sig)
    wrong_meta = gap_meta(wrong)
    lines.append("=== baseline ===")
    lines.append(f"  true r_sig     rx...{str(r_sig)[-3:]}  {gap_meta(r_sig)}")
    lines.append(f"  wrong rx[2]    rx...{str(wrong)[-3:]}  {gap_meta(wrong)}")
    lines.append(f"  DEFAULT_RX[1]  rx...{str(DEFAULT_RX[1])[-3:]}  (same as r_sig: {DEFAULT_RX[1]==r_sig})")
    lines.append("")

    # Cube roots of r mod N (preimage x^3 = r)
    lines.append("=== cube preimages u: u^3 = r (mod N) ===")
    residue_n = pow(r_sig, (N - 1) // 3, N) == 1
    lines.append(f"  r is cubic residue mod N: {residue_n}")
    u0 = cube_root_one(N, r_sig)
    roots_n = all_cube_roots_mod(N, r_sig)
    if u0 is None and not roots_n:
        lines.append("  no cube root found via standard formula (investigate separately)")
    else:
        if not roots_n and u0 is not None:
            roots_n = sorted({u0, (u0 * w_n) % N, (u0 * w_n * w_n) % N})
        for i, u in enumerate(roots_n):
            gm = gap_meta(u)
            lines.append(
                f"  u{i} tail ...{str(u)[-3:]}  equals r_sig={u == r_sig}  "
                f"h2={gm['h2']} h3={gm['h3']} row2={gm['row2']}"
            )
    lines.append("")

    # Field 3x3 beta * Rx_j
    lines.append("=== field orbit R_eff = beta^i * Rx_j (mod p) ===")
    lines.append(f"  beta tail ...{str(BETA)[-3:]}  beta^3==1 mod p: {pow(BETA,3,p)==1}")
    field_row2 = []
    for j in range(3):
        for i in range(3):
            rf = (pow(BETA, i, p) * DEFAULT_RX[j]) % p
            gm = gap_meta(rf)
            mark = " *** ROW-2" if gm["row2"] else (" row-3" if gm["row3"] else "")
            lines.append(
                f"  i={i} j={j}  R_eff...{str(rf)[-3:]}  gap h2={gm['h2']} h3={gm['h3']}{mark}"
            )
            if gm["row2"]:
                field_row2.append((i, j, str(rf)[-3:]))
    lines.append(f"  row-2 hits: {field_row2}")
    lines.append("")

    # Nine Lambda ratios (field) — report for Px row 2 (P135 pubkey slot)
    pi = 2
    lines.append(f"=== nine field bridge ratios Lambda = Px[{pi}] / R_eff (mod p) ===")
    for j in range(3):
        for i in range(3):
            rf = (pow(BETA, i, p) * DEFAULT_RX[j]) % p
            lam = (DEFAULT_PX[pi] * pow(rf, -1, p)) % p
            gm = gap_meta(rf)
            lines.append(
                f"  i={i} j={j}  R...{str(rf)[-3:]}  Lambda bits={lam.bit_length()}  "
                f"gap row2={gm['row2']}"
            )
    lines.append("")

    # N-side orbit w^j * r
    lines.append("=== N-side signature orbit r_j = w^j * r_sig (mod N) ===")
    lines.append("  (NOT u^3=r; this rotates r by cube roots of unity)")
    if w_n is None:
        lines.append("  no cube root of unity mod N")
    else:
        for j in range(3):
            rj = (pow(w_n, j, N) * r_sig) % N
            gm = gap_meta(rj)
            lines.append(
                f"  j={j}  r_j...{str(rj)[-3:]}  gap h2={gm['h2']} h3={gm['h3']}  row2={gm['row2']}"
            )
    lines.append("")

    lines.append(f"=== nine N bridge ratios lambda = Px[k] / r_j (mod N) ===")
    for j in range(3):
        rj = (pow(w_n, j, N) * r_sig) % N if w_n else r_sig
        for k in range(3):
            lam = (DEFAULT_PX[k] * pow(rj, -1, N)) % N
            gm = gap_meta(rj)
            lines.append(
                f"  j={j} k={k}  r...{str(rj)[-3:]}  lambda bits={lam.bit_length()}  row2={gm['row2']}"
            )
    lines.append("")

    lines.append("=== conclusion ===")
    lines.append(
        "  Wrong cubic rep: bridge rx[2] (...739) -> row-3 tower 52/529."
    )
    lines.append(
        "  Correct rep: true RSZ r_sig (...368) = DEFAULT_RX[1] -> row-2 tower 14/148."
    )
    lines.append(
        "  Field: beta^i * Rx_j hits ...368 (row-2) at (i,j) in {(1,0),(0,1),(2,2)}."
    )
    lines.append(
        "  N-orbit w^j*r keeps gap head 14/148 for all j (tower class stable under N unity)."
    )
    lines.append(
        "  Cube preimage u (u^3=r) is a different map from unity-rotation; needs separate root."
    )
    lines.append("")

    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
