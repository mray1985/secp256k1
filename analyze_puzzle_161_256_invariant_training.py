#!/usr/bin/env python3
"""
Train on puzzle pubkeys 161-256: can pubkey-only invariants predict index n?

Falsification test for creator-generation hypotheses.
If no invariant correlates with n, applying same invariant to P135 is unsupported.
"""

from __future__ import annotations

import json
import math
import random
import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_catalog import load_catalog  # noqa: E402

getcontext().prec = 80

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
DATA = ROOT / "ARCHIVE" / "briefcase" / "puzzlepubkeys" / "puzzle_161_256_pubkeys.json"
OUT = ROOT / "ARCHIVE" / "briefcase" / "puzzlepubkeys"


def pubkey_xy(comp: str) -> tuple[int, int, int]:
    prefix = comp[:2]
    px = int(comp[2:], 16)
    y_sq = (pow(px, 3, P) + 7) % P
    y = pow(y_sq, (P + 1) // 4, P)
    if (y % 2 == 0) != (prefix == "02"):
        y = P - y
    parity = 0 if prefix == "02" else 1
    return px, y, parity


def echo_frac(val: int, num: int, den: int = 256) -> float:
    if val <= 0:
        return 0.0
    return float((Decimal(val).ln() * Decimal(num) / Decimal(den)).exp())


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else 0.0


def popcount(x: int) -> int:
    return x.bit_count()


def dec_lead(k: int, digits: int = 5) -> int:
    return int(str(k)[:digits]) if k else 0


def carry_pmy_mod9(py: int) -> int:
    pmy = P - py
    return sum(int(c) for c in str(pmy)) % 9


def load_rows() -> list[dict]:
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    rows = []
    for r in raw:
        n = r["puzzle"]
        comp = r["pubkey_compressed"]
        px, py, ypar = pubkey_xy(comp)
        h = int(r["hash160"], 16)
        band_lo = 1 << (n - 1)
        rows.append(
            {
                "n": n,
                "px": px,
                "py": py,
                "y_parity": ypar,
                "hash160": h,
                "comp": comp,
                "band_lo": band_lo,
                "band_hi": (1 << n) - 1,
            }
        )
    return sorted(rows, key=lambda x: x["n"])


def feature_dict(row: dict, *, include_n_coupled: bool = False) -> dict[str, float]:
    n, px, py = row["n"], row["px"], row["py"]
    h = row["hash160"]
    pmy = P - py
    inv_px = pow(px, P - 2, P)
    y_sq = (pow(px, 3, P) + 7) % P
    out = {
        "log10_px": math.log10(px + 1),
        "log10_py": math.log10(py + 1),
        "log10_hash160": math.log10(h + 1),
        "px_mod_p_frac": px / P,
        "py_mod_p_frac": py / P,
        "p_minus_px_frac": (P - px) / P,
        "p_minus_py_frac": pmy / P,
        "inv_px_frac": inv_px / P,
        "y_sq_frac": y_sq / P,
        "echo_px_256": echo_frac(px, 256),
        "echo_py_256": echo_frac(py, 256),
        "echo_h_256": echo_frac(h, 256),
        "hash160_left5": dec_lead(h),
        "px_left5": dec_lead(px),
        "py_left5": dec_lead(py),
        "px_mod256": px % 256,
        "py_mod256": py % 256,
        "px_mod9": px % 9,
        "py_mod9": py % 9,
        "carry_pmy_mod9": carry_pmy_mod9(py),
        "px_popcount": popcount(px),
        "py_popcount": popcount(py),
        "y_parity": float(row["y_parity"]),
        "px_xor_py_pop": popcount(px ^ py),
        "px_py_ratio_log": math.log10(px + 1) - math.log10(py + 1),
    }
    if include_n_coupled:
        band_lo = row["band_lo"]
        out.update(
            {
                "px_over_band_lo": px / band_lo,
                "py_over_band_lo": py / band_lo,
                "h_over_band_lo": h / band_lo,
                "echo_px_n": echo_frac(px, n),
                "echo_py_n": echo_frac(py, n),
                "echo_h_n": echo_frac(h, n),
            }
        )
    return out


def consecutive_features(rows: list[dict]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {
        "delta_px_mod_p_frac": [],
        "delta_py_mod_p_frac": [],
        "parity_flip": [],
    }
    for i in range(1, len(rows)):
        a, b = rows[i - 1], rows[i]
        out["delta_px_mod_p_frac"].append((b["px"] - a["px"]) % P / P)
        out["delta_py_mod_p_frac"].append((b["py"] - a["py"]) % P / P)
        out["parity_flip"].append(float(b["y_parity"] != a["y_parity"]))
    return out


def perm_p_value(obs: float, xs: list[float], ys: list[float], trials: int = 5000) -> float:
    random.seed(0)
    count = 0
    for _ in range(trials):
        sh = ys[:]
        random.shuffle(sh)
        r = pearson(xs, sh)
        if abs(r) >= abs(obs):
            count += 1
    return count / trials


def linear_r2_predict_n(rows: list[dict], feat_names: list[str]) -> float:
    """Simple OLS R^2 predicting n from features (no intercept adjustment needed for ranking)."""
    import statistics

    n = len(rows)
    Y = [float(r["n"]) for r in rows]
    my = statistics.mean(Y)
    ss_tot = sum((y - my) ** 2 for y in Y)
    # normalize features
    X = {f: [feature_dict(r, include_n_coupled=False)[f] for r in rows] for f in feat_names}
    means = {f: statistics.mean(X[f]) for f in feat_names}
    stds = {f: statistics.pstdev(X[f]) or 1.0 for f in feat_names}
    k = len(feat_names)
    preds = []
    for row in rows:
        pred = my
        for f in feat_names:
            z = (feature_dict(row, include_n_coupled=False)[f] - means[f]) / stds[f]
            r = pearson(X[f], Y)
            pred += r * z * statistics.pstdev(Y) / k
        preds.append(pred)
    ss_res = sum((y - p) ** 2 for y, p in zip(Y, preds))
    return 1 - ss_res / ss_tot if ss_tot else 0.0


def main() -> None:
    rows = load_rows()
    print(f"Loaded {len(rows)} pubkeys (P161-P256)")
    ns = [float(r["n"]) for r in rows]

    # --- per-point features vs n (pubkey-only; no n in formula) ---
    sample = feature_dict(rows[0], include_n_coupled=False)
    feat_names = list(sample.keys())
    corrs_honest: list[tuple[str, float]] = []
    for f in feat_names:
        vals = [feature_dict(r, include_n_coupled=False)[f] for r in rows]
        corrs_honest.append((f, pearson(ns, vals)))
    corrs_honest.sort(key=lambda t: abs(t[1]), reverse=True)

    perm_cache: dict[str, float] = {}

    def pval(f: str, r: float, vals: list[float]) -> float:
        if f not in perm_cache:
            perm_cache[f] = perm_p_value(r, ns, vals, trials=500)
        return perm_cache[f]

    print("\n=== HONEST pubkey-only features (n NOT in formula) ===")
    print(f"{'feature':28s} {'r':>8s} {'p_perm':>8s}")
    for f, r in corrs_honest[:15]:
        vals = [feature_dict(row, include_n_coupled=False)[f] for row in rows]
        pval_v = pval(f, r, vals)
        print(f"{f:28s} {r:8.4f} {pval_v:8.4f}")

    # --- n-coupled artifacts (for comparison) ---
    corrs_artifact: list[tuple[str, float]] = []
    for f in feature_dict(rows[0], include_n_coupled=True):
        if f not in feat_names:
            vals = [feature_dict(r, include_n_coupled=True)[f] for r in rows]
            corrs_artifact.append((f, pearson(ns, vals)))
    corrs_artifact.sort(key=lambda t: abs(t[1]), reverse=True)
    print("\n=== ARTIFACT features (embed n — NOT valid predictors) ===")
    for f, r in corrs_artifact[:6]:
        print(f"  {f:24s} r={r:.4f}  (uses n or 2^(n-1) in definition)")

    corrs = corrs_honest

    # --- consecutive / EC-adjacent ---
    print("\n=== Consecutive puzzle deltas (n vs n+1) ===")
    cons = consecutive_features(rows)
    idx_ns = [float(rows[i]["n"]) for i in range(1, len(rows))]
    for f, vals in cons.items():
        r = pearson(idx_ns, vals)
        print(f"  {f:26s} r={r:.4f}")

    # --- y parity vs n ---
    ypar = [float(r["y_parity"]) for r in rows]
    even_count = sum(1 for y in ypar if y == 0)
    print(f"\n=== y parity (02=0, 03=1) ===")
    print(f"  count 03-prefix: {int(sum(ypar))}/96  (expect ~48)")
    print(f"  Pearson(y_parity, n) = {pearson(ns, ypar):.4f}")

    # --- x progression test: linear fit px vs n ---
    px_vals = [float(r["px"]) for r in rows]
    r_px_n = pearson(ns, px_vals)
    print(f"\n=== Naive arithmetic progression tests ===")
    print(f"  Pearson(px, n) = {r_px_n:.4f}  (NOT EC diff; integer px vs index)")
    print(f"  Pearson(log10(px), n) = {pearson(ns, [math.log10(r['px']+1) for r in rows]):.4f}")

    # --- multi-feature predict n (precomputed features) ---
    import statistics

    best5 = [f for f, _ in corrs[:5]]
    feat_matrix = {f: [feature_dict(r, include_n_coupled=False)[f] for r in rows] for f in best5}
    Y = ns[:]
    my = statistics.mean(Y)
    ss_tot = sum((y - my) ** 2 for y in Y)
    preds = []
    for i in range(len(rows)):
        pred = my
        for f in best5:
            r = pearson(feat_matrix[f], Y)
            z = (feat_matrix[f][i] - statistics.mean(feat_matrix[f])) / (statistics.pstdev(feat_matrix[f]) or 1.0)
            pred += r * z * statistics.pstdev(Y) / len(best5)
        preds.append(pred)
    r2 = 1 - sum((y - p) ** 2 for y, p in zip(Y, preds)) / ss_tot
    random.seed(1)
    null_r2 = []
    for _ in range(200):
        sh = Y[:]
        random.shuffle(sh)
        null_preds = []
        for i in range(len(rows)):
            pred = my
            for f in best5:
                r = pearson(feat_matrix[f], sh)
                z = (feat_matrix[f][i] - statistics.mean(feat_matrix[f])) / (statistics.pstdev(feat_matrix[f]) or 1.0)
                pred += r * z * statistics.pstdev(sh) / len(best5)
            null_preds.append(pred)
        null_r2.append(1 - sum((y - p) ** 2 for y, p in zip(sh, null_preds)) / ss_tot)
    null_r2.sort()
    print(f"\n=== Multi-feature index recovery (top-5 correlated features) ===")
    print(f"  R² predict n: {r2:.4f}")
    print(f"  null R² (200 shuffles) median: {null_r2[100]:.4f}  95th pct: {null_r2[190]:.4f}")

    # --- P135 projection ---
    cat = load_catalog()
    p135_comp = cat[135].public_key
    px135, py135, yp135 = pubkey_xy(p135_comp)
    h135 = int(cat[135].address_hash or 0, 16) if hasattr(cat[135], "address_hash") else 0
    if not h135:
        import hashlib

        comp = bytes.fromhex(p135_comp)
        h135 = int.from_bytes(
            hashlib.new("ripemd160", hashlib.sha256(comp).digest()).digest(), "big"
        )
    row135 = {
        "n": 135,
        "px": px135,
        "py": py135,
        "y_parity": yp135,
        "hash160": h135,
        "band_lo": 1 << 134,
        "band_hi": (1 << 135) - 1,
    }
    f135 = feature_dict(row135, include_n_coupled=False)

    print("\n=== P135 vs 161-256 training distribution (honest features) ===")
    for f, r in corrs[:8]:
        train = [feature_dict(row, include_n_coupled=False)[f] for row in rows]
        t_mean = sum(train) / len(train)
        t_std = math.sqrt(sum((x - t_mean) ** 2 for x in train) / len(train)) or 1.0
        z135 = (f135[f] - t_mean) / t_std
        print(f"  {f:24s} P135 z-score vs train: {z135:+.2f}  (train r={r:+.3f})")

    # --- ruling ---
    max_abs_r = max(abs(r) for _, r in corrs)
    best_f, best_r = corrs[0]
    best_p = pval(best_f, best_r, [feature_dict(row, include_n_coupled=False)[best_f] for row in rows])

    print("\n=== RULING ===")
    if max_abs_r < 0.15 or best_p > 0.05:
        print("NO pubkey-only invariant recovers puzzle index on 161-256.")
        print("Keys look independently uniform; creator construction not visible in public points.")
        print("Applying echo/p-N/TDAD-style invariants to P135 is NOT supported by this training set.")
    else:
        print(f"Weak signal: best {best_f} r={best_r:.3f} p={best_p:.4f} — inspect, do not treat as compass.")

    report = {
        "n_train": len(rows),
        "top_correlations": [
            {
                "feature": f,
                "r": r,
                "p_perm": pval(f, r, [feature_dict(row, include_n_coupled=False)[f] for row in rows]),
            }
            for f, r in corrs[:15]
        ],
        "artifact_correlations": [{"feature": f, "r": r} for f, r in corrs_artifact[:10]],
        "y_parity_03_count": int(sum(ypar)),
        "r_px_vs_n": r_px_n,
        "r2_top5": r2,
        "null_r2_median": null_r2[100],
        "p135_zscores": {
            f: (f135[f] - sum(feature_dict(row, include_n_coupled=False)[f] for row in rows) / len(rows))
            / (
                math.sqrt(
                    sum(
                        (feature_dict(row, include_n_coupled=False)[f] - sum(feature_dict(row, include_n_coupled=False)[f] for row in rows) / len(rows)) ** 2
                        for row in rows
                    )
                    / len(rows)
                )
                or 1
            )
            for f, _ in corrs[:8]
        },
        "ruling": "no_signal" if max_abs_r < 0.15 or best_p > 0.05 else "weak_signal",
    }
    out_json = OUT / "puzzle_161_256_invariant_training.json"
    out_md = OUT / "puzzle_161_256_invariant_training.md"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Puzzle 161-256 pubkey invariant training",
        "",
        "Question: can public-key-only features predict puzzle index n?",
        "",
        f"Training set: {len(rows)} revealed pubkeys from genesis spend.",
        "",
        "## Top correlations with n",
        "",
        "| feature | r | p_perm |",
        "|---------|---|--------|",
    ]
    for item in report["top_correlations"][:15]:
        lines.append(f"| {item['feature']} | {item['r']:.4f} | {item['p_perm']:.4f} |")
    lines.extend(
        [
            "",
            f"**R² (top-5 features → n):** {r2:.4f}  (null median {null_r2[100]:.4f})",
            "",
            f"**Ruling:** {report['ruling']}",
            "",
        ]
    )
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out_json}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
