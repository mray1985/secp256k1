#!/usr/bin/env python3
"""
Canonical fractional sqrt-half-logs: {log2 sqrt(v)} = {log2(v)/2}

d does not "land back" at hinge in full log space; test whether
{log2 sqrt d} correlates with {log2 sqrt x}, {log2 sqrt y}, and cross gaps.
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
from ecdlp_full_pipeline import N, p, y_roots  # noqa: E402
from puzzle_keys_53125 import parse_53125

PN = p - N
REPORT = ROOT / "ARCHIVE" / "hinge_sqrt_root_canonical.txt"
CSV_OUT = ROOT / "ARCHIVE" / "hinge_sqrt_root_canonical.csv"


def frac(x: float) -> float:
    return x - math.floor(x)


def l2s(v: int) -> float:
    """log2(sqrt(v)) full."""
    if v <= 0:
        return float("nan")
    getcontext().prec = 80
    return float(Decimal(v).ln() / Decimal(2).ln()) / 2


def f2s(v: int) -> float:
    """{log2 sqrt(v)} canonical fraction."""
    return frac(l2s(v))


def corr(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else 0.0


def main() -> int:
    getcontext().prec = 80
    fh = frac(float(Decimal(PN).ln() / Decimal(2).ln()))
    fh2 = frac(float(Decimal(PN).ln() / Decimal(2).ln()) / 2)

    keys = parse_53125()
    rows = []

    for n, pk in sorted(keys.items()):
        if pk.d <= 0:
            continue
        d, dm = pk.d, N - pk.d
        try:
            cfg = build_config(pk)
            slots = cfg.Px
            tr = cfg.row
        except Exception:
            slots = [pk.px]
            tr = 0

        fd = f2s(d)
        fnd = f2s(dm)
        while len(slots) < 3:
            slots.append(slots[-1])

        for i, xi in enumerate(slots[:3]):
            yp, yn = y_roots(xi)
            for yl, yi in (("y", yp), ("-y", yn)):
                fx, fy = f2s(xi), f2s(yi)
                is_true = i == tr and yi == pk.py
                rows.append(
                    {
                        "puzzle": n,
                        "slot": i,
                        "true_row": tr,
                        "y_branch": yl,
                        "is_true": is_true,
                        "f_sqrt_d": fd,
                        "f_sqrt_nd": fnd,
                        "f_sqrt_x": fx,
                        "f_sqrt_y": fy,
                        "x_minus_d": fx - fd,
                        "y_minus_d": fy - fd,
                        "y_minus_x": fy - fx,
                        "x_minus_H2": fx - fh2,
                        "y_minus_H": fy - fh,
                        "d_minus_H2": fd - fh2,
                        "nd_minus_H2": fnd - fh2,
                        "two_f_sqrt_d": frac(2 * fd),
                        "two_f_sqrt_x": frac(2 * fx),
                    }
                )

    true = [r for r in rows if r["is_true"]]
    ns = [r["puzzle"] for r in true]

    pairs = [
        ("f_sqrt_d", "f_sqrt_x", "sqrt d vs sqrt x"),
        ("f_sqrt_d", "f_sqrt_y", "sqrt d vs sqrt y"),
        ("f_sqrt_x", "f_sqrt_y", "sqrt x vs sqrt y"),
        ("f_sqrt_d", "f_sqrt_nd", "sqrt d vs sqrt N-d"),
        ("x_minus_d", "y_minus_x", "x-d vs y-x"),
        ("x_minus_d", "y_minus_d", "x-d vs y-d"),
        ("d_minus_H2", "x_minus_H2", "d-H/2 vs x-H/2"),
        ("f_sqrt_d", "two_f_sqrt_x", "sqrt d vs {2 sqrt x}"),
        ("two_f_sqrt_d", "two_f_sqrt_x", "{2 sqrt d} vs {2 sqrt x}"),
    ]

    lines = [
        "CANONICAL {log2 sqrt(v)} correlation study",
        f"{{H}}={fh:.6f}  {{H/2}}={fh2:.6f}  (fixed shelves)",
        f"true-branch rows: {len(true)}",
        "",
        "All values are fractional parts of log2(sqrt(.)) unless noted.",
        "",
        "=== correlations (true slot + true y only) ===",
    ]
    for a, b, label in pairs:
        lines.append(
            f"  {label:28} corr={corr([r[a] for r in true], [r[b] for r in true]):+.4f}"
        )

    lines.extend(["", "=== corr(puzzle n, canonical fraction) ==="])
    for key, label in [
        ("f_sqrt_d", "sqrt d"),
        ("f_sqrt_x", "sqrt x"),
        ("f_sqrt_y", "sqrt y"),
        ("x_minus_d", "sqrt x - sqrt d"),
        ("y_minus_H", "sqrt y - H"),
        ("x_minus_H2", "sqrt x - H/2"),
    ]:
        lines.append(f"  n vs {label:20} corr={corr(ns, [r[key] for r in true]):+.4f}")

    lines.extend(["", "=== mean cross gaps (true branch) ==="])
    for key in ("x_minus_d", "y_minus_d", "y_minus_x", "d_minus_H2", "x_minus_H2", "y_minus_H"):
        vals = [r[key] for r in true]
        lines.append(
            f"  {key:14} mean={sum(vals)/len(vals):+.6f}  "
            f"std={math.sqrt(sum((v-sum(vals)/len(vals))**2 for v in vals)/len(vals)):.6f}"
        )

    lines.extend(["", "=== tightest |sqrt x - sqrt d| (true branch) ==="])
    for r in sorted(true, key=lambda x: abs(x["x_minus_d"]))[:12]:
        lines.append(
            f"  P{r['puzzle']:3d} x-d={r['x_minus_d']:+.6f}  "
            f"fx={r['f_sqrt_x']:.4f} fd={r['f_sqrt_d']:.4f}  "
            f"x-H2={r['x_minus_H2']:+.4f} y-H={r['y_minus_H']:+.4f}"
        )

    lines.extend(["", "=== |x-d| < 0.02 count ==="])
    tight = [r for r in true if abs(r["x_minus_d"]) < 0.02]
    lines.append(f"  {len(tight)}/{len(true)} puzzles")
    for r in sorted(tight, key=lambda x: abs(x["x_minus_d"])):
        lines.append(f"    P{r['puzzle']} {r['x_minus_d']:+.6f}")

    lines.extend(["", "=== P135 (RSZ pubkey, no d) ==="])
    from hashkeys_rsz import PUZZLE_RSZ  # noqa: WPS433

    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn
    fx, fy = f2s(px), f2s(py)
    fyn = f2s(yn if py == yp else yp)
    lines.append(f"  {{sqrt x}}={fx:.6f}  {{sqrt y}}={fy:.6f}  {{sqrt -y}}={fyn:.6f}")
    lines.append(f"  x-H2={fx-fh2:+.6f}  y-H={fy-fh:+.6f}  -y-H={fyn-fh:+.6f}")
    lines.append(f"  y-x={fy-fx:+.6f}  -y-x={fyn-fx:+.6f}")

    lines.extend(["", "=== read ==="])
    lines.append("  Fractions do not compose back to hinge when you square (2*f wraps mod 1).")
    lines.append("  Strongest usable link on true branch: sqrt-x minus sqrt-d (x-d column).")
    lines.append("  sqrt-d vs sqrt-y: weak global corr; per-puzzle x-d can be tight (P27).")

    text = "\n".join(lines)
    REPORT.write_text(text + "\n", encoding="utf-8")
    with CSV_OUT.open("w", newline="", encoding="utf-8") as fh_out:
        w = csv.DictWriter(fh_out, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(text)
    print(f"\nwrote {REPORT}")
    print(f"wrote {CSV_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
