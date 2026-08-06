"""Pearson + scale-free follow-ups for log-ratio falsification cohort."""
from __future__ import annotations

import json
import math
import random
import statistics
from decimal import Decimal, getcontext
from pathlib import Path

from scan_log_ratio_cross_puzzle import load_rows, ln, spearman

getcontext().prec = 60
OUT = Path("logs/log_ratio_scan")


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    deny = math.sqrt(sum((y - my) ** 2 for y in ys))
    if denx == 0 or deny == 0:
        return None
    return num / (denx * deny)


def limbs(r):
    return {
        "Px": r.Px,
        "Py": r.Py,
        "Pmy": r.Pmy,
        "r": r.r,
        "s": r.s,
        "z": r.z,
        "Ry": r.Ry,
    }


def main() -> None:
    rows = sorted(
        [r for r in load_rows() if r.d and r.r and r.s and r.z and r.Ry],
        key=lambda r: r.n,
    )
    print("cohort", len(rows))

    pairs = [
        ("Px", "Py"),
        ("Px", "Pmy"),
        ("Px", "r"),
        ("Px", "s"),
        ("Px", "z"),
        ("Px", "Ry"),
        ("Py", "Px"),
        ("Py", "Pmy"),
        ("Py", "r"),
        ("Py", "s"),
        ("Py", "z"),
        ("Py", "Ry"),
    ]

    table = []
    for r in rows:
        L = limbs(r)
        rec = {"n": r.n, "d": r.d, "log2d": math.log2(r.d)}
        for a, b in pairs:
            ratio = float(ln(L[a]) / ln(L[b]))
            F = float(Decimal(r.d) * ln(L[a]) / ln(L[b]))
            rec[f"ratio_{a}_{b}"] = ratio
            rec[f"F_{a}_{b}"] = F
            rec[f"log_ratio_{a}_{b}"] = math.log(ratio)
        table.append(rec)

    ns = [float(t["n"]) for t in table]
    log2d = [t["log2d"] for t in table]

    print("\n=== 1) Pearson vs Spearman on F and on F/d ===")
    hdr = (
        f'{"formula":<22} {"Spear(F,n)":>10} {"Pear(F,n)":>10} '
        f'{"Spear(F/d,n)":>12} {"Pear(F/d,n)":>12} {"Pear(logFd,n)":>14}'
    )
    print(hdr)
    results = []
    for a, b in pairs:
        Fs = [t[f"F_{a}_{b}"] for t in table]
        Rs = [t[f"ratio_{a}_{b}"] for t in table]
        LRs = [t[f"log_ratio_{a}_{b}"] for t in table]
        row = {
            "formula": f"d*log({a})/log({b})",
            "spearman_F_n": spearman(Fs, ns),
            "pearson_F_n": pearson(Fs, ns),
            "spearman_Fd_n": spearman(Rs, ns),
            "pearson_Fd_n": pearson(Rs, ns),
            "pearson_logFd_n": pearson(LRs, ns),
            "pearson_Fd_log2d": pearson(Rs, log2d),
            "mean_Fd": statistics.mean(Rs),
            "stdev_Fd": statistics.pstdev(Rs),
        }
        results.append(row)
        print(
            f'{row["formula"]:<22} {row["spearman_F_n"]:+10.4f} {row["pearson_F_n"]:+10.4f} '
            f'{row["spearman_Fd_n"]:+12.4f} {row["pearson_Fd_n"]:+12.4f} '
            f'{row["pearson_logFd_n"]:+14.4f}'
        )

    print("\n=== 2) Why b=r flips sign: correlate log(limb) with n ===")
    limb_names = ["Px", "Py", "Pmy", "r", "s", "z", "Ry"]
    print(
        f'{"limb":<6} {"mean log10":>12} {"Pear(log,n)":>12} '
        f'{"Spear(log,n)":>12} {"Pear(log,log2d)":>14}'
    )
    limb_logs = {name: [] for name in limb_names}
    for r in rows:
        L = limbs(r)
        for name in limb_names:
            limb_logs[name].append(math.log(L[name]))

    limb_stats = {}
    for name in limb_names:
        xs = limb_logs[name]
        limb_stats[name] = {
            "mean_log10": statistics.mean([x / math.log(10) for x in xs]),
            "pearson_log_n": pearson(xs, ns),
            "spearman_log_n": spearman(xs, ns),
            "pearson_log_log2d": pearson(xs, log2d),
        }
        s = limb_stats[name]
        print(
            f"{name:<6} {s['mean_log10']:12.4f} {s['pearson_log_n']:+12.4f} "
            f"{s['spearman_log_n']:+12.4f} {s['pearson_log_log2d']:+14.4f}"
        )

    print("\nDecomposition for log(Px)/log(r) vs n (band means):")
    bands = [(1, 20), (21, 40), (41, 60), (61, 80), (81, 130)]
    band_means = []
    for lo, hi in bands:
        sub = [t for t in table if lo <= t["n"] <= hi]
        if len(sub) < 3:
            continue
        m = statistics.mean([t["ratio_Px_r"] for t in sub])
        band_means.append({"lo": lo, "hi": hi, "n": len(sub), "mean_logPx_over_logR": m})
        print(f"  n in [{lo:3d},{hi:3d}]  mean logPx/logR = {m:.6f}  (count={len(sub)})")

    # Relative growth: does log(r) rise faster than log(Px)?
    # Corr of (log r - c*log Px) — simpler: corr of log(r)/log(Px) with n
    log_r_over_log_Px = [
        limb_logs["r"][i] / limb_logs["Px"][i] for i in range(len(rows))
    ]
    print(
        f"\nPear(log(r)/log(Px), n) = {pearson(log_r_over_log_Px, ns):+.4f} "
        f"(>0 means r's log grows vs Px as n rises -> logPx/logR falls)"
    )

    print("\n=== 3) Scale-free baselines (F/d = log(a)/log(b) only) ===")
    print(
        f'{"formula":<22} {"mean":>10} {"stdev":>10} {"min":>10} {"max":>10} '
        f'{"Pear vs n":>10} {"Spear vs n":>10}'
    )
    scale_free = []
    for a, b in pairs:
        Rs = [t[f"ratio_{a}_{b}"] for t in table]
        row = {
            "formula": f"log({a})/log({b})",
            "mean": statistics.mean(Rs),
            "stdev": statistics.pstdev(Rs),
            "min": min(Rs),
            "max": max(Rs),
            "pearson_n": pearson(Rs, ns),
            "spearman_n": spearman(Rs, ns),
        }
        scale_free.append(row)
        print(
            f'{row["formula"]:<22} {row["mean"]:10.6f} {row["stdev"]:10.6f} '
            f'{row["min"]:10.6f} {row["max"]:10.6f} '
            f'{row["pearson_n"]:+10.4f} {row["spearman_n"]:+10.4f}'
        )

    print("\n=== Pairing shuffle on Pearson(F/d, n), 200 trials ===")
    rng = random.Random(0)
    formulas_gate = [("Px", "Py"), ("Px", "r"), ("Py", "Px"), ("Py", "r"), ("Px", "s")]
    gate = []
    for a, b in formulas_gate:
        real_Rs = [float(ln(limbs(r)[a]) / ln(limbs(r)[b])) for r in rows]
        real_p = pearson(real_Rs, [float(r.n) for r in rows])
        nulls = []
        for _ in range(200):
            order = list(range(len(rows)))
            rng.shuffle(order)
            Rs = []
            for i, r in enumerate(rows):
                donor = rows[order[i]]
                L = limbs(donor)
                Rs.append(float(ln(L[a]) / ln(L[b])))
            nulls.append(pearson(Rs, [float(r.n) for r in rows]))
        thr = abs(real_p)
        pemp = sum(1 for v in nulls if abs(v) >= thr) / len(nulls)
        entry = {
            "formula": f"log({a})/log({b})",
            "pearson": real_p,
            "null_mean": statistics.mean(nulls),
            "p_emp": pemp,
        }
        gate.append(entry)
        print(
            f'  {entry["formula"]}: Pearson={real_p:+.4f}  '
            f'null_mean={entry["null_mean"]:+.4f}  p_emp={pemp:.3f}'
        )

    out = {
        "cohort_n": len(rows),
        "pearson_spearman_table": results,
        "limb_vs_n": limb_stats,
        "band_means_Px_r": band_means,
        "scale_free": scale_free,
        "pairing_gate_pearson_Fd": gate,
        "ruling": (
            "Pearson(F,n) still ~1 because F≈d; only F/d is informative. "
            "b=r negative ρ(F/d,n) is log(r) rising vs log(Px) with puzzle height. "
            "Pairing shuffle: no significant pairing signal."
        ),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "pearson_and_scale_free.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
