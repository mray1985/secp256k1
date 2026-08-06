#!/usr/bin/env python3
"""Held-out tests on signature-normalization (a,b) — no d in features.

1) Cross-validation: predict Hamming-weight cohort from (a,b,theta,centered) only.
2) Modular distances from P150/P155 shelf to all solved (a,b) points.

Not a path to d. Pairing/shuffle nulls included.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

from puzzle_catalog import load_catalog
from scan_log_ratio_cross_puzzle import N, load_rows
from sig_norm_a_b_test import (
    SigRow,
    build_rows,
    circ_dist,
    circ_mean_theta,
    mod_center,
)

OUT = Path("logs/log_ratio_scan/rank_first_full_matrix")
TWO_PI = 2.0 * math.pi


def wt_cohort(wt: int, edges: tuple[int, int, int]) -> str:
    """low / mid / high by empirical quintile edges (lo_max, hi_min)."""
    lo_max, mid_max, _ = edges
    if wt <= lo_max:
        return "low"
    if wt <= mid_max:
        return "mid"
    return "high"


def feature_vec(r: SigRow) -> list[float]:
    """Public-only features (no d, no k)."""
    return [
        r.a / N,
        r.b / N,
        r.a_tilde / (N / 2),
        r.b_tilde / (N / 2),
        math.cos(r.theta_a),
        math.sin(r.theta_a),
        math.cos(r.theta_b),
        math.sin(r.theta_b),
        circ_dist(r.a, 0) / (N / 2),
        circ_dist(r.b, 0) / (N / 2),
        r.addr_y / (1 << 32),
    ]


def knn_predict(train: list[tuple[list[float], str]], x: list[float], k: int = 5) -> str:
    dists = []
    for fv, lab in train:
        d = math.sqrt(sum((a - b) ** 2 for a, b in zip(fv, x)))
        dists.append((d, lab))
    dists.sort()
    votes = Counter(lab for _, lab in dists[:k])
    return votes.most_common(1)[0][0]


def cross_validate(solved: list[SigRow], edges: tuple[int, int, int], folds: int = 10, seed: int = 0) -> dict:
    rng = random.Random(seed)
    indexed = list(enumerate(solved))
    rng.shuffle(indexed)
    fold_size = max(1, len(indexed) // folds)
    preds = []
    # majority baseline
    labels = [wt_cohort(r.wt, edges) for r in solved]
    maj = Counter(labels).most_common(1)[0][0]
    maj_acc = sum(1 for lab in labels if lab == maj) / len(labels)

    for f in range(folds):
        te = indexed[f * fold_size : (f + 1) * fold_size] if f < folds - 1 else indexed[f * fold_size :]
        te_idx = {i for i, _ in te}
        train = [
            (feature_vec(r), wt_cohort(r.wt, edges))
            for i, r in indexed
            if i not in te_idx
        ]
        for i, r in te:
            pred = knn_predict(train, feature_vec(r), k=5)
            truth = wt_cohort(r.wt, edges)
            preds.append(pred == truth)

    # shuffle null: permute labels in train each fold (aggregate)
    null_accs = []
    for trial in range(100):
        rng2 = random.Random(seed + 1000 + trial)
        labs = [wt_cohort(r.wt, edges) for r in solved]
        rng2.shuffle(labs)
        # single random split 80/20
        order = list(range(len(solved)))
        rng2.shuffle(order)
        cut = int(0.8 * len(order))
        tr_i, te_i = order[:cut], order[cut:]
        train = [(feature_vec(solved[i]), labs[i]) for i in tr_i]
        ok = 0
        for i in te_i:
            if knn_predict(train, feature_vec(solved[i]), k=5) == labs[i]:
                # compare to TRUE label of test row, not shuffled — proper null is:
                # features real, labels shuffled globally then CV
                pass
        # redo null properly: shuffle weight labels assigned to rows
        assign = {solved[i].n: labs[i] for i in range(len(solved))}
        # Actually labs[i] was shuffled relative to solved order
        train = [(feature_vec(solved[i]), labs[i]) for i in tr_i]
        ok = sum(
            1
            for i in te_i
            if knn_predict(train, feature_vec(solved[i]), k=5) == labs[i]
        )
        # This tests predicting shuffled labels — should be ~chance if using shuffled as truth
        # Better null: keep truth, shuffle feature pairing
        pass

    # Feature-shuffle null: permute feature vectors among solved, keep true wt labels
    feat_null = []
    for trial in range(200):
        rng3 = random.Random(seed + 5000 + trial)
        feats = [feature_vec(r) for r in solved]
        labs_true = [wt_cohort(r.wt, edges) for r in solved]
        rng3.shuffle(feats)
        order = list(range(len(solved)))
        rng3.shuffle(order)
        cut = int(0.8 * len(order))
        tr, te = order[:cut], order[cut:]
        train = [(feats[i], labs_true[i]) for i in tr]
        ok = sum(1 for i in te if knn_predict(train, feats[i], k=5) == labs_true[i])
        feat_null.append(ok / len(te))

    real_acc = sum(preds) / len(preds)
    return {
        "folds": folds,
        "accuracy": real_acc,
        "majority_baseline": maj_acc,
        "majority_class": maj,
        "feature_shuffle_null_mean": sum(feat_null) / len(feat_null),
        "feature_shuffle_null_p95": sorted(feat_null)[int(0.95 * len(feat_null))],
        "beats_null": real_acc > sorted(feat_null)[int(0.95 * len(feat_null))],
        "n": len(solved),
        "label_counts": dict(Counter(labels)),
    }


def shelf_distances(rows: list[SigRow], shelf: list[int], solved: list[SigRow]) -> dict:
    by_n = {r.n: r for r in rows}
    out = {}
    for sn in shelf:
        if sn not in by_n:
            continue
        s = by_n[sn]
        dists = []
        for t in solved:
            dists.append(
                {
                    "solved_n": t.n,
                    "wt": t.wt,
                    "circ_a": circ_dist(s.a, t.a),
                    "circ_b": circ_dist(s.b, t.b),
                    "circ_a_frac": circ_dist(s.a, t.a) / N,
                    "circ_b_frac": circ_dist(s.b, t.b) / N,
                    "abs_addr_y": abs(s.addr_y - t.addr_y),
                    "abs_wt": abs(s.wt - t.wt),
                }
            )
        dists.sort(key=lambda d: (d["circ_a"], d["circ_b"]))
        out[str(sn)] = {
            "theta_a": s.theta_a,
            "theta_b": s.theta_b,
            "theta_a_deg": s.theta_a * 180 / math.pi,
            "theta_b_deg": s.theta_b * 180 / math.pi,
            "nearest_by_circ_a": dists[:10],
            "nearest_by_circ_b": sorted(dists, key=lambda d: d["circ_b"])[:10],
            "nearest_joint": sorted(
                dists, key=lambda d: d["circ_a_frac"] + d["circ_b_frac"]
            )[:10],
        }
    # shelf mutual
    if all(n in by_n for n in shelf):
        u, v = by_n[shelf[0]], by_n[shelf[1]]
        out["shelf_pair"] = {
            "pair": shelf,
            "circ_dist_a": circ_dist(u.a, v.a),
            "circ_dist_b": circ_dist(u.b, v.b),
            "circ_a_frac": circ_dist(u.a, v.a) / N,
            "circ_b_frac": circ_dist(u.b, v.b) / N,
            "delta_theta_a": abs(u.theta_a - v.theta_a),
            "delta_theta_b": abs(u.theta_b - v.theta_b),
            "note": "Small circ_a with large circ_b = angular lock on a only, not shared nonce path.",
        }
        # null: how often two random solved pairs have circ_a as small as shelf
        shelf_a = circ_dist(u.a, v.a)
        rng = random.Random(0)
        closer = 0
        trials = 2000
        for _ in range(trials):
            x, y = rng.sample(solved, 2)
            if circ_dist(x.a, y.a) <= shelf_a:
                closer += 1
        out["shelf_pair"]["null_frac_solved_pairs_circ_a_le_shelf"] = closer / trials
        out["shelf_pair"]["shelf_circ_a"] = shelf_a
    return out


def verify_group_claims(rows: list[SigRow]) -> dict:
    """Check AI claims about low/high wt theta means."""
    solved = [r for r in rows if r.solved]
    wts = sorted(r.wt for r in rows)
    # quintiles on rows-with-rsz
    q1 = wts[len(wts) // 5]
    q4 = wts[(4 * len(wts)) // 5]
    low = [r for r in rows if r.wt <= q1]
    high = [r for r in rows if r.wt >= q4]
    mid = [r for r in rows if q1 < r.wt < q4]
    return {
        "q1_wt_max": q1,
        "q4_wt_min": q4,
        "low_theta_a_circ_mean": circ_mean_theta([r.theta_a for r in low]),
        "high_theta_a_circ_mean": circ_mean_theta([r.theta_a for r in high]),
        "high_theta_b_circ_mean": circ_mean_theta([r.theta_b for r in high]),
        "mid_mean_circ_a_to_0": sum(circ_dist(r.a, 0) for r in mid) / len(mid),
        "high_mean_circ_a_to_0": sum(circ_dist(r.a, 0) for r in high) / len(high),
        "low_n": len(low),
        "high_n": len(high),
        "mid_n": len(mid),
        "focus": {
            str(n): {
                "theta_a": next(r.theta_a for r in rows if r.n == n),
                "theta_b": next(r.theta_b for r in rows if r.n == n),
                "deg_a": next(r.theta_a for r in rows if r.n == n) * 180 / math.pi,
                "deg_b": next(r.theta_b for r in rows if r.n == n) * 180 / math.pi,
                "wt": next(r.wt for r in rows if r.n == n),
            }
            for n in (135, 150, 155, 160)
            if any(r.n == n for r in rows)
        },
    }


def main() -> None:
    rows = build_rows()
    solved = [r for r in rows if r.solved]
    wts = sorted(r.wt for r in solved)
    # edges from solved quintiles for classification target
    lo_max = wts[len(wts) // 5]
    hi_min = wts[(4 * len(wts)) // 5]
    # mid between
    edges = (lo_max, hi_min - 1, 999)

    claims = verify_group_claims(rows)
    cv = cross_validate(solved, edges)
    shelf = shelf_distances(rows, [150, 155], solved)

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "claims_check": claims,
        "cv_weight_cohort_from_ab_theta": cv,
        "shelf_150_155": shelf,
        "ruling": (
            "CV: if accuracy does not beat feature-shuffle null, (a,b,theta) do not classify "
            "Hamming cohorts. Shelf: report circ distances + null fraction; small circ_a alone "
            "is not a shared nonce path. Still no public path to d."
        ),
    }
    (OUT / "SIG_NORM_HELD_OUT_SHELF.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "HELD-OUT + SHELF TESTS on (a,b) normalization",
        "",
        "=== Focus angles (verified) ===",
    ]
    for n, d in claims["focus"].items():
        lines.append(
            f"P{n}: wt={d['wt']}  theta_a={d['theta_a']:.4f} ({d['deg_a']:.1f} deg)  "
            f"theta_b={d['theta_b']:.4f} ({d['deg_b']:.1f} deg)"
        )

    lines += [
        "",
        "=== Group circular means (rsz rows) ===",
        f"low wt quintile theta_a circ mean: {claims['low_theta_a_circ_mean']:.4f} (n={claims['low_n']})",
        f"high wt quintile theta_a circ mean: {claims['high_theta_a_circ_mean']:.4f}",
        f"high wt quintile theta_b circ mean: {claims['high_theta_b_circ_mean']:.4f} (n={claims['high_n']})",
        f"mid mean circ_a_to_0: {claims['mid_mean_circ_a_to_0']:.6e}",
        f"high mean circ_a_to_0: {claims['high_mean_circ_a_to_0']:.6e}",
        "",
        "=== CV: predict wt cohort from (a,b,theta,...) only — no d ===",
        f"accuracy: {cv['accuracy']:.4f}",
        f"majority baseline: {cv['majority_baseline']:.4f} ({cv['majority_class']})",
        f"feature-shuffle null mean: {cv['feature_shuffle_null_mean']:.4f}",
        f"feature-shuffle null p95: {cv['feature_shuffle_null_p95']:.4f}",
        f"beats null p95: {cv['beats_null']}",
        f"label_counts: {cv['label_counts']}",
        "",
        "=== P150/P155 shelf vs solved ===",
    ]
    sp = shelf.get("shelf_pair", {})
    lines.append(
        f"shelf circ_a={sp.get('circ_dist_a')} ({sp.get('circ_a_frac',0):.6e} of N)  "
        f"circ_b={sp.get('circ_dist_b')} ({sp.get('circ_b_frac',0):.6e} of N)"
    )
    lines.append(
        f"null frac solved pairs with circ_a <= shelf: "
        f"{sp.get('null_frac_solved_pairs_circ_a_le_shelf')}"
    )
    for sn in ("150", "155"):
        if sn not in shelf:
            continue
        lines.append(f"P{sn} nearest solved by joint circ(a)+circ(b):")
        for d in shelf[sn]["nearest_joint"][:5]:
            lines.append(
                f"  P{d['solved_n']} wt={d['wt']}  "
                f"circ_a/N={d['circ_a_frac']:.4f} circ_b/N={d['circ_b_frac']:.4f}"
            )

    lines += [
        "",
        "RULING:",
        "- Angular proximity of theta_a for 150/155 is measurable; interpret as shared nonce path: NO.",
        "- Weight-cohort prediction from (a,b,theta) must beat shuffle null to count as signal.",
        "- Still signature normalization only; DLP intact without k.",
    ]
    (OUT / "SIG_NORM_HELD_OUT_SHELF.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "cv_acc": cv["accuracy"],
        "maj": cv["majority_baseline"],
        "null_p95": cv["feature_shuffle_null_p95"],
        "beats_null": cv["beats_null"],
        "shelf_circ_a_frac": sp.get("circ_a_frac"),
        "shelf_circ_b_frac": sp.get("circ_b_frac"),
        "shelf_null": sp.get("null_frac_solved_pairs_circ_a_le_shelf"),
        "focus": claims["focus"],
    }, indent=2))
    print(f"wrote {OUT / 'SIG_NORM_HELD_OUT_SHELF.txt'}")


if __name__ == "__main__":
    main()
