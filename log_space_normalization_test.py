#!/usr/bin/env python3
"""
Log-space normalization: bit-shift (256/135) vs curve-constant (256/(128+log2(7))).

Verify toy mod-255 arithmetic and test solved puzzle keys for invariants.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import puzzle_band  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "log_space_normalization_test.txt"

LOG2_7 = math.log2(7)
EXP_BIT = 256 / 135  # 128/256 + (256/7)/256
EXP_CURVE = 256 / (128 + LOG2_7)


def log_mod(x: float, mod: float) -> float:
    """Reduce x into [0, mod) in log-space."""
    if mod <= 0:
        raise ValueError("mod must be positive")
    r = x % mod
    return r if r >= 0 else r + mod


def main() -> int:
    lines = [
        "LOG-SPACE NORMALIZATION TEST",
        "",
        "=== Case 1: seven BITS ===",
        f"  256/128 + 256/7 = 256/135 = {256/135:.17f}",
        f"  puzzle-135 exponent (n/256 if n=135): {135/256:.17f}",
        "",
        "=== Case 2: curve constant 7 ===",
        f"  log2(7) = {LOG2_7:.17f}",
        f"  256/(128 + log2(7)) = {EXP_CURVE:.17f}",
        f"  delta (bit - curve) = {EXP_BIT - EXP_CURVE:.17f}",
        "",
        "=== Toy mod 255 (mixed units — invalid) ===",
    ]

    l254 = math.log2(254)
    l255 = math.log2(255)
    mixed = (254**3 + LOG2_7) % 255
    lines.append(f"  254^3 mod 255 = {254**3 % 255}")
    lines.append(f"  (254^3 + log2(7)) mod 255 = {mixed:.17f}  [mixed integer+log]")
    lines.append("")
    lines.append("=== Full log-space (consistent units) ===")
    full = log_mod(3 * l254 + LOG2_7, l255)
    via_product = log_mod(math.log2(254**3 * 7), l255)
    lines.append(f"  (3*log2(254) + log2(7)) mod log2(255) = {full:.17f}")
    lines.append(f"  log2(254^3 * 7) mod log2(255)           = {via_product:.17f}")
    lines.append(f"  (equivalent forms match: {abs(full - via_product) < 1e-9})")
    lines.append("")

    keys = parse_53125()
    solved = [(n, pk) for n, pk in sorted(keys.items()) if pk.d > 0]

    lines.append("=== Solved puzzles: band fraction vs normalizations ===")
    lines.append(
        "  frac = (d - LO) / LO   in_band_pos = log2(d) - (n-1)"
    )
    lines.append(
        f"  {'n':>4}  {'bits':>4}  {'frac':>12}  {'log2(d)-n+1':>12}  "
        f"{'|frac-exp_bit|':>14}  {'|frac-exp_curve|':>14}"
    )

    bit_res: list[tuple[int, float]] = []
    curve_res: list[tuple[int, float]] = []

    for n, pk in solved:
        if n < 5:
            continue
        d = pk.d
        lo, hi, _ = puzzle_band(n)
        if not (lo <= d < hi):
            continue
        frac = (d - lo) / lo
        log_pos = math.log2(d) - (n - 1)
        exp_bit_n = n / 256
        exp_curve_n = n / (128 + LOG2_7)
        db = abs(frac - exp_bit_n)
        dc = abs(frac - exp_curve_n)
        bit_res.append((n, db))
        curve_res.append((n, dc))
        if n in (115, 125, 130, 135) or n <= 20 or db < 0.05 or dc < 0.05:
            lines.append(
                f"  {n:4d}  {d.bit_length():4d}  {frac:12.8f}  {log_pos:12.8f}  "
                f"{db:14.8f}  {dc:14.8f}"
            )

    if bit_res:
        avg_b = sum(x[1] for x in bit_res) / len(bit_res)
        avg_c = sum(x[1] for x in curve_res) / len(curve_res)
        best_b = min(bit_res, key=lambda t: t[1])
        best_c = min(curve_res, key=lambda t: t[1])
        lines.append("")
        lines.append(f"  puzzles tested: {len(bit_res)}")
        lines.append(f"  mean |frac - n/256|:           {avg_b:.8f}")
        lines.append(f"  mean |frac - n/(128+log2(7))|: {avg_c:.8f}")
        lines.append(f"  best bit match:   P{best_b[0]} err={best_b[1]:.8f}")
        lines.append(f"  best curve match: P{best_c[0]} err={best_c[1]:.8f}")

    lines.append("")
    lines.append("=== log2(7) in offset-bit space (d mod LO) ===")
    lo135, _, _ = puzzle_band(135)
    lines.append(f"  LO_135 bits = {lo135.bit_length()}")
    lines.append(f"  log2(7) = {LOG2_7:.6f} bits")
    lines.append(f"  128 + log2(7) = {128 + LOG2_7:.6f}  (cf puzzle ~130-131 band)")

    for n in (115, 125, 130):
        pk = keys.get(n)
        if not pk or not pk.d:
            continue
        lo, _, _ = puzzle_band(n)
        off = pk.d - lo
        lines.append(
            f"  P{n} offset bits={off.bit_length()}  "
            f"offset/log2(7)={off / LOG2_7:.4f}  offset/(128+log2(7))={off / (128 + LOG2_7):.4f}"
        )

    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
