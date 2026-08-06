#!/usr/bin/env python3
"""Correlate hinge-distance metrics with log2(d) for solved puzzles."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_keys_53125 import parse_53125

CSV_IN = ROOT / "ARCHIVE" / "hinge_distance_all_puzzles.csv"
REPORT = ROOT / "ARCHIVE" / "hinge_vs_log2d_correlation.txt"


def corr(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else 0.0


def main() -> int:
    rows = list(csv.DictReader(CSV_IN.open(encoding="utf-8")))
    keys = parse_53125()

    pairs = []
    for r in rows:
        if r["solved"] != "True":
            continue
        n = int(r["puzzle"])
        if n not in keys or keys[n].d <= 0:
            continue
        d = keys[n].d
        log2d = math.log2(d)
        pairs.append(
            {
                "n": n,
                "log2d": log2d,
                "log2d134": log2d - 134,
                "dx": float(r["delta_x"]),
                "dy": float(r["delta_y"]),
                "min_d": float(r["min_delta"]),
                "lsx": float(r["log2_sqrt_x"]),
                "lsy": float(r["log2_sqrt_y"]),
                "closer": r["closer_side"],
            }
        )

    # drop P52 y anomaly (bad y coord / overflow artifact)
    core = [p for p in pairs if p["min_d"] > 0]

    lines = [
        f"solved puzzles with d: {len(core)} (excluded {len(pairs)-len(core)} anomalies)",
        "",
        "=== corr(log2(d), metric) ===",
    ]

    metrics = [
        ("delta_x", "dx"),
        ("delta_y", "dy"),
        ("min_delta", "min_d"),
        ("log2(sqrt(x))", "lsx"),
        ("log2(sqrt(y))", "lsy"),
        ("puzzle n", "n"),
    ]
    for label, key in metrics:
        c = corr([p["log2d"] for p in core], [p[key] for p in core])
        lines.append(f"  corr(log2(d), {label}): {c:+.4f}")

    lines.append("")
    lines.append("=== corr(log2(d)-134, metric)  [band position] ===")
    for label, key in metrics:
        c = corr([p["log2d134"] for p in core], [p[key] for p in core])
        lines.append(f"  corr(log_pos, {label}): {c:+.4f}")

    # key structural check: log2(sqrt(coord)) vs log2(d)/2
    lines.append("")
    lines.append("=== coord half-log vs log2(d)/2 (expect ~strong if linked) ===")
    res_x = [p["lsx"] - p["log2d"] / 2 for p in core]
    res_y = [p["lsy"] - p["log2d"] / 2 for p in core]
    lines.append(f"  corr(log2(d), log2(sqrt(x)) - log2(d)/2): {corr([p['log2d'] for p in core], res_x):+.4f}")
    lines.append(f"  corr(log2(d), log2(sqrt(y)) - log2(d)/2): {corr([p['log2d'] for p in core], res_y):+.4f}")
    lines.append(f"  corr(log_pos, residual_y): {corr([p['log2d134'] for p in core], res_y):+.4f}")
    lines.append(f"  corr(log_pos, delta_y): {corr([p['log2d134'] for p in core], [p['dy'] for p in core]):+.4f}")

    # H - log2(d)/2 vs min_delta
    h = 128.34570214660884
    hinge_vs_d = [h - p["log2d"] / 2 for p in core]
    lines.append("")
    lines.append("=== H - log2(d)/2 vs hinge gaps ===")
    lines.append(f"  corr(H-log2(d)/2, delta_y): {corr(hinge_vs_d, [p['dy'] for p in core]):+.4f}")
    lines.append(f"  corr(H-log2(d)/2, min_delta): {corr(hinge_vs_d, [p['min_d'] for p in core]):+.4f}")

    lines.append("")
    lines.append("=== closer-side split: corr(log_pos, min_delta) ===")
    for side in ("x", "y"):
        sub = [p for p in core if p["closer"] == side]
        if len(sub) >= 3:
            c = corr([p["log2d134"] for p in sub], [p["min_d"] for p in sub])
            lines.append(f"  closer={side}: {c:+.4f}  n={len(sub)}")

    lines.append("")
    lines.append("=== sanity: log2(d) vs puzzle n (should be ~1.0) ===")
    lines.append(f"  corr(log2(d), n): {corr([p['log2d'] for p in core], [p['n'] for p in core]):+.4f}")

    lines.append("")
    lines.append("=== anchor puzzles ===")
    for n in (130, 135, 155, 160):
        hit = next((p for p in pairs if p["n"] == n), None)
        if hit:
            lines.append(
                f"  P{n}: log2(d)={hit['log2d']:.3f} log_pos={hit['log2d134']:.3f} "
                f"min_d={hit['min_d']:.4f} dy={hit['dy']:.4f}"
            )

    lines.append("")
    lines.append("=== tightest min_delta (solved) ===")
    for p in sorted(core, key=lambda x: x["min_d"])[:10]:
        lines.append(
            f"  P{p['n']:3d} log_pos={p['log2d134']:.3f} min_d={p['min_d']:.4f} closer={p['closer']}"
        )

    text = "\n".join(lines)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
