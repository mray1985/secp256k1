#!/usr/bin/env python3
"""Dual-gate P160: complement d + k*G==R + d*G==P (rem-sorted, fast)."""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import N, pubkey_from_scalar, puzzle_band  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ, recover_r_point_from_sig  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "p160_dual_gate_complement_rsz.txt"

NP1 = N + 1
STEP_57 = 2**57
M_BASE = 2**96
D_LO, D_HI = 1 << 159, 1 << 160
lo, hi, _ = puzzle_band(160)

P160_PUB = (
    ROOT / "puzzle160_keyhunt_bsgs" / "P160_compressed.pub"
).read_text(encoding="ascii").strip().splitlines()[0].strip()
P160_X = int(P160_PUB[2:], 16)
P160_Y_EVEN = P160_PUB.startswith("02")

rsz = PUZZLE_RSZ[160]
R, S, Z = rsz.r, rsz.s, rsz.z
R_POINT = recover_r_point_from_sig(R)


def k_from_d(d: int) -> int:
    return (pow(S, -1, N) * (Z + R * d)) % N


def check_d_p160(d: int) -> bool:
    if not (D_LO <= d < D_HI):
        return False
    x, y = pubkey_from_scalar(d)
    return x == P160_X and (y % 2 == 0) == P160_Y_EVEN


def check_k_r(k: int) -> bool:
    if R_POINT is None:
        return False
    return pubkey_from_scalar(k) == R_POINT


def main() -> None:
    t0 = time.time()
    eps_max = 500_000
    partners: list[tuple[int, int, int, str]] = []  # rem, j, d, label

    for j in range(eps_max + 1):
        m = M_BASE + j * STEP_57
        if m >= 2**97:
            break
        q, rem = divmod(NP1, m)
        for label, d in (("q", q), ("q+1", q + 1)):
            if label == "q+1" and rem == 0:
                continue
            if D_LO <= d < D_HI:
                partners.append((rem, j, d, label))

    partners.sort(key=lambda x: x[0])
    lines = [
        "P160 dual-gate (rem-sorted EC)",
        f"in-band partners from eps 0..{eps_max}: {len(partners)}",
        f"EC-checking top {min(10000, len(partners))} by smallest rem",
        "",
    ]

    dual = k_only = d_only = 0
    hits: list[str] = []

    for rem, j, d, label in partners[:10_000]:
        k = k_from_d(d)
        ok_k = check_k_r(k)
        ok_d = check_d_p160(d)
        if ok_k and ok_d:
            dual += 1
            hits.append(f"HIT j={j} {label} rem={rem} d={d}")
        elif ok_k:
            k_only += 1
        elif ok_d:
            d_only += 1

    lines.append(f"dual: {dual}  k_only: {k_only}  d_only: {d_only}")
    lines.extend(hits or ["  (no dual hits in top 10k rem)"])

    rem, j, d, label = partners[0]
    k = k_from_d(d)
    lines.append("")
    lines.append(f"best rem j={j} rem={rem} bf={(d-lo)/(hi-lo):.4f}")
    lines.append(f"  k*G==R {check_k_r(k)}  d*G==P {check_d_p160(d)}")

    text = "\n".join(lines) + f"\n\nelapsed {time.time()-t0:.1f}s\n"
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
