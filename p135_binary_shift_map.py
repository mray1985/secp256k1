#!/usr/bin/env python3
"""
Binary-shift view of Theorem B — decimal +1 hides bit structure.

For anchor d0, step d0 + 2^b and show how binary fields shift:
  d (band bits), floor((z+r*d)/s), pubkey x MSB nibbles.

Harvester scrolls +1 in d, but navigation needs bit-level shifts.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from p135_common import G, scalar_mult  # noqa: E402

REPORT = ROOT / "ARCHIVE" / "p135_binary_shift_map.txt"


def iq(z: int, r: int, s: int, d: int) -> int:
    return (z + r * d) // s


def bin_tail(n: int, width: int = 48) -> str:
    b = bin(n)[2:]
    return b[-width:].zfill(width) if len(b) >= width else b.zfill(width)


def nibble_prefix(x: int, n: int = 8) -> str:
    return "".join(f"{((x >> (4 * (63 - i))) & 0xF):x}" for i in range(n))


def d_anchor(s: int, z: int, r: int, n: int) -> int:
    return (s * (1 << n) - z) // r


def row(label: str, d: int, z: int, r: int, s: int, px: int) -> str:
    q = iq(z, r, s, d)
    pt = scalar_mult(d, G)
    x = pt[0] if pt else 0
    match = sum(1 for a, b in zip(nibble_prefix(x), nibble_prefix(px)) if a == b)
    return (
        f"{label:14s} d_dec={d}\n"
        f"  d_bin[134:]: {bin_tail(d, 40)}\n"
        f"  iq_dec={q}  iq_bin: {bin_tail(q, 40)}  iq_bits={q.bit_length()}\n"
        f"  x_pref=0x{nibble_prefix(x,8)}  target=0x{nibble_prefix(px,8)}  nib_match={match}\n"
    )


def bit_flip_scan(d0: int, lo: int, hi: int, z: int, r: int, s: int, px: int) -> list[str]:
    lines = ["=== bit-flip steps from d0 (d0 XOR 2^b) ==="]
    d0 = max(lo, min(hi - 1, d0))
    lines.append(row("d0", d0, z, r, s, px))
    best = (0, -1, 0)
    for b in range(0, 140):
        step = 1 << b
        for sign, tag in ((1, f"+2^{b}"), (-1, f"-2^{b}")):
            d = d0 + sign * step
            if not (lo <= d < hi):
                continue
            pt = scalar_mult(d, G)
            if not pt:
                continue
            x = pt[0]
            m = sum(1 for a, t in zip(nibble_prefix(x), nibble_prefix(px)) if a == t)
            if m > best[0]:
                best = (m, b, sign)
            if m >= 3 or b >= 130:
                lines.append(row(tag, d, z, r, s, px))
    lines.append(f"best nibble match from bit-step: {best[0]} nibbles @ 2^{best[1]} sign={best[2]}")
    return lines


def linear_vs_binary(d0: int, z: int, r: int, s: int, px: int, n_steps: int = 8) -> list[str]:
    """Show +1 decimal vs +1 bit-position shift effects on iq binary."""
    lines = ["", "=== +1 decimal vs single-bit carry (why decimal hides structure) ==="]
    d = d0
    lines.append(row("start", d, z, r, s, px))
    for i in range(1, n_steps + 1):
        d1 = d0 + i
        lines.append(row(f"d0+{i} dec", d1, z, r, s, px))
    # one carry at bit 134 boundary
    if d0.bit_length() >= 134:
        b = d0.bit_length() - 2
        d2 = d0 + (1 << b)
        lines.append(row(f"d0+2^{b} (bit carry)", d2, z, r, s, px))
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description="Binary shift map for P135 d search")
    ap.add_argument("--anchor-bits", type=int, default=135, help="n for d0=(s*2^n-z)//r")
    ap.add_argument("--steps", type=int, default=8, help="decimal +1 demo steps")
    args = ap.parse_args()

    rsz = PUZZLE_RSZ[135]
    r, s, z = int(rsz.r), int(rsz.s), int(rsz.z)
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    _ = yp if yp % 2 == 0 else yn
    lo, hi, _ = puzzle_band(135)

    d0 = d_anchor(s, z, r, args.anchor_bits)
    d0 = max(lo, min(hi - 1, d0))

    lines = [
        "P135 BINARY SHIFT MAP (decimal d, binary structure)",
        f"anchor n={args.anchor_bits}  d0={d0}",
        f"LO={lo}  HI={hi}",
        f"Px prefix 0x{nibble_prefix(px, 16)}",
        "",
    ]
    lines.extend(linear_vs_binary(d0, z, r, s, px, args.steps))
    lines.extend(bit_flip_scan(d0, lo, hi, z, r, s, px))

    text = "\n".join(lines)
    print(text)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
