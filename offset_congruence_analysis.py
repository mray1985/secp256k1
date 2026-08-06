#!/usr/bin/env python3
"""
Low-order congruence analysis on true shelf2 offsets.

For solved puzzles (row-2 cohort primary), study:
  o = (d - shelf2) mod LO
  o mod 2^t, mantissa, tier-boundary distances

Search for shared congruences o ≡ c (mod M) to estimate bit reduction inside
gap-1 / gap-2 bands for P135.
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import PUZZLE_LIST, build_config  # noqa: E402
from ecdlp_full_pipeline import (  # noqa: E402
    N,
    PuzzleConfig,
    apply_puzzle_defaults,
    carry,
    delta,
    puzzle_band,
)
from gap_tier_common import gap_from_observed, gap_interval  # noqa: E402
from genesis_calibration import bridge_state  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

ROW2 = [15, 35, 45, 50, 70, 90, 100, 120]
H135 = 135


def collect_offset(pk_n: int, keys: dict) -> dict | None:
    if pk_n not in keys or keys[pk_n].d == 0:
        return None
    pk = keys[pk_n]
    cfg = build_config(pk)
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(pk_n)
    shelf2 = st["oitc"].shelf2
    o = (pk.d - shelf2) % lo
    b = o.bit_length()
    gap, ob = gap_from_observed(pk.d, shelf2, pk_n, lo)
    return {
        "n": pk_n,
        "row": cfg.row,
        "d": pk.d,
        "shelf2": shelf2,
        "lo": lo,
        "hi": hi,
        "offset": o,
        "offset_bits": ob,
        "gap": gap,
        "mantissa_num": o,
        "mantissa_den": 1 << (b - 1) if b else 1,
        "dist_tier_lo": o - (1 << (b - 1)) if b else 0,
        "dist_tier_hi": (1 << b) - o if b else 0,
    }


def max_shared_power_of_two(residues: list[int]) -> tuple[int, int]:
    """Max t with all residues equal mod 2^t. Returns (t, residue mod 2^t)."""
    if not residues:
        return 0, 0
    t = 0
    while True:
        mod = 1 << (t + 1)
        vals = {r % mod for r in residues}
        if len(vals) != 1:
            break
        t += 1
        if t > 128:
            break
    if t == 0:
        return 0, residues[0] % 2
    mod = 1 << t
    return t, residues[0] % mod


def congruence_scan(cohort: list[dict], label: str) -> list[str]:
    lines = [f"COHORT: {label}  n={len(cohort)}", ""]
    if not cohort:
        return lines + ["  (empty)", ""]

    offsets = [c["offset"] for c in cohort]
    t_max, residue = max_shared_power_of_two(offsets)
    lines.append(f"  shared o mod 2^t:  t_max={t_max}  residue={residue}")
    if t_max:
        lines.append(f"    => o ≡ {residue} (mod 2^{t_max})  removes {t_max} bits from tier search")

    lines.append("")
    lines.append(f"  {'H':>4} {'gap':>3} {'ob':>3}  {'o mod 16':>10} {'o mod 256':>12} "
                 f"{'mantissa~':>10} {'d_lo':>6} {'d_hi':>6}")
    lines.append("  " + "-" * 70)
    for c in cohort:
        o = c["offset"]
        b = c["offset_bits"]
        m = o / (1 << (b - 1)) if b else 0
        lines.append(
            f"  {c['n']:4d} {c['gap']:3d} {b:3d}  {o % 16:10d} {o % 256:12d} "
            f"{m:10.6f} {c['dist_tier_lo']:6d} {c['dist_tier_hi']:6d}"
        )

    # Scan fixed t ladder
    lines.append("")
    lines.append("  fixed t ladder (all equal mod 2^t?):")
    for t in [4, 8, 12, 16, 20, 24, 32]:
        mod = 1 << t
        vals = [c["offset"] % mod for c in cohort]
        ok = len(set(vals)) == 1
        if ok or t <= 16:
            flag = "Y" if ok else "N"
            lines.append(f"    t={t:2d}: {flag}  residues={[hex(v) for v in vals[:6]]}"
                         + ("..." if len(vals) > 6 else ""))

    # Mantissa low bits (scale-invariant): floor(o / 2^(b-t)) for t=8
    lines.append("")
    lines.append("  mantissa low 8 bits: floor(o / 2^(b-8)) for b>=8:")
    m8 = []
    for c in cohort:
        b = c["offset_bits"]
        if b >= 8:
            m8.append(c["offset"] >> (b - 8))
    if m8:
        t8, r8 = max_shared_power_of_two(m8)
        lines.append(f"    shared among scaled mantissas: t={t8}  (weak cross-height invariant)")
        lines.append(f"    values: {m8}")

    lines.append("")
    return lines


def interval_after_congruence(
    puzzle_h: int, gap: int, modulus: int, residue: int
) -> tuple[int, int, int, float]:
    """Count o in gap tier interval satisfying o ≡ residue (mod modulus)."""
    _, o_lo, o_hi = gap_interval(puzzle_h, gap)
    width = o_hi - o_lo
    first = o_lo + ((residue - o_lo) % modulus)
    if first >= o_hi:
        count = 0
    else:
        count = 1 + (o_hi - 1 - first) // modulus
    bits_removed = modulus.bit_length() - 1 if modulus > 1 else 0
    eff_bits = math.log2(count) if count else 0
    return first, count, width, eff_bits


def p135_carry_rows() -> list[str]:
    lines = ["P135 ROW-1/ROW-2 CARRY (unified Λ_N row3)", ""]
    cfg = PuzzleConfig(puzzle_num=H135, row=2)
    apply_puzzle_defaults(cfg)
    lo, hi, _ = puzzle_band(H135)
    px, rx = cfg.Px, cfg.rx
    row = cfg.row
    Qx = [(x * delta) % N for x in px]
    qx = [(x * delta) % N for x in rx]
    lambda_n = (px[row] * pow(rx[row], -1, N)) % N
    shelf2 = bridge_state(cfg)["oitc"].shelf2

    rems: list[int] = []
    for i in range(3):
        num = lambda_n * qx[i] - Qx[i]
        ok, rem, b = carry(num, N)
        lines.append(
            f"  row{i+1}: carry_ok={ok}  rem_bits={rem.bit_length() if rem else 0}  "
            f"b_bits={b.bit_length() if b else 0}"
        )
        rems.append(rem)

    lines.append("")
    for i in range(2):
        if rems[i] == 0:
            continue
        d_mod = (-rems[i] * pow(qx[i], -1, N)) % N
        o = (d_mod - shelf2) % lo
        in_band = lo <= d_mod < hi
        lines.append(
            f"  close row{i+1} via d ≡ rem*qx^-1: d_mod bits={d_mod.bit_length()} "
            f"in_band={in_band}  implied o bits={o.bit_length()}"
        )
        for gap in (1, 2):
            _, o_lo, o_hi = gap_interval(H135, gap)
            lines.append(
                f"    gap={gap} tier hit: {o_lo <= o < o_hi}  "
                f"(o in [{o_lo.bit_length()}b..{o_hi.bit_length()}b))"
            )
    lines.append("")
    lines.append(
        "  Carry congruences give d mod N outside puzzle band — they constrain"
    )
    lines.append(
        "  a DIFFERENT layer than shelf2 offset unless linked by bridge law."
    )
    lines.append("")
    return lines


def main() -> None:
    keys = parse_53125()
    all_rows: list[dict] = []
    for n in PUZZLE_LIST:
        if n not in keys or keys[n].d == 0:
            continue
        rec = collect_offset(n, keys)
        if rec:
            all_rows.append(rec)

    lines = [
        "OFFSET CONGRUENCE ANALYSIS",
        "True offset: o = (d - shelf2) mod LO,  gap = H - bitlength(o)",
        "",
    ]

    row2 = [r for r in all_rows if r["n"] in ROW2]
    lines += congruence_scan(row2, "row-2 all (8 solved)")

    for gap in (1, 2):
        sub = [r for r in row2 if r["gap"] == gap]
        lines += congruence_scan(sub, f"row-2 gap={gap}")

    row2_g12 = [r for r in row2 if r["gap"] in (1, 2)]
    lines += congruence_scan(row2_g12, "row-2 gap in {1,2} (7 puzzles)")

    # All solved gap-1 / gap-2 for comparison
    g1_all = [r for r in all_rows if r["gap"] == 1]
    lines += congruence_scan(g1_all, f"all rows gap=1 ({len(g1_all)} puzzles)")

    lines += p135_carry_rows()

    # P135 projection from any row-2 congruence found
    lines.append("=" * 72)
    lines.append("P135 TIER WIDTH AFTER HYPOTHETICAL CONGRUENCES")
    lines.append("")
    _, o_lo1, o_hi1 = gap_interval(H135, 1)
    _, o_lo2, o_hi2 = gap_interval(H135, 2)
    lines.append(f"  gap=1 raw tier width: 2^{o_hi1.bit_length()-1}  [{o_lo1}, {o_hi1})")
    lines.append(f"  gap=2 raw tier width: 2^{o_lo2.bit_length()}  [{o_lo2}, {o_hi2})")
    lines.append("")
    lines.append("  bits to remove for ~2^60 search: ~73 (from 2^133 tier)")
    lines.append("")

    t_r2, res_r2 = max_shared_power_of_two([r["offset"] for r in row2_g12])
    for gap in (1, 2):
        sub = [r for r in row2 if r["gap"] == gap]
        if not sub:
            continue
        t, res = max_shared_power_of_two([r["offset"] for r in sub])
        mod = 1 << t if t else 1
        first, cnt, width, eff = interval_after_congruence(H135, gap, mod, res if t else 0)
        lines.append(
            f"  row-2 gap={gap} shared mod 2^{t}: residue={res}  "
            f"P135 tier-{gap} survivors={cnt:.3e}  ~2^{eff:.1f}  "
            f"(removed {t} bits)"
        )

    lines += [
        "",
        "VERDICT:",
        "  - Bit-length tier (gap 1/2): useful PRIOR, not falsified by 189-point miss",
        "  - Exact named bridge term: falsified for row-2 (term_exact=0/8)",
        "  - Low-bit congruence from row-2 cohort: see t_max above",
        "  - k_lane numeric proximity without s^-1 r Jacobian: misleading for ranking",
        "  - Next: combine carry residues with gap-tier CRT if law links layers",
        "",
        "K-LANE NOTE (do not rank by raw |k_transform - d|):",
        "  Δk ≡ s^-1 * r * Δd (mod N)  — modular circular distance required.",
    ]

    report = "\n".join(lines) + "\n"
    print(report)
    out = ROOT / "ARCHIVE" / "offset_congruence_report.txt"
    out.write_text(report, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
