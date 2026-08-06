#!/usr/bin/env python3
"""
Per-slot d (for science): E_d recalculated per x-slot, not copied.

d candidates per slot i:
  lambda_i     = lambda_ns[i] from N-side bridge (court row i)
  lambda_band  = band representative of lambda_i in puzzle band
  d_cbrt_i     = i-th mod-N cube root of true d (when 3 exist)
  d_true       = known d (only on true row, oracle reference)
  d_shared     = same true d every row (previous script behaviour)
"""

from __future__ import annotations

import csv
import math
import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import build_config  # noqa: E402
from ecdlp_full_pipeline import N, all_cube_roots_mod, p, puzzle_band, y_roots  # noqa: E402
from genesis_calibration import bridge_state  # noqa: E402
from puzzle_keys_53125 import parse_53125

REPORT = ROOT / "ARCHIVE" / "hinge_normalization_per_slot_d.txt"
CSV_OUT = ROOT / "ARCHIVE" / "hinge_normalization_per_slot_d.csv"

PN = p - N


def frac(x: float) -> float:
    return x - math.floor(x)


def log2_sqrt(v: int) -> float:
    if v <= 0:
        return float("nan")
    getcontext().prec = 80
    return float(Decimal(v).ln() / Decimal(2).ln()) / 2


def band_rep(c: int, lo: int, hi: int) -> int:
    return lo + (c % lo)


def e_d_from_scalar(d: int, fh2: float) -> tuple[float, float]:
    lsd = log2_sqrt(d)
    lsdm = log2_sqrt(N - d) if d < N else float("nan")
    return frac(lsd) - fh2, frac(lsdm) - fh2


def cube_roots_d_mod_n(d: int) -> list[int]:
    try:
        roots = all_cube_roots_mod(N, d % N)
        return sorted(set(r % N for r in roots))[:3]
    except Exception:
        return []


def main() -> int:
    getcontext().prec = 80
    h = float(Decimal(PN).ln() / Decimal(2).ln())
    fh2 = frac(h / 2)
    fh = frac(h)

    keys = parse_53125()
    rows = []

    for n, pk in sorted(keys.items()):
        if pk.d <= 0:
            continue
        try:
            cfg = build_config(pk)
            st = bridge_state(cfg)
            lns = st["lambda_ns"]
        except Exception as e:
            continue

        lo, hi, _ = puzzle_band(n)
        true_row = cfg.row
        d_true = pk.d
        cbrt_ds = cube_roots_d_mod_n(d_true)
        while len(cbrt_ds) < 3:
            cbrt_ds.append(cbrt_ds[-1] if cbrt_ds else d_true)

        slots = cfg.Px
        for i in range(3):
            xi = slots[i]
            yp, yn = y_roots(xi)
            lx = log2_sqrt(xi)
            ex = frac(lx) - fh2

            candidates = {
                "shared_d": d_true,
                "lambda_row": lns[i] % N,
                "lambda_band": band_rep(lns[i], lo, hi),
                "d_cbrt_slot": cbrt_ds[i],
                "d_true_oracle": d_true if i == true_row else None,
            }

            for y_label, yi in (("y", yp), ("-y", yn)):
                ly = log2_sqrt(yi)
                ey = frac(ly) - fh
                base = {
                    "puzzle": n,
                    "slot": i,
                    "true_row": true_row,
                    "y_branch": y_label,
                    "is_true_xy": i == true_row and yi == pk.py,
                    "E_x": ex,
                    "E_y": ey,
                }
                for d_name, d_val in candidates.items():
                    if d_val is None:
                        continue
                    ed, end = e_d_from_scalar(d_val, fh2)
                    rows.append(
                        {
                            **base,
                            "d_model": d_name,
                            "d_val_bits": d_val.bit_length(),
                            "E_d": ed,
                            "E_nd": end,
                            "E_x_minus_E_d": ex - ed,
                            "x_minus_d_frac": frac(lx) - frac(log2_sqrt(d_val)),
                            "in_band": lo <= d_val < hi,
                        }
                    )

    # summaries
    def mean_abs(vals):
        return sum(abs(v) for v in vals) / len(vals) if vals else float("nan")

    lines = [
        "PER-SLOT d experiment (for science)",
        f"{{H/2}}={fh2:.6f}  puzzles with bridge: {len(set(r['puzzle'] for r in rows))}",
        "",
        "d_model:",
        "  shared_d      = same true d on every row (OLD behaviour)",
        "  lambda_row    = lambda_ns[i] per court row",
        "  lambda_band   = band rep of lambda_ns[i]",
        "  d_cbrt_slot   = mod-N cube root branch i of true d",
        "  d_true_oracle = true d only on matching row",
        "",
    ]

    for model in ("shared_d", "lambda_row", "lambda_band", "d_cbrt_slot", "d_true_oracle"):
        sub = [r for r in rows if r["d_model"] == model and r["is_true_xy"]]
        if not sub:
            sub = [r for r in rows if r["d_model"] == model and r["y_branch"] == "y"]
        if not sub:
            continue
        lines.append(f"=== {model} (true xy or y branch) ===")
        lines.append(f"  mean |E_d|     = {mean_abs([r['E_d'] for r in sub]):.4f}")
        lines.append(f"  mean |E_x-E_d| = {mean_abs([r['E_x_minus_E_d'] for r in sub]):.4f}")
        lines.append(f"  mean |E_x|     = {mean_abs([r['E_x'] for r in sub]):.4f}")
        in_band = sum(1 for r in sub if r["in_band"])
        lines.append(f"  d in puzzle band: {in_band}/{len(sub)}")
        lines.append("")

    # P135 unsolved if in keys without d - skip
    for n in (130, 135):
        sub = [r for r in rows if r["puzzle"] == n and r["is_true_xy"]]
        if not sub:
            sub = [r for r in rows if r["puzzle"] == n and r["true_row"] == r["slot"]]
        if sub:
            lines.append(f"=== P{n} per-slot (true row) ===")
            for model in ("shared_d", "lambda_row", "lambda_band", "d_cbrt_slot"):
                r = next((x for x in sub if x["d_model"] == model and x["y_branch"] == "y"), None)
                if r:
                    lines.append(
                        f"  {model:14s} E_x={r['E_x']:+.6f} E_d={r['E_d']:+.6f} "
                        f"Ex-Ed={r['E_x_minus_E_d']:+.6f} in_band={r['in_band']}"
                    )

    # best model per puzzle: min |E_x - E_d| on true xy
    lines.extend(["", "=== best d_model per puzzle (min |E_x-E_d| on true branch) ==="])
    wins = {m: 0 for m in ("shared_d", "lambda_row", "lambda_band", "d_cbrt_slot", "d_true_oracle")}
    for n in sorted(set(r["puzzle"] for r in rows)):
        cands = [
            r
            for r in rows
            if r["puzzle"] == n and r["is_true_xy"]
        ]
        if not cands:
            cands = [r for r in rows if r["puzzle"] == n and r["slot"] == r["true_row"] and r["y_branch"] == "y"]
        if not cands:
            continue
        best = min(cands, key=lambda r: abs(r["E_x_minus_E_d"]))
        wins[best["d_model"]] = wins.get(best["d_model"], 0) + 1
        if n in (130, 115, 135) or abs(best["E_x_minus_E_d"]) < 0.01:
            lines.append(
                f"  P{n:3d} best={best['d_model']:14s} |Ex-Ed|={abs(best['E_x_minus_E_d']):.6f} "
                f"E_x={best['E_x']:+.4f} E_d={best['E_d']:+.4f}"
            )
    lines.append("")
    lines.append("wins (best |E_x-E_d| on true branch): " + ", ".join(f"{k}={v}" for k, v in sorted(wins.items(), key=lambda x: -x[1])))

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with CSV_OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("\n".join(lines))
    print(f"\nwrote {REPORT}")
    print(f"wrote {CSV_OUT} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
