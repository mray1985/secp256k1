#!/usr/bin/env python3
"""
Layer operators (not combined Delta constants).

  coarse X = x/p
  fine   F = y/p^2

For each schedule family, measure how the op moves X and F separately.
Exact Fraction. Search for RULES / algebraic families, not repeated Delta values.
"""
from __future__ import annotations

import csv
from collections import Counter
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_LAYER_OPERATORS.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\phi_layer_operators.csv")
KEYS = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LAMBDA = 0x5363AD4CC05C30E0A5261C028812645A122E22EA20816678DF02967C1B23BD72
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE

G = SECP256k1.generator


def point(d: int) -> tuple[int, int]:
    d %= N
    if d == 0:
        raise ValueError("O")
    pt = d * G
    return int(pt.x()), int(pt.y())


def layers(x: int, y: int) -> tuple[Fraction, Fraction]:
    return Fraction(x, P), Fraction(y, P * P)


def load_holdout() -> list[tuple[int, int]]:
    rows = []
    with KEYS.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pn = int(r["puzzle"])
            if pn == 135 or pn <= 100:
                continue
            raw = r["private_key"].strip()
            d = int(raw, 16) if any(c in raw.lower() for c in "abcdef") else int(raw)
            d %= N
            if d:
                rows.append((pn, d))
    return rows


def analyze_family(name: str, edges: list[tuple[int, int, str]], w) -> list[dict]:
    """edges: (d, d_net, label)."""
    rows_out: list[dict] = []
    n = len(edges)
    if n == 0:
        return rows_out

    X_fixed = F_fixed = 0
    F_reflect = 0
    F_negate_signed = 0
    X_beta = 0
    X_beta2 = 0
    parity_flip = 0
    dX_vals: list[Fraction] = []
    dF_vals: list[Fraction] = []
    rule_hits: Counter[str] = Counter()

    for d, d_net, label in edges:
        x, y = point(d)
        xn, yn = point(d_net)
        X, F = layers(x, y)
        Xn, Fn = layers(xn, yn)
        dX, dF = Xn - X, Fn - F

        flags = {
            "X_fixed": Xn == X,
            "F_fixed": Fn == F,
            "F_reflect": Fn == Fraction(1, P) - F,
            "F_signed_neg": Fn == -F,
            "X_beta": xn == (BETA * x) % P and yn == y,
            "X_beta2": xn == (BETA * BETA * x) % P and yn == y,
            "parity_flip": (y % 2) != (yn % 2),
        }
        if flags["X_fixed"]:
            X_fixed += 1
        if flags["F_fixed"]:
            F_fixed += 1
        if flags["F_reflect"]:
            F_reflect += 1
        if flags["F_signed_neg"]:
            F_negate_signed += 1
        if flags["X_beta"]:
            X_beta += 1
        if flags["X_beta2"]:
            X_beta2 += 1
        if flags["parity_flip"]:
            parity_flip += 1

        dX_vals.append(dX)
        dF_vals.append(dF)

        primary = "none"
        if flags["X_fixed"] and flags["F_reflect"]:
            primary = "negation_canonical_layers"
        elif flags["X_fixed"] and flags["F_signed_neg"]:
            primary = "negation_signed_fine_only"
        elif flags["F_fixed"] and flags["X_beta"]:
            primary = "glv_psi"
        elif flags["F_fixed"] and flags["X_beta2"]:
            primary = "glv_psi2"
        elif flags["X_fixed"] and flags["F_fixed"]:
            primary = "identity"
        rule_hits[primary] += 1

        rows_out.append(
            {
                "family": name,
                "label": label,
                "d": str(d),
                "d_net": str(d_net),
                "x": str(x),
                "y": str(y),
                "xn": str(xn),
                "yn": str(yn),
                "dX_num": str(dX.numerator),
                "dX_den": str(dX.denominator),
                "dF_num": str(dF.numerator),
                "dF_den": str(dF.denominator),
                "primary_rule": primary,
                "X_fixed": flags["X_fixed"],
                "F_fixed": flags["F_fixed"],
                "F_reflect": flags["F_reflect"],
                "X_beta": flags["X_beta"],
            }
        )

    uniq_dX = len(set(dX_vals))
    uniq_dF = len(set(dF_vals))

    w(f"  [{name}] n={n}")
    w(f"    COARSE X=x/p:")
    w(f"      X fixed:              {X_fixed}/{n}")
    w(f"      x'==beta*x (psi):     {X_beta}/{n}")
    w(f"      x'==beta^2*x:         {X_beta2}/{n}")
    w(f"      unique dX values:     {uniq_dX}/{n}")
    w(f"    FINE F=y/p^2:")
    w(f"      F fixed:              {F_fixed}/{n}")
    w(f"      F -> 1/p - F:         {F_reflect}/{n}")
    w(f"      F -> -F (signed):     {F_negate_signed}/{n}")
    w(f"      unique dF values:     {uniq_dF}/{n}")
    w(f"      y-parity flip:        {parity_flip}/{n}")
    w(f"    primary rule histogram: {dict(rule_hits)}")
    if X_fixed == n and F_reflect == n:
        op_X, op_F = "id", "reflect 1/p - F"
    elif F_fixed == n and X_beta == n:
        op_X, op_F = "x |-> beta*x mod p", "id"
    elif F_fixed == n and X_beta2 == n:
        op_X, op_F = "x |-> beta^2*x mod p", "id"
    elif X_fixed == 0 and F_fixed == 0 and uniq_dX == n:
        op_X, op_F = "generic (no id/beta)", "generic (no id/reflect)"
    else:
        op_X, op_F = "mixed/partial", "mixed/partial"
    w(f"    OPERATOR SUMMARY:  T_X: {op_X}")
    w(f"                       T_F: {op_F}")
    w()
    return rows_out


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("LAYER OPERATORS: coarse X=x/p  vs  fine F=y/p^2  (separate)")
    w("=" * 88)
    w("  Metric: algebraic RULES per layer, not repeated combined Delta.")
    w()

    all_csv: list[dict] = []

    w("-" * 88)
    w("A) Controlled schedules d=1..64")
    w("-" * 88)
    families = {
        "add_+1": [(d, d + 1, f"{d}->+1") for d in range(1, 65)],
        "double": [(d, 2 * d, f"{d}->2d") for d in range(1, 65)],
        "double_add_+1": [(d, 2 * d + 1, f"{d}->2d+1") for d in range(1, 65)],
        "negation": [(d, (-d) % N, f"{d}->-d") for d in range(1, 65)],
        "glv_lambda": [(d, (LAMBDA * d) % N, f"{d}->lam") for d in range(1, 65)],
        "glv_lambda2": [(d, (LAMBDA * LAMBDA * d) % N, f"{d}->lam2") for d in range(1, 65)],
    }
    for name in list(families):
        families[name] = [(a, b % N, lab) for a, b, lab in families[name] if b % N != 0]

    for name, edges in families.items():
        all_csv.extend(analyze_family(name, edges, w))

    w("-" * 88)
    w("B) Holdout puzzles>100")
    w("-" * 88)
    hold = load_holdout()
    hold_fams = {
        "hold_add_+1": [(d, (d + 1) % N, f"p{pn}") for pn, d in hold if (d + 1) % N],
        "hold_double": [(d, (2 * d) % N, f"p{pn}") for pn, d in hold if (2 * d) % N],
        "hold_neg": [(d, (-d) % N, f"p{pn}") for pn, d in hold if (-d) % N],
        "hold_glv": [(d, (LAMBDA * d) % N, f"p{pn}") for pn, d in hold if (LAMBDA * d) % N],
    }
    for name, edges in hold_fams.items():
        all_csv.extend(analyze_family(name, edges, w))

    w("-" * 88)
    w("C) Doubling: coarse/fine follow EC-double on (x,y)?")
    w("-" * 88)
    dbl_exact = 0
    for d in range(1, 65):
        x, y = point(d)
        xn, yn = point(2 * d)
        lam = (3 * x * x) * pow(2 * y, -1, P) % P
        x_expect = (lam * lam - 2 * x) % P
        y_expect = (lam * (x - x_expect) - y) % P
        if (xn, yn) == (x_expect, y_expect):
            dbl_exact += 1
    w(f"  d=1..64: 2*(dG) matches affine double: {dbl_exact}/64")
    w("  So for doubling, T_X/T_F are just EC-double — not a simpler decimal rule.")
    w()

    w("-" * 88)
    w("D) Layer operator table")
    w("-" * 88)
    w("  negation:  T_X = id,            T_F = reflect (1/p - F)")
    w("  GLV psi:   T_X = beta*x mod p,  T_F = id")
    w("  add/double: both move; entangled via full EC (no layer-local rule)")
    w("  Frequencies: neg ~ digits 76-80 (fine); add/double ~ digit 1 (coarse)")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Automorphisms = product operators on (X,F):")
    w("    neg=(id, reflect)   GLV=(beta-mul, id)")
    w("  Generic schedules entangle both layers.")
    w("  Right metric: layer RULES, not repeated combined Delta.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        fields = list(all_csv[0].keys()) if all_csv else []
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        wr.writerows(all_csv)
    print(f"Wrote {OUT}")
    print(f"Wrote {CSV_OUT}")


if __name__ == "__main__":
    main()
