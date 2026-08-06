#!/usr/bin/env python3
"""
Local-band / high-bit e_lo shell scan.

Uses e_lo = (n-1)/256 as preferred normalization (not a d predictor).
Compares only nearby puzzles so bit-length does not dominate.

Writes ONLY under ARCHIVE/briefcase/misalignments/
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from build_complexity_operations_ledger import BETA, BETA_SQ, inv, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "misalignments"

HINGE = 0.58496250072115618145373894394781650875981440769248106045575265
GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240

# High-bit telescope for P135
HIGH_BIT_CONTROLS = [110, 115, 120, 125, 130, 135, 140, 145, 150, 155, 160]
SIGNAL_KEYS = [
    "Px", "Py", "p_minus_y", "Px1", "Px2", "packet_frac",
    "Px_minus_Gx", "Px_times_Gx_inv",
]


def e_lo(n: int) -> float:
    return (n - 1) / 256.0


def e_hinge(n: int) -> float:
    return (n - 1 + HINGE) / 256.0


def e_hi(n: int) -> float:
    return n / 256.0


def fp_elo(n: int, px: int, py: int) -> dict[str, float]:
    e = e_lo(n)
    pmy = (p - py) % p
    px2 = (px * inv(BETA, p)) % p
    px1 = (px * inv(BETA_SQ, p)) % p

    def pw(v: int) -> float:
        v = v % p
        return ((v if v else 1) / float(p)) ** e

    packet_p = float(f"{px}.{pmy}") / float(p)
    return {
        "Px": pw(px),
        "Py": pw(py),
        "p_minus_y": pw(pmy),
        "Px1": pw(px1),
        "Px2": pw(px2),
        "packet_frac": packet_p ** e,
        "Px_minus_Gx": pw((px - GX) % p),
        "Px_times_Gx_inv": pw((px * inv(GX, p)) % p),
        "e_lo": e,
    }


def dist(a: dict[str, float], b: dict[str, float]) -> float:
    return math.sqrt(sum((a[k] - b[k]) ** 2 for k in SIGNAL_KEYS))


def spearman(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")

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
        return float("nan")
    return num / (dx * dy)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()

    # build fingerprints for all pubkey puzzles
    fps: dict[int, dict] = {}
    for n in range(1, 161):
        e = catalog[n]
        if not e.public_key:
            continue
        px, py = pubkey_xy(e.public_key)
        rec = {
            "puzzle": n,
            "solved": e.solved,
            "fingerprint": fp_elo(n, px, py),
            "has_pubkey": True,
        }
        if e.solved and e.private_key > 0:
            lo, hi = e.range_min, e.range_max
            width = hi - lo + 1
            rec["scalar_position"] = (e.private_key - lo) / width
            rec["d"] = str(e.private_key)
        fps[n] = rec

    # local-band scans for each solved target: n±10, n±20
    local_results = []
    for n, rec in fps.items():
        if not rec.get("solved"):
            continue
        for radius in (10, 20):
            band = [
                fps[m]
                for m in range(max(1, n - radius), min(160, n + radius) + 1)
                if m in fps and fps[m].get("solved") and m != n
            ]
            if len(band) < 3:
                continue
            # distances from target fingerprint
            dists = []
            for o in band:
                dists.append({
                    "puzzle": o["puzzle"],
                    "distance": dist(rec["fingerprint"], o["fingerprint"]),
                    "scalar_position": o["scalar_position"],
                })
            dists.sort(key=lambda x: x["distance"])
            top = dists[: min(5, len(dists))]
            # does closer fingerprint ⇒ closer scalar_position?
            # spearman(distance, |scalar_i - scalar_target|)
            target_sp = rec["scalar_position"]
            xs = [d["distance"] for d in dists]
            ys = [abs(d["scalar_position"] - target_sp) for d in dists]
            rho = spearman(xs, ys)
            # positive rho: larger fp distance ⇒ larger scalar distance (good clustering)
            local_results.append({
                "target": n,
                "radius": radius,
                "band_solved": len(band),
                "spearman_dist_vs_scalar_gap": rho,
                "top_neighbors": top,
                "neighbor_mean_scalar": sum(t["scalar_position"] for t in top) / len(top),
                "target_scalar": target_sp,
            })

    # aggregate: how often local rho is promising?
    rhos_10 = [
        r["spearman_dist_vs_scalar_gap"]
        for r in local_results
        if r["radius"] == 10 and r["spearman_dist_vs_scalar_gap"] == r["spearman_dist_vs_scalar_gap"]
    ]
    rhos_20 = [
        r["spearman_dist_vs_scalar_gap"]
        for r in local_results
        if r["radius"] == 20 and r["spearman_dist_vs_scalar_gap"] == r["spearman_dist_vs_scalar_gap"]
    ]

    def stats(xs: list[float]) -> dict:
        if not xs:
            return {}
        mu = sum(xs) / len(xs)
        return {
            "n": len(xs),
            "mean": mu,
            "stdev": math.sqrt(sum((x - mu) ** 2 for x in xs) / len(xs)),
            "frac_positive": sum(1 for x in xs if x > 0) / len(xs),
            "frac_gt_0_15": sum(1 for x in xs if x > 0.15) / len(xs),
        }

    # High-bit telescope for P135
    fp135 = fps[135]["fingerprint"]
    high_bit_rows = []
    for n in HIGH_BIT_CONTROLS:
        if n not in fps:
            high_bit_rows.append({"puzzle": n, "status": "no_pubkey"})
            continue
        rec = fps[n]
        high_bit_rows.append({
            "puzzle": n,
            "status": "solved" if rec.get("solved") else "public_only",
            "e_lo": rec["fingerprint"]["e_lo"],
            "distance_to_P135": dist(fp135, rec["fingerprint"]) if n != 135 else 0.0,
            "scalar_position": rec.get("scalar_position"),
        })
    # nearest solved in high-bit set
    solved_hb = [r for r in high_bit_rows if r.get("scalar_position") is not None and r["puzzle"] != 135]
    solved_hb.sort(key=lambda r: r["distance_to_P135"])
    if solved_hb:
        nn_mean = sum(r["scalar_position"] for r in solved_hb[: min(3, len(solved_hb))]) / min(3, len(solved_hb))
        cluster = (
            "lower_third" if nn_mean < 0.33
            else "middle_third" if nn_mean < 0.66
            else "upper_third"
        )
    else:
        nn_mean = None
        cluster = "no_solved_in_high_bit_set"

    # note: puzzles 110-130 may be unsolved (no pubkey or no d)
    # check which are solved
    high_bit_solved = [n for n in HIGH_BIT_CONTROLS if n in fps and fps[n].get("solved")]

    payload = {
        "exhibit": "elo_local_band_scan",
        "location": "ARCHIVE/briefcase/misalignments/",
        "shell": "e_lo = (n-1)/256",
        "use": [
            "candidate comparison",
            "solved-puzzle normalization",
            "distance-to-public-fingerprint scoring",
        ],
        "do_not_use": ["deriving d directly"],
        "local_band_stats": {
            "radius_10": stats(rhos_10),
            "radius_20": stats(rhos_20),
            "interpretation": (
                "Positive spearman(dist, |scalar_gap|) means closer e_lo fingerprints "
                "have closer scalar positions locally. Mean near 0 => no local compass."
            ),
        },
        "high_bit_controls": HIGH_BIT_CONTROLS,
        "high_bit_solved_present": high_bit_solved,
        "P135_high_bit": {
            "neighbors_solved": solved_hb,
            "top3_mean_scalar": nn_mean,
            "cluster_hint": cluster,
            "confidence": "weak",
            "actionable": False,
        },
        "local_results_sample": [
            r for r in local_results if r["target"] in (65, 70, 75, 80, 100, 105, 115, 120, 125, 130)
        ],
        "ruling": (
            "e_lo wins the shell; it does not open the door. "
            "Local-band scan tests whether the lens helps nearby, without n-confound."
        ),
    }

    (OUT / "elo_local_band_scan.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "# elo_local_band_scan",
        "",
        "Preferred shell: `e_lo = (n−1)/256` — filter coordinate, not scalar predictor.",
        "",
        "## Local-band: does e_lo distance track scalar gap?",
        "",
        "For each solved target, neighbors in `n±10` / `n±20` (solved only).",
        "Spearman(fingerprint_distance, |scalar_position − target|).",
        "",
        "Positive ⇒ closer fingerprints sit closer in range (local clustering).",
        "",
    ]
    for radius, st in (("10", stats(rhos_10)), ("20", stats(rhos_20))):
        lines.append(f"### radius ±{radius}")
        lines.append("")
        if not st:
            lines.append("_insufficient bands_")
        else:
            lines.append(f"- n targets: `{st['n']}`")
            lines.append(f"- mean spearman: `{st['mean']:+.4f}`")
            lines.append(f"- stdev: `{st['stdev']:.4f}`")
            lines.append(f"- fraction ρ > 0: `{st['frac_positive']:.2f}`")
            lines.append(f"- fraction ρ > 0.15: `{st['frac_gt_0_15']:.2f}`")
        lines.append("")

    lines.extend([
        "## High-bit telescope (P135)",
        "",
        f"Control set: `{HIGH_BIT_CONTROLS}`",
        f"Solved present in set: `{high_bit_solved}`",
        "",
        "| puzzle | status | e_lo | dist to P135 | scalar_position |",
        "|--------|--------|------|--------------|-----------------|",
    ])
    for r in high_bit_rows:
        if r.get("status") == "no_pubkey":
            lines.append(f"| {r['puzzle']} | no_pubkey | — | — | — |")
        else:
            sp = r.get("scalar_position")
            sp_s = f"{sp:.4f}" if sp is not None else "—"
            lines.append(
                f"| {r['puzzle']} | {r['status']} | {r['e_lo']:.6f} | "
                f"{r['distance_to_P135']:.6f} | {sp_s} |"
            )

    lines.extend([
        "",
        f"Solved-neighbor cluster hint: **{cluster}** "
        f"(mean scalar `{nn_mean}`)" if nn_mean is not None else "",
        "",
        "## Verdict",
        "",
        "```text",
        "REJECTED: three-slice power as scalar predictor",
        "VALID:    e_lo as preferred normalization shell",
        "LOCAL:    see spearman stats above",
        "DOOR:     candidate gate stack / [d]G / RSZ",
        "```",
        "",
        "`e_lo` wins the shell; it does not open the door.",
        "",
        "Judge Popcorn: **we found the best lens, not the star's address.**",
        "",
    ])

    (OUT / "elo_local_band_scan.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"local ±10: {stats(rhos_10)}")
    print(f"local ±20: {stats(rhos_20)}")
    print(f"high_bit_solved: {high_bit_solved}")
    print(f"P135 cluster: {cluster} mean={nn_mean}")
    print(f"wrote {OUT / 'elo_local_band_scan.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
