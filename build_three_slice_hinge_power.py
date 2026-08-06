#!/usr/bin/env python3
"""
Three-slice hinge-power scan.

For puzzle n:
  e_hi    = n / 256
  e_lo    = (n - 1) / 256
  e_hinge = (n - 1 + HINGE) / 256

Example P130:
  ^130/256
  ^129/256
  ^129.58496.../256

signal = (v / p) ** e
priv   = (d / 2^256) ** e   and other normalizations

distance = |signal - priv|

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
TWO256 = float(1 << 256)


def slices(n: int) -> dict[str, float]:
    return {
        "e_hi": n / 256.0,
        "e_lo": (n - 1) / 256.0,
        "e_hinge": (n - 1 + HINGE) / 256.0,
    }


def norm_field(v: int) -> float:
    v = v % p
    return (v if v else 1) / float(p)


def powered_field(v: int, e: float) -> float:
    return norm_field(v) ** e


def priv_norms(d: int, n: int, lo: int, hi: int, e: float) -> dict[str, float]:
    width = hi - lo + 1
    # avoid 0**e
    dn = max(d, 1)
    return {
        "d_over_2_256": (dn / TWO256) ** e,
        "d_over_2_n": (dn / float(1 << n)) ** e,
        "d_over_2_n_minus_1": (dn / float(1 << (n - 1))) ** e,
        "d_over_N": (dn / float(N)) ** e,
        "scalar_position": (d - lo) / width,  # not powered — linear range pos
        "scalar_position_pow": ((d - lo) / width) ** e if (d - lo) > 0 else 0.0,
    }


def field_vals(px: int, py: int) -> dict[str, int]:
    pmy = (p - py) % p
    return {
        "Px": px,
        "Py": py,
        "p_minus_y": pmy,
        "Px1": (px * inv(BETA_SQ, p)) % p,
        "Px2": (px * inv(BETA, p)) % p,
        "Px3": px,
        "Px_minus_Gx": (px - GX) % p,
        "Px_times_Gx_inv": (px * inv(GX, p)) % p,
        "Px_sq": pow(px, 2, p),
        "Px_cubed_plus_7": (pow(px, 3, p) + 7) % p,
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


def verdict(rho: float) -> str:
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

    qty_names = list(field_vals(GX, 1).keys())
    priv_names = [
        "d_over_2_256",
        "d_over_2_n",
        "d_over_2_n_minus_1",
        "d_over_N",
        "scalar_position",
        "scalar_position_pow",
    ]
    slice_names = ["e_lo", "e_hinge", "e_hi"]

    rows = []
    # collect distances for correlation: for each (slice, qty, priv_norm) -> list of distances
    # and also correlation of powered signal vs priv_norm across puzzles

    for n in range(1, 161):
        e = catalog[n]
        if not e.solved or not e.public_key or e.private_key <= 0:
            continue
        d = e.private_key
        lo, hi = e.range_min, e.range_max
        px, py = pubkey_xy(e.public_key)
        qtys = field_vals(px, py)
        exps = slices(n)

        slice_block = {}
        for sname in slice_names:
            e_n = exps[sname]
            sigs = {q: powered_field(qtys[q], e_n) for q in qty_names}
            pmy = (p - py) % p
            packet_p = float(f"{px}.{pmy}") / float(p)
            sigs["packet_frac"] = packet_p ** e_n
            privs = priv_norms(d, n, lo, hi, e_n)

            distances = {}
            closest = None
            closest_dist = None
            for q, sig in sigs.items():
                for pn, pv in privs.items():
                    dist = abs(sig - pv)
                    key = f"{q}__vs__{pn}"
                    distances[key] = dist
                    if closest_dist is None or dist < closest_dist:
                        closest_dist = dist
                        closest = key

            slice_block[sname] = {
                "exponent": e_n,
                "signals": sigs,
                "priv_norms": privs,
                "distances": distances,
                "closest_pair": closest,
                "closest_distance": closest_dist,
            }

        # which slice is overall closest (min over all pairs)
        best_slice = min(
            slice_names,
            key=lambda s: slice_block[s]["closest_distance"],
        )
        rows.append({
            "puzzle": n,
            "d": str(d),
            "exponents": exps,
            "slices": slice_block,
            "best_slice": best_slice,
            "best_slice_distance": slice_block[best_slice]["closest_distance"],
            "best_slice_pair": slice_block[best_slice]["closest_pair"],
        })

    # which slice wins most often?
    best_counts = {s: 0 for s in slice_names}
    for r in rows:
        best_counts[r["best_slice"]] += 1

    # mean closest distance per slice
    mean_closest = {}
    for s in slice_names:
        vals = [r["slices"][s]["closest_distance"] for r in rows]
        mean_closest[s] = sum(vals) / len(vals)

    # correlations: powered Px vs each priv_norm, per slice
    corr_table = []
    for s in slice_names:
        for q in ["Px", "Py", "packet_frac", "Px_minus_Gx", "Px_times_Gx_inv"]:
            for pn in priv_names:
                xs = [r["slices"][s]["signals"][q] for r in rows]
                ys = [r["slices"][s]["priv_norms"][pn] for r in rows]
                rho = spearman(xs, ys)
                corr_table.append({
                    "slice": s,
                    "signal": q,
                    "priv_norm": pn,
                    "spearman": rho,
                    "abs_spearman": abs(rho),
                    "verdict": verdict(rho),
                })
    corr_table.sort(key=lambda r: -r["abs_spearman"])

    # mean distance for key pairs per slice
    key_pairs = [
        ("Px", "d_over_2_256"),
        ("Px", "d_over_2_n"),
        ("Px", "d_over_2_n_minus_1"),
        ("Px", "scalar_position"),
        ("packet_frac", "d_over_2_256"),
        ("packet_frac", "scalar_position"),
        ("Px", "scalar_position_pow"),
    ]
    pair_means = []
    for s in slice_names:
        for q, pn in key_pairs:
            key = f"{q}__vs__{pn}"
            vals = [r["slices"][s]["distances"][key] for r in rows]
            pair_means.append({
                "slice": s,
                "pair": key,
                "mean_distance": sum(vals) / len(vals),
                "stdev": math.sqrt(
                    sum((v - sum(vals) / len(vals)) ** 2 for v in vals) / len(vals)
                ),
            })
    pair_means.sort(key=lambda r: r["mean_distance"])

    # P135 public-only: three-slice signals (no priv distance)
    e135 = catalog[135]
    px, py = pubkey_xy(e135.public_key)
    qtys = field_vals(px, py)
    exps135 = slices(135)
    p135_slices = {}
    for sname, e_n in exps135.items():
        sigs = {q: powered_field(qtys[q], e_n) for q in qty_names}
        pmy = (p - py) % p
        packet_p = float(f"{px}.{pmy}") / float(p)
        sigs["packet_frac"] = packet_p ** e_n
        p135_slices[sname] = {"exponent": e_n, "signals": sigs}

    # example P130 exponents
    ex130 = slices(130)

    payload = {
        "exhibit": "three_slice_hinge_power",
        "location": "ARCHIVE/briefcase/misalignments/",
        "formula": {
            "e_hi": "n / 256",
            "e_lo": "(n - 1) / 256",
            "e_hinge": "(n - 1 + HINGE) / 256",
            "signal": "(v / p) ** e",
            "priv": "(d / 2^256) ** e  etc.",
            "distance": "|signal - priv|",
        },
        "HINGE": HINGE,
        "example_P130": ex130,
        "example_P135": exps135,
        "n_solved": len(rows),
        "best_slice_counts": best_counts,
        "mean_closest_distance_by_slice": mean_closest,
        "closest_pairs_overall": pair_means[:15],
        "correlations": corr_table[:30],
        "summary": {
            "winning_slice": max(best_counts, key=best_counts.get),
            "best_corr": corr_table[0] if corr_table else None,
            "any_promising": any(c["verdict"] in ("PROMISING", "STRONG") for c in corr_table),
        },
        "P135_public_slices": p135_slices,
        "rows": [
            {
                "puzzle": r["puzzle"],
                "best_slice": r["best_slice"],
                "best_slice_pair": r["best_slice_pair"],
                "best_slice_distance": r["best_slice_distance"],
                "exponents": r["exponents"],
                "slice_closest": {
                    s: {
                        "exponent": r["slices"][s]["exponent"],
                        "closest_pair": r["slices"][s]["closest_pair"],
                        "closest_distance": r["slices"][s]["closest_distance"],
                        "Px_vs_d_over_2_256": r["slices"][s]["distances"]["Px__vs__d_over_2_256"],
                        "Px_vs_scalar_position": r["slices"][s]["distances"]["Px__vs__scalar_position"],
                        "packet_vs_scalar_position": r["slices"][s]["distances"][
                            "packet_frac__vs__scalar_position"
                        ],
                    }
                    for s in slice_names
                },
            }
            for r in rows
        ],
    }

    (OUT / "three_slice_hinge_power.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "# three_slice_hinge_power",
        "",
        "For puzzle `n`:",
        "",
        "```text",
        "e_hi    = n / 256",
        "e_lo    = (n - 1) / 256",
        "e_hinge = (n - 1 + HINGE) / 256",
        "",
        "signal = (v / p) ** e",
        "priv   = (d / 2^256) ** e   (and d/2^n, d/2^(n-1), d/N, scalar_position)",
        "distance = |signal - priv|",
        "```",
        "",
        f"P130: `e_hi={ex130['e_hi']}` `e_lo={ex130['e_lo']}` `e_hinge={ex130['e_hinge']}`",
        f"P135: `e_hi={exps135['e_hi']}` `e_lo={exps135['e_lo']}` `e_hinge={exps135['e_hinge']}`",
        "",
        "## Which slice lands closest to priv?",
        "",
        f"| slice | wins (of {len(rows)}) | mean closest distance |",
        f"|-------|----------------------|------------------------|",
    ]
    for s in slice_names:
        lines.append(
            f"| `{s}` | {best_counts[s]} | {mean_closest[s]:.6f} |"
        )

    lines.extend([
        "",
        f"**Winning slice:** `{payload['summary']['winning_slice']}`",
        "",
        "## Smallest mean distances (signal vs priv)",
        "",
        "| slice | pair | mean_distance | stdev |",
        "|-------|------|---------------|-------|",
    ])
    for r in pair_means[:12]:
        lines.append(
            f"| `{r['slice']}` | `{r['pair']}` | {r['mean_distance']:.6f} | {r['stdev']:.6f} |"
        )

    lines.extend([
        "",
        "## Rank correlation (powered signal vs priv norm)",
        "",
        "| slice | signal | priv_norm | spearman | verdict |",
        "|-------|--------|-----------|----------|---------|",
    ])
    for c in corr_table[:15]:
        lines.append(
            f"| `{c['slice']}` | `{c['signal']}` | `{c['priv_norm']}` | "
            f"{c['spearman']:+.4f} | **{c['verdict']}** |"
        )

    # confound control: correlation may be driven by bit-length n
    ns = [float(r["puzzle"]) for r in rows]
    px_lo = [r["slices"]["e_lo"]["signals"]["Px"] for r in rows]
    d256_lo = [r["slices"]["e_lo"]["priv_norms"]["d_over_2_256"] for r in rows]
    confound = {
        "spearman_Px_pow_vs_d_pow": spearman(px_lo, d256_lo),
        "spearman_Px_pow_vs_n": spearman(px_lo, ns),
        "spearman_d_pow_vs_n": spearman(d256_lo, ns),
        "bands": {},
    }
    for lo_b, hi_b in ((1, 40), (41, 80), (65, 130)):
        xs, ys = [], []
        for r in rows:
            n = r["puzzle"]
            if lo_b <= n <= hi_b:
                xs.append(r["slices"]["e_lo"]["signals"]["Px"])
                ys.append(r["slices"]["e_lo"]["priv_norms"]["d_over_2_256"])
        confound["bands"][f"{lo_b}_{hi_b}"] = {
            "n": len(xs),
            "spearman": spearman(xs, ys) if len(xs) >= 3 else None,
        }
    payload["confound_control"] = confound
    # rewrite json with confound
    (OUT / "three_slice_hinge_power.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines.extend([
        "",
        f"Any PROMISING/STRONG on full set? **{payload['summary']['any_promising']}**",
        "",
        "## Confound control (bit-length n)",
        "",
        "Both `(Px/p)^e` and `(d/2^256)^e` depend on `e(n)`. Across all bit lengths this",
        "inflates Spearman:",
        "",
        f"- Px_pow vs d_pow: `{confound['spearman_Px_pow_vs_d_pow']:+.4f}`",
        f"- Px_pow vs n: `{confound['spearman_Px_pow_vs_n']:+.4f}`",
        f"- d_pow vs n: `{confound['spearman_d_pow_vs_n']:+.4f}` (monotonic in n)",
        "",
        "Within bit-length bands:",
        "",
    ])
    for band, st in confound["bands"].items():
        lines.append(
            f"- band `{band}`: n={st['n']} spearman=`{st['spearman']}`"
        )
    lines.extend([
        "",
        "**Ruling:** full-set STRONG is mostly **n-confound**. Band 65–130 collapses to ~0.",
        "Three-slice warp remains a fingerprint tool, not a priv-distance compass.",
        "",
        "## Sample (first 12 solved)",
        "",
        "| P | best_slice | closest_pair | distance |",
        "|---|------------|--------------|----------|",
    ])
    for r in rows[:12]:
        lines.append(
            f"| {r['puzzle']} | `{r['best_slice']}` | `{r['best_slice_pair']}` | "
            f"{r['best_slice_distance']:.6f} |"
        )

    lines.extend([
        "",
        "## Ruling",
        "",
        "Three range-height warps (floor, hinge, ceiling of the bit window).",
        "Distance to priv norms tests whether any slice aligns public power with scalar power.",
        "Still a filter/fingerprint lane unless correlation is PROMISING+.",
        "",
        "Door: candidate gate stack / [d]G / RSZ.",
        "",
    ])

    (OUT / "three_slice_hinge_power.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"P130 slices: {ex130}")
    print(f"best_slice_counts: {best_counts}")
    print(f"mean_closest: {mean_closest}")
    for c in corr_table[:6]:
        print(
            f"  {c['verdict']:10} {c['slice']:8} {c['signal']:20} vs {c['priv_norm']:20} "
            f"rho={c['spearman']:+.4f}"
        )
    print(f"wrote {OUT / 'three_slice_hinge_power.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
