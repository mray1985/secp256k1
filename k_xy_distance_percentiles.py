#!/usr/bin/env python3
"""Percentile |d - result| for kx_r1/r2, ky_r1/r2 across solved puzzles."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_IN = ROOT / "ARCHIVE" / "k_xy_distance_table_5_135.csv"
CSV_OUT = ROOT / "ARCHIVE" / "k_xy_distance_percentiles.txt"

PROBES = ("kx_r1", "kx_r2", "ky_r1", "ky_r2")
PCTS = (0, 5, 25, 50, 75, 95, 99, 100)
PCT_LABELS = ("min", "p5", "p25", "p50", "p75", "p95", "p99", "max")


def percentile(sorted_vals: list[int | float], p: float) -> float:
    if not sorted_vals:
        raise ValueError("empty")
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    k = (len(sorted_vals) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    return sorted_vals[f] + (k - f) * (sorted_vals[c] - sorted_vals[f])


def fmt_val(v: float, *, bits: bool) -> str:
    if bits:
        return str(int(round(v)))
    if v >= 1e9:
        return f"{v:.4e}"
    return str(int(round(v)))


def pct_table(vals: list[int], *, bits: bool) -> list[str]:
    s = sorted(vals)
    row: list[str] = []
    for p in PCTS:
        v = percentile(s, p) if p < 100 else float(s[-1])
        row.append(fmt_val(v, bits=bits))
    return row


def main() -> None:
    rows: list[dict] = []
    with CSV_IN.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["d"] or r.get("best") == "OPEN":
                continue
            rows.append(
                {
                    "puzzle": int(r["puzzle"]),
                    **{f"{p}_dist": int(r[f"{p}_dist"]) for p in PROBES},
                    **{f"{p}_dist_bits": int(r[f"{p}_dist_bits"]) for p in PROBES},
                    "best": r["best"],
                    "best_dist": int(r["best_dist"]),
                    "best_dist_bits": int(r["best_dist_bits"]),
                }
            )

    lines: list[str] = [
        f"Percentile distances to d — {len(rows)} solved puzzles (5–130 step 5)",
        "r1 = (k mod 2^(N-1)) + 2^(N-1);  r2 = k mod (2^N-1) band-lifted",
        "",
    ]

    hdr = f"{'probe':<10} " + " ".join(f"{lb:>10}" for lb in PCT_LABELS)

    for title, bits in (("RAW |d - result|", False), ("Distance (bits)", True)):
        lines.append(f"=== {title} ===")
        lines.append(hdr)
        for p in PROBES + ("best",):
            key = f"{p}_dist_bits" if bits else f"{p}_dist"
            vals = [r[key] for r in rows]
            row = pct_table(vals, bits=bits)
            lines.append(f"{p:<10} " + " ".join(f"{x:>10}" for x in row))
        lines.append("")

    # Closest-probe win counts
    lines.append("=== Closest to d (min of 4 probes) ===")
    wins = Counter(r["best"] for r in rows)
    for p in PROBES:
        lines.append(f"  {p}: {wins[p]}/{len(rows)}")
    lines.append("")

    # Per-puzzle table: dist_bits for each probe
    lines.append("=== Per-puzzle distance bits ===")
    lines.append(
        f"{'puzzle':>6} {'d_bits':>6} "
        + " ".join(f"{p+'_b':>8}" for p in PROBES)
        + f" {'best':>8} {'gap':>4}"
    )
    for r in sorted(rows, key=lambda x: x["puzzle"]):
        gap = r["puzzle"] - r["best_dist_bits"]
        lines.append(
            f"{r['puzzle']:6d} {r['puzzle']:6d} "
            + " ".join(f"{r[f'{p}_dist_bits']:8d}" for p in PROBES)
            + f" {r['best']:>8} {gap:4d}"
        )

    text = "\n".join(lines)
    CSV_OUT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nWrote {CSV_OUT}")


if __name__ == "__main__":
    main()
