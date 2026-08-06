#!/usr/bin/env python3
"""Puzzles 5-135 step 5: k_x/k_y per-puzzle height mod vs priv d.

Table columns:
  puzzle | d | kx_r1 | dist | kx_r2 | dist | ky_r1 | dist | ky_r2 | dist | best

r1 = floor_lift     = (k mod 2^n) + 2^n
r2 = height_residue = k mod (2^n - 1)
dist = |d - result|

Win condition: stable distance *pattern* across solved puzzles (not a single exact hit).
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import PUZZLE_LIST, build_config  # noqa: E402
from ecdlp_full_pipeline import PuzzleConfig, apply_puzzle_defaults  # noqa: E402
from k_xy_mod134_distance import bridge_k_pair, puzzle_k_transforms  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402


def in_band(n: int, v: int) -> bool:
    lo = 1 << (n - 1)
    top = (1 << n) - 1
    return lo <= v <= top


def lane_row(n: int, d: int, k: int) -> dict:
    t = puzzle_k_transforms(n, k)
    r1, r2 = t["floor_lift"], t["height_residue"]
    if not in_band(n, r1) or not in_band(n, r2):
        raise ValueError(f"P{n} transform out of band: r1={r1} r2={r2} LO..TOP")
    d1, d2 = abs(d - r1), abs(d - r2)
    return {
        "r1": r1,
        "r2": r2,
        "dist_r1": d1,
        "dist_r2": d2,
        "dist_r1_bits": d1.bit_length(),
        "dist_r2_bits": d2.bit_length(),
    }


def analyze_pattern(rows: list[dict]) -> str:
    """Summarize cross-puzzle stability of distance-bit patterns."""
    if not rows:
        return "No solved rows."

    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("PATTERN ANALYSIS (win = stable law across solved puzzles)")
    lines.append("=" * 72)

    # Which lane+transform wins most often?
    best_ctr = Counter(r["best"] for r in rows)
    lines.append("\nBest column frequency (smallest |d - result|):")
    for name, cnt in best_ctr.most_common():
        lines.append(f"  {name:12s}  {cnt:2d}/{len(rows)}")

    # r1 vs r2 win rate per lane
    for lane in ("kx", "ky"):
        r1_wins = sum(1 for r in rows if r[f"{lane}_r1_dist"] <= r[f"{lane}_r2_dist"])
        lines.append(f"\n{lane}: r1 closer than r2 in {r1_wins}/{len(rows)} puzzles")

    lines.append("\nDistance-bit gap from puzzle height n (n - dist_bits):")
    lines.append(f"  {'puzzle':>6}  {'kx_r1':>6}  {'kx_r2':>6}  {'ky_r1':>6}  {'ky_r2':>6}  best")
    gaps: dict[str, list[int]] = {k: [] for k in ("kx_r1", "kx_r2", "ky_r1", "ky_r2")}
    for r in rows:
        n = r["puzzle"]
        g = {
            "kx_r1": n - r["kx_r1_dist_bits"],
            "kx_r2": n - r["kx_r2_dist_bits"],
            "ky_r1": n - r["ky_r1_dist_bits"],
            "ky_r2": n - r["ky_r2_dist_bits"],
        }
        for k, v in g.items():
            gaps[k].append(v)
        lines.append(
            f"  {n:6d}  {g['kx_r1']:6d}  {g['kx_r2']:6d}  {g['ky_r1']:6d}  {g['ky_r2']:6d}  {r['best']}"
        )

    # Stable gap stats
    lines.append("\nGap = n - dist_bits (mean / stdev-ish range):")
    for col in ("kx_r1", "kx_r2", "ky_r1", "ky_r2"):
        vals = gaps[col]
        mean = sum(vals) / len(vals)
        spread = max(vals) - min(vals)
        mode = Counter(vals).most_common(1)[0]
        lines.append(
            f"  {col:6s}  mean={mean:5.1f}  min={min(vals):3d}  max={max(vals):3d}  "
            f"spread={spread:3d}  mode={mode[0]} ({mode[1]}x)"
        )

    # Check fixed-gap hypotheses (H-10 style: gap = 10?)
    for target in (0, 5, 10, 15):
        hits = sum(1 for r in rows if (r["puzzle"] - r["best_dist_bits"]) == target)
        if hits:
            lines.append(f"\n  n - best_dist_bits == {target}: {hits}/{len(rows)} puzzles")

    # Exact hits
    exact = [r for r in rows if r["best_dist"] == 0]
    lines.append(f"\nExact hits (dist=0): {len(exact)}/{len(rows)}")
    if exact:
        for r in exact:
            lines.append(f"  P{r['puzzle']} via {r['best']}")

    # Stable gap on *best* column only (the meaningful probe)
    best_gaps = [r["gap_n_minus_best"] for r in rows]
    lines.append("\nBest-column gap = n - best_dist_bits:")
    lines.append(f"  min={min(best_gaps)}  max={max(best_gaps)}  mean={sum(best_gaps)/len(best_gaps):.1f}  spread={max(best_gaps)-min(best_gaps)}")
    gap_ctr = Counter(best_gaps)
    lines.append("  histogram: " + ", ".join(f"{g}:{c}" for g, c in sorted(gap_ctr.items())))

    lines.append("\nVerdict:")
    best_spread = max(best_gaps) - min(best_gaps)
    if best_spread <= 10:
        lines.append(
            f"  STABLE best-column gap: n - best_dist_bits in [{min(best_gaps)}, {max(best_gaps)}] "
            f"(spread {best_spread}) across {len(rows)} puzzles."
        )
        lines.append(
            f"  Dominant transform: r2 (height_residue) wins {best_ctr.get('kx_r2',0)+best_ctr.get('ky_r2',0)}/{len(rows)}; "
            f"r1 (floor_lift) wins {best_ctr.get('kx_r1',0)+best_ctr.get('ky_r1',0)}/{len(rows)}."
        )
        lines.append(
            f"  No exact hits — win condition is this gap law, not dist=0. "
            f"For P135 expect best_dist_bits ≈ 135 - gap (gap typically 0–6)."
        )
    else:
        lines.append(
            f"  Loose best-column gap spread {best_spread}; lane/transform choice varies by puzzle."
        )

    return "\n".join(lines)


def main() -> None:
    keys = parse_53125()
    csv_rows: list[dict] = []

    print("Per-puzzle mod: r1=(k mod 2^(N-1))+2^(N-1), r2=k mod (2^N-1) [band lift]")
    print()
    hdr = (
        f"{'puzzle':>6} | {'d':>40} | "
        f"{'kx_r1':>22} {'dist':>6} | {'kx_r2':>22} {'dist':>6} | "
        f"{'ky_r1':>22} {'dist':>6} | {'ky_r2':>22} {'dist':>6} | best"
    )
    print(hdr)
    print("-" * len(hdr))

    for n in PUZZLE_LIST:
        if n not in keys:
            print(f"{n:6d}  MISSING")
            continue

        is_open = n == 135 or keys[n].d == 0
        d = None if is_open else keys[n].d

        try:
            if n == 135:
                cfg = PuzzleConfig(puzzle_num=135, row=2)
                apply_puzzle_defaults(cfg)
            else:
                cfg = build_config(keys[n])
            kx, ky, _, _ = bridge_k_pair(cfg)
        except Exception as exc:
            print(f"{n:6d}  ERROR: {exc}")
            continue

        if d is None:
            tx = puzzle_k_transforms(n, kx)
            ty = puzzle_k_transforms(n, ky)
            print(
                f"{n:6d} | OPEN | "
                f"kx_r1={tx['floor_lift']} | kx_r2={tx['height_residue']} | "
                f"ky_r1={ty['floor_lift']} | ky_r2={ty['height_residue']}"
            )
            csv_rows.append(
                {
                    "puzzle": n,
                    "d": "",
                    "kx_r1": tx["floor_lift"],
                    "kx_r1_dist": "",
                    "kx_r2": tx["height_residue"],
                    "kx_r2_dist": "",
                    "ky_r1": ty["floor_lift"],
                    "ky_r1_dist": "",
                    "ky_r2": ty["height_residue"],
                    "ky_r2_dist": "",
                    "best": "OPEN",
                    "best_dist": "",
                    "best_dist_bits": "",
                }
            )
            continue

        kx_row = lane_row(n, d, kx)
        ky_row = lane_row(n, d, ky)

        candidates = [
            ("kx_r1", kx_row["dist_r1"], kx_row["dist_r1_bits"]),
            ("kx_r2", kx_row["dist_r2"], kx_row["dist_r2_bits"]),
            ("ky_r1", ky_row["dist_r1"], ky_row["dist_r1_bits"]),
            ("ky_r2", ky_row["dist_r2"], ky_row["dist_r2_bits"]),
        ]
        best_name, best_dist, best_bits = min(candidates, key=lambda x: x[1])

        rec = {
            "puzzle": n,
            "d": d,
            "d_bits": d.bit_length(),
            "kx": kx,
            "ky": ky,
            "kx_r1": kx_row["r1"],
            "kx_r1_dist": kx_row["dist_r1"],
            "kx_r1_dist_bits": kx_row["dist_r1_bits"],
            "kx_r2": kx_row["r2"],
            "kx_r2_dist": kx_row["dist_r2"],
            "kx_r2_dist_bits": kx_row["dist_r2_bits"],
            "ky_r1": ky_row["r1"],
            "ky_r1_dist": ky_row["dist_r1"],
            "ky_r1_dist_bits": ky_row["dist_r1_bits"],
            "ky_r2": ky_row["r2"],
            "ky_r2_dist": ky_row["dist_r2"],
            "ky_r2_dist_bits": ky_row["dist_r2_bits"],
            "best": best_name,
            "best_dist": best_dist,
            "best_dist_bits": best_bits,
            "gap_n_minus_best": n - best_bits,
        }
        csv_rows.append(rec)

        print(
            f"{n:6d} | {d:40d} | "
            f"{kx_row['r1']:22d} {kx_row['dist_r1']:6d} | "
            f"{kx_row['r2']:22d} {kx_row['dist_r2']:6d} | "
            f"{ky_row['r1']:22d} {ky_row['dist_r1']:6d} | "
            f"{ky_row['r2']:22d} {ky_row['dist_r2']:6d} | "
            f"{best_name} ({best_bits}b)"
        )

    solved = [r for r in csv_rows if r.get("d") and r["d"] != ""]
    analysis = analyze_pattern(solved)
    print()
    print(analysis)

    out = ROOT / "ARCHIVE" / "k_xy_distance_table_5_135.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "puzzle",
        "d",
        "d_bits",
        "kx",
        "ky",
        "kx_r1",
        "kx_r1_dist",
        "kx_r1_dist_bits",
        "kx_r2",
        "kx_r2_dist",
        "kx_r2_dist_bits",
        "ky_r1",
        "ky_r1_dist",
        "ky_r1_dist_bits",
        "ky_r2",
        "ky_r2_dist",
        "ky_r2_dist_bits",
        "best",
        "best_dist",
        "best_dist_bits",
        "gap_n_minus_best",
    ]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(csv_rows)

    report = ROOT / "ARCHIVE" / "k_xy_distance_pattern_analysis.txt"
    report.write_text(analysis + f"\n\nCSV: {out}\n", encoding="utf-8")
    print(f"\nWrote {out}")
    print(f"Wrote {report}")


if __name__ == "__main__":
    main()
