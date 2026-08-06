#!/usr/bin/env python3
"""Permutation-tested regression: continuous address targets vs (a,b) features.

Targets (continuous, not Hamming buckets):
  u = addr_y / 2^32          checksum fractional part
  v = A / 2^32               = rmd160 + u  (full address-derived real)

Features (signature-normalization only; no d):
  a/N, b/N, (a+b)/N mod 1

Held-out R^2 + permutation null on feature pairing.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

from sig_norm_a_b_test import build_rows, N

OUT = Path("logs/log_ratio_scan/rank_first_full_matrix")
TWO32 = 1 << 32


def features(r) -> list[float]:
    aN = r.a / N
    bN = r.b / N
    return [aN, bN, (aN + bN) % 1.0]


def fit_ols(X: list[list[float]], y: list[float]) -> tuple[list[float], float]:
    """Return beta (with intercept) via normal equations; yhat R^2 on same set optional."""
    n = len(X)
    p = len(X[0]) + 1
    # design with intercept
    A = [[1.0] + row[:] for row in X]
    # AtA, Atb
    AtA = [[0.0] * p for _ in range(p)]
    Atb = [0.0] * p
    for i in range(n):
        for j in range(p):
            Atb[j] += A[i][j] * y[i]
            for k in range(p):
                AtA[j][k] += A[i][j] * A[i][k]
    beta = _solve(AtA, Atb)
    return beta


def _solve(M: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivot."""
    n = len(b)
    A = [M[i][:] + [b[i]] for i in range(n)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(A[r][col]))
        A[col], A[piv] = A[piv], A[col]
        if abs(A[col][col]) < 1e-18:
            return [0.0] * n
        div = A[col][col]
        for j in range(col, n + 1):
            A[col][j] /= div
        for r in range(n):
            if r == col:
                continue
            f = A[r][col]
            for j in range(col, n + 1):
                A[r][j] -= f * A[col][j]
    return [A[i][n] for i in range(n)]


def predict(beta: list[float], x: list[float]) -> float:
    return beta[0] + sum(beta[i + 1] * x[i] for i in range(len(x)))


def r2_score(y: list[float], yhat: list[float]) -> float:
    ym = sum(y) / len(y)
    ss_tot = sum((yi - ym) ** 2 for yi in y)
    ss_res = sum((yi - yh) ** 2 for yi, yh in zip(y, yhat))
    if ss_tot < 1e-30:
        return 0.0
    return 1.0 - ss_res / ss_tot


def pearson(y: list[float], yhat: list[float]) -> float:
    n = len(y)
    my = sum(y) / n
    mh = sum(yhat) / n
    num = sum((a - my) * (b - mh) for a, b in zip(y, yhat))
    den = math.sqrt(sum((a - my) ** 2 for a in y) * sum((b - mh) ** 2 for b in yhat))
    return num / den if den else 0.0


def held_out_eval(
    X: list[list[float]], y: list[float], folds: int = 10, seed: int = 0
) -> dict:
    rng = random.Random(seed)
    idx = list(range(len(y)))
    rng.shuffle(idx)
    fold = max(1, len(idx) // folds)
    y_true, y_pred = [], []
    for f in range(folds):
        te = idx[f * fold : (f + 1) * fold] if f < folds - 1 else idx[f * fold :]
        te_set = set(te)
        tr = [i for i in idx if i not in te_set]
        if len(tr) < 5 or not te:
            continue
        beta = fit_ols([X[i] for i in tr], [y[i] for i in tr])
        for i in te:
            y_true.append(y[i])
            y_pred.append(predict(beta, X[i]))
    return {
        "r2": r2_score(y_true, y_pred),
        "pearson": pearson(y_true, y_pred),
        "n_pred": len(y_true),
        "mae": sum(abs(a - b) for a, b in zip(y_true, y_pred)) / len(y_true),
    }


def perm_null(
    X: list[list[float]], y: list[float], trials: int = 500, seed: int = 1
) -> dict:
    """Shuffle feature rows relative to y; held-out R^2 distribution."""
    rng = random.Random(seed)
    null_r2 = []
    for t in range(trials):
        Xp = X[:]
        rng.shuffle(Xp)
        null_r2.append(held_out_eval(Xp, y, folds=5, seed=10 + t)["r2"])
    null_r2.sort()
    return {
        "trials": trials,
        "mean": sum(null_r2) / len(null_r2),
        "p95": null_r2[int(0.95 * len(null_r2))],
        "p99": null_r2[min(len(null_r2) - 1, int(0.99 * len(null_r2)))],
    }


def run_target(name: str, rows, y: list[float], subset_label: str) -> dict:
    X = [features(r) for r in rows]
    real = held_out_eval(X, y, folds=10, seed=0)
    # also in-sample for reference
    beta = fit_ols(X, y)
    yhat = [predict(beta, x) for x in X]
    ins = {"r2": r2_score(y, yhat), "pearson": pearson(y, yhat), "beta": beta}
    null = perm_null(X, y, trials=400, seed=2)
    return {
        "target": name,
        "subset": subset_label,
        "n": len(rows),
        "held_out": real,
        "in_sample": ins,
        "perm_null": null,
        "beats_null_p95": real["r2"] > null["p95"],
        "beats_null_p99": real["r2"] > null["p99"],
    }


def main() -> None:
    rows = build_rows()
    # need addr_y and reconstruct A = h160<<32 | addr_y conceptually
    # SigRow has h160 and addr_y
    solved = [r for r in rows if r.solved]
    all_rsz = rows

    def targets(rs):
        u = [r.addr_y / TWO32 for r in rs]
        # A/2^32 = h160 + addr_y/2^32
        v = [r.h160 + r.addr_y / TWO32 for r in rs]
        # fractional-only of full A/2^32 is just u; also test {a/N} style wrap of v is huge
        return u, v

    results = []
    for label, subset in [("all_rsz", all_rsz), ("solved_only", solved)]:
        u, v = targets(subset)
        results.append(run_target("u=addr_y/2^32", subset, u, label))
        results.append(run_target("v=A/2^32=h160+u", subset, v, label))
        # also fractional part of (a+b)/N already in features; test u vs each single feature
        for j, fname in enumerate(["a/N", "b/N", "(a+b)/N mod 1"]):
            X1 = [[features(r)[j]] for r in subset]
            real = held_out_eval(X1, u, folds=10, seed=0)
            null = perm_null(X1, u, trials=300, seed=3 + j)
            results.append(
                {
                    "target": "u=addr_y/2^32",
                    "subset": label,
                    "features": fname,
                    "n": len(subset),
                    "held_out": real,
                    "perm_null": {
                        "mean": null["mean"],
                        "p95": null["p95"],
                        "p99": null["p99"],
                    },
                    "beats_null_p95": real["r2"] > null["p95"],
                }
            )

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SIG_NORM_ADDR_REGRESSION.json").write_text(
        json.dumps(
            {
                "features": ["a/N", "b/N", "(a+b)/N mod 1"],
                "note": "Continuous address targets; Hamming buckets abandoned.",
                "results": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    lines = [
        "PERMUTATION-TESTED REGRESSION: address continuity vs (a,b)",
        "Targets: u=addr_y/2^32  and  v=A/2^32=rmd160+u",
        "Features: a/N, b/N, (a+b)/N mod 1",
        "No d in features. Held-out R^2 vs feature-permutation null.",
        "",
    ]
    for r in results:
        if "features" in r and isinstance(r["features"], str):
            lines.append(
                f"[{r['subset']}] u ~ {r['features']}: "
                f"R2={r['held_out']['r2']:+.4f}  null_p95={r['perm_null']['p95']:+.4f}  "
                f"beats={r['beats_null_p95']}"
            )
        elif r.get("target", "").startswith("u=") or r.get("target", "").startswith("v="):
            if "in_sample" in r:
                lines.append(
                    f"[{r['subset']}] {r['target']} ~ (a/N,b/N,(a+b)/N mod1): "
                    f"held_R2={r['held_out']['r2']:+.4f}  pearson={r['held_out']['pearson']:+.4f}  "
                    f"null_p95={r['perm_null']['p95']:+.4f}  beats_p95={r['beats_null_p95']}"
                )
    lines += [
        "",
        "RULING: if held-out R^2 does not beat permutation null, (a,b) do not linearly",
        "explain address checksum fraction or A/2^32. Signature normalization remains",
        "valid ECDSA rewrite; address linearity claim stays unproven.",
    ]
    (OUT / "SIG_NORM_ADDR_REGRESSION.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # print summary
    for r in results:
        if "in_sample" in r:
            print(
                f"{r['subset']:12} {r['target']:22} "
                f"R2={r['held_out']['r2']:+.4f} null95={r['perm_null']['p95']:+.4f} "
                f"beats={r['beats_null_p95']}"
            )
    print(f"wrote {OUT / 'SIG_NORM_ADDR_REGRESSION.txt'}")


if __name__ == "__main__":
    main()
