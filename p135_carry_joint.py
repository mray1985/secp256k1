#!/usr/bin/env python3
"""
Carry ↔ offset joint analysis.

For unified Λ_N (row-3 slot), row i closes when:
  (Λ_N + shift) * qx[i] ≡ Qx[i] (mod N)  =>  shift ≡ -rem_i * qx[i]^-1 (mod N)

Test shift = d_mod, band_representative(d_mod), and offset o = (d_true - shelf2) mod LO
on solved row-2 cohort, then apply to P135 with EC gate.
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
    PuzzleConfig,
    apply_puzzle_defaults,
    band_representative,
    carry,
    delta,
    pubkey_from_scalar,
    puzzle_band,
)
from gap_tier_common import (  # noqa: E402
    gap_from_observed,
    gap_interval,
    observed_offset,
    offset_in_gap_tier,
)
from genesis_calibration import bridge_state  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

ROW2 = [15, 35, 45, 50, 70, 90, 100, 120]


def solve_linear(a: int, b: int, mod: int) -> tuple[int, int] | None:
    """a*x ≡ b (mod mod). Returns (x0, period) for x = x0 + k*period, or None."""
    a %= mod
    b %= mod
    g = math.gcd(a, mod)
    if b % g != 0:
        return None
    a1, b1, m1 = a // g, b // g, mod // g
    inv = pow(a1, -1, m1)
    x0 = (b1 * inv) % m1
    return x0, m1


def bridge_ints(cfg: PuzzleConfig) -> dict:
    apply_puzzle_defaults(cfg)
    row = cfg.row
    px, rx = cfg.Px, cfg.rx
    lo, hi, _ = puzzle_band(cfg.puzzle_num)
    Qx = [(x * delta) % N for x in px]
    qx = [(x * delta) % N for x in rx]
    lambda_n = (px[row] * pow(rx[row], -1, N)) % N
    st = bridge_state(cfg)
    shelf2 = st["oitc"].shelf2
    rems: list[int] = []
    for i in range(3):
        _, rem, _ = carry(lambda_n * qx[i] - Qx[i], N)
        rems.append(rem)
    shifts: list[tuple[int, int] | None] = []
    for i in range(3):
        if rems[i] == 0:
            shifts.append((0, 1))
        else:
            shifts.append(solve_linear(qx[i], (-rems[i]) % N, N))
    return {
        "cfg": cfg,
        "lo": lo,
        "hi": hi,
        "lambda_n": lambda_n,
        "Qx": Qx,
        "qx": qx,
        "rems": rems,
        "shifts": shifts,
        "shelf2": shelf2,
        "px": px[row],
        "py": cfg.Py,
    }


def shift_closes_row(b: dict, shift: int, row_i: int) -> bool:
    lam = (b["lambda_n"] + shift) % N
    ok, rem, _ = carry(lam * b["qx"][row_i] - b["Qx"][row_i], N)
    return ok and rem == 0


def ec(d: int, px: int, py: int) -> bool:
    try:
        x, y = pubkey_from_scalar(d)
        return x == px and y == py
    except Exception:
        return False


def analyze_puzzle(n: int, keys: dict, *, ec_test: bool) -> list[str]:
    pk = keys[n]
    cfg = build_config(pk)
    b = bridge_ints(cfg)
    lo, hi = b["lo"], b["hi"]
    d_true = pk.d
    o_true = observed_offset(d_true, b["shelf2"], lo)
    gap, ob = gap_from_observed(d_true, b["shelf2"], n, lo)
    px, py = b["px"], b["py"]

    lines = [f"P{n} row={cfg.row} gap={gap} offset_bits={ob}"]

    for i in range(3):
        sh = b["shifts"][i]
        if sh is None:
            lines.append(f"  row{i+1}: no shift solution")
            continue
        x0, period = sh
        d_band = band_representative(x0, lo, hi)
        closes_sol = shift_closes_row(b, x0, i)
        closes_band = shift_closes_row(b, d_band, i)
        closes_true = shift_closes_row(b, d_true, i)
        closes_o = shift_closes_row(b, o_true, i)
        hit_band = ec(d_band, px, py) if ec_test else False
        lines.append(
            f"  row{i+1}: rem={b['rems'][i].bit_length()}b  "
            f"shift_sol closes={closes_sol}  band_rep closes={closes_band}  "
            f"d_true closes={closes_true}  o_true closes={closes_o}  "
            f"EC(band_rep)={hit_band}"
        )
        if i < 2:
            ob_band = observed_offset(d_band, b["shelf2"], lo).bit_length()
            lines.append(
                f"         band_rep d_bits={d_band.bit_length()}  "
                f"implied offset_bits={ob_band}  gap={n - ob_band}"
            )

    # CRT row1 + row2 shift classes (if both solvable)
    s1, s2 = b["shifts"][0], b["shifts"][1]
    if s1 and s2:
        x1, m1 = s1
        x2, m2 = s2
        g = math.gcd(m1, m2)
        if (x1 - x2) % g == 0:
            m = (m1 // g) * m2
            inv = pow(m1 // g, -1, m2 // g) if m2 // g > 1 else 1
            t = ((x2 - x1) // g) * inv % (m2 // g) if m2 // g > 1 else 0
            x_crt = (x1 + (m1 // g) * t * g) % m
            d_crt = band_representative(x_crt, lo, hi)
            c1 = shift_closes_row(b, 0, 0) and shift_closes_row(b, 0, 1)
            c_crt = shift_closes_row(b, x_crt, 0) and shift_closes_row(b, x_crt, 1)
            c_d = shift_closes_row(b, d_crt, 0) and shift_closes_row(b, d_crt, 1)
            hit_crt = ec(d_crt, px, py) if ec_test else False
            lines.append(
                f"  CRT(row1,row2): x_crt closes r1&r2={c_crt}  "
                f"band_rep closes r1&r2={c_d}  EC={hit_crt}"
            )
        else:
            lines.append("  CRT(row1,row2): inconsistent (no common shift mod N)")

    lines.append("")
    return lines


def p135_candidates() -> list[str]:
    cfg = PuzzleConfig(puzzle_num=135, row=2)
    b = bridge_ints(cfg)
    lo, hi = b["lo"], b["hi"]
    px, py = b["px"], b["py"]
    lines = ["P135 CARRY-JOINT CANDIDATES", ""]

    pool: dict[int, str] = {}

    def add(d: int, name: str) -> None:
        if lo <= d < hi and d not in pool:
            pool[d] = name

    for i in range(3):
        sh = b["shifts"][i]
        if not sh:
            continue
        x0, _ = sh
        add(band_representative(x0, lo, hi), f"carry_row{i+1}_band_rep")
        if lo <= (x0 % N) < hi:
            add(x0 % N, f"carry_row{i+1}_modN")

    s1, s2 = b["shifts"][0], b["shifts"][1]
    if s1 and s2:
        x1, m1 = s1
        x2, m2 = s2
        g = math.gcd(m1, m2)
        if (x1 - x2) % g == 0:
            if m2 // g > 1:
                inv = pow(m1 // g, -1, m2 // g)
                t = ((x2 - x1) // g) * inv % (m2 // g)
                x_crt = (x1 + (m1 // g) * t * g) % ((m1 // g) * m2)
            else:
                x_crt = x1
            add(band_representative(x_crt, lo, hi), "CRT_row1_row2_band_rep")

    lines.append(f"  unique band candidates: {len(pool)}")
    hits = []
    for d, name in sorted(pool.items()):
        o = observed_offset(d, b["shelf2"], lo)
        ob = o.bit_length() if o else 0
        gap = 135 - ob
        in_g1 = offset_in_gap_tier(o, 135, 1) if o else False
        in_g2 = offset_in_gap_tier(o, 135, 2) if o else False
        ok = ec(d, px, py)
        tier = "gap1" if in_g1 else ("gap2" if in_g2 else "other")
        lines.append(
            f"    {name}: d={d}  gap={gap} tier={tier} EC={ok}"
        )
        if ok:
            hits.append((d, name))

    lines.append(f"  EC hits: {len(hits)}")
    for d, name in hits:
        lines.append(f"    *** d={d}  {name}")
    lines.append("")
    return lines


def main() -> None:
    keys = parse_53125()
    lines = [
        "CARRY-OFFSET JOINT ANALYSIS",
        "shift in (Λ_N + shift)*qx - Qx ≡ 0 (mod N)",
        "band_rep(d) = LO + (d mod LO)  — unique scalar in puzzle band per mod-LO class",
        "",
        "=== ROW-2 CALIBRATION (does carry predict true d?) ===",
        "",
    ]

    row2_hits = 0
    row2_total = 0
    for n in ROW2:
        if n not in keys:
            continue
        chunk = analyze_puzzle(n, keys, ec_test=True)
        lines += chunk
        for ln in chunk:
            if "EC(band_rep)=True" in ln:
                row2_hits += 1
            if "EC(band_rep)=" in ln:
                row2_total += 1

    lines += [
        f"Row-2 carry band_rep EC hits on row lines: {row2_hits}/{row2_total}",
        "",
        "=== P135 ===",
        "",
    ]
    lines += p135_candidates()

    lines += [
        "INTERPRETATION:",
        "  If row-2 EC(band_rep)=False everywhere: carry shift ≠ puzzle scalar via band_rep.",
        "  If o_true closes rows: notebook shift may be offset o, not d.",
        "  P135: finite carry-CRT candidates exhausted; open search needs new bit laws.",
    ]

    report = "\n".join(lines) + "\n"
    print(report)
    out = ROOT / "ARCHIVE" / "p135_carry_joint_report.txt"
    out.write_text(report, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
