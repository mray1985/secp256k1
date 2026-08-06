#!/usr/bin/env python3
"""Unreduced curve ledger + RMD160-centered rank accounting over puzzles 1..160.

Raw-value ledger (when pubkey known):
  Y = y^2
  X = x^3 + 7
  C = (X - Y) / p     exact integer
  X - Y - C*p = 0

Replace mod-p columns with:
  y2_full, x3plus7_full, p_carry

Linear-rank ledger:
  H_n = rmd160 linear rank over all 160
  For fields with only M available rows, stretch to 160-line:
    R^160 = 1 + (r - 1) * 159 / (M - 1)
  E_f(n) = R_f^160(n) - H_n

Spine: rows ordered by RMD160 rank.
h160 and address_payload share one ordering (count once).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from puzzle_catalog import load_catalog
from scan_log_ratio_cross_puzzle import load_rows, recover_xy_from_pubkey, P, spearman
from analyze_log_ratio_pearson import pearson

OUT = Path("logs/log_ratio_scan")


def ranks_for(values: dict[int, int | float]) -> dict[int, int]:
    """Ascending rank 1..M for present keys (average ties)."""
    items = sorted(values.items(), key=lambda kv: kv[1])
    out: dict[int, int] = {}
    i = 0
    n = len(items)
    while i < n:
        j = i
        while j + 1 < n and items[j + 1][1] == items[i][1]:
            j += 1
        # average rank of tied group, but user charts used dense 1..M unique mostly
        # use competition rank mid: average of (i+1)..(j+1)
        avg = (i + j) / 2.0 + 1.0
        # store as int if exact else float — for stretch use float ranks
        for k in range(i, j + 1):
            out[items[k][0]] = avg  # type: ignore
        i = j + 1
    return out  # type: ignore


def dense_ranks(values: dict[int, int | float]) -> dict[int, int]:
    """Unique ascending: 1 = smallest (stable by puzzle_n on ties)."""
    items = sorted(values.items(), key=lambda kv: (kv[1], kv[0]))
    return {pn: i for i, (pn, _) in enumerate(items, start=1)}


def stretch(r: float, m: int) -> float:
    """Map rank in 1..M onto 1..160 line."""
    if m <= 1:
        return 1.0
    return 1.0 + (r - 1.0) * 159.0 / (m - 1)


def main() -> None:
    cat = load_catalog()
    rsz = {r.n: r for r in load_rows()}

    # --- build per-puzzle raw fields ---
    rows: dict[int, dict] = {}
    for n in range(1, 161):
        e = cat[n]
        h160 = int(e.hash160, 16)
        rows[n] = {
            "puzzle_n": n,
            "rmd160": h160,
            "address": e.address,
            "d": e.private_key if e.private_key > 0 else None,
        }

        px = py = None
        if e.public_key:
            px, py = recover_xy_from_pubkey(e.public_key)
        rr = rsz.get(n)
        if px is None and rr and rr.Px:
            px, py = rr.Px, rr.Py

        if px is not None and py is not None:
            Y = py * py
            X = px * px * px + 7
            diff = X - Y
            if diff % P != 0:
                raise RuntimeError(f"P{n}: X-Y not divisible by p")
            C = diff // P
            rows[n].update(
                {
                    "Px": px,
                    "Py": py,
                    "neg_y": (-py) % P,
                    "Pmy": P - py,
                    "y2_full": Y,
                    "x3plus7_full": X,
                    "p_carry": C,
                    # keep mod-p for reference only (not spine)
                    "y2_mod_p": Y % P,
                    "x3_plus_7_mod_p": X % P,
                }
            )
            assert X - Y - C * P == 0

        if rr:
            rows[n]["r"] = rr.r
            rows[n]["s"] = rr.s
            rows[n]["z"] = rr.z
            rows[n]["Ry"] = rr.Ry

    # verify P135 carry against previously locked constant
    c135 = rows[135]["p_carry"]
    expected = int(
        "67486721255910183740991446335613708753681155265976913090529890301610"
        "16954248076489895037255118891744016671471702653958435380935561367662"
        "507549862547089"
    )
    assert c135 == expected, f"P135 carry mismatch:\n{c135}\n{expected}"

    # --- ranks ---
    # RMD160 spine over all 160
    h_rank = dense_ranks({n: rows[n]["rmd160"] for n in range(1, 161)})
    for n in range(1, 161):
        rows[n]["H"] = h_rank[n]  # 1..160

    # fields to rank (independent); pay omitted (same order as rmd160)
    rank_fields = [
        "d",
        "Px",
        "Py",
        "neg_y",
        "Pmy",
        "y2_full",
        "x3plus7_full",
        "p_carry",
        "r",
        "s",
        "z",
        "Ry",
    ]

    field_ranks: dict[str, dict[int, int]] = {}
    field_M: dict[str, int] = {}
    for f in rank_fields:
        vals = {n: rows[n][f] for n in range(1, 161) if rows[n].get(f) is not None}
        field_ranks[f] = dense_ranks(vals)
        field_M[f] = len(vals)
        for n, r in field_ranks[f].items():
            rows[n][f"r_{f}"] = r
            rows[n][f"R160_{f}"] = stretch(r, field_M[f])
            rows[n][f"E_{f}"] = rows[n][f"R160_{f}"] - rows[n]["H"]

    # also stretch H is already 1..160
    for n in range(1, 161):
        rows[n]["R160_rmd160"] = float(rows[n]["H"])
        rows[n]["E_rmd160"] = 0.0

    # --- fit weights: predict H from available R160 (only puzzles with all ECC limbs) ---
    # Use subset that has Px (curve account) + r,s,z when possible
    ecc_feats = ["Px", "Py", "neg_y", "y2_full", "x3plus7_full", "p_carry"]
    # puzzles with full curve account
    train = [n for n in range(1, 161) if all(rows[n].get(f) is not None for f in ecc_feats)]

    # Least-squares: H ≈ sum w_f R160_f, sum w = 1
    # Solve unconstrained then project, or use all but one free.
    # Simple: minimize ||A w - H|| with sum w=1 via last weight = 1 - sum others
    import numpy as np

    F = ecc_feats
    A_full = np.array([[rows[n][f"R160_{f}"] for f in F] for n in train], dtype=float)
    Hvec = np.array([rows[n]["H"] for n in train], dtype=float)
    # reduce: w[:-1] free, w[-1] = 1 - sum(w[:-1])
    # H ≈ A[:,:-1] w' + A[:,-1]*(1-sum w') = (A[:,:-1]-A[:,-1]) w' + A[:,-1]
    A_red = A_full[:, :-1] - A_full[:, -1:]
    target = Hvec - A_full[:, -1]
    w_free, *_ = np.linalg.lstsq(A_red, target, rcond=None)
    w = list(w_free) + [1.0 - float(sum(w_free))]
    w = [float(x) for x in w]

    for n in train:
        rows[n]["H_hat"] = sum(w[i] * rows[n][f"R160_{F[i]}"] for i in range(len(F)))
        rows[n]["B"] = rows[n]["H_hat"] - rows[n]["H"]  # prediction residual
        # also weighted E balance
        rows[n]["B_E"] = sum(w[i] * rows[n][f"E_{F[i]}"] for i in range(len(F)))

    # metrics
    resid = [rows[n]["B"] for n in train]
    mae = sum(abs(x) for x in resid) / len(resid)
    rmse = math.sqrt(sum(x * x for x in resid) / len(resid))
    sp = spearman([rows[n]["H_hat"] for n in train], [float(rows[n]["H"]) for n in train])
    pr = pearson([rows[n]["H_hat"] for n in train], [float(rows[n]["H"]) for n in train])

    # --- exports ---
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "rmd160_unreduced_ledger"
    dest.mkdir(parents=True, exist_ok=True)

    # JSON dump of raw ledger
    raw_out = []
    for n in range(1, 161):
        r = rows[n]
        entry = {
            "puzzle_n": n,
            "H_rmd160_rank": r["H"],
            "rmd160": r["rmd160"],
            "address": r["address"],
            "d": r.get("d"),
        }
        for f in [
            "Px",
            "Py",
            "neg_y",
            "y2_full",
            "x3plus7_full",
            "p_carry",
            "r",
            "s",
            "z",
            "Ry",
        ]:
            if r.get(f) is not None:
                entry[f] = r[f]
                if f"r_{f}" in r:
                    entry[f"r_{f}"] = r[f"r_{f}"]
                    entry[f"R160_{f}"] = r[f"R160_{f}"]
                    entry[f"E_{f}"] = r[f"E_{f}"]
        if "H_hat" in r:
            entry["H_hat"] = r["H_hat"]
            entry["B"] = r["B"]
            entry["B_E"] = r["B_E"]
        if r.get("y2_full") is not None:
            entry["ledger_check_X_minus_Y_minus_Cp"] = (
                r["x3plus7_full"] - r["y2_full"] - r["p_carry"] * P
            )
        raw_out.append(entry)

    (dest / "ledger.json").write_text(
        json.dumps(
            {
                "p": P,
                "notes": {
                    "raw": "X=x^3+7, Y=y^2, C=(X-Y)/p; X-Y-Cp=0",
                    "replaced": "y2_mod_p/x3_plus_7_mod_p -> y2_full/x3plus7_full/p_carry",
                    "spine": "rows ordered by RMD160 rank H=1..160",
                    "stretch": "R160=1+(r-1)*159/(M-1) for M-row fields",
                    "E": "E_f = R160_f - H",
                    "pay": "omitted as duplicate of rmd160 ordering",
                },
                "fit": {
                    "features": F,
                    "weights": dict(zip(F, w)),
                    "weights_sum": sum(w),
                    "train_n": len(train),
                    "mae_H": mae,
                    "rmse_H": rmse,
                    "spearman_Hhat_H": sp,
                    "pearson_Hhat_H": pr,
                },
                "p135_p_carry_verified": True,
                "rows": raw_out,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    # Chart: rows by H ascending; columns = ranks, R160, E, and raw C/X/Y when present
    chart_fields = [
        "Px",
        "Py",
        "neg_y",
        "y2_full",
        "x3plus7_full",
        "p_carry",
        "r",
        "s",
        "z",
        "Ry",
        "d",
    ]

    # CSV wide
    headers = ["puzzle_n", "H", "rmd160"]
    for f in chart_fields:
        headers += [f"r_{f}", f"R160_{f}", f"E_{f}"]
    headers += ["y2_full", "x3plus7_full", "p_carry", "H_hat", "B", "B_E"]

    ordered = sorted(range(1, 161), key=lambda n: rows[n]["H"])
    csv_path = dest / "CHART_BY_RMD160.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(",".join(headers) + "\n")
        for n in ordered:
            r = rows[n]
            cells = [str(n), str(r["H"]), str(r["rmd160"])]
            for f in chart_fields:
                cells.append("" if f"r_{f}" not in r else str(r[f"r_{f}"]))
                cells.append("" if f"R160_{f}" not in r else f"{r[f'R160_{f}']:.6f}")
                cells.append("" if f"E_{f}" not in r else f"{r[f'E_{f}']:.6f}")
            for f in ["y2_full", "x3plus7_full", "p_carry"]:
                cells.append("" if r.get(f) is None else str(r[f]))
            cells.append("" if "H_hat" not in r else f"{r['H_hat']:.6f}")
            cells.append("" if "B" not in r else f"{r['B']:.6f}")
            cells.append("" if "B_E" not in r else f"{r['B_E']:.6f}")
            fh.write(",".join(cells) + "\n")

    # Fixed-width text spine
    lines = [
        "RMD160-SPINE CHART — unreduced curve ledger",
        "Rows: H = rmd160 linear rank 1..160",
        "Curve account: X=x^3+7, Y=y^2, C=(X-Y)/p  (NOT mod p)",
        "R160 = 1+(r-1)*159/(M-1);  E = R160 - H",
        f"Fit features {F}",
        f"weights={dict(zip(F, [round(x,6) for x in w]))}",
        f"train={len(train)}  MAE(H_hat-H)={mae:.4f}  RMSE={rmse:.4f}  spearman={sp:.4f}",
        "P135 p_carry verified against provided C_135",
        "",
    ]
    # compact header
    short = [
        ("n", 3),
        ("H", 3),
        ("rPx", 3),
        ("rPy", 3),
        ("r-y", 3),
        ("rY2", 3),
        ("rX3", 3),
        ("rC", 3),
        ("EPx", 6),
        ("EPy", 6),
        ("EY2", 6),
        ("EX3", 6),
        ("EC", 6),
        ("B", 7),
    ]
    lines.append(" ".join(h.rjust(w) for h, w in short))
    lines.append("-" * (sum(w for _, w in short) + len(short) - 1))

    def cell(v, w):
        if v is None or v == "":
            s = ""
        elif isinstance(v, float):
            s = f"{v:.2f}"
        else:
            s = str(v)
        return s[:w].rjust(w)

    for n in ordered:
        r = rows[n]
        vals = [
            n,
            r["H"],
            r.get("r_Px"),
            r.get("r_Py"),
            r.get("r_neg_y"),
            r.get("r_y2_full"),
            r.get("r_x3plus7_full"),
            r.get("r_p_carry"),
            r.get("E_Px"),
            r.get("E_Py"),
            r.get("E_y2_full"),
            r.get("E_x3plus7_full"),
            r.get("E_p_carry"),
            r.get("B"),
        ]
        lines.append(" ".join(cell(v, w) for v, (_, w) in zip(vals, short)))

    # sequences for new full-value fields
    lines.append("")
    lines.append("=" * 72)
    lines.append("puzzle_n sequences (value ascending) — unreduced")
    for f in ["y2_full", "x3plus7_full", "p_carry"]:
        seq = [
            str(pn)
            for pn, _ in sorted(
                ((n, rows[n][f]) for n in range(1, 161) if rows[n].get(f) is not None),
                key=lambda kv: kv[1],
            )
        ]
        lines.append("")
        lines.append(f)
        lines.append(",".join(seq))

    # per-puzzle raw ledger blocks for curve-known
    raw_txt = dest / "UNREDUCED_CURVE_LEDGER.txt"
    raw_lines = [
        "UNREDUCED CURVE LEDGER — all puzzles with pubkey",
        "X = x^3+7",
        "Y = y^2",
        "C = (X-Y)/p",
        "identity: X - Y - C*p = 0",
        "",
    ]
    for n in sorted(train):
        r = rows[n]
        raw_lines.append(f"=== puzzle {n}  H={r['H']} ===")
        raw_lines.append(f"Px={r['Px']}")
        raw_lines.append(f"Py={r['Py']}")
        raw_lines.append(f"Y=y2_full={r['y2_full']}")
        raw_lines.append(f"X=x3plus7_full={r['x3plus7_full']}")
        raw_lines.append(f"C=p_carry={r['p_carry']}")
        raw_lines.append(f"X-Y-C*p={r['x3plus7_full']-r['y2_full']-r['p_carry']*P}")
        raw_lines.append(
            f"ranks: Y={r['r_y2_full']} X={r['r_x3plus7_full']} C={r['r_p_carry']} "
            f"(distinct; ranking not additive)"
        )
        raw_lines.append("")
    raw_txt.write_text("\n".join(raw_lines), encoding="utf-8")

    chart_txt = dest / "CHART_BY_RMD160.txt"
    chart_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # summary md
    (dest / "README.md").write_text(
        "\n".join(
            [
                "# RMD160-spine unreduced curve ledger",
                "",
                "## Raw-value ledger",
                "",
                "$$x^3+7 = y^2 + C p$$",
                "",
                "Columns: `y2_full`, `x3plus7_full`, `p_carry` (not mod p).",
                "",
                f"Puzzles with curve account: **{len(train)}**. All satisfy `X-Y-Cp=0`.",
                f"P135 `p_carry` matches provided constant: **yes**.",
                "",
                "## Rank ledger",
                "",
                "Spine: RMD160 rank `H` over 160.",
                "Stretch: `R160 = 1+(r-1)*159/(M-1)`.",
                "`E_f = R160_f - H`.",
                "`pay` omitted (same order as rmd160).",
                "",
                f"Fit `H_hat = sum w_f R160_f` on {F}:",
                f"- weights: `{dict(zip(F, [round(x,6) for x in w]))}`",
                f"- MAE={mae:.4f}, RMSE={rmse:.4f}, Spearman={sp:.4f}",
                "",
                "Files:",
                "- `CHART_BY_RMD160.csv` / `.txt`",
                "- `UNREDUCED_CURVE_LEDGER.txt`",
                "- `ledger.json`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"curve puzzles: {len(train)}")
    print(f"P135 C verified: True")
    print(f"weights: {dict(zip(F, w))}")
    print(f"MAE={mae:.4f} RMSE={rmse:.4f} spearman={sp:.4f}")
    # show that y2 and x3 FULL ranks differ (unlike mod-p)
    same_yx = sum(
        1
        for n in train
        if rows[n]["r_y2_full"] == rows[n]["r_x3plus7_full"]
    )
    print(f"same rank y2_full vs x3plus7_full: {same_yx}/{len(train)}")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
