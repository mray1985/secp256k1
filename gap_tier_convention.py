#!/usr/bin/env python3
"""Verify gap = H - offset_bits convention and null-model concentration test."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from compare_family_mirror_batch import PUZZLE_LIST, analyze_one  # noqa: E402
from gap_tier_common import (  # noqa: E402
    binomial_tail_ge,
    gap_interval,
    gap_to_offset_bits,
    offset_bits_to_interval,
    uniform_lo_null_p_gap,
    uniform_lo_null_p_gap12,
    verify_convention_row,
)
from puzzle_keys_53125 import parse_53125  # noqa: E402


def main() -> None:
    keys = parse_53125()
    lines = [
        "GAP-TIER CONVENTION VERIFICATION",
        "",
        "Definitions (matches compute_alignment_frame in ecdlp_full_pipeline.py):",
        "  LO = 2^(H-1),  HI = 2^H",
        "  offset = (d - shelf2) mod LO",
        "  offset_bits = offset.bit_length()   [Python int.bit_length; offset>0]",
        "  gap = H - offset_bits",
        "",
        "Bit-length interval:",
        "  offset_bits = k  <=>  2^(k-1) <= offset < 2^k",
        "",
        "Gap tiers:",
        "  gap=1  -> offset_bits=H-1  -> offset in [2^(H-2), 2^(H-1))",
        "  gap=2  -> offset_bits=H-2  -> offset in [2^(H-3), 2^(H-2))",
        "",
        "P135 (H=135) priority tiers:",
    ]
    for gap in (1, 2):
        ob, o_lo, o_hi = gap_interval(135, gap)
        lines.append(
            f"  gap={gap}: offset_bits={ob}, offset in [2^{ob-1}, 2^{ob}) "
            f"= [{o_lo}, {o_hi})"
        )
    lines += [
        "",
        "NOTE: offset_bits=132 means o in [2^131,2^132), NOT o=2^132.",
        "      For H=135: gap=1 uses offset_bits=134, not 132.",
        "",
        "SOLVED-PUZZLE CHECK (26 keys):",
        f"  {'H':>4} {'row':>3} {'offset_bits':>11} {'gap':>4}  "
        f"{'gap=H-ob':>8} {'in interval':>11}",
        "  " + "-" * 52,
    ]

    ok_gap = 0
    ok_interval = 0
    gap12 = 0
    n = 0
    for h in PUZZLE_LIST:
        if h == 135 or h not in keys or keys[h].d == 0:
            continue
        row = analyze_one(keys[h])
        lo = 2 ** (h - 1)
        v = verify_convention_row(h, row["d"], row["shelf2"], lo)
        n += 1
        if v["gap_eq_h_minus_offset_bits"]:
            ok_gap += 1
        if v["offset_in_bit_interval"]:
            ok_interval += 1
        if v["gap"] in (1, 2):
            gap12 += 1
        lines.append(
            f"  {h:4d} {row['row']:3d} {v['offset_bits']:11d} {v['gap']:4d}  "
            f"{'Y' if v['gap_eq_h_minus_offset_bits'] else 'N':>8} "
            f"{'Y' if v['offset_in_bit_interval'] else 'N':>11}"
        )

    lines += [
        "",
        f"  gap == H - offset_bits: {ok_gap}/{n}",
        f"  offset in [2^(ob-1), 2^ob): {ok_interval}/{n}",
        f"  gap in {{1,2}}: {gap12}/{n}",
        "",
        "NULL MODEL (offset uniform on [0, LO), independent per puzzle):",
        f"  P(gap=1) = 1/2, P(gap=2) = 1/4, P(gap in {{1,2}}) = 3/4",
        f"  Observed gap in {{1,2}}: {gap12}/{n} = {100*gap12/n:.1f}%",
    ]
    p_pool = 0.75
    tail = binomial_tail_ge(n, gap12, p_pool)
    lines.append(
        f"  Binomial(n={n}, p=0.75) P(X>={gap12}) = {tail:.4f} "
        f"({'not significant at 5%' if tail > 0.05 else 'significant at 5%'})"
    )
    lines.append("")
    lines.append("Per-puzzle null P(gap in {1,2}) under uniform-o (varies only via H=constant 3/4):")
    for gap in (1, 2, 3, 4, 10):
        lines.append(f"  P(gap={gap}) = {uniform_lo_null_p_gap(135, gap):.6f}")

    # Example decode for one puzzle
    h = 115
    if h in keys:
        row = analyze_one(keys[h])
        lo = 2 ** (h - 1)
        v = verify_convention_row(h, row["d"], row["shelf2"], lo)
        ob = v["offset_bits"]
        ilo, ihi = offset_bits_to_interval(ob)
        lines += [
            "",
            "P115 outlier decode:",
            f"  gap={v['gap']} offset_bits={ob} offset in [{ilo}, {ihi})",
            f"  (H-10 hit: offset_bits={gap_to_offset_bits(115, 10)} = 105)",
        ]

    report = "\n".join(lines) + "\n"
    print(report)
    out = ROOT / "ARCHIVE" / "gap_tier_convention_report.txt"
    out.write_text(report, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
