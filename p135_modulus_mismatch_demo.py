#!/usr/bin/env python3
"""
P135 modulus mismatch demonstration — Field bridge (Lambda mod p) vs Scalar bridge (mod N).

Also cubic-root paths on r and on lambda_B.
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
    N,
    P135_R_TRUE_X,
    all_cube_roots_mod_p,
    p,
    primitive_cube_root_of_unity,
    pubkey_from_scalar,
    puzzle_band,
)
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402

PX_PUB = DEFAULT_PX[2]
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
LO, HI, _ = puzzle_band(135)


def lam_a(px: int, denom: int) -> int:
    """Field bridge: (Px * denom^-1 mod p) mod N."""
    return ((px * pow(denom % p, -1, p)) % p) % N


def lam_b(px: int, denom: int) -> int:
    """Scalar bridge: Px * denom^-1 mod N."""
    return (px * pow(denom % N, -1, N)) % N


def arrest(lam: int, r: int, s: int, z: int) -> tuple[int | None, int | None]:
    d = (s - r * lam) % N
    if d == 0:
        return None, None
    k = (z * pow(d, -1, N)) % N
    x = (lam * k) % N
    return k, x


def ec_hit(x: int) -> bool:
    try:
        gx, gy = pubkey_from_scalar(x)
        return gx == PX_PUB and gy == PY
    except Exception:
        return False


def cbrt_n(r: int) -> list[int]:
    r %= N
    if pow(r, (N - 1) // 3, N) != 1:
        return []
    u0 = pow(r, (N + 2) // 9, N)
    if pow(u0, 3, N) != r:
        return []
    w = primitive_cube_root_of_unity(N)
    if not w:
        return [u0]
    return [u0, (u0 * w) % N, (u0 * w * w) % N]


def cbrt_p_lift(x: int) -> list[int]:
    roots = all_cube_roots_mod_p(x % p)
    return [r % N for r in roots]


def row(label: str, lam: int, r: int, s: int, z: int) -> str:
    k, x = arrest(lam, r, s, z)
    if x is None:
        return f"  {label}: D=0"
    return (
        f"  {label}: lam_tail ...{str(lam)[-5:]}  k_bits={k.bit_length()}  "
        f"x_bits={x.bit_length()}  band={LO <= x < HI}  ec={ec_hit(x)}"
    )


def main() -> int:
    rsz = PUZZLE_RSZ[135]
    r, s, z = rsz.r, rsz.s, rsz.z
    lines = [
        "P135 MODULUS MISMATCH DEMONSTRATION",
        f"Px_pub tail ...{str(PX_PUB)[-3:]}  r_sig tail ...{str(r)[-3:]}",
        f"band [{LO}, {HI})",
        "",
        "=== 1. Field vs Scalar bridge (Px[2] / denom) ===",
    ]

    denoms = [
        ("r_sig", r),
        ("rx[0]", DEFAULT_RX[0]),
        ("rx[1]=r_true", DEFAULT_RX[1]),
        ("rx[2]", DEFAULT_RX[2]),
    ]
    for dname, denom in denoms:
        la, lb = lam_a(PX_PUB, denom), lam_b(PX_PUB, denom)
        same = la == lb
        lines.append(f"\n--- denom {dname} tail ...{str(denom)[-3:]}  lam_A==lam_B? {same} ---")
        lines.append(row("Candidate A (field)", la, r, s, z))
        lines.append(row("Candidate B (scalar)", lb, r, s, z))
        if not same:
            lines.append(f"    Delta (B-A) mod N tail ...{str((lb - la) % N)[-5:]}")

    lines.append("")
    lines.append("=== 2. Full 3x3 shelf grid (A vs B) ===")
    hits = 0
    for pi, px in enumerate(DEFAULT_PX):
        for ri, rx in enumerate(DEFAULT_RX):
            la, lb = lam_a(px, rx), lam_b(px, rx)
            _, xa = arrest(la, r, s, z)
            _, xb = arrest(lb, r, s, z)
            if xa and (ec_hit(xa) or LO <= xa < HI):
                hits += 1
                lines.append(f"  HIT A Px[{pi}]/rx[{ri}] x={xa}")
            if xb and (ec_hit(xb) or LO <= xb < HI):
                hits += 1
                lines.append(f"  HIT B Px[{pi}]/rx[{ri}] x={xb}")
    lines.append(f"  grid hits: {hits}")

    lines.append("")
    lines.append("=== 3. Cubic root of r — Path 2 (mod N) ===")
    for j, u in enumerate(cbrt_n(r)):
        lines.append(f"\n  u{j} tail ...{str(u)[-3:]}")
        lines.append(row("  A: Px/u field", lam_a(PX_PUB, u), r, s, z))
        lines.append(row("  B: Px/u scalar", lam_b(PX_PUB, u), r, s, z))

    lines.append("")
    lines.append("=== 4. Cubic root of r — Path 1 (mod p, lift mod N) ===")
    seen: set[int] = set()
    for j, u in enumerate(cbrt_p_lift(r)):
        if u in seen:
            continue
        seen.add(u)
        lines.append(f"\n  u_p{j} tail ...{str(u)[-3:]}  u^3==r(N)? {pow(u,3,N)==r}")
        lines.append(row("  A: Px/u field", lam_a(PX_PUB, u), r, s, z))
        lines.append(row("  B: Px/u scalar", lam_b(PX_PUB, u), r, s, z))

    lines.append("")
    lines.append("=== 5. Cubic root of lambda_B (scalar ratio Px/r_sig mod N) ===")
    lb0 = lam_b(PX_PUB, r)
    lines.append(f"  lambda_B tail ...{str(lb0)[-5:]}")
    for j, u in enumerate(cbrt_n(lb0)):
        lines.append(f"\n  cbrt(lam_B) u{j} tail ...{str(u)[-3:]}  u^3==lam_B? {pow(u,3,N)==lb0}")
        lines.append(row("  arrest w/ u as lambda", u, r, s, z))

    lines.append("")
    lines.append("=== 6. Solved control P130 (does A or B recover d?) ===")
    from puzzle_keys_53125 import parse_53125  # noqa: E402

    pk = parse_53125()[130]
    rsz130 = PUZZLE_RSZ[130]
    d, px = pk.d, pk.px
    r0, s0, z0 = rsz130.r, rsz130.s, rsz130.z
    k_true = (pow(s0, -1, N) * (z0 + r0 * d)) % N
    lam_true = (d * pow(k_true, -1, N)) % N
    la = lam_a(px, r0)
    lb = lam_b(px, r0)
    _, xa = arrest(la, r0, s0, z0)
    _, xb = arrest(lb, r0, s0, z0)
    lines.append(f"  true d/k tail ...{str(lam_true)[-3:]}")
    lines.append(f"  A matches d/k? {la == lam_true}  arrest x==d? {xa == d}")
    lines.append(f"  B matches d/k? {lb == lam_true}  arrest x==d? {xb == d}")

    text = "\n".join(lines)
    out = ROOT / "ARCHIVE" / "p135_modulus_mismatch_demo.txt"
    out.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
