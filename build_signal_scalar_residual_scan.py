#!/usr/bin/env python3
"""
Signal ↔ scalar residual / rank-correlation / nearest-neighbor scan.

Does NOT use expected = L + floor(frac(signal)·width).
Asks whether public signals order or cluster scalar behavior.

Writes ONLY under ARCHIVE/briefcase/misalignments/
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from build_complexity_operations_ledger import BETA, BETA_SQ, DELTA, N, inv, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "misalignments"

GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240
SIGNAL_NAMES = [
    "x_ratio",
    "y_ratio",
    "pmy_ratio",
    "packet_frac",
    "packet_defect_frac",
    "packet_N_frac",
    "packet_B4_frac",
    "gx_ratio",
    "px1_ratio",
    "px2_ratio",
    "p_to_n_floor_drift",  # 0 or 1 normalized
    "defect_displacement_frac",
]


def frac(x: float) -> float:
    return x - math.floor(x)


def fingerprint(px: int, py: int) -> dict[str, float]:
    pmy = (p - py) % p
    packet = float(f"{px}.{pmy}")
    packet_p = packet / float(p)
    px_r = px / float(p)
    py_r = py / float(p)
    pmy_r = pmy / float(p)
    gx_r = ((px * inv(GX, p)) % p) / float(p)
    px2 = (px * inv(BETA, p)) % p
    px1 = (px * inv(BETA_SQ, p)) % p
    floor_n = math.floor(packet_p * float(N))
    map_n = (N * px) // p
    drift = float(floor_n - map_n)  # 0 or 1
    defect_disp = packet_p * float(DELTA)
    b4 = float(((1 << 32) + 977) ** 4)
    return {
        "x_ratio": px_r,
        "y_ratio": py_r,
        "pmy_ratio": pmy_r,
        "packet_frac": frac(packet_p),
        "packet_defect_frac": frac(packet_p * float(DELTA)),
        "packet_N_frac": frac(packet_p * float(N)),
        "packet_B4_frac": frac(packet_p * b4),
        "gx_ratio": gx_r,
        "px1_ratio": px1 / float(p),
        "px2_ratio": px2 / float(p),
        "p_to_n_floor_drift": drift,
        "defect_displacement_frac": frac(defect_disp),
    }


def spearman(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0

    def ranks(vals: list[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = math.sqrt(sum((rx[i] - mx) ** 2 for i in range(n)))
    dy = math.sqrt(sum((ry[i] - my) ** 2 for i in range(n)))
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


def kendall_tau(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = xs[i] - xs[j]
            dy = ys[i] - ys[j]
            if dx == 0 or dy == 0:
                continue
            if dx * dy > 0:
                conc += 1
            else:
                disc += 1
    tot = conc + disc
    if tot == 0:
        return 0.0
    return (conc - disc) / tot


def verdict_corr(rho: float) -> str:
    a = abs(rho)
    if a < 0.15:
        return "REJECT"
    if a < 0.35:
        return "WEAK"
    if a < 0.60:
        return "PROMISING"
    return "STRONG"


def euclid(a: dict[str, float], b: dict[str, float], keys: list[str]) -> float:
    return math.sqrt(sum((a[k] - b[k]) ** 2 for k in keys))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()

    rows = []
    for n in range(1, 161):
        e = catalog[n]
        if not e.public_key:
            continue
        px, py = pubkey_xy(e.public_key)
        fp = fingerprint(px, py)
        lo, hi = e.range_min, e.range_max
        width = hi - lo + 1
        row = {
            "puzzle": n,
            "solved": e.solved,
            "fingerprint": fp,
        }
        if e.solved and e.private_key > 0:
            d = e.private_key
            scalar_pos = (d - lo) / width
            row["d"] = str(d)
            row["scalar_position"] = scalar_pos
            row["offset_from_midpoint"] = scalar_pos - 0.5
            residuals = {}
            for name in SIGNAL_NAMES:
                residuals[f"scalar_minus_{name}"] = scalar_pos - fp[name]
            row["residuals"] = residuals
        rows.append(row)

    solved = [r for r in rows if r.get("solved") and "scalar_position" in r]
    scalars = [r["scalar_position"] for r in solved]

    # correlations
    corr_table = []
    for name in SIGNAL_NAMES:
        xs = [r["fingerprint"][name] for r in solved]
        rho = spearman(xs, scalars)
        tau = kendall_tau(xs, scalars)
        corr_table.append({
            "signal": name,
            "spearman": rho,
            "kendall_tau": tau,
            "abs_spearman": abs(rho),
            "verdict": verdict_corr(rho),
        })
    corr_table.sort(key=lambda r: -r["abs_spearman"])

    # residual summary stats
    residual_stats = {}
    for name in SIGNAL_NAMES:
        key = f"scalar_minus_{name}"
        vals = [r["residuals"][key] for r in solved]
        mu = sum(vals) / len(vals)
        var = sum((v - mu) ** 2 for v in vals) / len(vals)
        residual_stats[name] = {
            "mean": mu,
            "stdev": math.sqrt(var),
            "min": min(vals),
            "max": max(vals),
        }

    # nearest neighbors for P135 (public fingerprint only)
    r135 = next(r for r in rows if r["puzzle"] == 135)
    fp135 = r135["fingerprint"]
    # use continuous signals only (exclude drift 0/1 dominance)
    nn_keys = [k for k in SIGNAL_NAMES if k != "p_to_n_floor_drift"]
    neighbors = []
    for r in solved:
        dist = euclid(fp135, r["fingerprint"], nn_keys)
        neighbors.append({
            "puzzle": r["puzzle"],
            "distance": dist,
            "scalar_position": r["scalar_position"],
            "offset_from_midpoint": r["offset_from_midpoint"],
            "d": r["d"],
        })
    neighbors.sort(key=lambda x: x["distance"])
    top_nn = neighbors[:10]

    # cluster suggestion from neighbors
    nn_positions = [n["scalar_position"] for n in top_nn]
    nn_mean = sum(nn_positions) / len(nn_positions)
    if nn_mean < 0.33:
        cluster = "lower_third"
    elif nn_mean < 0.66:
        cluster = "middle_third"
    else:
        cluster = "upper_third"

    strong = [c for c in corr_table if c["verdict"] == "STRONG"]
    promising = [c for c in corr_table if c["verdict"] == "PROMISING"]

    payload = {
        "exhibit": "signal_scalar_residual_scan",
        "location": "ARCHIVE/briefcase/misalignments/",
        "model": "residual / rank / neighbor — NOT frac(signal)*width",
        "n_solved": len(solved),
        "correlations": corr_table,
        "residual_stats": residual_stats,
        "P135_nearest_neighbors": top_nn,
        "P135_neighbor_cluster_hint": {
            "mean_scalar_position": nn_mean,
            "cluster": cluster,
            "note": "hint only — not a d prediction; must still pass [d]G",
        },
        "summary": {
            "strong": [c["signal"] for c in strong],
            "promising": [c["signal"] for c in promising],
            "best_signal": corr_table[0]["signal"] if corr_table else None,
            "best_spearman": corr_table[0]["spearman"] if corr_table else None,
            "any_promising_or_strong": bool(strong or promising),
        },
        "rows_solved": [
            {
                "puzzle": r["puzzle"],
                "scalar_position": r["scalar_position"],
                "fingerprint": r["fingerprint"],
                "residuals": r["residuals"],
            }
            for r in solved
        ],
        "ruling": (
            "Direct projection is false. "
            "Ask whether signals order/scaffold scalar tendencies via rank/residual/neighbors."
        ),
    }

    (OUT / "signal_scalar_residual_scan.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "# signal_scalar_residual_scan",
        "",
        "Wrong model (rejected): `frac(signal) · width → d`",
        "",
        "This scan:",
        "",
        "```text",
        "scalar_position = (d - L) / width",
        "residual = scalar_position - signal",
        "spearman / kendall(signal, scalar_position)",
        "P135 nearest neighbors in public fingerprint space",
        "```",
        "",
        "## Rank correlations",
        "",
        "| signal | spearman | kendall | verdict |",
        "|--------|----------|---------|---------|",
    ]
    for c in corr_table:
        lines.append(
            f"| `{c['signal']}` | {c['spearman']:+.4f} | {c['kendall_tau']:+.4f} | "
            f"**{c['verdict']}** |"
        )

    lines.extend([
        "",
        f"Best: `{payload['summary']['best_signal']}` "
        f"spearman={payload['summary']['best_spearman']:+.4f}",
        "",
        f"Any PROMISING/STRONG? **{payload['summary']['any_promising_or_strong']}**",
        "",
        "## Residual stats (scalar_position − signal)",
        "",
        "| signal | mean | stdev | min | max |",
        "|--------|------|-------|-----|-----|",
    ])
    for name in SIGNAL_NAMES:
        s = residual_stats[name]
        lines.append(
            f"| `{name}` | {s['mean']:+.4f} | {s['stdev']:.4f} | "
            f"{s['min']:+.4f} | {s['max']:+.4f} |"
        )

    lines.extend([
        "",
        "## P135 nearest solved neighbors (public fingerprint)",
        "",
        f"Neighbor mean scalar_position = `{nn_mean:.4f}` → cluster hint: **{cluster}**",
        "",
        "| rank | puzzle | distance | scalar_position | offset_from_mid |",
        "|------|--------|----------|-----------------|-----------------|",
    ])
    for i, n in enumerate(top_nn, 1):
        lines.append(
            f"| {i} | {n['puzzle']} | {n['distance']:.4f} | "
            f"{n['scalar_position']:.4f} | {n['offset_from_midpoint']:+.4f} |"
        )

    lines.extend([
        "",
        "## Ruling",
        "",
        "```text",
        "The map is real.",
        "The direct projection is false.",
        "The fingerprint instrument is valid.",
        "The scalar mask is not in raw range or raw packet fractions.",
        "```",
        "",
        "Ask: do packet/defect/β signals cluster solved puzzles by scalar behavior?",
        "",
        "Judge Popcorn: **the stars are real, but the first star chart used a "
        "flat ruler on curved sky.**",
        "",
    ])

    (OUT / "signal_scalar_residual_scan.md").write_text("\n".join(lines), encoding="utf-8")

    (OUT / "README.md").write_text(
        "\n".join([
            "# briefcase/misalignments",
            "",
            "| File | Purpose |",
            "|------|---------|",
            "| `p1_baseline_misalignments.*` | P1 origin |",
            "| `range_error_bitmask.*` | range-only rulers (entropy ≈ 6.3) |",
            "| `packet_range_error_bitmask.*` | direct frac·width projection (also ~6.3) |",
            "| `signal_scalar_residual_scan.*` | residual / rank / neighbor (not direct landing) |",
            "",
            "```text",
            "python build_p1_baseline_misalignments.py",
            "python build_range_error_bitmask.py",
            "python build_packet_range_error_bitmask.py",
            "python build_signal_scalar_residual_scan.py",
            "```",
            "",
        ]),
        encoding="utf-8",
    )

    print(f"solved={len(solved)}")
    for c in corr_table:
        print(
            f"  {c['verdict']:10} {c['signal']:28} "
            f"spearman={c['spearman']:+.4f} kendall={c['kendall_tau']:+.4f}"
        )
    print(f"P135 neighbor cluster hint: {cluster} (mean pos={nn_mean:.4f})")
    print("top neighbors:", [n["puzzle"] for n in top_nn[:5]])
    print(f"wrote {OUT / 'signal_scalar_residual_scan.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
