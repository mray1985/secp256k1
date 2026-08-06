#!/usr/bin/env python3
"""Batch corrected-lambda bridge checks across all puzzles in PUZZLE_LIST."""

from __future__ import annotations

import csv
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
    p,
    run_bridge_regression,
    verify_core_lambda_laws,
)
from puzzle_keys_53125 import parse_53125  # noqa: E402


def law_x_mod_p(px: int, rx: int, py: int, ry: int) -> bool:
    lam_x = (px * pow(rx, -1, p)) % p
    lhs = pow(lam_x, 3, p)
    rhs = ((pow(py, 2, p) - 7) * pow(pow(ry, 2, p) - 7, -1, p)) % p
    return lhs == rhs


def analyze_lambda(pk_n: int, keys: dict) -> dict:
    if pk_n == 135 or (pk_n in keys and keys[pk_n].d == 0):
        cfg = PuzzleConfig(puzzle_num=135)
        apply_puzzle_defaults(cfg)
        known_d = None
    else:
        cfg = build_config(keys[pk_n])
        known_d = cfg.known_d

    row = cfg.row
    px, rx = cfg.Px[row], cfg.rx[row]
    py, ry = cfg.Py, cfg.ry

    laws = verify_core_lambda_laws(
        px=px,
        rx=rx,
        py=py,
        ry=ry,
        row=row,
        px_triple=cfg.Px,
        rx_triple=cfg.rx,
    )

    lam_p_all = [(cfg.Px[i] * pow(cfg.rx[i], -1, p)) % p for i in range(3)]
    lam_n_all = [(cfg.Px[i] * pow(cfg.rx[i], -1, N)) % N for i in range(3)]
    lam_y_p = (py * pow(ry, -1, p)) % p
    lam_x_n = (px * pow(rx, -1, N)) % N
    lam_y_n = (py * pow(ry, -1, N)) % N

    w_p = (pow(lam_y_p, 2, p) * pow(ry, 2, p) - pow(lam_p_all[row], 3, p) * pow(rx, 3, p)) % p
    g_n = (pow(py, 2, N) - pow(px, 3, N)) % N
    w_n = (pow(lam_y_n, 2, N) * pow(ry, 2, N) - pow(lam_x_n, 3, N) * pow(rx, 3, N)) % N

    bare_p_plus7 = pow(lam_y_p, 2, p) == (pow(lam_p_all[row], 3, p) + 7) % p
    bare_n_eq_g = (pow(lam_x_n, 3, N) - pow(lam_y_n, 2, N)) % N == g_n

    reg_ok, reg_msgs = run_bridge_regression(cfg)

    return {
        "n": pk_n,
        "row": row,
        "known_d": known_d is not None,
        "law_p": laws.p_curve_law,
        "law_n": laws.n_law,
        "law_x": law_x_mod_p(px, rx, py, ry),
        "lambda_p_unified": len(set(lam_p_all)) == 1,
        "px_eq_lam_rx": px == (lam_p_all[row] * rx) % p,
        "weighted_p_eq_7": w_p == 7,
        "weighted_n_eq_G": w_n == g_n,
        "bare_lam_y2_eq_lam_x3_plus7": bare_p_plus7,
        "bare_lam_x3_minus_lam_y2_eq_G": bare_n_eq_g,
        "naive_n_curve_law": laws.n_naive_curve_law,
        "naive_n_cubic_mix": laws.naive_n_cubic_mix,
        "lambda_ne_px": lam_p_all[row] != px,
        "lambda_ne_py": lam_y_p != py,
        "lambda_n_distinct_rows": len(set(lam_n_all)) == 3,
        "bridge_regression": reg_ok,
        "reg_detail": "; ".join(reg_msgs),
    }


def main() -> None:
    keys = parse_53125()
    rows: list[dict] = []
    errors: list[tuple[int, str]] = []

    for n in PUZZLE_LIST:
        if n not in keys and n != 135:
            errors.append((n, "missing from 53125"))
            continue
        try:
            rows.append(analyze_lambda(n, keys))
        except Exception as exc:
            errors.append((n, str(exc)))

    out_csv = ROOT / "ARCHIVE" / "lambda_corrected_batch.csv"
    out_txt = ROOT / "ARCHIVE" / "lambda_corrected_batch_report.txt"
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    fields = list(rows[0].keys()) if rows else []
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    def count(key: str) -> tuple[int, int]:
        return sum(1 for r in rows if r.get(key)), len(rows)

    lines = [
        "CORRECTED LAMBDA BATCH — all puzzles",
        f"puzzles: {len(PUZZLE_LIST)}  analyzed: {len(rows)}  errors: {len(errors)}",
        "",
        "Definitions: Lambda = Px/rx, lambda_y = Py/ry (NOT coordinates).",
        "",
        "MUST PASS (corrected setup):",
    ]
    for label, key in [
        ("LAW-P", "law_p"),
        ("LAW-N (heaven)", "law_n"),
        ("LAW-X cubic", "law_x"),
        ("Lambda_p unified (3 rows)", "lambda_p_unified"),
        ("Px == Lambda*rx", "px_eq_lam_rx"),
        ("weighted mod p == 7", "weighted_p_eq_7"),
        ("weighted mod N == G", "weighted_n_eq_G"),
        ("Lambda != Px", "lambda_ne_px"),
        ("lambda_y != Py", "lambda_ne_py"),
        ("bridge regression", "bridge_regression"),
    ]:
        c, t = count(key)
        lines.append(f"  {label:28s} {c}/{t}")

    lines += [
        "",
        "MUST FAIL (misreadings):",
    ]
    for label, key, expect in [
        ("bare lam_y^2 == lam_x^3+7", "bare_lam_y2_eq_lam_x3_plus7", False),
        ("bare lam_x^3 - lam_y^2 == G", "bare_lam_x3_minus_lam_y2_eq_G", False),
        ("naive N curve law", "naive_n_curve_law", False),
        ("lambda_yN^2 == Lambda_N^3", "naive_n_cubic_mix", False),
    ]:
        if expect is False:
            c = sum(1 for r in rows if not r.get(key))
            lines.append(f"  {label:28s} fails {c}/{len(rows)} (want all fail)")

    fails = [r for r in rows if not r["bridge_regression"]]
    lines += [
        "",
        f"{'n':>4} {'row':>3} {'d?':>3}  "
        f"{'LP':>2} {'LN':>2} {'LX':>2} {'w7':>2} {'wG':>2} {'reg':>3}  bare+7",
        "-" * 52,
    ]
    for r in rows:
        lines.append(
            f"{r['n']:4d} {r['row']:3d} {'Y' if r['known_d'] else 'N':>3}  "
            f"{'Y' if r['law_p'] else 'N':>2} "
            f"{'Y' if r['law_n'] else 'N':>2} "
            f"{'Y' if r['law_x'] else 'N':>2} "
            f"{'Y' if r['weighted_p_eq_7'] else 'N':>2} "
            f"{'Y' if r['weighted_n_eq_G'] else 'N':>2} "
            f"{'Y' if r['bridge_regression'] else 'N':>3}  "
            f"{'Y' if r['bare_lam_y2_eq_lam_x3_plus7'] else 'N'}"
        )

    if fails:
        lines += ["", "BRIDGE REGRESSION FAILURES:"]
        for r in fails:
            lines.append(f"  P{r['n']}: {r['reg_detail']}")

    if errors:
        lines += ["", "ERRORS:"]
        for n, msg in errors:
            lines.append(f"  P{n}: {msg}")

    unsolved = [r for r in rows if not r["known_d"]]
    if unsolved:
        lines += [
            "",
            "UNSOLVED (bridge closed, d open):",
        ]
        for r in unsolved:
            lines.append(
                f"  P{r['n']}: regression={'PASS' if r['bridge_regression'] else 'FAIL'}, "
                f"all laws pass={r['law_p'] and r['law_n'] and r['law_x']}"
            )

    text = "\n".join(lines) + "\n"
    out_txt.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {out_csv}")
    print(f"wrote {out_txt}")


if __name__ == "__main__":
    main()
