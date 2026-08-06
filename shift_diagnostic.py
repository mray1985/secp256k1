#!/usr/bin/env python3
"""
Derive per-row shift s_i from exact integer carry, then compare to d, o, curve data.

Unreduced:  (Λ + s_i) * q_x,i - Q_x,i = c_i * N   (integer c_i, not mod-N)

On solved puzzles, enumerate shift solutions and test whether any identification
shift = d | o | band_rep | ... survives calibration.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import PUZZLE_LIST, build_config  # noqa: E402
from ecdlp_full_pipeline import (  # noqa: E402
    N,
    delta,
    p as FIELD_P,
    pubkey_from_scalar,
    puzzle_band,
)
from gap_tier_common import observed_offset  # noqa: E402
from genesis_calibration import bridge_state  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

ROW2 = [15, 35, 45, 50, 70, 90, 100, 120]


def exact_carry_solutions(
    lam: int, qx_i: int, Qx_i: int, *, d_target: int | None = None
) -> list[tuple[int, int]]:
    """
    All integer s with (lam + s)*qx - Qx = c*N exactly.
    Returns list of (s, c) with |s| minimized first; includes s matching d_target if any.
    """
    num0 = lam * qx_i - Qx_i
    g = math.gcd(qx_i, N)
    # num0 + s*qx_i ≡ 0 (mod N)  =>  s ≡ -num0 * inv(qx_i) mod (N/g)
    qx1, n1 = qx_i // g, N // g
    if num0 % g != 0:
        return []
    inv = pow(qx1, -1, n1)
    s0 = (-(num0 // g) * inv) % n1
    period = n1

    out: list[tuple[int, int]] = []
    seen: set[int] = set()

    def add_s(s: int) -> None:
        if s in seen:
            return
        num = (lam + s) * qx_i - Qx_i
        if num % N != 0:
            return
        c = num // N
        seen.add(s)
        out.append((s, c))

    # Sample k around 0 and around d_target if given
    ks = list(range(-3, 4))
    if d_target is not None:
        if period > 0:
            k0 = (d_target - s0) // period
            for dk in range(-2, 3):
                ks.append(k0 + dk)

    for k in sorted(set(ks)):
        add_s(s0 + k * period)

    out.sort(key=lambda t: (abs(t[0]).bit_length(), abs(t[0])))
    return out


def analyze_puzzle(n: int, keys: dict) -> list[str]:
    pk = keys[n]
    cfg = build_config(pk)
    row_eps = cfg.row
    px, rx = cfg.Px, cfg.rx
    lo, hi, _ = puzzle_band(n)
    st = bridge_state(cfg)
    shelf2 = st["oitc"].shelf2
    d = pk.d
    o = observed_offset(d, shelf2, lo)
    dx, dy = pubkey_from_scalar(d)
    lam_row = [(px[i] * pow(rx[i], -1, FIELD_P)) % FIELD_P for i in range(3)]
    lam_n = [(px[i] * pow(rx[i], -1, N)) % N for i in range(3)]
    lam_unified = lam_n[row_eps]
    Qx = [(x * delta) % N for x in px]
    qx = [(x * delta) % N for x in rx]
    lam_y = (pk.py * pow(cfg.ry or rx[row_eps], -1, FIELD_P)) % FIELD_P

    lines = [
        f"P{n}  eps_row={row_eps}  d_bits={d.bit_length()}  o_bits={o.bit_length()}  "
        f"gap={n - o.bit_length()}",
        f"  x(dG) bits={dx.bit_length()}  y(dG) bits={dy.bit_length()}",
        "",
    ]

    for label, lam in (
        ("unified_Λ(eps)", lam_unified),
        ("per-row Λ_i", None),
    ):
        for i in range(3):
            lam_i = lam if lam is not None else lam_n[i]
            sols = exact_carry_solutions(lam_i, qx[i], Qx[i], d_target=d)
            num0 = lam_i * qx[i] - Qx[i]
            rem = num0 % N
            c_floor = num0 // N
            lines.append(
                f"  [{label} row{i+1}] rem_bits={rem.bit_length() if rem else 0}  "
                f"c_floor_bits={c_floor.bit_length() if c_floor else 0}  "
                f"exact_s_count={len(sols)}"
            )
            if not sols:
                continue
            # Best by |s|, and member matching d or o if any
            for tag, target in (("d", d), ("o", o)):
                hit = next(((s, c) for s, c in sols if s == target), None)
                if hit:
                    lines.append(f"    ** s == {tag}  c_bits={hit[1].bit_length()}")
            s_min, c_min = sols[0]
            lines.append(
                f"    s_min bits={s_min.bit_length()}  c_bits={c_min.bit_length()}  "
                f"s-d bits={(s_min - d).bit_length() if s_min != d else 0}  "
                f"s-o bits={(s_min - o).bit_length() if s_min != o else 0}"
            )
            if s_min != 0 and math.gcd(s_min, N) == 1:
                ratio = (s_min * pow(d, -1, N)) % N
                lines.append(f"    s/d mod N bits={ratio.bit_length()}")
            # Curve comparisons on s_min
            for name, val in (
                ("x(dG)", dx),
                ("y(dG)", dy),
                ("Px_row", px[row_eps]),
                ("lam_y", lam_y),
            ):
                if s_min == val:
                    lines.append(f"    ** s_min == {name}")
                elif val and math.gcd(val, N) == 1:
                    r = (s_min * pow(val, -1, N)) % N
                    if r.bit_length() < 40:
                        lines.append(f"    s_min/{name} mod N = {r} ({r.bit_length()}b)")
        lines.append("")

    return lines


def cross_puzzle_pattern(keys: dict) -> list[str]:
    """Summarize whether s==d or s==o ever occurs on unified Λ row1/2."""
    lines = ["CROSS-PUZZLE PATTERN (unified Λ, exact integer carry)", ""]
    stats = {
        "s_eq_d": 0,
        "s_eq_o": 0,
        "s_min_eq_d": 0,
        "tests": 0,
    }
    for n in PUZZLE_LIST:
        if n not in keys or keys[n].d == 0 or n == 135:
            continue
        pk = keys[n]
        cfg = build_config(pk)
        row_eps = cfg.row
        px, rx = cfg.Px, cfg.rx
        lo, _, _ = puzzle_band(n)
        st = bridge_state(cfg)
        shelf2 = st["oitc"].shelf2
        d = pk.d
        o = observed_offset(d, shelf2, lo)
        lam = (px[row_eps] * pow(rx[row_eps], -1, N)) % N
        Qx = [(x * delta) % N for x in px]
        qx = [(x * delta) % N for x in rx]
        for i in range(3):
            sols = exact_carry_solutions(lam, qx[i], Qx[i], d_target=d)
            if not sols:
                continue
            stats["tests"] += 1
            if any(s == d for s, _ in sols):
                stats["s_eq_d"] += 1
            if any(s == o for s, _ in sols):
                stats["s_eq_o"] += 1
            if sols[0][0] == d:
                stats["s_min_eq_d"] += 1
    lines.append(f"  row tests with exact s: {stats['tests']}")
    lines.append(f"  any s == d: {stats['s_eq_d']}")
    lines.append(f"  any s == o: {stats['s_eq_o']}")
    lines.append(f"  minimal |s| == d: {stats['s_min_eq_d']}")
    lines.append("")
    return lines


def p135_shift_structure() -> list[str]:
    lines = ["P135 (unsolved) — exact shift structure only", ""]
    from ecdlp_full_pipeline import PuzzleConfig, apply_puzzle_defaults

    c = PuzzleConfig(puzzle_num=135, row=2)
    apply_puzzle_defaults(c)
    row_eps = c.row
    px, rx = c.Px, c.rx
    lo, hi, _ = puzzle_band(135)
    st = bridge_state(c)
    shelf2 = st["oitc"].shelf2
    lam = (px[row_eps] * pow(rx[row_eps], -1, N)) % N
    Qx = [(x * delta) % N for x in px]
    qx = [(x * delta) % N for x in rx]

    for i in range(3):
        sols = exact_carry_solutions(lam, qx[i], Qx[i])
        lines.append(f"  row{i+1}: {len(sols)} exact shift classes (sampled)")
        for s, c_i in sols[:3]:
            ob = observed_offset(lo + (s % lo), shelf2, lo).bit_length() if s else 0
            lines.append(
                f"    s_bits={s.bit_length()} c_bits={c_i.bit_length()} "
                f"band_o_gap={135-ob if ob else '?'}"
            )
    lines.append("")
    return lines


def main() -> None:
    keys = parse_53125()
    lines = [
        "SHIFT DIAGNOSTIC — derive s_i from (Λ+s)qx - Qx = c·N",
        "Compare s_i to d, o, x(dG), y(dG) on solved puzzles.",
        "",
        "=== ROW-2 DETAIL ===",
        "",
    ]
    for n in ROW2:
        if n in keys:
            lines += analyze_puzzle(n, keys)

    lines += ["=== ALL SOLVED (batch list) ===", ""]
    for n in PUZZLE_LIST:
        if n not in keys or keys[n].d == 0 or n in ROW2:
            continue
        lines += analyze_puzzle(n, keys)

    lines += cross_puzzle_pattern(keys)
    lines += p135_shift_structure()
    lines += [
        "VERDICT:",
        "  If s==d and s==o counts are 0: shift is a distinct object from scalar/offset.",
        "  If per-row Λ_i gives s=0 on own row with integer c: own-row carry is exact;",
        "  unified Λ requires row-specific shift — test f_i(d) not global shift.",
    ]

    report = "\n".join(lines) + "\n"
    print(report)
    out = ROOT / "ARCHIVE" / "shift_diagnostic_report.txt"
    out.write_text(report, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
