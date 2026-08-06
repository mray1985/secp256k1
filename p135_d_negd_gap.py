#!/usr/bin/env python3
"""How EC coordinates react as scalar gap |d - (-d)| = |2d - N| shrinks."""
from __future__ import annotations

import hashlib

from ecdsa import SECP256k1, SigningKey

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
HALF = N // 2


def pt(d: int) -> tuple[int, int] | None:
    d %= N
    if d == 0:
        return None
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1, hashfunc=hashlib.sha256)
    raw = sk.get_verifying_key().to_string()
    return int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")


def gap(d: int) -> int:
    return abs(2 * (d % N) - N)


def main() -> None:
    print("=" * 80)
    print("SCALAR: d and -d = N-d")
    print("=" * 80)
    print("Integer width between them: |2d - N|")
    print("  near d=0 or d=N:   gap ~ N  (maximum width)")
    print("  near d=N/2:        gap ~ 0  (minimum width)")
    print()
    print("CURVE: always (-d)G = -(dG)")
    print("  => same x-coordinate")
    print("  => y' = p - y  (opposite sign mod p)")
    print("  This is INDEPENDENT of how close d and -d are as integers.")
    print()

    print("=" * 80)
    print("SAMPLES: gap shrinks, x does NOT systematically shrink")
    print("=" * 80)
    print(f"{'d_bits':>7} {'gap_bits':>9} {'x_bits':>7} {'x_same':>7} {'y+y=0':>7} {'y_parity':>10}")
    samples = [
        1, 2, 100, 1 << 10, 1 << 32, 1 << 64, 1 << 128, 1 << 134, 1 << 135, 1 << 200,
        HALF, HALF + 1, HALF - 1, HALF + 2, HALF - 2,
        HALF + (1 << 10), HALF - (1 << 10),
        HALF + (1 << 32), HALF - (1 << 32),
        HALF + (1 << 64), HALF - (1 << 64),
        HALF + (1 << 128), HALF - (1 << 128),
    ]
    seen: set[int] = set()
    for d in samples:
        d %= N
        if d in seen or d == 0:
            continue
        seen.add(d)
        P, Q = pt(d), pt(N - d)
        assert P and Q
        g = gap(d)
        print(
            f"{d.bit_length():7d} {g.bit_length():9d} {P[0].bit_length():7d} "
            f"{str(P[0] == Q[0]):>7} {str((P[1] + Q[1]) % p == 0):>7} "
            f"{P[1] % 2}/{Q[1] % 2:>8}"
        )

    print()
    print("=" * 80)
    print("AS d -> N/2: gap -> 0, but x stays ~256-bit random-looking")
    print("=" * 80)
    for off in [1 << 200, 1 << 100, 1 << 50, 1 << 20, 1 << 10, 1, 0]:
        d = (HALF + off) % N
        P = pt(d)
        assert P
        g = gap(d)
        print(f"  off_bits={off.bit_length() if off else 0:3d}  gap_bits={g.bit_length():3d}  x_bits={P[0].bit_length():3d}")

    print()
    print("=" * 80)
    print("YOUR PUBLIC COORDINATES as residues mod N (not scalars d)")
    print("=" * 80)
    Px3 = 9210836494447108270027136741376870869791784014198948301625976867708124077590
    rx2 = 90653255469745952335985143920649543885181555095025199315947044135806663628368
    for name, v in [("Px3", Px3), ("rx2", rx2)]:
        g = abs(2 * v - N)
        print(f"  {name}: bits={v.bit_length()}  |2v-N| bits={g.bit_length()}  fraction={g / N:.6f}")
        print(f"         (this is residue gap, NOT private-key gap)")

    print()
    print("=" * 80)
    print("WHAT ACTUALLY CHANGES WHEN |d-(-d)| SHRINKS")
    print("=" * 80)
    print("  CHANGES:  integer distance between the two scalars")
    print("  CHANGES:  which half of [1,N) they sit in (both near N/2)")
    print("  FIXED:    point relation (-d)G = -dG  (same x, flip y)")
    print("  FIXED:    x-coordinate size ~ full field (no collapse toward 0)")
    print("  FIXED:    134-power: still exactly {d, -d} as residue pair IF")
    print("            you were powering the SCALAR - but your screenshots")
    print("            power COORDINATES (Px, rx), not d")
    print()
    print("BOTTOM LINE:")
    print("  Closer d and -d (near N/2) does NOT make their EC x-coords")
    print("  closer together - they already SHARE the same x always.")
    print("  Only y flips. Width of the scalar pair is independent of")
    print("  the geometric x.")


if __name__ == "__main__":
    main()
