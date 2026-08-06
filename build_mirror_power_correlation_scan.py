#!/usr/bin/env python3
"""
Mirror-power correlation scan — true scalar-order roof.

Roofs:
  e_roof_binary   = 256/256 = 1          (abstract binary ceiling)
  e_roof_N        = log2(N) / 256        (true scalar-order ceiling, < 1)
  e_mirror_proxy  = 255/256              (coarse one-bit-below proxy)

Direct shells (puzzle n):
  e_hi    = n / 256
  e_lo    = (n - 1) / 256
  e_hinge = (n - 1 + HINGE) / 256

Mirror shells:
  e_q              = log2(N - d) / 256           solved only
  e_q_window_low   = log2(N - 2^n) / 256
  e_q_window_high  = log2(N - 2^(n-1)) / 256

Writes ONLY under ARCHIVE/briefcase/ecdlp_range/
"""

from __future__ import annotations

import json
import math
from decimal import Decimal, getcontext
from pathlib import Path

from build_complexity_operations_ledger import BETA, BETA_SQ, N, inv, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog

getcontext().prec = 80

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "ecdlp_range"

HINGE = 0.58496250072115618145373894394781650875981440769248106045575265
GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240

E_ROOF_BINARY = Decimal(1)
E_MIRROR_PROXY = Decimal(255) / Decimal(256)


def log2_int(x: int) -> Decimal:
    """High-precision log2(x). float64 collapses log2(N) to 256."""
    if x <= 0:
        raise ValueError("log2 domain")
    return Decimal(x).ln() / Decimal(2).ln()


def e_from_int(x: int) -> Decimal:
    """log2(x) / 256 as Decimal."""
    return log2_int(x) / Decimal(256)


# True scalar-order roof (N < 2^256 ⇒ e_roof_N < 1).
# Must stay Decimal: 1 - e_roof_N ≈ 2e-41, invisible in float64.
E_ROOF_N = e_from_int(N)
E_ROOF_N_DEFICIT = E_ROOF_BINARY - E_ROOF_N  # how far below 1


def direct_shells(n: int) -> dict[str, Decimal]:
    return {
        "e_hi": Decimal(n) / Decimal(256),
        "e_lo": Decimal(n - 1) / Decimal(256),
        "e_hinge": (Decimal(n - 1) + Decimal(str(HINGE))) / Decimal(256),
    }


def mirror_window_shells(n: int) -> dict:
    # N - 2^n and N - 2^(n-1) must be positive
    low = N - (1 << n)
    high = N - (1 << (n - 1))
    return {
        "e_q_window_low": e_from_int(low),
        "e_q_window_high": e_from_int(high),
        "N_minus_2_n": str(low),
        "N_minus_2_n_minus_1": str(high),
    }


def dec_str(x: Decimal) -> str:
    return format(x, "f")


def powered(v: int, e: float) -> float:
    v = v % p
    base = (v if v else 1) / float(p)
    return base ** e


def fingerprint(px: int, py: int, e: float) -> dict[str, float]:
    pmy = (p - py) % p
    packet_p = float(f"{px}.{pmy}") / float(p)
    return {
        "Px": powered(px, e),
        "Py": powered(py, e),
        "p_minus_y": powered(pmy, e),
        "packet_frac": packet_p ** e,
        "Px_minus_Gx": powered((px - GX) % p, e),
        "Px_times_Gx_inv": powered((px * inv(GX, p)) % p, e),
        "Px2": powered((px * inv(BETA, p)) % p, e),
    }


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


def verdict(rho: float) -> str:
    if rho != rho:
        return "NA"
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

    solved_rows: list[dict] = []
    all_rows: list[dict] = []

    for n in range(1, 161):
        e = catalog[n]
        direct = direct_shells(n)
        mirror_win = mirror_window_shells(n)
        row: dict = {
            "puzzle": n,
            "direct_shells": {k: dec_str(v) for k, v in direct.items()},
            "mirror_window_shells": {
                "e_q_window_low": dec_str(mirror_win["e_q_window_low"]),
                "e_q_window_high": dec_str(mirror_win["e_q_window_high"]),
            },
            "N_mirror_bounds": {
                "N_minus_2_n": mirror_win["N_minus_2_n"],
                "N_minus_2_n_minus_1": mirror_win["N_minus_2_n_minus_1"],
            },
            "has_pubkey": bool(e.public_key),
            "solved": e.solved and e.private_key > 0,
        }

        # distances of direct shells to roofs / mirror window (Decimal)
        dists = {}
        for dname, de in direct.items():
            dists[f"{dname}_vs_e_roof_N"] = dec_str(abs(de - E_ROOF_N))
            dists[f"{dname}_vs_e_mirror_proxy"] = dec_str(abs(de - E_MIRROR_PROXY))
            dists[f"{dname}_vs_e_roof_binary"] = dec_str(abs(de - E_ROOF_BINARY))
            dists[f"{dname}_vs_e_q_window_low"] = dec_str(
                abs(de - mirror_win["e_q_window_low"])
            )
            dists[f"{dname}_vs_e_q_window_high"] = dec_str(
                abs(de - mirror_win["e_q_window_high"])
            )
            lo_e, hi_e = mirror_win["e_q_window_low"], mirror_win["e_q_window_high"]
            dists[f"{dname}_in_mirror_exp_band"] = bool(lo_e <= de <= hi_e)
        row["shell_distances"] = dists

        if e.public_key:
            px, py = pubkey_xy(e.public_key)
            # float powering: e_roof_N is indistinguishable from 1.0 in float64
            fps = {}
            for dname, de in direct.items():
                fps[dname] = fingerprint(px, py, float(de))
            fps["e_roof_N"] = fingerprint(px, py, 1.0)  # ≡ identity in float64
            fps["e_mirror_proxy"] = fingerprint(px, py, float(E_MIRROR_PROXY))
            fps["_note"] = (
                "e_roof_N powering uses float 1.0; deficit from 1 is ~1e-41 (Decimal only)"
            )
            row["fingerprints"] = fps

        if e.solved and e.private_key > 0:
            d = e.private_key
            q = (N - d) % N
            e_q = e_from_int(q)
            row["d"] = str(d)
            row["N_minus_d"] = str(q)
            row["e_q"] = dec_str(e_q)
            dist_roof = abs(e_q - E_ROOF_N)
            dist_proxy = abs(e_q - E_MIRROR_PROXY)
            row["e_q_closer_to"] = (
                "e_roof_N" if dist_roof <= dist_proxy else "e_mirror_proxy"
            )
            row["e_q_dist_to_e_roof_N"] = dec_str(dist_roof)
            row["e_q_dist_to_e_mirror_proxy"] = dec_str(dist_proxy)
            row["e_q_dist_to_e_roof_binary"] = dec_str(abs(e_q - E_ROOF_BINARY))
            for dname, de in direct.items():
                row[f"e_q_dist_to_{dname}"] = dec_str(abs(e_q - de))
            lo_e, hi_e = mirror_win["e_q_window_low"], mirror_win["e_q_window_high"]
            row["e_q_in_mirror_exp_band"] = bool(lo_e <= e_q <= hi_e)
            # float powering for filter scores (e_q ≈ 1 in float for all solved)
            e_q_f = float(e_q)  # will be 1.0
            row["priv_at_e_q"] = (d / float(1 << 256)) ** e_q_f
            row["priv_at_e_roof_N"] = (d / float(1 << 256)) ** 1.0
            if e.public_key:
                px, py = pubkey_xy(e.public_key)
                row["fp_at_e_q"] = fingerprint(px, py, e_q_f)
                row["dist_Px_pow_e_q_vs_priv"] = abs(
                    row["fp_at_e_q"]["Px"] - row["priv_at_e_q"]
                )
                row["dist_Px_pow_e_roof_N_vs_priv"] = abs(
                    row["fingerprints"]["e_roof_N"]["Px"] - row["priv_at_e_roof_N"]
                )
            lo, hi = e.range_min, e.range_max
            row["scalar_position"] = (d - lo) / (hi - lo + 1)
            # keep Decimal e_q for aggregate stats
            row["_e_q_dec"] = e_q
            row["_dist_roof_dec"] = dist_roof
            row["_dist_proxy_dec"] = dist_proxy
            solved_rows.append(row)

        all_rows.append(row)

    # --- correlations (band-controlled) ---
    corr = []
    mean_e_q = sum(r["_e_q_dec"] for r in solved_rows) / len(solved_rows)
    mean_dist_roof = sum(r["_dist_roof_dec"] for r in solved_rows) / len(solved_rows)
    mean_dist_proxy = sum(r["_dist_proxy_dec"] for r in solved_rows) / len(solved_rows)
    corr.append({
        "pair": "e_q vs roofs",
        "mean_e_q": dec_str(mean_e_q),
        "mean_dist_e_q_to_e_roof_N": dec_str(mean_dist_roof),
        "mean_dist_e_q_to_e_mirror_proxy": dec_str(mean_dist_proxy),
        "frac_closer_to_e_roof_N": sum(
            1 for r in solved_rows if r["e_q_closer_to"] == "e_roof_N"
        )
        / len(solved_rows),
        "frac_e_q_in_mirror_exp_band": sum(
            1 for r in solved_rows if r["e_q_in_mirror_exp_band"]
        )
        / len(solved_rows),
        "note": (
            "e_q sits just under e_roof_N; deficit from 1 is Decimal-scale (~1e-41). "
            "float64 cannot distinguish e_roof_N from 1.0 for powering."
        ),
    })

    # powered signal correlations at e_q and e_roof_N — with band control
    for label, get_sig, get_priv in (
        (
            "Px_pow(e_q) vs priv(e_q)",
            lambda r: r["fp_at_e_q"]["Px"],
            lambda r: r["priv_at_e_q"],
        ),
        (
            "Px_pow(e_roof_N) vs priv(e_roof_N)",
            lambda r: r["fingerprints"]["e_roof_N"]["Px"],
            lambda r: r["priv_at_e_roof_N"],
        ),
        (
            "Px_pow(e_lo) vs priv(e_q)",
            lambda r: r["fingerprints"]["e_lo"]["Px"],
            lambda r: r["priv_at_e_q"],
        ),
    ):
        xs = [get_sig(r) for r in solved_rows]
        ys = [get_priv(r) for r in solved_rows]
        rho_all = spearman(xs, ys)
        # band 65-130
        xs_b, ys_b = [], []
        for r in solved_rows:
            if 65 <= r["puzzle"] <= 130:
                xs_b.append(get_sig(r))
                ys_b.append(get_priv(r))
        rho_band = spearman(xs_b, ys_b)
        corr.append({
            "pair": label,
            "spearman_all": rho_all,
            "spearman_band_65_130": rho_band,
            "verdict_all": verdict(rho_all),
            "verdict_band": verdict(rho_band),
        })

    # local-band: for high-bit targets, distance of e_q to e_roof_N
    # P135 public-only mirror band
    p135 = next(r for r in all_rows if r["puzzle"] == 135)
    p135_report = {
        "direct_shells": p135["direct_shells"],
        "mirror_window_shells": p135["mirror_window_shells"],
        "N_mirror_bounds": p135["N_mirror_bounds"],
        "shell_distances": p135["shell_distances"],
        "e_roof_N": dec_str(E_ROOF_N),
        "e_mirror_proxy": dec_str(E_MIRROR_PROXY),
        "note": (
            "q = N-d unknown; use e_q_window_low..high as mirror exponent band "
            "right under e_roof_N"
        ),
    }

    # which direct shell is closest to e_roof_N for each n
    closest_to_roof = {"e_lo": 0, "e_hinge": 0, "e_hi": 0}
    for r in all_rows:
        d = r["shell_distances"]
        best = min(
            ("e_lo", Decimal(d["e_lo_vs_e_roof_N"])),
            ("e_hinge", Decimal(d["e_hinge_vs_e_roof_N"])),
            ("e_hi", Decimal(d["e_hi_vs_e_roof_N"])),
            key=lambda t: t[1],
        )[0]
        closest_to_roof[best] += 1

    payload = {
        "exhibit": "mirror_power_correlation_scan",
        "location": "ARCHIVE/briefcase/ecdlp_range/",
        "roofs": {
            "e_roof_binary": dec_str(E_ROOF_BINARY),
            "e_roof_N": dec_str(E_ROOF_N),
            "e_roof_N_deficit_from_1": dec_str(E_ROOF_N_DEFICIT),
            "e_mirror_proxy": dec_str(E_MIRROR_PROXY),
            "note": (
                "e_roof_N = log2(N)/256 < 1 because N < 2^256. "
                "Deficit is ~1e-41 — must use Decimal; float64 rounds to 1.0."
            ),
        },
        "hierarchy": [
            "256/256 = 1 — ideal binary ceiling (identity warp)",
            "log2(N)/256 — true scalar-order ceiling",
            "255/256 — coarse one-bit-below proxy",
            "log2(N-d)/256 — true solved mirror height",
            "log2(N-2^n)/256 .. log2(N-2^(n-1))/256 — unsolved mirror window band",
        ],
        "closest_direct_shell_to_e_roof_N_counts": closest_to_roof,
        "correlations": corr,
        "P135": p135_report,
        "solved_summary": {
            "n": len(solved_rows),
            "frac_e_q_closer_to_e_roof_N": sum(
                1 for r in solved_rows if r["e_q_closer_to"] == "e_roof_N"
            )
            / len(solved_rows),
            "frac_e_q_in_mirror_exp_band": sum(
                1 for r in solved_rows if r["e_q_in_mirror_exp_band"]
            )
            / len(solved_rows),
            "mean_e_q": dec_str(mean_e_q),
            "mean_e_q_dist_to_e_roof_N": dec_str(mean_dist_roof),
            "mean_e_q_dist_to_e_mirror_proxy": dec_str(mean_dist_proxy),
        },
        "rows": [
            {k: v for k, v in r.items() if not k.startswith("_")} for r in all_rows
        ],
        "ruling": (
            "e_roof_N = log2(N)/256 is the true near-1 scalar ceiling. "
            "e_q = log2(N-d)/256 is the solved mirror height and sits in the "
            "mirror exponent band under e_roof_N. Direct shells n/256 are "
            "range-height warps, not the order roof."
        ),
    }

    (OUT / "mirror_power_correlation_scan.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "# mirror_power_correlation_scan",
        "",
        "## Roofs",
        "",
        "```text",
        f"e_roof_binary  = 256/256 = {dec_str(E_ROOF_BINARY)}",
        f"e_roof_N       = log2(N)/256 = {dec_str(E_ROOF_N)}",
        f"1 - e_roof_N   = {dec_str(E_ROOF_N_DEFICIT)}",
        f"e_mirror_proxy = 255/256 = {dec_str(E_MIRROR_PROXY)}",
        "```",
        "",
        "Because `N < 2^256`, `e_roof_N < 1`. Deficit is ~1e-41 — **Decimal only**",
        "(float64 rounds `e_roof_N` to `1.0`).",
        "",
        "## Hierarchy",
        "",
    ]
    for h in payload["hierarchy"]:
        lines.append(f"- {h}")

    lines.extend([
        "",
        "## Solved: e_q = log2(N−d)/256",
        "",
        f"- mean e_q: `{payload['solved_summary']['mean_e_q']}`",
        f"- mean |e_q − e_roof_N|: `{payload['solved_summary']['mean_e_q_dist_to_e_roof_N']}`",
        f"- fraction closer to e_roof_N than 255/256: "
        f"**{payload['solved_summary']['frac_e_q_closer_to_e_roof_N']:.2f}**",
        f"- fraction e_q in mirror exp band: "
        f"**{payload['solved_summary']['frac_e_q_in_mirror_exp_band']:.2f}**",
        "",
        "## Direct shell closest to e_roof_N",
        "",
        f"`{closest_to_roof}`",
        "",
        "## Correlations (with band control)",
        "",
        "| pair | spearman all | spearman 65–130 | verdict all | verdict band |",
        "|------|--------------|-----------------|-------------|--------------|",
    ])
    for c in corr:
        if "spearman_all" not in c:
            continue
        lines.append(
            f"| `{c['pair']}` | {c['spearman_all']:+.4f} | "
            f"{c['spearman_band_65_130']:+.4f} | **{c['verdict_all']}** | "
            f"**{c['verdict_band']}** |"
        )

    lines.extend([
        "",
        "## P135 (unsolved) mirror exponent band",
        "",
        f"- e_hi / e_lo / e_hinge: `{p135['direct_shells']}`",
        f"- e_q_window_low: `{p135['mirror_window_shells']['e_q_window_low']}`",
        f"- e_q_window_high: `{p135['mirror_window_shells']['e_q_window_high']}`",
        f"- e_roof_N: `{dec_str(E_ROOF_N)}`",
        "",
        "q = N−d unknown; band sits right under e_roof_N.",
        "",
        "## Ruling",
        "",
        "```text",
        "256/256 = 1:     abstract binary ceiling (identity warp)",
        "log2(N)/256:     true scalar-order roof (use this; Decimal)",
        "log2(N-d)/256:   solved mirror height (sits under e_roof_N)",
        "mirror window:   log2(N-2^n)/256 .. log2(N-2^(n-1))/256",
        "255/256:         coarse proxy (farther from e_q than e_roof_N)",
        "```",
        "",
        "Judge Popcorn: **the better roof is the order roof, not the abstract 256.**",
        "",
        "Rebuild: `python build_mirror_power_correlation_scan.py`",
        "",
    ])

    (OUT / "mirror_power_correlation_scan.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    readme = OUT / "README.md"
    prev = readme.read_text(encoding="utf-8") if readme.exists() else ""
    if "mirror_power" not in prev:
        readme.write_text(
            prev.rstrip()
            + "\n\n| `mirror_power_correlation_scan.*` | "
            "e_roof_N = log2(N)/256, e_q, mirror window |\n\n"
            "```text\npython build_mirror_power_correlation_scan.py\n```\n",
            encoding="utf-8",
        )

    print(f"e_roof_N = {dec_str(E_ROOF_N)}")
    print(f"1 - e_roof_N = {dec_str(E_ROOF_N_DEFICIT)}")
    print(f"e_mirror_proxy = {dec_str(E_MIRROR_PROXY)}")
    print(
        f"frac e_q closer to e_roof_N: "
        f"{payload['solved_summary']['frac_e_q_closer_to_e_roof_N']}"
    )
    print(
        f"frac e_q in mirror band: "
        f"{payload['solved_summary']['frac_e_q_in_mirror_exp_band']}"
    )
    print(f"mean |e_q - e_roof_N| = {payload['solved_summary']['mean_e_q_dist_to_e_roof_N']}")
    print(f"closest direct shell to e_roof_N: {closest_to_roof}")
    for c in corr:
        if "spearman_all" in c:
            print(
                f"  {c['pair']}: all={c['spearman_all']:+.4f} "
                f"band={c['spearman_band_65_130']:+.4f} "
                f"({c['verdict_band']})"
            )
    print(f"P135 mirror band: {p135['mirror_window_shells']}")
    print(f"wrote {OUT / 'mirror_power_correlation_scan.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
