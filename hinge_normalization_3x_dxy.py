#!/usr/bin/env python3
"""
Hinge normalization on full 3-slot lattice:

  row i in {0,1,2}:  d, N-d, x_i, y_i, -y_i
  (three cube-root x-slots; same d each row)

  E_x = {log2(sqrt(x))} - {H/2}
  E_y = {log2(sqrt(y))} - {H}
  E_d = {log2(sqrt(d))} - {H/2}
  E_nd = {log2(sqrt(N-d))} - {H/2}

Also cross: {log2 sqrt x} - {log2 sqrt d}, etc.
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

from ecdlp_full_pipeline import N, all_cube_roots_mod_p, p, y_roots  # noqa: E402
from puzzle_keys_53125 import parse_53125

REPORT = ROOT / "ARCHIVE" / "hinge_normalization_3x_dxy.txt"
CSV_OUT = ROOT / "ARCHIVE" / "hinge_normalization_3x_dxy.csv"

PN = p - N


def frac(x: float) -> float:
    return x - math.floor(x)


def log2_sqrt(v: int) -> float:
    if v <= 0:
        return float("nan")
    getcontext().prec = 80
    return float(Decimal(v).ln() / Decimal(2).ln()) / 2


def corr(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else 0.0


def px_slots(py: int, witness_px: int) -> list[int]:
    res = (py * py - 7) % p
    roots = all_cube_roots_mod_p(res, witness=witness_px)
    if witness_px not in roots:
        roots = sorted(all_cube_roots_mod_p(res))
    else:
        roots = sorted(roots)
    while len(roots) < 3:
        roots.append(roots[-1] if roots else witness_px)
    return roots[:3]


def main() -> int:
    getcontext().prec = 80
    h = float(Decimal(PN).ln() / Decimal(2).ln())
    fh, fh2 = frac(h), frac(h / 2)

    keys = parse_53125()
    rows_out = []
    slot_rows = []

    for n, pk in sorted(keys.items()):
        if pk.d <= 0 or pk.px <= 0 or pk.py <= 0:
            continue
        d, dm = pk.d, N - pk.d
        lsd, lsdm = log2_sqrt(d), log2_sqrt(dm)
        ed = frac(lsd) - fh2
        end = frac(lsdm) - fh2

        slots = px_slots(pk.py, pk.px)
        true_slot = slots.index(pk.px) if pk.px in slots else 0

        for i, xi in enumerate(slots):
            yp, yn = y_roots(xi)
            for y_label, yi in (("y", yp), ("-y", yn)):
                ls = log2_sqrt(yi)
                lx = log2_sqrt(xi)
                ex = frac(lx) - fh2
                ey = frac(ls) - fh
                is_true = i == true_slot and yi == pk.py
                slot_rows.append(
                    {
                        "puzzle": n,
                        "slot": i,
                        "true_slot": true_slot,
                        "y_branch": y_label,
                        "is_true_xy": is_true,
                        "E_x": ex,
                        "E_y": ey,
                        "E_d": ed,
                        "E_nd": end,
                        "x_minus_d": frac(lx) - frac(lsd),
                        "y_minus_d": frac(ls) - frac(lsd),
                        "x_minus_nd": frac(lx) - frac(lsdm),
                        "y_minus_x": frac(ls) - frac(lx),
                    }
                )

        true_rows = [r for r in slot_rows if r["puzzle"] == n and r["slot"] == true_slot]
        true_xy = next((r for r in true_rows if r["is_true_xy"]), None)
        if true_xy is None:
            # fallback: match slot + even y parity
            true_xy = next(
                (r for r in true_rows if r["y_branch"] == ("y" if pk.py % 2 == 0 else "-y")),
                true_rows[0],
            )
        best_ey = min(true_rows, key=lambda r: abs(r["E_y"]))
        best_ex = min(true_rows, key=lambda r: abs(r["E_x"]))
        all_n = [r for r in slot_rows if r["puzzle"] == n]
        best_ey_any = min(all_n, key=lambda r: abs(r["E_y"]))
        best_ex_any = min(all_n, key=lambda r: abs(r["E_x"]))

        rows_out.append(
            {
                "puzzle": n,
                "true_slot": true_slot,
                "E_d": ed,
                "E_nd": end,
                "E_x_true_y": true_xy["E_x"],
                "E_y_true": true_xy["E_y"],
                "E_x_best_on_slot": best_ex["E_x"],
                "E_y_best_on_slot": best_ey["E_y"],
                "E_x_min_all18": best_ex_any["E_x"],
                "E_y_min_all18": best_ey_any["E_y"],
                "pick_y_branch": best_ey["y_branch"],
                "min_abs_Ed": min(abs(ed), abs(end)),
            }
        )

    # stats: single pubkey vs best-of-3x2
    ex1 = [r["E_x_true_y"] for r in rows_out]
    ey1 = [r["E_y_true"] for r in rows_out]
    exb = [r["E_x_min_all18"] for r in rows_out]
    eyb = [r["E_y_min_all18"] for r in rows_out]
    ns = [r["puzzle"] for r in rows_out]

    def stats(vals):
        m = sum(vals) / len(vals)
        s = math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals))
        return m, s, min(vals), max(vals)

    lines = [
        "HINGE NORMALIZATION: 3 x-slots x (d, N-d, x, y, -y)",
        f"H={h:.12f}  {{H}}={fh:.6f}  {{H/2}}={fh2:.6f}",
        f"solved puzzles: {len(rows_out)}  (3 slots x 2 y = 6 coord rows each)",
        "",
        "Per row i: same d, N-d; x_i = cube root slot; y_i, -y_i from y_roots(x_i)",
        "",
        "=== E on TRUE pubkey (known x slot + correct y) ===",
        f"  E_x: mean={stats(ex1)[0]:+.4f} std={stats(ex1)[1]:.4f} range=[{stats(ex1)[2]:+.4f},{stats(ex1)[3]:+.4f}]",
        f"  E_y: mean={stats(ey1)[0]:+.4f} std={stats(ey1)[1]:.4f} range=[{stats(ey1)[2]:+.4f},{stats(ey1)[3]:+.4f}]",
        f"  corr(n, E_x)={corr(ns, ex1):+.4f}  corr(n, E_y)={corr(ns, ey1):+.4f}",
        "",
        "=== E after MIN over 3 slots x 2 y branches (oracle best) ===",
        f"  min|E_x|: mean={sum(abs(x) for x in exb)/len(exb):.4f}  max={max(abs(x) for x in exb):.4f}",
        f"  min|E_y|: mean={sum(abs(y) for y in eyb)/len(eyb):.4f}  max={max(abs(y) for y in eyb):.4f}",
        "",
        "=== scalar d / N-d (same all 3 rows) ===",
        f"  E_d:  mean={sum(r['E_d'] for r in rows_out)/len(rows_out):+.4f}",
        f"  E_nd: mean={sum(r['E_nd'] for r in rows_out)/len(rows_out):+.4f}",
        f"  min(|E_d|,|E_nd|) mean={sum(r['min_abs_Ed'] for r in rows_out)/len(rows_out):.4f}",
        "",
        "=== cross fractional (true slot, true y) ===",
    ]
    xmd = []
    ymd = []
    for p in rows_out:
        tr = next(r for r in slot_rows if r["puzzle"] == p["puzzle"] and r["slot"] == p["true_slot"] and r["y_branch"] == ("y" if keys[p["puzzle"]].py % 2 == 0 else "-y"))
        xmd.append(tr["x_minus_d"])
        ymd.append(tr["y_minus_d"])
    def std(vals: list[float]) -> float:
        m = sum(vals) / len(vals)
        return math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals))

    lines.append(f"  {{log2 sqrt x}}-{{log2 sqrt d}}: mean={sum(xmd)/len(xmd):+.6f} std={std(xmd):.6f}")
    lines.append(f"  {{log2 sqrt y}}-{{log2 sqrt d}}: mean={sum(ymd)/len(ymd):+.6f}")

    lines.extend(["", "=== P135-style: true row detail (anchors) ==="])
    for n in (130, 135, 155, 160):
        if n in keys and keys[n].d > 0:
            r = next(x for x in rows_out if x["puzzle"] == n)
            lines.append(
                f"  P{n}: slot={r['true_slot']} E_x={r['E_x_true_y']:+.6f} E_y={r['E_y_true']:+.6f} "
                f"E_d={r['E_d']:+.6f} E_nd={r['E_nd']:+.6f} min18 Ey={r['E_y_min_all18']:+.6f}"
            )
        elif n == 135:
            # unsolved from RSZ
            from hashkeys_rsz import PUZZLE_RSZ  # noqa: WPS433

            rsz = PUZZLE_RSZ[135]
            px = int(rsz.pub_compressed[2:], 16)
            yp, yn = y_roots(px)
            py = yp if yp % 2 == 0 else yn
            slots = px_slots(py, px)
            ts = slots.index(px) if px in slots else 2
            lines.append(f"  P135 (unsolved): true slot={ts}")
            for i, xi in enumerate(slots):
                for yl, yi in (("y", yp), ("-y", yn)):
                    lx, ly = log2_sqrt(xi), log2_sqrt(yi)
                    mark = "*" if i == ts and yi == py else " "
                    lines.append(
                        f"    {mark} slot{i} {yl}: E_x={frac(lx)-fh2:+.6f} E_y={frac(ly)-fh:+.6f} "
                        f"x-d={frac(lx)-fh2:+.6f} (no d)"
                    )

    lines.extend(["", "=== all 3 slots for P130 (example) ==="])
    for r in slot_rows:
        if r["puzzle"] == 130:
            m = "TRUE" if r["is_true_xy"] else ""
            lines.append(
                f"  slot{r['slot']} {r['y_branch']:2s} {m:4s} E_x={r['E_x']:+.6f} E_y={r['E_y']:+.6f} "
                f"E_d={r['E_d']:+.6f} x-d={r['x_minus_d']:+.6f}"
            )

    lines.extend(["", "=== tightest |E_y| true pubkey ==="])
    for r in sorted(rows_out, key=lambda x: abs(x["E_y_true"]))[:8]:
        lines.append(
            f"  P{r['puzzle']:3d} slot={r['true_slot']} E_y={r['E_y_true']:+.6f} E_x={r['E_x_true_y']:+.6f} "
            f"E_d={r['E_d']:+.6f}"
        )

    lines.extend(["", "=== verdict ==="])
    if sum(abs(y) for y in eyb) / len(eyb) < 0.15:
        lines.append("  ORACLE min over 3x2 TIGHT — branch choice matters, hinge may be structural per slot")
    elif sum(abs(y) for y in ey1) / len(ey1) < sum(abs(y) for y in eyb) / len(eyb) * 0.5:
        lines.append("  TRUE branch already near best — single-pubkey E_y is meaningful")
    else:
        lines.append("  Wide spread on true branch; oracle min only modestly better")
    lines.append(f"  mean|E_y| true={sum(abs(y) for y in ey1)/len(ey1):.4f}  oracle={sum(abs(y) for y in eyb)/len(eyb):.4f}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with CSV_OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(slot_rows[0].keys()))
        w.writeheader()
        w.writerows(slot_rows)

    print("\n".join(lines))
    print(f"\nwrote {REPORT}")
    print(f"wrote {CSV_OUT} ({len(slot_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
