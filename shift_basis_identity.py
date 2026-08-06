#!/usr/bin/env python3
"""
Test shift basis identity: s_i ≡ Λ_i - Λ_ε (mod N) for unified-Λ carry closure.

Then analyze integer quotient tuple (c_1, c_2, c_3) on solved puzzles.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import PUZZLE_LIST, build_config  # noqa: E402
from ecdlp_full_pipeline import N, delta, pubkey_from_scalar, puzzle_band  # noqa: E402
from gap_tier_common import observed_offset  # noqa: E402
from genesis_calibration import bridge_state  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402
from shift_diagnostic import exact_carry_solutions  # noqa: E402


def centered(x: int, mod: int = N) -> int:
    x %= mod
    if x > mod // 2:
        x -= mod
    return x


def bridge_lambdas(cfg) -> tuple[list[int], list[int], list[int], int]:
    row_eps = cfg.row
    px, rx = cfg.Px, cfg.rx
    lam_n = [(px[i] * pow(rx[i], -1, N)) % N for i in range(3)]
    Qx = [(x * delta) % N for x in px]
    qx = [(x * delta) % N for x in rx]
    lam_eps = lam_n[row_eps]
    return lam_n, Qx, qx, lam_eps


def integer_quotient(lam: int, qx_i: int, Qx_i: int) -> int | None:
    num = lam * qx_i - Qx_i
    if num % N != 0:
        return None
    return num // N


def main() -> None:
    keys = parse_53125()
    lines = [
        "SHIFT BASIS IDENTITY TEST",
        "Hypothesis: unified closure shift s_i ≡ Λ_i - Λ_ε (mod N)",
        "",
        "=== PART 1: r_i = s_i - (Λ_i - Λ_ε) mod N ===",
        "",
    ]

    r_zero = 0
    r_tests = 0
    center_match = 0
    center_tests = 0

    for n in PUZZLE_LIST:
        if n not in keys or keys[n].d == 0:
            continue
        pk = keys[n]
        cfg = build_config(pk)
        lam_n, Qx, qx, lam_eps = bridge_lambdas(cfg)

        for i in range(3):
            delta_lam = (lam_n[i] - lam_eps) % N
            sols = exact_carry_solutions(lam_eps, qx[i], Qx[i], d_target=pk.d)
            if not sols:
                continue
            s_min = sols[0][0]
            r_i = (s_min - delta_lam) % N
            r_tests += 1
            if r_i == 0:
                r_zero += 1

            c_s = centered(s_min)
            c_d = centered(delta_lam)
            center_tests += 1
            if c_s == c_d:
                center_match += 1

            if n in (15, 120, 135) or r_i != 0:
                if r_i != 0 or n <= 20:
                    lines.append(
                        f"  P{n} row{i+1}: r_i={'0' if r_i == 0 else hex(r_i)}  "
                        f"centered(s)={c_s.bit_length()}b  centered(ΔΛ)={c_d.bit_length()}b  "
                        f"match={c_s == c_d}"
                    )

    lines += [
        "",
        f"  r_i == 0: {r_zero}/{r_tests}",
        f"  centered(s_min) == centered(Λ_i-Λ_ε): {center_match}/{center_tests}",
        "",
        "=== PART 2: Λ difference matrix (sample P135) ===",
        "",
    ]

    from ecdlp_full_pipeline import PuzzleConfig, apply_puzzle_defaults

    c135 = PuzzleConfig(puzzle_num=135, row=2)
    apply_puzzle_defaults(c135)
    lam_n, _, _, lam_eps = bridge_lambdas(c135)
    D = [[(lam_n[i] - lam_n[j]) % N for j in range(3)] for i in range(3)]
    cycle = (D[0][1] + D[1][2] + D[2][0]) % N
    lines.append(f"  P135 Λ_ε = row {c135.row}")
    for i in range(3):
        for j in range(3):
            if i != j:
                lines.append(f"    D_{i+1}{j+1} = Λ_{i+1}-Λ_{j+1} bits={D[i][j].bit_length()}")
    lines.append(f"  D_12+D_23+D_31 mod N == 0: {cycle == 0}")
    lines.append(
        f"  unified s_i (Λ_i-Λ_ε) bits: "
        + ", ".join(str(centered((lam_n[i] - lam_eps) % N).bit_length()) for i in range(3))
    )
    lines.append("")

    lines += [
        "=== PART 3: Integer quotient tuple (c_1,c_2,c_3) vs d ===",
        "  c_i = (Λ_i·qx_i - Qx_i) / N  (per-row Λ, exact integer)",
        "",
    ]

    quot_hits: dict[str, int] = {
        "c_sum mod LO == o": 0,
        "c_sum mod LO == d mod LO": 0,
        "c1+c2+c3 == C_floor (shelf)": 0,
        "any c_i == d": 0,
    }
    qtests = 0

    for n in PUZZLE_LIST:
        if n not in keys or keys[n].d == 0:
            continue
        pk = keys[n]
        cfg = build_config(pk)
        lo, _, _ = puzzle_band(n)
        st = bridge_state(cfg)
        shelf2 = st["oitc"].shelf2
        c_floor = st["oitc"].c_floor
        d = pk.d
        o = observed_offset(d, shelf2, lo)
        lam_n, Qx, qx, _ = bridge_lambdas(cfg)
        cs = [integer_quotient(lam_n[i], qx[i], Qx[i]) for i in range(3)]
        if any(c is None for c in cs):
            continue
        qtests += 1
        c1, c2, c3 = cs  # type: ignore
        c_sum = c1 + c2 + c3
        if c_sum % lo == o % lo:
            quot_hits["c_sum mod LO == o"] += 1
        if c_sum % lo == d % lo:
            quot_hits["c_sum mod LO == d mod LO"] += 1
        if c_sum == c_floor:
            quot_hits["c1+c2+c3 == C_floor (shelf)"] += 1
        if d in (c1, c2, c3):
            quot_hits["any c_i == d"] += 1

        if n in (15, 45, 115, 120, 130):
            dx, dy = pubkey_from_scalar(d)
            lines.append(
                f"  P{n}: c_bits=({c1.bit_length()},{c2.bit_length()},{c3.bit_length()})  "
                f"sum_bits={c_sum.bit_length()}  gap={n - o.bit_length()}  "
                f"C_floor_bits={c_floor.bit_length()}"
            )
            lines.append(
                f"       c_sum mod LO == o: {c_sum % lo == o}  "
                f"c_sum == C_floor: {c_sum == c_floor}"
            )

    lines.append("")
    lines.append(f"  quotient tests: {qtests}")
    for k, v in quot_hits.items():
        lines.append(f"    {k}: {v}/{qtests}")

    lines += [
        "",
        "VERDICT:",
    ]
    if r_zero == r_tests:
        lines.append("  s_i ≡ Λ_i - Λ_ε (mod N): CLOSED on all unified-Λ row-tests.")
        lines.append("  Shift is basis conversion, not private-key unknown.")
    else:
        lines.append(f"  Identity fails on {r_tests - r_zero}/{r_tests} tests — investigate gcd(qx,N).")

    report = "\n".join(lines) + "\n"
    print(report)
    out = ROOT / "ARCHIVE" / "shift_basis_identity_report.txt"
    out.write_text(report, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
