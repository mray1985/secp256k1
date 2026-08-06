#!/usr/bin/env python3
"""Numeric ratios: height=2^n-1, result=height-d, complement=N-result."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_da_sequence import PUZZLE
from puzzle_keys_53125 import parse_53125

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def d_for(n: int, keys: dict) -> int | None:
    if n in PUZZLE:
        return PUZZLE[n]
    if n in keys:
        return keys[n].d
    return None


def main() -> None:
    keys = parse_53125()
    rows: list[dict] = []
    prev_d: int | None = None
    prev_result: int | None = None

    for n in range(1, 131):
        d = d_for(n, keys)
        if d is None:
            continue
        height = 2**n - 1
        lo = 2 ** (n - 1)
        result = height - d
        complement = N - result
        row = {
            "puzzle": n,
            "d": d,
            "height": height,
            "result": result,
            "complement": complement,
            "d_over_height": d / height,
            "result_over_height": result / height,
            "d_over_lo": d / lo,
            "result_over_d": result / d if d else 0,
            "d_over_prev_d": d / prev_d if prev_d else "",
            "result_over_prev_result": result / prev_result if prev_result and result else "",
        }
        rows.append(row)
        prev_d = d
        prev_result = result if result else prev_result

    txt = ROOT / "ARCHIVE" / "puzzle_ratios_P1_P130.txt"
    csv_path = ROOT / "ARCHIVE" / "puzzle_ratios_P1_P130.csv"

    lines = [
        "PUZZLE NUMERIC RATIOS (solved only, through P130)",
        "  height = 2^n - 1",
        "  result = height - d",
        "  complement = N - result",
        "",
        "P    n   d/height   result/height   d/LO      result/d    d/d_prev   result/result_prev",
        "---  --  --------   -------------   ------    --------    --------   ------------------",
    ]
    for r in rows:
        dpr = f"{r['d_over_prev_d']:.6f}" if r["d_over_prev_d"] != "" else "-"
        rpr = (
            f"{r['result_over_prev_result']:.6f}"
            if r["result_over_prev_result"] != ""
            else "-"
        )
        lines.append(
            f"P{r['puzzle']:02d}  {r['puzzle']:2d}  "
            f"{r['d_over_height']:.6f}   {r['result_over_height']:.6f}      "
            f"{r['d_over_lo']:.6f}  {r['result_over_d']:.6f}   {dpr}  {rpr}"
        )

    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("\n".join(lines[:10]))
    print("...")
    print("\n".join(lines[-8:]))
    print(f"\n{len(rows)} solved puzzles through P130")
    print(f"wrote {txt}")
    print(f"wrote {csv_path}")


if __name__ == "__main__":
    main()
