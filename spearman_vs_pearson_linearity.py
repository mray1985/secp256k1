#!/usr/bin/env python3
"""Spearman (order) vs Pearson (linearity) on the same limb cohort."""

from __future__ import annotations

import json
import math
from pathlib import Path

from analyze_log_ratio_pearson import pearson
from scan_log_ratio_cross_puzzle import load_rows, spearman

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
    core = ["n", "d", "log2d", "Px", "Py", "Pmy", "r", "s", "z", "Ry"]
    S: dict[str, list[float]] = {
        "n": [float(r.n) for r in rows],
        "d": [float(r.d) for r in rows],
        "log2d": [math.log2(r.d) for r in rows],
        "Px": [float(r.Px) for r in rows],
        "Py": [float(r.Py) for r in rows],
        "Pmy": [float(r.Pmy) for r in rows],
        "r": [float(r.r) for r in rows],
        "s": [float(r.s) for r in rows],
        "z": [float(r.z) for r in rows],
        "Ry": [float(r.Ry) for r in rows],
    }
    for x in ["Px", "Py", "Pmy", "r", "s", "z", "Ry"]:
        S[f"log_{x}"] = [math.log(v) for v in S[x]]

    print("cohort", len(rows))
    print()
    print("Pearson RAW (linearity in integer magnitude):")
    hdr = "".join(f"{c:>8}" for c in core)
    print(f"{'':>8}{hdr}")
    pear_raw = {a: {} for a in core}
    for a in core:
        row = []
        for b in core:
            v = pearson(S[a], S[b])
            pear_raw[a][b] = v
            row.append(f"{v:+8.3f}")
        print(f"{a:>8}{''.join(row)}")

    logs = ["n", "log2d"] + [f"log_{x}" for x in ["Px", "Py", "Pmy", "r", "s", "z", "Ry"]]
    print()
    print("Pearson LOG limbs (linearity in log-magnitude):")
    print(f"{'':>8}" + "".join(f"{c:>8}" for c in logs))
    pear_log = {a: {} for a in logs}
    for a in logs:
        row = []
        for b in logs:
            v = pearson(S[a], S[b])
            pear_log[a][b] = v
            row.append(f"{v:+8.3f}")
        print(f"{a:>8}{''.join(row)}")

    print()
    print("pair         Spear  Pear_raw Pear_log  reading")
    limbs = ["Px", "Py", "Pmy", "r", "s", "z", "Ry"]
    pairs = []
    for i, a in enumerate(limbs):
        for b in limbs[i + 1 :]:
            sp = spearman(S[a], S[b])
            pr = pearson(S[a], S[b])
            pl = pearson(S[f"log_{a}"], S[f"log_{b}"])
            if abs(sp) > 0.9:
                note = "algebraic/near-perfect order"
            elif abs(sp) < 0.2 and abs(pr) < 0.2:
                note = "no order, no line"
            elif abs(sp - pr) > 0.15:
                note = "order != linear scale"
            else:
                note = "weak/moderate both"
            pairs.append(
                {"a": a, "b": b, "spearman": sp, "pearson_raw": pr, "pearson_log": pl, "note": note}
            )
            print(f"{a}-{b:4}  {sp:+6.3f}  {pr:+7.3f}  {pl:+7.3f}  {note}")

    OUT.mkdir(parents=True, exist_ok=True)
    out = {
        "cohort": len(rows),
        "interpretation": {
            "spearman": "monotonic ORDER alignment (not geometric rotation on the curve)",
            "pearson_raw": "LINEAR association in raw integer values",
            "pearson_log": "LINEAR association in log-magnitudes",
            "rotation_note": (
                "A correlation matrix is pairwise alignment of scalars across puzzles, "
                "not elliptic-curve point rotation. 'Rotation' language here only means "
                "how one column co-varies with another in rank/linear space."
            ),
        },
        "pearson_raw_core": pear_raw,
        "pearson_log": {a: {b: pear_log[a][b] for b in logs} for a in logs},
        "limb_pairs": pairs,
    }
    path = OUT / "spearman_vs_pearson_linearity.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
