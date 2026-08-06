#!/usr/bin/env python3
"""Distance from mod 2^(n-1) and LO+(mod) bridge quantities to solved priv d."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from genesis_calibration import bridge_state  # noqa: E402
from compare_family_mirror_batch import PUZZLE_LIST, build_config  # noqa: E402
from ecdlp_full_pipeline import puzzle_band  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402


def lo_dist(d: int, val: int, lo: int) -> int:
    diff = (d - val) % lo
    return min(diff, lo - diff)


def main() -> None:
    keys = parse_53125()
    out_rows: list[dict] = []

    for n in PUZZLE_LIST:
        if n == 135 or n not in keys or keys[n].d == 0:
            continue
        pk = keys[n]
        d = pk.d
        lo, hi, _ = puzzle_band(n)
        two_n = 1 << n

        try:
            cfg = build_config(pk)
            st = bridge_state(cfg)
            o = st["oitc"]
            gap = st["gap"]
        except Exception as exc:
            out_rows.append({"n": n, "error": str(exc)})
            continue

        qty = {
            "shelf2": o.shelf2,
            "shelf3": o.shelf3,
            "shelf_y": o.shelf_y,
            "C_floor": o.c_floor,
            "res2": o.d_cube_res2,
            "lift2": o.d_cube_lift2,
            "res3": o.d_cube_res3,
            "lift3": o.d_cube_lift3,
            "res_y": o.d_cube_res_y,
            "GAP": gap,
        }

        row: dict = {
            "n": n,
            "d": d,
            "d_minus_LO": d - lo,
            "d_minus_LO_bits": (d - lo).bit_length(),
        }

        best_mod = (lo, "", "")
        best_plus = (lo, "", "")

        for name, q in qty.items():
            r_lo = q % lo
            r_2n = q % two_n
            plus_lo = lo + r_lo
            plus_2n = two_n + r_2n

            dm_lo = lo_dist(d, r_lo, lo)
            dm_2n = lo_dist(d, r_2n % lo, lo)
            dp_lo = lo_dist(d, plus_lo, lo) if lo <= plus_lo < hi else lo
            dp_2n = lo_dist(d, plus_2n, lo) if lo <= plus_2n < hi else lo

            row[f"{name}_modLO_dist"] = dm_lo
            row[f"{name}_modLO_bits"] = dm_lo.bit_length()
            row[f"{name}_mod2n_modLO_bits"] = dm_2n.bit_length()
            row[f"{name}_plusLO_dist"] = dp_lo if dp_lo < lo else ""
            row[f"{name}_plusLO_bits"] = dp_lo.bit_length() if dp_lo < lo else ""
            row[f"{name}_plus2n_modLO_bits"] = dp_2n.bit_length() if dp_2n < lo else ""

            if dm_lo < best_mod[0]:
                best_mod = (dm_lo, name, "Q mod LO")
            if dp_lo < best_plus[0]:
                best_plus = (dp_lo, name, "LO + Q mod LO")

        row["best_modLO_name"] = best_mod[1]
        row["best_modLO_dist"] = best_mod[0]
        row["best_modLO_bits"] = best_mod[0].bit_length()
        row["best_plusLO_name"] = best_plus[1]
        row["best_plusLO_dist"] = best_plus[0]
        row["best_plusLO_bits"] = best_plus[0].bit_length()
        out_rows.append(row)

    # Console summary
    print("mod 2^(n-1) vs LO+(mod) distances to priv d")
    print(f"{'n':>4} {'d-LO':>5} {'best mod LO':>22} {'best LO+mod':>22} {'shelf2+':>8} {'lift2+':>8}")
    print("-" * 78)
    for r in out_rows:
        if "error" in r:
            print(f"{r['n']:4d}  ERROR: {r['error'][:50]}")
            continue
        print(
            f"{r['n']:4d} {r['d_minus_LO_bits']:5d} "
            f"{r['best_modLO_name']+' '+str(r['best_modLO_bits'])+'b':>22} "
            f"{r['best_plusLO_name']+' '+str(r['best_plusLO_bits'])+'b':>22} "
            f"{r.get('shelf2_plusLO_bits',''):>8} "
            f"{r.get('lift2_plusLO_bits',''):>8}"
        )

    # P115 detail
    r115 = next((r for r in out_rows if r.get("n") == 115), None)
    if r115:
        print()
        print("P115 (solved calibration) — distances in bits:")
        for name in ("shelf2", "lift2", "lift3", "C_floor", "GAP"):
            print(
                f"  {name:8s}  mod LO: {r115[f'{name}_modLO_bits']:3d}b  "
                f"LO+mod: {r115.get(f'{name}_plusLO_bits',''):>3}b  "
                f"dist_mod={r115[f'{name}_modLO_dist']}"
            )

    # Exact hits (distance 0 on LO+mod)
    print()
    print("Exact LO+(Q mod LO) == d:")
    any_exact = False
    for r in out_rows:
        if "error" in r:
            continue
        for name in ("shelf2", "shelf3", "shelf_y", "C_floor", "lift2", "lift3", "res_y", "GAP"):
            if r.get(f"{name}_plusLO_dist") == 0:
                print(f"  P{r['n']}: {name}")
                any_exact = True
    if not any_exact:
        print("  (none across batch)")

    csv_path = ROOT / "ARCHIVE" / "mod_lo_distance_report.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for r in out_rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)
    print(f"\nWrote {csv_path}")


if __name__ == "__main__":
    main()
