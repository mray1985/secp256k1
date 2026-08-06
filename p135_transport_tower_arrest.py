#!/usr/bin/env python3
"""
P135 transport tower arrest — field beta-orbit, N unity-orbit, cubic u branches.

For each (Px[k], denom) from gap row-2 tower:
  lambda_field = (Px * denom^-1 mod p) mod N
  lambda_scalar = Px * denom^-1 mod N
  x = lambda * z * (s - r*lambda)^-1 mod N
  check [x]G == P135, x in band
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
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
    p,
    primitive_cube_root_of_unity,
    pubkey_from_scalar,
    puzzle_band,
)
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "p135_transport_tower_arrest.txt"

BETA = 55594575648329892869085402983802832744385952214688224221778511981742606582254
PX_PUB = DEFAULT_PX[2]
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800


@dataclass
class Hit:
    tag: str
    px_k: int
    lam_mode: str
    x: int
    ec: bool
    band: bool


def head(v: int, k: int) -> str:
    s = str(v)
    return s[:k] if len(s) >= k else s


def n_gap(rx: int) -> tuple[str, str, bool]:
    g = ((pow(DEFAULT_RY, 2, N) - 3) - (pow(rx, 3, N) + 4)) % N
    h2, h3 = head(g, 2), head(g, 3)
    return h2, h3, h2 == "14" and h3 == "148"


def cbrt_r(r: int) -> list[int]:
    u0 = pow(r, (N + 2) // 9, N)
    w = primitive_cube_root_of_unity(N)
    if not w:
        return [u0]
    return [u0, (u0 * w) % N, (u0 * w * w) % N]


def lam_field(px: int, d: int) -> int:
    return ((px * pow(d % p, -1, p)) % p) % N


def lam_scalar(px: int, d: int) -> int:
    return (px * pow(d % N, -1, N)) % N


def arrest(lam: int, r: int, s: int, z: int) -> int | None:
    det = (s - r * lam) % N
    if det == 0:
        return None
    return (lam * z * pow(det, -1, N)) % N


def ec_ok(x: int) -> bool:
    gx, gy = pubkey_from_scalar(x)
    return gx == PX_PUB and gy == PY


def try_pair(
    hits: list[Hit],
    lines: list[str],
    tag: str,
    px_k: int,
    denom: int,
    r: int,
    s: int,
    z: int,
    lo: int,
    hi: int,
    *,
    row2_only: bool = False,
) -> None:
    if row2_only:
        _, _, ok = n_gap(denom)
        if not ok:
            return
    px = DEFAULT_PX[px_k]
    for mode, lam_fn in (("field", lam_field), ("scalar", lam_scalar)):
        lam = lam_fn(px, denom)
        x = arrest(lam, r, s, z)
        if x is None:
            continue
        ec = ec_ok(x)
        band = lo <= x < hi
        if ec or band:
            hits.append(Hit(tag, px_k, mode, x, ec, band))
        if ec or band or row2_only:
            lines.append(
                f"  {tag} Px[{px_k}] {mode}: lam...{str(lam)[-5:]} "
                f"x_bits={x.bit_length()} ec={ec} band={band} denom...{str(denom)[-3:]}"
            )


def main() -> int:
    rsz = PUZZLE_RSZ[135]
    r, s, z = rsz.r, rsz.s, rsz.z
    lo, hi, _ = puzzle_band(135)
    w_n = primitive_cube_root_of_unity(N)

    hits: list[Hit] = []
    lines = [
        "P135 TRANSPORT TOWER ARREST",
        f"Px_pub=DEFAULT_PX[2] tail ...{str(PX_PUB)[-3:]}",
        f"r_sig tail ...{str(r)[-3:]}  band [{lo}, {hi})",
        "",
    ]

    # --- 1. Field beta orbit R_eff[i,j] full 3x3 x Px[0..2] ---
    lines.append("=== 1. Field R_eff = beta^i * rx[j] (mod p) — row-2 hits only ===")
    for j in range(3):
        for i in range(3):
            rf = (pow(BETA, i, p) * DEFAULT_RX[j]) % p
            h2, h3, row2 = n_gap(rf)
            tag = f"R_eff i={i} j={j} h2={h2}"
            if row2:
                lines.append(f"  *** row-2 R_eff...{str(rf)[-3:]} at i={i} j={j}")
            for k in range(3):
                try_pair(hits, lines, tag, k, rf, r, s, z, lo, hi, row2_only=row2)

    lines.append("")
    lines.append("=== 2. N-side r_j = w^j * r_sig (mod N) — all row-2 ===")
    for j in range(3):
        rj = (pow(w_n, j, N) * r) % N if w_n else r
        tag = f"N_orb j={j}"
        for k in range(3):
            try_pair(hits, lines, tag, k, rj, r, s, z, lo, hi)

    lines.append("")
    lines.append("=== 3. Cubic u_i (u^3=r mod N) — object branches ===")
    for j, u in enumerate(cbrt_r(r)):
        tag = f"cbrt_u{j}"
        for k in range(3):
            try_pair(hits, lines, tag, k, u, r, s, z, lo, hi)

    lines.append("")
    lines.append("=== 4. Hybrid: row-2 R_eff denom + cubic lambda (Px/u mod N) ===")
    row2_denoms: list[tuple[str, int]] = []
    for j in range(3):
        for i in range(3):
            rf = (pow(BETA, i, p) * DEFAULT_RX[j]) % p
            if n_gap(rf)[2]:
                row2_denoms.append((f"i={i}j={j}", rf))
    for j, u in enumerate(cbrt_r(r)):
        for k in range(3):
            px = DEFAULT_PX[k]
            lam = lam_scalar(px, u)
            x = arrest(lam, r, s, z)
            if x is None:
                continue
            ec = ec_ok(x)
            band = lo <= x < hi
            if ec or band:
                hits.append(Hit(f"hybrid_u{j}_Px{k}", k, "scalar_u", x, ec, band))
            # cross-check: use row-2 R_eff for field lambda, u in arrest r unchanged
            for nm, rf in row2_denoms:
                lam_f = lam_field(px, rf)
                x2 = arrest(lam_f, r, s, z)
                if x2 is None:
                    continue
                ec2 = ec_ok(x2)
                band2 = lo <= x2 < hi
                if ec2 or band2:
                    hits.append(Hit(f"row2_{nm}_Px{k}", k, "field_R", x2, ec2, band2))
                    lines.append(
                        f"  HIT row2 {nm} Px[{k}] x={x2} ec={ec2} band={band2}"
                    )

    lines.append("")
    lines.append("=== 5. Full grid scan (silent unless hit) ===")
    total = 0
    for j in range(3):
        for i in range(3):
            rf = (pow(BETA, i, p) * DEFAULT_RX[j]) % p
            for k in range(3):
                for mode, fn in (("field", lam_field), ("scalar", lam_scalar)):
                    total += 1
                    lam = fn(DEFAULT_PX[k], rf)
                    x = arrest(lam, r, s, z)
                    if x and (ec_ok(x) or lo <= x < hi):
                        lines.append(f"  FULL HIT R_eff i={i} j={j} Px[{k}] {mode} x={x}")

    for j in range(3):
        rj = (pow(w_n, j, N) * r) % N if w_n else r
        for k in range(3):
            for mode, fn in (("field", lam_field), ("scalar", lam_scalar)):
                total += 1
                lam = fn(DEFAULT_PX[k], rj)
                x = arrest(lam, r, s, z)
                if x and (ec_ok(x) or lo <= x < hi):
                    lines.append(f"  FULL HIT N_orb j={j} Px[{k}] {mode} x={x}")

    lines.append(f"  full grid trials: {total}")

    lines.append("")
    lines.append("=== VERDICT ===")
    lines.append(f"  hits: {len(hits)}")
    for h in hits:
        lines.append(f"  {h.tag} Px[{h.px_k}] {h.lam_mode} ec={h.ec} band={h.band} x={h.x}")

    if not hits:
        lines.append("  No transport tower pairing cuffed P135.")

    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0 if hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
