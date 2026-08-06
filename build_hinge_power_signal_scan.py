#!/usr/bin/env python3
"""
Hinge-power signal scan.

For puzzle n:
  e_n = (n - 1 + HINGE) / 256

Raise normalized field quantities (x, y, differences, β-slots, ratios)
to e_n in the reals:

  signal = (v / p) ** e_n

Then test rank correlation with scalar_position and P135 neighbors.

Not modular exponentiation (e_n is fractional).
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

HINGE = 0.58496250072115618145373894394781650875981440769248106045575265
GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240
GY = 32670510020758816978083085130507043184471273380659243275938904335757337482424


def exponent(n: int) -> float:
    """(n - 1 + hinge) / 256 — e.g. P130 → 129.58496.../256."""
    return (n - 1 + HINGE) / 256.0


def norm(v: int) -> float:
    """Map field element to (0,1]."""
    v = v % p
    if v == 0:
        return 1e-300  # avoid 0**e
    return v / float(p)


def powered(v: int, e: float) -> float:
    return norm(v) ** e


def field_quantities(px: int, py: int) -> dict[str, int]:
    pmy = (p - py) % p
    px3 = px
    px2 = (px * inv(BETA, p)) % p
    px1 = (px * inv(BETA_SQ, p)) % p
    return {
        "Px": px,
        "Py": py,
        "p_minus_y": pmy,
        "Px1": px1,
        "Px2": px2,
        "Px3": px3,
        "Px_minus_Gx": (px - GX) % p,
        "Py_minus_Gy": (py - GY) % p,
        "pmy_minus_Gy": (pmy - GY) % p,
        "Px_times_Gx_inv": (px * inv(GX, p)) % p,
        "Py_times_Gy_inv": (py * inv(GY, p)) % p,
        "Px_plus_Gx": (px + GX) % p,
        "Px_sq": pow(px, 2, p),
        "Py_sq": pow(py, 2, p),
        "Px_cubed_plus_7": (pow(px, 3, p) + 7) % p,
        "DELTA_mod_p": DELTA % p,
        "map_shadow": (N * px) // p,  # not mod p; handle separately
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
    return (conc - disc) / tot if tot else 0.0


def verdict_corr(rho: float) -> str:
    a = abs(rho)
    if a < 0.15:
        return "REJECT"
    if a < 0.35:
        return "WEAK"
    if a < 0.60:
        return "PROMISING"
    return "STRONG"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()

    # quantity names (exclude map_shadow from mod-p set; add powered forms)
    qty_names = [
        "Px", "Py", "p_minus_y", "Px1", "Px2", "Px3",
        "Px_minus_Gx", "Py_minus_Gy", "pmy_minus_Gy",
        "Px_times_Gx_inv", "Py_times_Gy_inv",
        "Px_plus_Gx", "Px_sq", "Py_sq", "Px_cubed_plus_7",
    ]

    solved_rows = []
    all_fp_rows = []

    for n in range(1, 161):
        e = catalog[n]
        if not e.public_key:
            continue
        px, py = pubkey_xy(e.public_key)
        e_n = exponent(n)
        qtys = field_quantities(px, py)
        powered_signals = {name: powered(qtys[name], e_n) for name in qty_names}
        # also power the unit ratios themselves with e_n (same as powered for Px etc.)
        # packet-style: (packet_p)**e_n
        pmy = (p - py) % p
        packet_p = float(f"{px}.{pmy}") / float(p)
        powered_signals["packet_frac_pow"] = packet_p ** e_n
        powered_signals["x_ratio_pow"] = (px / float(p)) ** e_n
        powered_signals["defect_frac_pow"] = (
            (packet_p * float(DELTA)) - math.floor(packet_p * float(DELTA))
        ) ** e_n if packet_p * float(DELTA) > 0 else 0.0

        # difference-of-powers: Px^e - Gx^e (real, normalized)
        powered_signals["Px_pow_minus_Gx_pow"] = abs(
            powered(px, e_n) - powered(GX, e_n)
        )
        powered_signals["Py_pow_minus_Gy_pow"] = abs(
            powered(py, e_n) - powered(GY, e_n)
        )

        row = {
            "puzzle": n,
            "exponent": e_n,
            "exponent_formula": f"({n}-1+HINGE)/256",
            "signals": powered_signals,
            "solved": e.solved,
        }
        if e.solved and e.private_key > 0:
            lo, hi = e.range_min, e.range_max
            width = hi - lo + 1
            scalar_pos = (e.private_key - lo) / width
            row["scalar_position"] = scalar_pos
            row["d"] = str(e.private_key)
            residuals = {
                f"scalar_minus_{k}": scalar_pos - v
                for k, v in powered_signals.items()
            }
            row["residuals"] = residuals
            solved_rows.append(row)
        all_fp_rows.append(row)

    signal_names = list(solved_rows[0]["signals"].keys())
    scalars = [r["scalar_position"] for r in solved_rows]

    corr_table = []
    for name in signal_names:
        xs = [r["signals"][name] for r in solved_rows]
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

    # P135 neighbors in hinge-power fingerprint space
    r135 = next(r for r in all_fp_rows if r["puzzle"] == 135)
    fp135 = r135["signals"]
    keys = signal_names
    neighbors = []
    for r in solved_rows:
        dist = math.sqrt(
            sum((fp135[k] - r["signals"][k]) ** 2 for k in keys)
        )
        neighbors.append({
            "puzzle": r["puzzle"],
            "distance": dist,
            "scalar_position": r["scalar_position"],
            "exponent": r["exponent"],
        })
    neighbors.sort(key=lambda x: x["distance"])
    top_nn = neighbors[:10]
    nn_mean = sum(n["scalar_position"] for n in top_nn) / len(top_nn)
    cluster = (
        "lower_third" if nn_mean < 0.33
        else "middle_third" if nn_mean < 0.66
        else "upper_third"
    )

    # example exponents for report
    examples = {n: exponent(n) for n in (1, 65, 130, 135, 160)}

    payload = {
        "exhibit": "hinge_power_signal_scan",
        "location": "ARCHIVE/briefcase/misalignments/",
        "formula": "signal = (v/p) ** ((n-1+HINGE)/256)",
        "HINGE": HINGE,
        "example_exponents": examples,
        "example_P130": (130 - 1 + HINGE) / 256,
        "n_solved": len(solved_rows),
        "correlations": corr_table,
        "P135_exponent": exponent(135),
        "P135_nearest_neighbors": top_nn,
        "P135_neighbor_cluster_hint": {
            "mean_scalar_position": nn_mean,
            "cluster": cluster,
            "confidence": "weak",
            "actionable": False,
        },
        "summary": {
            "best_signal": corr_table[0]["signal"],
            "best_spearman": corr_table[0]["spearman"],
            "strong": [c["signal"] for c in corr_table if c["verdict"] == "STRONG"],
            "promising": [c["signal"] for c in corr_table if c["verdict"] == "PROMISING"],
            "beats_plain_x_ratio": abs(corr_table[0]["spearman"]) > 0.274,
        },
        "prior_plain_x_ratio_spearman": -0.2738,
        "ruling": (
            "Hinge-power warps each puzzle's coordinates by its range height in 256-bit space. "
            "Use as filter/fingerprint only unless rank correlation is PROMISING+."
        ),
    }

    (OUT / "hinge_power_signal_scan.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "# hinge_power_signal_scan",
        "",
        "For puzzle `n`:",
        "",
        "```text",
        "e_n = (n - 1 + HINGE) / 256",
        "signal = (v / p) ** e_n",
        "```",
        "",
        f"Example P130: `e_130 = (129 + HINGE) / 256 = {examples[130]}`",
        f"Example P135: `e_135 = {examples[135]}`",
        "",
        "Applied to Px, Py, p−y, β-slots, differences from G, ratios, squares, curve polynomial.",
        "",
        "## Rank correlations vs scalar_position",
        "",
        f"Prior plain `x_ratio` spearman ≈ **-0.2738**",
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
        f"({payload['summary']['best_spearman']:+.4f})",
        "",
        f"Beats plain x_ratio? **{payload['summary']['beats_plain_x_ratio']}**",
        "",
        "## P135 hinge-power neighbors",
        "",
        f"e_135 = `{examples[135]}`",
        f"Neighbor mean scalar_position = `{nn_mean:.4f}` → **{cluster}** (weak hint)",
        "",
        "| rank | puzzle | distance | scalar_position |",
        "|------|--------|----------|-----------------|",
    ])
    for i, n in enumerate(top_nn, 1):
        lines.append(
            f"| {i} | {n['puzzle']} | {n['distance']:.6f} | {n['scalar_position']:.4f} |"
        )

    lines.extend([
        "",
        "## Ledger placement",
        "",
        "```text",
        "REJECTED (still):",
        "  direct frac(signal)·width → d",
        "  transferable binary error mask from range/packet rulers",
        "",
        "VALID:",
        "  fingerprint / exclusion filter",
        "  hinge-power as per-puzzle warp of public coordinates",
        "",
        "DOOR:",
        "  candidate d/k → range → [d]G == P135 → RSZ",
        "```",
        "",
        "Judge Popcorn: **stars confirm where we think we are; "
        "they do not pave a road to d.**",
        "",
    ])

    (OUT / "hinge_power_signal_scan.md").write_text("\n".join(lines), encoding="utf-8")

    # README
    (OUT / "README.md").write_text(
        "\n".join([
            "# briefcase/misalignments",
            "",
            "| File | Purpose |",
            "|------|---------|",
            "| `range_error_bitmask.*` | range-only rulers |",
            "| `packet_range_error_bitmask.*` | direct frac·width |",
            "| `signal_scalar_residual_scan.*` | residual / rank / neighbor |",
            "| `hinge_power_signal_scan.*` | `(v/p)^((n-1+hinge)/256)` warp |",
            "| `p1_baseline_misalignments.*` | P1 origin |",
            "",
            "```text",
            "python build_hinge_power_signal_scan.py",
            "```",
            "",
        ]),
        encoding="utf-8",
    )

    print(f"e_130={examples[130]}")
    print(f"e_135={examples[135]}")
    for c in corr_table[:8]:
        print(
            f"  {c['verdict']:10} {c['signal']:28} "
            f"spearman={c['spearman']:+.4f}"
        )
    print(
        f"beats_plain_x_ratio={payload['summary']['beats_plain_x_ratio']} "
        f"best={payload['summary']['best_signal']}"
    )
    print(f"P135 neighbors: {[n['puzzle'] for n in top_nn[:5]]} cluster={cluster}")
    print(f"wrote {OUT / 'hinge_power_signal_scan.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
