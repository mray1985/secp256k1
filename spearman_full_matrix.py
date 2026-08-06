#!/usr/bin/env python3
"""Full Spearman matrix: n, d, limbs (Px,Py,r,...), logs, q-ratios, F-features."""

from __future__ import annotations

import json
import math
from decimal import Decimal, getcontext
from pathlib import Path

from scan_log_ratio_cross_puzzle import load_rows, ln, spearman

getcontext().prec = 80
OUT = Path("logs/log_ratio_scan")


def main() -> None:
    rows = sorted(
        [
            r
            for r in load_rows()
            if r.d and r.Px and r.Py and r.Pmy and r.r and r.s and r.z is not None and r.Ry
        ],
        key=lambda r: r.n,
    )
    print("cohort", len(rows))

    limbs_i = {
        "Px": [r.Px for r in rows],
        "Py": [r.Py for r in rows],
        "Pmy": [r.Pmy for r in rows],
        "r": [r.r for r in rows],
        "s": [r.s for r in rows],
        "z": [r.z for r in rows],
        "Ry": [r.Ry for r in rows],
    }

    S: dict[str, list[float]] = {
        "n": [float(r.n) for r in rows],
        "d": [float(r.d) for r in rows],
        "log2d": [math.log2(r.d) for r in rows],
    }
    for name, vals in limbs_i.items():
        S[name] = [float(v) for v in vals]
        S[f"log_{name}"] = [math.log(v) for v in vals]

    pairs = [
        ("Px", "Py"),
        ("Py", "Px"),
        ("Px", "r"),
        ("Py", "r"),
        ("Px", "z"),
        ("Py", "z"),
        ("Px", "s"),
        ("Py", "s"),
        ("r", "s"),
        ("Px", "Ry"),
        ("Py", "Ry"),
        ("Px", "Pmy"),
        ("Py", "Pmy"),
    ]
    for a, b in pairs:
        qs: list[float] = []
        Fs: list[float] = []
        for i, r in enumerate(rows):
            q = float(ln(limbs_i[a][i]) / ln(limbs_i[b][i]))
            F = float(Decimal(r.d) * ln(limbs_i[a][i]) / ln(limbs_i[b][i]))
            qs.append(q)
            Fs.append(F)
        S[f"q_{a}_{b}"] = qs
        S[f"F_{a}_{b}"] = Fs

    names = list(S.keys())
    mat: dict[str, dict[str, float | None]] = {a: {} for a in names}
    for i, a in enumerate(names):
        for b in names[i:]:
            rho = spearman(S[a], S[b])
            mat[a][b] = rho
            mat[b][a] = rho

    core = ["n", "d", "log2d", "Px", "Py", "Pmy", "r", "s", "z", "Ry"]
    print("\nSpearman core (raw limbs + scalars):")
    print(f"{'':>8}" + "".join(f"{c:>8}" for c in core))
    for a in core:
        print(f"{a:>8}" + "".join(f"{mat[a][b]:+8.3f}" for b in core))

    print("\nlog(limb) vs n / log2d / d:")
    for a in [f"log_{x}" for x in ["Px", "Py", "Pmy", "r", "s", "z", "Ry"]]:
        print(
            f"  {a:10}  n={mat[a]['n']:+.4f}  log2d={mat[a]['log2d']:+.4f}  "
            f"d={mat[a]['d']:+.4f}"
        )

    print("\nStrongest |Spearman| among raw limbs:")
    limbs_only = ["Px", "Py", "Pmy", "r", "s", "z", "Ry"]
    ranked = []
    for i, a in enumerate(limbs_only):
        for b in limbs_only[i + 1 :]:
            ranked.append((abs(mat[a][b] or 0.0), mat[a][b], a, b))
    ranked.sort(reverse=True)
    for _, rho, a, b in ranked:
        print(f"  {a:4} vs {b:4}: {rho:+.4f}")

    print("\nq-ratios vs n / log2d (scale-free):")
    for a, b in pairs:
        k = f"q_{a}_{b}"
        print(f"  {k:16}  n={mat[k]['n']:+.4f}  log2d={mat[k]['log2d']:+.4f}")

    print("\nF-features vs n / log2d / d:")
    for a, b in pairs:
        k = f"F_{a}_{b}"
        print(
            f"  {k:16}  n={mat[k]['n']:+.4f}  log2d={mat[k]['log2d']:+.4f}  "
            f"d={mat[k]['d']:+.4f}"
        )

    # Rx note: in this catalog Rx == r (x of R)
    note = (
        "Rx is not a separate column in the cohort cache; ECDSA r is the x-coordinate "
        "of R=[k]G (affine), so 'r' is Rx. Ry is recovered when k is known."
    )
    print("\n" + note)

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "spearman_full_matrix.json"
    path.write_text(
        json.dumps(
            {
                "cohort": len(rows),
                "note_Rx": note,
                "variables": names,
                "matrix": {a: {b: mat[a][b] for b in names} for a in names},
                "core_order": core,
                "strongest_limb_pairs": [
                    {"a": a, "b": b, "spearman": rho} for _, rho, a, b in ranked
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
