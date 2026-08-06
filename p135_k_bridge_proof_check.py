#!/usr/bin/env python3
"""Falsify/verify the 135-bit k bridge proof against live P135 RSZ."""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    P115_K,
    P115_D,
    P115_R_TRUE_X,
    P135_R_TRUE_X,
    P135_R_TRUE_Y,
    puzzle_band,
)
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
PN = p - N


def log2(x: int | float) -> float:
    return math.log2(x)


def largest_prime_factor(n: int, limit: int = 10_000_000) -> tuple[int, int | None]:
    """Return (n, largest_prime_found) with trial division up to limit."""
    orig = n
    lp = 1
    x = n
    d = 2
    while d * d <= x and d <= limit:
        while x % d == 0:
            lp = d
            x //= d
        d += 1 if d == 2 else 2
    if x > 1 and x <= limit * limit:
        lp = max(lp, x)
    return orig, lp if lp > 1 else None


def factor_small(n: int) -> dict[int, int]:
    f: dict[int, int] = {}
    x = n
    for d in range(2, 100000):
        while x % d == 0:
            f[d] = f.get(d, 0) + 1
            x //= d
        if x == 1:
            break
    if x > 1:
        f[x] = f.get(x, 0) + 1
    return f


def main() -> int:
    rsz = PUZZLE_RSZ[135]
    r = int(rsz.r)
    s = int(rsz.s)
    z = int(rsz.z)
    rx = P135_R_TRUE_X
    ry_user = 49718016424073922119905047162783160486633985582059386347593464154527367200316
    ry_true = P135_R_TRUE_Y

    lo, hi, _ = puzzle_band(135)

    lines = ["P135 k-BRIDGE PROOF CHECK", ""]

    # --- geometric ---
    lines.append("=== 1. Geometric (199-bit pivot) ===")
    pivot = 198.95
    for name, ry in [("user_ry", ry_user), ("true_ry", ry_true)]:
        lry = log2(ry)
        lsry = lry / 2
        lsk = pivot - lsry
        lk = 2 * lsk
        lines.append(f"  {name}:")
        lines.append(f"    log2(ry)={lry:.4f}  log2(sqrt(ry))={lsry:.4f}")
        lines.append(f"    pivot {pivot} -> log2(sqrt(k))={lsk:.4f}  log2(k)={lk:.4f} bits")
        lines.append(f"    shift to 135: {lk:.2f} - 8 = {lk-8:.2f} bits")

    lines.append(f"  log2(sqrt(N*p/(p-N))) = {log2(math.sqrt(N*p/PN)):.4f}  (191.827 field ratio)")

    # --- signature linear structure ---
    lines.append("")
    lines.append("=== 2. Signature linear (mod N) ===")
    k0 = (z * pow(s, -1, N)) % N
    delta_k = (r * pow(s, -1, N)) % N
    lines.append(f"  k = k0 + d * delta_k  (mod N)")
    lines.append(f"  k0 bits={k0.bit_length()}  delta_k bits={delta_k.bit_length()}")
    lines.append(f"  r==rx? {r == rx}  (sig r vs kG x)")

    # If d were 135-bit, k magnitude in integers (not mod N)
    lines.append("")
    lines.append("=== 3. Integer magnitude (heuristic, NOT mod N) ===")
    d_guess = 4.35e40  # user's 135-bit k companion
    lines.append(f"  s bits={s.bit_length()}  rx bits={rx.bit_length()}")
    lines.append(f"  s*4.35e40 ~ {s * 4.35e40:.4e}")
    lines.append(f"  rx*d for d~7.4e39 ~ {rx * 7.4e39:.4e}")

    # --- prime factors (small only) ---
    lines.append("")
    lines.append("=== 4. Small prime factors (trial, partial) ===")
    for name, val in [("s", s), ("rx", rx), ("r", r), ("z", z)]:
        fac = factor_small(val)
        small = {k: v for k, v in fac.items() if k <= 1000}
        big = [k for k in fac if k > 1000]
        lines.append(f"  {name}: small={small}  large_cofactors={len(big)}")

    # largest factors via quick estimate
    lines.append("")
    lines.append("=== 5. Large prime claims (approximate) ===")
    # Remove small factors and report cofactor size
    def cofactor_bits(n: int) -> int:
        x = n
        for d in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]:
            while x % d == 0:
                x //= d
        return x.bit_length()

    sb = cofactor_bits(s)
    rxb = cofactor_bits(rx)
    lines.append(f"  s after small factor strip: ~2^{sb} cofactor")
    lines.append(f"  rx after small factor strip: ~2^{rxb} cofactor")
    lines.append(f"  ratio bits rx/s ~ 2^{rxb - sb}")

    # --- ratio test ---
    lines.append("")
    lines.append("=== 6. L_rx / L_s ratio test ===")
    ratio = rx / s
    lines.append(f"  rx/s = {ratio:.6e}  log2={log2(ratio):.4f}")
    lines.append(f"  claim 2^86.2 vs actual 2^{log2(ratio):.4f}")
    lines.append(f"  2^(86.2+8) * 2^40 = 2^134.2 claim vs rx/s * d needed")

    # --- known solved puzzle calibration ---
    lines.append("")
    lines.append("=== 7. Calibration P115 (known k, d) ===")
    r115 = DEFAULT_RX = None
    rsz115 = PUZZLE_RSZ[115]
    r115 = int(rsz115.r)
    s115 = int(rsz115.s)
    z115 = int(rsz115.z)
    k0_115 = (z115 * pow(s115, -1, N)) % N
    dk_115 = (r115 * pow(s115, -1, N)) % N
    k_rec = (k0_115 + P115_D * dk_115) % N
    lines.append(f"  P115 d bits={P115_D.bit_length()}  k bits={P115_K.bit_length()}")
    lines.append(f"  k0+ d*delta_k == k? {k_rec == P115_K % N}")
    lines.append(f"  rx/s log2 = {log2(P115_R_TRUE_X / s115):.4f}")

    # --- arrest formula from proof ---
    lines.append("")
    lines.append("=== 8. Boxed arrest formula (does NOT yield k or d) ===")
    # Round(L_rx/L_s * prod small) - use rx/s * product of small factors from s
    small_prod = 1
    for d, e in factor_small(s).items():
        if d <= 43:
            small_prod *= d**e
    arrest = int(ratio * small_prod)
    lines.append(f"  (rx/s)*small_factors(s) bits={arrest.bit_length()} in_135_band={lo <= arrest < hi}")
    lines.append(f"  != k (256-bit) != d")

    text = "\n".join(lines)
    out = ROOT / "ARCHIVE" / "p135_k_bridge_proof_check.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
