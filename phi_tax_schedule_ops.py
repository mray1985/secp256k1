#!/usr/bin/env python3
"""
Tax = scalar operation schedule (not r*=p/y-2 correlation).

  gross d, adjustment tau, net d' = (d + tau) mod N
  (or d' = op(d) for double / GLV / neg)

  Delta_+ = Phi_+(d'G) - Phi_+(dG)
  Delta_- = Phi_-(d'G) - Phi_-(dG)

Exact Fraction throughout. No float64 for p,y,Phi,residuals.
"""
from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from decimal import Decimal, getcontext, ROUND_DOWN
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_TAX_SCHEDULE_OPS.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\phi_tax_schedule_ops.csv")
KEYS = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
MATRIX = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_scalar_deltas.csv")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LAMBDA = 0x5363AD4CC05C30E0A5261C028812645A122E22EA20816678DF02967C1B23BD72
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE

getcontext().prec = 400
getcontext().rounding = ROUND_DOWN
G = SECP256k1.generator


def phi_plus(x: int, y: int) -> Fraction:
    return Fraction(x, P) + Fraction(y, P * P)


def phi_minus(x: int, y: int) -> Fraction:
    return Fraction(x, P) - Fraction(y, P * P)


def point(d: int) -> tuple[int, int]:
    d = d % N
    if d == 0:
        raise ValueError("infinity")
    pt = d * G
    return int(pt.x()), int(pt.y())


def first_diff_digit(a: Fraction, b: Fraction, places: int = 160) -> int | None:
    da = Decimal(a.numerator) / Decimal(a.denominator)
    db = Decimal(b.numerator) / Decimal(b.denominator)
    qa = da.quantize(Decimal(1).scaleb(-places), rounding=ROUND_DOWN)
    qb = db.quantize(Decimal(1).scaleb(-places), rounding=ROUND_DOWN)
    sa = format(qa, "f").split(".", 1)[1][:places]
    sb = format(qb, "f").split(".", 1)[1][:places]
    for i, (ca, cb) in enumerate(zip(sa, sb), start=1):
        if ca != cb:
            return i
    return None


def load_keys() -> dict[int, int]:
    out: dict[int, int] = {}
    with KEYS.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pn = int(r["puzzle"])
            if pn == 135:
                continue
            raw = r["private_key"].strip()
            d = int(raw, 16) if any(c in raw.lower() for c in "abcdef") else int(raw)
            d %= N
            if d:
                out[pn] = d
    return out


def classify_matrix_edge(d0: int, d1: int, classic: str, affine: str) -> tuple[str, int]:
    """Return (family, tau) with tau = (d1 - d0) mod N in signed sense for add."""
    tau = (d1 - d0) % N
    if tau > N // 2:
        tau_signed = tau - N
    else:
        tau_signed = tau

    # exact op detection (preferred over CSV labels)
    if d1 % N == (-d0) % N:
        return "negation", 0
    if d1 % N == (LAMBDA * d0) % N:
        return "glv_lambda", 0
    if d1 % N == (2 * d0) % N:
        return "double", 0
    if d1 % N == (2 * d0 + 1) % N:
        return "double_and_add_+1", 1
    if d1 % N == (2 * d0 - 1) % N:
        return "double_and_add_-1", -1
    if classic:
        # e.g. 1d+1
        for label in classic.split("|"):
            label = label.strip()
            if label == "1d+1":
                return "add_constant", 1
            if label == "1d-1":
                return "add_constant", -1
            if label == "2d+0" or label == "2d0":
                return "double", 0
            if label.startswith("2d"):
                return "double_and_add_labeled", tau_signed
    # affine a,b head
    if affine:
        a_s, b_s = affine.split(";")[0].split(",")
        a, b = int(a_s), int(b_s)
        if a == 1:
            return "add_constant", b
        if a == 2:
            return "double_and_add_affine", b
        if a == 0:
            return "replace_constant", b  # d' = b
        return f"affine_a{a}", b
    return "matrix_unlabeled_add", tau_signed


def edge_record(
    family: str,
    d: int,
    d_net: int,
    tau: int,
    label: str,
) -> dict:
    x, y = point(d)
    xn, yn = point(d_net)
    pp, pm = phi_plus(x, y), phi_minus(x, y)
    ppn, pmn = phi_plus(xn, yn), phi_minus(xn, yn)
    dp, dm = ppn - pp, pmn - pm
    # layer reads
    X, Fine = Fraction(x, P), Fraction(y, P * P)
    Xn, Fine_n = Fraction(xn, P), Fraction(yn, P * P)
    return {
        "family": family,
        "label": label,
        "d": d,
        "d_net": d_net,
        "tau": tau,
        "Delta_plus": dp,
        "Delta_minus": dm,
        "X": X,
        "Xn": Xn,
        "Fine": Fine,
        "Fine_n": Fine_n,
        "dX": Xn - X,
        "dFine": Fine_n - Fine,
        "first_diff_Phi_plus": first_diff_digit(pp, ppn),
        "y_parity_flip": (y % 2) != (yn % 2),
        "same_x": x == xn,
        # algebraic markers
        "is_neg_residual": dp == Fraction(P - 2 * y, P * P) and same_x_check(x, xn),
        "is_glv_same_fine": Fine_n == Fine and x != xn,
    }


def same_x_check(x: int, xn: int) -> bool:
    return x == xn


def summarize_family(name: str, rows: list[dict], w) -> None:
    n = len(rows)
    if n == 0:
        return
    uniq_p = len({r["Delta_plus"] for r in rows})
    uniq_m = len({r["Delta_minus"] for r in rows})
    uniq_dF = len({r["dFine"] for r in rows})
    uniq_dX = len({r["dX"] for r in rows})
    diffs = [r["first_diff_Phi_plus"] for r in rows if r["first_diff_Phi_plus"] is not None]
    in_7578 = sum(1 for d in diffs if 75 <= d <= 78)
    early = sum(1 for d in diffs if d is not None and d < 75)
    parity_flips = sum(1 for r in rows if r["y_parity_flip"])
    same_x = sum(1 for r in rows if r["same_x"])
    glv_fine = sum(1 for r in rows if r["is_glv_same_fine"])
    neg_res = sum(1 for r in rows if r["is_neg_residual"])

    w(f"  [{name}] n={n}")
    w(f"    unique Delta_+ : {uniq_p}/{n}  (repeated exact residual if uniq << n)")
    w(f"    unique Delta_- : {uniq_m}/{n}")
    w(f"    unique dFine   : {uniq_dF}/{n}")
    w(f"    unique dX      : {uniq_dX}/{n}")
    if diffs:
        diffs_s = sorted(diffs)
        w(
            f"    first-diff Phi_+ digits: min={diffs_s[0]} med={diffs_s[len(diffs_s)//2]} "
            f"max={diffs_s[-1]}  in[75,78]={in_7578}/{len(diffs)}  early<75={early}/{len(diffs)}"
        )
    w(f"    same x: {same_x}/{n}  y-parity flip: {parity_flips}/{n}")
    w(f"    marker neg-residual form: {neg_res}/{n}  GLV-same-Fine: {glv_fine}/{n}")
    # entropy proxy
    w(f"    residual entropy proxy unique/n: Delta_+={uniq_p/n:.3f}  Delta_-={uniq_m/n:.3f}")
    w()


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("TAX AS OPERATION SCHEDULE  (not corr(d, p/y-2))")
    w("=" * 88)
    w("  gross d -> tau / op -> net d'")
    w("  Delta_+/- on signed Phi layers, exact Fraction")
    w()
    w("  CORRECTION: prior r*=p/y-2 vs d Pearson test is closed as off-target.")
    w()

    keys = load_keys()
    by_family: dict[str, list[dict]] = defaultdict(list)
    csv_rows: list[dict] = []

    # ----- A) Synthetic schedules on small walk -----
    w("-" * 88)
    w("A) Synthetic schedules on d=1..48 (controlled families)")
    w("-" * 88)

    def add_edge(fam: str, d: int, d_net: int, tau: int, label: str) -> None:
        if d % N == 0 or d_net % N == 0:
            return
        rec = edge_record(fam, d % N, d_net % N, tau, label)
        by_family[fam].append(rec)
        csv_rows.append(
            {
                "family": fam,
                "label": label,
                "d": str(d),
                "d_net": str(d_net),
                "tau": str(tau),
                "Delta_plus_num": str(rec["Delta_plus"].numerator),
                "Delta_plus_den": str(rec["Delta_plus"].denominator),
                "Delta_minus_num": str(rec["Delta_minus"].numerator),
                "Delta_minus_den": str(rec["Delta_minus"].denominator),
                "first_diff_Phi_plus": rec["first_diff_Phi_plus"],
                "same_x": rec["same_x"],
                "y_parity_flip": rec["y_parity_flip"],
            }
        )

    for d in range(1, 49):
        add_edge("add_constant_+1", d, d + 1, 1, "d->d+1")
        add_edge("double", d, 2 * d, 0, "d->2d")
        add_edge("double_and_add_+1", d, 2 * d + 1, 1, "d->2d+1")
        add_edge("negation", d, (-d) % N, 0, "d->-d")
        add_edge("glv_lambda", d, (LAMBDA * d) % N, 0, "d->lambda*d")

    for fam in (
        "add_constant_+1",
        "double",
        "double_and_add_+1",
        "negation",
        "glv_lambda",
    ):
        summarize_family(fam, by_family[fam], w)

    # ----- B) Matrix edges from factoradic CSV -----
    w("-" * 88)
    w("B) Matrix edges (factoradic_scalar_deltas.csv) labeled by op family")
    w("-" * 88)
    matrix_fams: dict[str, list[dict]] = defaultdict(list)
    if MATRIX.exists():
        with MATRIX.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                n0, n1 = int(row["n0"]), int(row["n1"])
                if n0 not in keys or n1 not in keys:
                    continue
                if n0 == 135 or n1 == 135:
                    continue
                d0, d1 = keys[n0], keys[n1]
                fam, tau = classify_matrix_edge(
                    d0, d1, row.get("classic") or "", row.get("affine") or ""
                )
                # use add form d' = d+tau for unlabeled; else exact d1
                rec = edge_record(fam, d0, d1, tau, f"puzzle {n0}->{n1}")
                matrix_fams[fam].append(rec)
                by_family[f"matrix::{fam}"].append(rec)
                csv_rows.append(
                    {
                        "family": f"matrix::{fam}",
                        "label": f"{n0}->{n1}",
                        "d": str(d0),
                        "d_net": str(d1),
                        "tau": str(tau),
                        "Delta_plus_num": str(rec["Delta_plus"].numerator),
                        "Delta_plus_den": str(rec["Delta_plus"].denominator),
                        "Delta_minus_num": str(rec["Delta_minus"].numerator),
                        "Delta_minus_den": str(rec["Delta_minus"].denominator),
                        "first_diff_Phi_plus": rec["first_diff_Phi_plus"],
                        "same_x": rec["same_x"],
                        "y_parity_flip": rec["y_parity_flip"],
                    }
                )
        for fam in sorted(matrix_fams):
            summarize_family(f"matrix::{fam}", matrix_fams[fam], w)
    else:
        w("  matrix CSV missing")
    w()

    # ----- C) Factoradic lead-carry schedule (plateau lead da * k!) -----
    w("-" * 88)
    w("C) Factoradic lead-carry: within max_k plateau, tau = (a1-a0)*k!")
    w("-" * 88)

    def to_fac(n: int) -> list[int]:
        digs: list[int] = []
        i = 1
        x = abs(int(n))
        while x:
            digs.append(x % i)
            x //= i
            i += 1
        return digs

    def max_k(d: int) -> int:
        digs = to_fac(d)
        return len(digs) - 1 if digs else 0

    by_k: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for pn, d in keys.items():
        by_k[max_k(d)].append((pn, d))
    lead_rows: list[dict] = []
    for k, grp in sorted(by_k.items()):
        grp = sorted(grp)
        if len(grp) < 2 or k < 2:
            continue
        fk = math.factorial(k)
        for i in range(1, len(grp)):
            n0, d0 = grp[i - 1]
            n1, d1 = grp[i]
            fac0, fac1 = to_fac(d0), to_fac(d1)
            if len(fac0) <= k or len(fac1) <= k:
                continue
            da = fac1[k] - fac0[k]
            if da == 0:
                continue
            tau = da * fk
            # lead-only net (not always equal to d1 — remainder also moves)
            d_lead = (d0 + tau) % N
            rec_lead = edge_record("factoradic_lead_tau", d0, d_lead, tau, f"lead {n0}->{n1} k={k}")
            rec_full = edge_record("factoradic_plateau_full", d0, d1, (d1 - d0) % N, f"full {n0}->{n1}")
            lead_rows.append(rec_lead)
            by_family["factoradic_lead_tau"].append(rec_lead)
            by_family["factoradic_plateau_full"].append(rec_full)
    summarize_family("factoradic_lead_tau", by_family["factoradic_lead_tau"], w)
    summarize_family("factoradic_plateau_full", by_family["factoradic_plateau_full"], w)

    # ----- D) Holdout: synthetic add/double on solved >100 -----
    w("-" * 88)
    w("D) Holdout solved puzzles>100: same synthetic ops (skip 135)")
    w("-" * 88)
    hold = [(pn, d) for pn, d in keys.items() if pn > 100]
    hold_fams: dict[str, list[dict]] = defaultdict(list)
    for pn, d in hold:
        for fam, d_net, tau, lab in (
            ("hold_add_+1", (d + 1) % N, 1, f"p{pn}+1"),
            ("hold_double", (2 * d) % N, 0, f"p{pn}*2"),
            ("hold_neg", (-d) % N, 0, f"p{pn} neg"),
            ("hold_glv", (LAMBDA * d) % N, 0, f"p{pn} lam"),
        ):
            if d_net == 0:
                continue
            rec = edge_record(fam, d, d_net, tau, lab)
            hold_fams[fam].append(rec)
    for fam in sorted(hold_fams):
        summarize_family(fam, hold_fams[fam], w)

    # ----- E) What repeated residual would look like -----
    w("-" * 88)
    w("E) Interpretation")
    w("-" * 88)
    w("  add_constant_+1: Delta_+ almost all unique — no single repeated Phi residual")
    w("    (expected: +G is nonlinear on (x,y); tax schedule is scalar-linear only)")
    w("  negation: same x; Delta_+ = (p-2y)/p^2 family — formula-repeated, value-unique")
    w("  glv_lambda: Fine invariant (dFine=0); dX from beta*x wrap — orbit schedule")
    w("  matrix edges: mostly large unique tau adds — residual entropy ~1")
    w("  factoradic lead_tau: tests carry path on lead only; full plateau moves rem too")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Tax reframed as op: d --tau/op--> d' with Phi+/- deltas. Prior r* corr closed.")
    w("  Exact Fraction used; no float for residuals.")
    w("  Negation / GLV show structured residual FAMILIES (not one constant Delta).")
    w("  Add/double/matrix-add show high unique Delta_+ (no cheap repeated Phi tax stamp).")
    w("  Next: if a matrix schedule has low unique/n, that family is the candidate.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "family",
            "label",
            "d",
            "d_net",
            "tau",
            "Delta_plus_num",
            "Delta_plus_den",
            "Delta_minus_num",
            "Delta_minus_den",
            "first_diff_Phi_plus",
            "same_x",
            "y_parity_flip",
        ]
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        for r in csv_rows:
            wr.writerow(r)
    print(f"Wrote {OUT}")
    print(f"Wrote {CSV_OUT}")


if __name__ == "__main__":
    main()
