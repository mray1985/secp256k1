#!/usr/bin/env python3
"""Emit each series sorted by value, tagged with source puzzle n (and d)."""

from __future__ import annotations

import json
import math
from pathlib import Path

from scan_log_ratio_cross_puzzle import load_rows

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

    series = {
        "n": [(r.n, r.n, r.d) for r in rows],
        "d": [(r.d, r.n, r.d) for r in rows],
        "log2d": [(math.log2(r.d), r.n, r.d) for r in rows],
        "Px": [(r.Px, r.n, r.d) for r in rows],
        "Py": [(r.Py, r.n, r.d) for r in rows],
        "Pmy": [(r.Pmy, r.n, r.d) for r in rows],
        "r": [(r.r, r.n, r.d) for r in rows],
        "s": [(r.s, r.n, r.d) for r in rows],
        "z": [(r.z, r.n, r.d) for r in rows],
        "Ry": [(r.Ry, r.n, r.d) for r in rows],
        "log_Px": [(math.log(r.Px), r.n, r.d) for r in rows],
        "log_Py": [(math.log(r.Py), r.n, r.d) for r in rows],
        "log_Pmy": [(math.log(r.Pmy), r.n, r.d) for r in rows],
        "log_r": [(math.log(r.r), r.n, r.d) for r in rows],
        "log_s": [(math.log(r.s), r.n, r.d) for r in rows],
        "log_z": [(math.log(r.z), r.n, r.d) for r in rows],
        "log_Ry": [(math.log(r.Ry), r.n, r.d) for r in rows],
    }

    ordered: dict[str, list[dict]] = {}
    for name, triples in series.items():
        ranked = sorted(enumerate(triples), key=lambda it: it[1][0])
        entries = []
        for linear_rank, (orig_idx, (val, puzzle_n, d)) in enumerate(ranked, start=1):
            entries.append(
                {
                    "linear_rank": linear_rank,  # 1 = smallest value
                    "value": val if not isinstance(val, float) else val,
                    "value_repr": str(val) if isinstance(val, int) else repr(val),
                    "puzzle_n": puzzle_n,
                    "d": d,
                    "catalog_order_index": orig_idx,  # 0 = lowest puzzle n in cohort
                }
            )
        ordered[name] = entries

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "linear_order_with_source_n.json"
    path.write_text(
        json.dumps({"cohort": len(rows), "series": ordered}, indent=2, default=str),
        encoding="utf-8",
    )

    # Human-readable tables
    md_lines = [
        "# Linear order with source puzzle n",
        "",
        f"Cohort: {len(rows)}. Each series sorted ascending by value.",
        "`linear_rank` 1 = smallest. `puzzle_n` = puzzle it came from.",
        "",
    ]
    show = ["Px", "Py", "Pmy", "r", "s", "z", "Ry", "d", "log2d"]
    for name in show:
        md_lines.append(f"## {name}")
        md_lines.append("")
        md_lines.append("| linear_rank | value | puzzle_n | d |")
        md_lines.append("|------------:|------:|---------:|---|")
        for e in ordered[name]:
            v = e["value"]
            if isinstance(v, float):
                vs = f"{v:.15g}"
            else:
                vs = str(v)
            md_lines.append(
                f"| {e['linear_rank']} | `{vs}` | **{e['puzzle_n']}** | `{e['d']}` |"
            )
        md_lines.append("")

    md_path = OUT / "LINEAR_ORDER_WITH_SOURCE_N.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    # Print compact view to stdout: rank -> puzzle_n for each limb
    for name in show:
        print(f"\n=== {name} (ascending value) rank -> puzzle_n [value] ===")
        for e in ordered[name]:
            v = e["value"]
            if isinstance(v, float):
                vs = f"{v:.6g}"
            else:
                vs = str(v)
            print(f"  rank {e['linear_rank']:2d}  puzzle_n={e['puzzle_n']:3d}  value={vs}")

    # Compact sequences + full listing
    full_path = OUT / "LINEAR_ORDER_FULL.txt"
    with full_path.open("w", encoding="utf-8") as fh:
        fh.write(f"cohort={len(rows)}\n")
        fh.write("Each block: sorted ascending by value.\n")
        fh.write("columns: linear_rank  puzzle_n  value\n\n")
        for name in show + ["n", "log_Px", "log_Py", "log_r", "log_s", "log_z", "log_Ry"]:
            if name not in ordered:
                continue
            fh.write("=" * 72 + "\n")
            fh.write(f"{name}\n")
            fh.write("=" * 72 + "\n")
            for e in ordered[name]:
                v = e["value"]
                vs = f"{v:.15g}" if isinstance(v, float) else str(v)
                fh.write(f"{e['linear_rank']:3d}  n={e['puzzle_n']:3d}  {vs}\n")
            seq = ",".join(str(e["puzzle_n"]) for e in ordered[name])
            fh.write(f"\npuzzle_n sequence (small->large {name}):\n{seq}\n\n")

    print(f"\nwrote {path}")
    print(f"wrote {md_path}")
    print(f"wrote {full_path}")


if __name__ == "__main__":
    main()
