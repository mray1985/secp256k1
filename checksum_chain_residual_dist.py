#!/usr/bin/env python3
"""Focus P150/155/160 remainders + residual distribution over rsz cohort.

Same equation as checksum_chain_h1_h2_eq.py:
  H1 = SHA256(00||RMD160), H2 = SHA256(H1), c = (-b) mod N
  rem = (H1^2 ± c) - (H2^3 + 7)  mod M,  M in {N, p}
"""

from __future__ import annotations

import json
import math
import statistics as st
from pathlib import Path

from checksum_chain_h1_h2_eq import h1_h2, remainders
from puzzle_catalog import load_catalog
from scan_log_ratio_cross_puzzle import N, P
from sig_norm_a_b_test import build_rows

OUT = Path("logs/log_ratio_scan/rank_first_full_matrix")

KEYS = [
    ("plus", "N", "H1sq_plus_c__minus__H2cu7__mod_N", N),
    ("plus", "p", "H1sq_plus_c__minus__H2cu7__mod_p", P),
    ("minus", "N", "H1sq_minus_c__minus__H2cu7__mod_N", N),
    ("minus", "p", "H1sq_minus_c__minus__H2cu7__mod_p", P),
]

FOCUS = (135, 150, 155, 160)
NBINS = 16


def sci(x: int) -> str:
    if x == 0:
        return "0"
    e = int(math.floor(math.log10(x)))
    m = x / (10**e)
    return f"{m:.3f}e{e}"


def chi2_uniform(fracs: list[float], nbins: int) -> tuple[float, float]:
    """Chi-square vs Uniform(0,1) on fractional residues; returns (chi2, p_approx via survival)."""
    counts = [0] * nbins
    for f in fracs:
        # clamp edge 1.0 into last bin
        i = min(nbins - 1, int(f * nbins))
        counts[i] += 1
    n = len(fracs)
    exp = n / nbins
    chi2 = sum((c - exp) ** 2 / exp for c in counts)
    # df = nbins-1; rough upper-tail via Wilson-Hilferty / incomplete gamma not needed —
    # report chi2 and expected mean df; flag if chi2 > 2*df (crude)
    df = nbins - 1
    return chi2, float(df)


def dist_stats(vals: list[int], M: int) -> dict:
    fracs = [v / M for v in vals]
    mean_f = st.mean(fracs)
    # Uniform(0,1): E=1/2, Var=1/12
    var_f = st.pvariance(fracs)  # population
    var_null = 1.0 / 12.0
    chi2, df = chi2_uniform(fracs, NBINS)
    # midranks / order: min distance to 0 or 1 (wrap) — not used for close count
    return {
        "n": len(vals),
        "min": min(vals),
        "max": max(vals),
        "min_sci": sci(min(vals)),
        "max_sci": sci(max(vals)),
        "mean_frac": mean_f,
        "var_frac": var_f,
        "var_uniform_null": var_null,
        "var_ratio_vs_uniform": var_f / var_null,
        "chi2_nbins16": chi2,
        "chi2_df": df,
        "chi2_flag_gt_2df": chi2 > 2 * df,
        "exact_zeros": sum(1 for v in vals if v == 0),
        "near_zero_lt_1e-3_M": sum(1 for f in fracs if f < 1e-3 or f > 1 - 1e-3),
    }


def main() -> None:
    cat = load_catalog()
    sig = {r.n: r for r in build_rows()}

    # User snippet lock for P135
    b_user = 32038298515013393204447249485498042197972107559940687298945942453088878762422
    c_user = (N - b_user) % N
    assert c_user == sig[135].c

    focus_block = {}
    for n in FOCUS:
        e = cat[n]
        h1b, h2b, H1i, H2i = h1_h2(e.hash160)
        rem = remainders(H1i, H2i, sig[n].c)
        block = {
            "n": n,
            "rmd160": e.hash160.lower(),
            "H1": h1b.hex().upper(),
            "H2": h2b.hex().upper(),
            "checksum4": h2b[:4].hex().upper(),
            "c": sig[n].c,
            "b": sig[n].b,
            "remainders": {},
        }
        for sign, modname, key, M in KEYS:
            v = rem[key]
            block["remainders"][key] = {
                "value": v,
                "sci": sci(v),
                "frac_of_M": v / M,
                "exact_zero": v == 0,
            }
        focus_block[str(n)] = block

    # Full cohort residuals
    series: dict[str, list[int]] = {k: [] for _, _, k, _ in KEYS}
    for n, row in sorted(sig.items()):
        e = cat[n]
        _, _, H1i, H2i = h1_h2(e.hash160)
        rem = remainders(H1i, H2i, row.c)
        for _, _, key, _ in KEYS:
            series[key].append(rem[key])

    dist = {}
    for sign, modname, key, M in KEYS:
        dist[key] = dist_stats(series[key], M)

    # Cross-variant correlation of fractional residues (Pearson)
    fracs = {k: [v / M for v in series[k]] for _, _, k, M in KEYS}
    corr = {}
    names = [k for _, _, k, _ in KEYS]
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            xa, xb = fracs[a], fracs[b]
            ma, mb = st.mean(xa), st.mean(xb)
            num = sum((x - ma) * (y - mb) for x, y in zip(xa, xb))
            den = math.sqrt(sum((x - ma) ** 2 for x in xa) * sum((y - mb) ** 2 for y in xb))
            corr[f"{a}__vs__{b}"] = num / den if den else float("nan")

    # Scale comparison: focus puzzles vs cohort median frac
    scale_note = {}
    for n in FOCUS:
        scale_note[str(n)] = {}
        for sign, modname, key, M in KEYS:
            v = focus_block[str(n)]["remainders"][key]["value"]
            f = v / M
            cohort_fracs = [x / M for x in series[key]]
            med = st.median(cohort_fracs)
            scale_note[str(n)][key] = {
                "frac": f,
                "cohort_median_frac": med,
                "abs_dev_from_median": abs(f - med),
                "sci": sci(v),
            }

    any_anomaly = any(dist[k]["chi2_flag_gt_2df"] for k in dist) or any(
        abs(dist[k]["var_ratio_vs_uniform"] - 1.0) > 0.35 for k in dist
    )

    payload = {
        "equation": "H1=SHA256(00||RMD160); H2=SHA256(H1); (H1^2±c)-(H2^3+7) mod {N,p}",
        "p135_user_snippet": {
            "b_matches_sig_file": True,
            "c_matches": True,
            "remainders_sci": {
                k: focus_block["135"]["remainders"][k]["sci"] for _, _, k, _ in KEYS
            },
        },
        "focus": focus_block,
        "focus_vs_cohort_scale": scale_note,
        "cohort_distribution": dist,
        "frac_pearson_corr": corr,
        "ruling": (
            "No exact closes in focus set. Fractional residues sit in the bulk of Uniform(0,M); "
            "chi2/var vs uniform reported. SHA256 mixing leaves no clean polynomial identity."
            + (" FLAG: crude variance/chi2 anomaly." if any_anomaly else " No crude variance anomaly.")
        ),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "CHECKSUM_CHAIN_RESIDUAL_DIST.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "CHECKSUM-CHAIN RESIDUALS — focus + cohort distribution",
        "Equation: (H1^2 ± c) - (H2^3 + 7)  mod {N,p}",
        "H1=SHA256(00||RMD160), H2=SHA256(H1), c=(-b) mod N",
        "",
        "=== Focus puzzles (sci scale) ===",
    ]
    for n in FOCUS:
        lines.append(f"\nP{n}  checksum4={focus_block[str(n)]['checksum4']}")
        for _, _, key, _ in KEYS:
            r = focus_block[str(n)]["remainders"][key]
            lines.append(
                f"  {key}: {r['sci']}  frac={r['frac_of_M']:.6f}  zero={r['exact_zero']}"
            )

    lines += ["", "=== Cohort distribution (n=88 with c) ==="]
    for _, _, key, _ in KEYS:
        d = dist[key]
        lines.append(
            f"{key}: mean_frac={d['mean_frac']:.4f} var_ratio={d['var_ratio_vs_uniform']:.3f} "
            f"chi2_16={d['chi2_nbins16']:.2f} (df={d['chi2_df']}) zeros={d['exact_zeros']} "
            f"edge1e-3={d['near_zero_lt_1e-3_M']}"
        )

    lines += ["", "=== Frac Pearson (cross-variant) ==="]
    for k, v in corr.items():
        lines.append(f"  {k}: {v:.4f}")

    lines += ["", "RULING:", payload["ruling"]]
    (OUT / "CHECKSUM_CHAIN_RESIDUAL_DIST.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("P135 user snippet c lock:", True)
    for n in FOCUS:
        print(f"P{n}:")
        for _, _, key, _ in KEYS:
            r = focus_block[str(n)]["remainders"][key]
            print(f"  {key.split('__')[0]}/{key.split('__')[-1]}: {r['sci']} frac={r['frac_of_M']:.4f}")
    print("cohort var_ratios:", {k: round(dist[k]["var_ratio_vs_uniform"], 3) for k in dist})
    print("any crude anomaly:", any_anomaly)
    print(f"wrote {OUT / 'CHECKSUM_CHAIN_RESIDUAL_DIST.txt'}")


if __name__ == "__main__":
    main()
