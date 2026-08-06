#!/usr/bin/env python3
"""Test locked branch: s/R ≈ 10 where R = (H1^2 + c - (H2^3+7)) mod N.

Fixed branch only (plus-c, mod-N). Full rsz cohort + Hamming anchors 135/150/155/160.
"""

from __future__ import annotations

import json
import math
import random
import statistics as st
from pathlib import Path

from checksum_chain_h1_h2_eq import h1_h2, remainders
from puzzle_catalog import load_catalog
from scan_log_ratio_cross_puzzle import N
from sig_norm_a_b_test import build_rows

OUT = Path("logs/log_ratio_scan/rank_first_full_matrix")
ANCHORS = (135, 150, 155, 160)
TARGET = 10.0

# closeness bands on |s/R - 10|
BANDS = (0.01, 0.05, 0.10, 0.25, 0.50, 1.0)


def R_plus_N(H1: int, H2: int, c: int) -> int:
    return remainders(H1, H2, c)["H1sq_plus_c__minus__H2cu7__mod_N"]


def metrics(s: int, R: int) -> dict:
    if R == 0:
        return {
            "R": 0,
            "s": s,
            "s_over_R": None,
            "tenR_over_s": None,
            "abs_s_over_R_minus_10": None,
            "rel_gap_pct_from_10R_over_s": None,
            "tenR_minus_s": None,
            "near_s_over_10": False,
        }
    s_over_R = s / R
    tenR_over_s = (10 * R) / s
    return {
        "R": R,
        "s": s,
        "s_over_R": s_over_R,
        "tenR_over_s": tenR_over_s,
        "abs_s_over_R_minus_10": abs(s_over_R - TARGET),
        "rel_gap_pct_from_10R_over_s": abs(tenR_over_s - 1.0) * 100.0,
        "tenR_minus_s": 10 * R - s,
        "near_s_over_10": abs(s_over_R - TARGET) < 0.1,  # within 10% of ratio 10
    }


def main() -> None:
    cat = load_catalog()
    rows = build_rows()
    sig = {r.n: r for r in rows}

    # --- P135 lock ---
    r135 = sig[135]
    _, _, H1, H2 = h1_h2(cat[135].hash160)
    R135 = R_plus_N(H1, H2, r135.c)
    m135 = metrics(r135.s, R135)
    expected_s = 15509729875763924304053419655647994379903175655107184284998698212653288468986
    expected_R = 1565200300425559749940371920518064216348400514642441815930434353217014888406
    lock = {
        "s_match": r135.s == expected_s,
        "R_match": R135 == expected_R,
        "tenR_minus_s": m135["tenR_minus_s"],
        "tenR_over_s": m135["tenR_over_s"],
        "s_over_R": m135["s_over_R"],
        "rel_gap_pct": m135["rel_gap_pct_from_10R_over_s"],
    }

    # --- all rows ---
    all_m = []
    for r in rows:
        _, _, H1i, H2i = h1_h2(cat[r.n].hash160)
        R = R_plus_N(H1i, H2i, r.c)
        m = metrics(r.s, R)
        m.update({"n": r.n, "wt": r.wt, "solved": r.solved, "anchor": r.n in ANCHORS})
        all_m.append(m)

    usable = [m for m in all_m if m["s_over_R"] is not None]
    ratios = [m["s_over_R"] for m in usable]
    abs_dev = [m["abs_s_over_R_minus_10"] for m in usable]
    rel_pct = [m["rel_gap_pct_from_10R_over_s"] for m in usable]

    band_counts = {
        f"abs_sR_minus_10_lt_{b}": sum(1 for d in abs_dev if d < b) for b in BANDS
    }
    band_counts["rel_gap_pct_lt_1"] = sum(1 for x in rel_pct if x < 1.0)
    band_counts["rel_gap_pct_lt_5"] = sum(1 for x in rel_pct if x < 5.0)
    band_counts["rel_gap_pct_lt_10"] = sum(1 for x in rel_pct if x < 10.0)

    # log10(|s/R|) distribution — P135 ~1
    log10_abs = [math.log10(abs(x)) if x != 0 else float("-inf") for x in ratios]

    # null: permute s against fixed R
    rng = random.Random(135)
    R_list = [m["R"] for m in usable]
    s_list = [m["s"] for m in usable]
    null_best = []
    null_p135_style = []  # count how often shuffled pair has rel_gap < P135's
    p135_gap = m135["rel_gap_pct_from_10R_over_s"]
    for _ in range(2000):
        ss = s_list[:]
        rng.shuffle(ss)
        gaps = []
        for s, R in zip(ss, R_list):
            if R == 0:
                continue
            gaps.append(abs((10 * R) / s - 1.0) * 100.0)
        null_best.append(min(gaps))
        null_p135_style.append(sum(1 for g in gaps if g <= p135_gap))

    # expected under uniform: s and R independent ~U(1,N) roughly — s/R has heavy tail;
    # report empirical null rate for rel_gap < 1%
    null_rate_lt_p135 = st.mean([c / len(usable) for c in null_p135_style])

    anchors = {str(m["n"]): m for m in all_m if m["n"] in ANCHORS}

    # wt-cohort around anchors: |wt - wt_anchor| <= 4
    wt_neighbors = {}
    for an in ANCHORS:
        aw = sig[an].wt
        neigh = [
            {
                "n": m["n"],
                "wt": m["wt"],
                "s_over_R": m["s_over_R"],
                "rel_gap_pct": m["rel_gap_pct_from_10R_over_s"],
                "abs_s_over_R_minus_10": m["abs_s_over_R_minus_10"],
            }
            for m in usable
            if abs(m["wt"] - aw) <= 4
        ]
        neigh.sort(key=lambda x: x["abs_s_over_R_minus_10"] or 1e99)
        wt_neighbors[str(an)] = {
            "anchor_wt": aw,
            "n_neighbors": len(neigh),
            "best5": neigh[:5],
            "n_rel_gap_lt_5pct": sum(1 for x in neigh if x["rel_gap_pct"] is not None and x["rel_gap_pct"] < 5),
            "n_rel_gap_lt_1pct": sum(1 for x in neigh if x["rel_gap_pct"] is not None and x["rel_gap_pct"] < 1),
        }

    # also check other three branches briefly for s/R~10 (falsify "only this branch")
    other_branch_hits = {"minus_N": 0, "plus_p": 0, "minus_p": 0}
    other_keys = {
        "minus_N": "H1sq_minus_c__minus__H2cu7__mod_N",
        "plus_p": "H1sq_plus_c__minus__H2cu7__mod_p",
        "minus_p": "H1sq_minus_c__minus__H2cu7__mod_p",
    }
    for r in rows:
        _, _, H1i, H2i = h1_h2(cat[r.n].hash160)
        rem = remainders(H1i, H2i, r.c)
        for name, key in other_keys.items():
            R = rem[key]
            if R and abs(r.s / R - 10) < 0.1:
                other_branch_hits[name] += 1

    payload = {
        "locked_branch": "R=(H1^2+c)-(H2^3+7) mod N; test s/R ≈ 10",
        "p135_lock": lock,
        "anchors": {
            k: {
                "n": v["n"],
                "wt": v["wt"],
                "s": v["s"],
                "R": v["R"],
                "s_over_R": v["s_over_R"],
                "tenR_over_s": v["tenR_over_s"],
                "rel_gap_pct": v["rel_gap_pct_from_10R_over_s"],
                "abs_s_over_R_minus_10": v["abs_s_over_R_minus_10"],
            }
            for k, v in anchors.items()
        },
        "cohort_n": len(usable),
        "cohort_s_over_R": {
            "min": min(ratios),
            "max": max(ratios),
            "median": st.median(ratios),
            "mean": st.mean(ratios),
            "median_abs_dev_from_10": st.median(abs_dev),
            "mean_abs_dev_from_10": st.mean(abs_dev),
            "median_rel_gap_pct": st.median(rel_pct),
            "best_rel_gap_pct": min(rel_pct),
            "best_n": min(usable, key=lambda m: m["rel_gap_pct_from_10R_over_s"])["n"],
            "p135_rank_by_rel_gap": sorted(rel_pct).index(p135_gap) + 1,
        },
        "band_counts": band_counts,
        "wt_neighbors": wt_neighbors,
        "null_shuffle_s_vs_R": {
            "trials": 2000,
            "mean_fraction_with_gap_le_p135": null_rate_lt_p135,
            "median_best_gap_pct_per_trial": st.median(null_best),
            "p135_gap_pct": p135_gap,
        },
        "other_branches_hits_abs_sR_minus_10_lt_0.1": other_branch_hits,
        "all_rows": [
            {
                "n": m["n"],
                "wt": m["wt"],
                "solved": m["solved"],
                "s_over_R": m["s_over_R"],
                "tenR_over_s": m["tenR_over_s"],
                "rel_gap_pct": m["rel_gap_pct_from_10R_over_s"],
                "abs_s_over_R_minus_10": m["abs_s_over_R_minus_10"],
                "R": m["R"],
                "s": m["s"],
            }
            for m in sorted(usable, key=lambda m: m["rel_gap_pct_from_10R_over_s"])
        ],
        "ruling": None,
    }

    n_close_1pct = band_counts["rel_gap_pct_lt_1"]
    n_close_5pct = band_counts["rel_gap_pct_lt_5"]
    anchors_close = [
        n
        for n in ANCHORS
        if anchors[str(n)]["rel_gap_pct_from_10R_over_s"] is not None
        and anchors[str(n)]["rel_gap_pct_from_10R_over_s"] < 5.0
    ]
    payload["ruling"] = (
        f"P135 locks s/R~{m135['s_over_R']:.6f} (gap {p135_gap:.4f}%). "
        f"Cohort: {n_close_1pct}/88 within 1% of 10R~s, {n_close_5pct}/88 within 5%. "
        f"Anchors 150/155/160 with gap<5%: {anchors_close}. "
        f"Shuffle null mean fraction <=P135-gap: {null_rate_lt_p135:.4f}. "
        + (
            "Fixed-branch s~10R does NOT generalize to Hamming anchors / cohort."
            if len(anchors_close) <= 1 and n_close_5pct < 5
            else "Some cohort hits near s~10R; check null rate before claiming structure."
        )
    )

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "S_OVER_R_NEAR_10.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "LOCKED BRANCH: R = (H1^2 + c) - (H2^3 + 7)  mod N",
        "TEST: s/R ~ 10   (equivalently 10R/s ~ 1)",
        "",
        "=== P135 lock ===",
        f"s match: {lock['s_match']}",
        f"R match: {lock['R_match']}",
        f"10R - s = {lock['tenR_minus_s']}",
        f"10R/s   = {lock['tenR_over_s']}",
        f"s/R     = {lock['s_over_R']}",
        f"rel gap = {lock['rel_gap_pct']:.10f}%",
        "",
        "=== Anchors ===",
    ]
    for n in ANCHORS:
        m = anchors[str(n)]
        lines.append(
            f"P{n} wt={m['wt']}: s/R={m['s_over_R']:.6f}  10R/s={m['tenR_over_s']:.6f}  "
            f"gap={m['rel_gap_pct_from_10R_over_s']:.4f}%"
        )

    lines += [
        "",
        f"=== Cohort (n={len(usable)}) ===",
        f"median s/R = {st.median(ratios):.6g}",
        f"median |s/R-10| = {st.median(abs_dev):.6g}",
        f"median rel gap % = {st.median(rel_pct):.4f}",
        f"best rel gap % = {min(rel_pct):.6f} (P{payload['cohort_s_over_R']['best_n']})",
        f"P135 rank by gap = {payload['cohort_s_over_R']['p135_rank_by_rel_gap']} / {len(usable)}",
        "",
        "band counts:",
    ]
    for k, v in band_counts.items():
        lines.append(f"  {k}: {v}")

    lines += [
        "",
        "=== Null (shuffle s vs R, 2000 trials) ===",
        f"P135 gap % = {p135_gap:.6f}",
        f"mean fraction of rows with gap <= P135: {null_rate_lt_p135:.6f}",
        f"median best-gap-per-trial %: {st.median(null_best):.6f}",
        "",
        "=== Other branches |s/R-10|<0.1 hits ===",
        str(other_branch_hits),
        "",
        "=== All rows by ascending rel gap ===",
    ]
    for m in sorted(usable, key=lambda x: x["rel_gap_pct_from_10R_over_s"])[:20]:
        lines.append(
            f"  P{m['n']:3d} wt={m['wt']:3d}  s/R={m['s_over_R']:12.6f}  gap={m['rel_gap_pct_from_10R_over_s']:10.4f}%"
        )
    lines.append("  ...")
    for m in sorted(usable, key=lambda x: x["rel_gap_pct_from_10R_over_s"])[-5:]:
        lines.append(
            f"  P{m['n']:3d} wt={m['wt']:3d}  s/R={m['s_over_R']:12.6f}  gap={m['rel_gap_pct_from_10R_over_s']:10.4f}%"
        )

    lines += ["", "RULING:", payload["ruling"]]
    (OUT / "S_OVER_R_NEAR_10.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("P135 lock:", lock)
    for n in ANCHORS:
        m = anchors[str(n)]
        print(
            f"P{n}: s/R={m['s_over_R']:.6f} gap={m['rel_gap_pct_from_10R_over_s']:.4f}%"
        )
    print("bands:", band_counts)
    print("null frac <=P135 gap:", null_rate_lt_p135)
    print("ruling:", payload["ruling"])
    print(f"wrote {OUT / 'S_OVER_R_NEAR_10.txt'}")


if __name__ == "__main__":
    main()
