#!/usr/bin/env python3
"""
Coupled RSZ invariants on genesis spend panel (184 rows).

Tests multi-variable quantities f(r,s,z,k,d,p,N) — not marginal r/N vs n.

Lanes:
  A. ECDSA system: k from d, x([k]G)==r, residuals sk+rd-z
  B. Roof stitch: (r - map_p_to_n(Px)) mod N
  C. k-structure: k/d, k-TDAD, k^-1 vs 5^-1 anchor
  D. Field defect: (N*Px mod p) coupled with r mod p

Writes:
  ARCHIVE/briefcase/puzzlepubkeys/puzzle_genesis_rsz_coupled.{json,md}
"""

from __future__ import annotations

import json
import math
import random
import re
import statistics
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

from build_complexity_operations_ledger import N, map_p_to_n, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog
from puzzle_keys_53125 import parse_53125

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "ARCHIVE" / "briefcase" / "puzzlepubkeys" / "puzzle_genesis_rsz_1_256.json"
PUB161 = ROOT / "ARCHIVE" / "briefcase" / "puzzlepubkeys" / "puzzle_161_256_pubkeys.json"
TDAD_TXT = ROOT / "02_Research" / "notes" / "double_and_add.txt"
OUT_JSON = ROOT / "ARCHIVE" / "briefcase" / "puzzlepubkeys" / "puzzle_genesis_rsz_coupled.json"
OUT_MD = ROOT / "ARCHIVE" / "briefcase" / "puzzlepubkeys" / "puzzle_genesis_rsz_coupled.md"

INV5 = pow(5, -1, N)


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else 0.0


def partial_corr(x: list[float], y: list[float], z: list[float]) -> float:
    def resid(a, b):
        rb = pearson(a, b)
        sa, sb = statistics.pstdev(a), statistics.pstdev(b)
        if sa == 0:
            return [0.0] * len(a)
        ma, mb = statistics.mean(a), statistics.mean(b)
        return [ai - ma - rb * (sb / sa) * (bi - mb) for ai, bi in zip(a, b)]

    return pearson(resid(x, z), resid(y, z))


def perm_p(ns: list[float], ys: list[float], trials: int = 2000) -> float:
    random.seed(1)
    obs = abs(pearson(ns, ys))
    count = 0
    for _ in range(trials):
        sh = ys[:]
        random.shuffle(sh)
        if abs(pearson(ns, sh)) >= obs:
            count += 1
    return count / trials


def norm_mod(x: int) -> float:
    return x / N


def signed_norm_mod(x: int) -> float:
    x = x % N
    if x > N // 2:
        x -= N
    return x / N


def recover_k(r: int, s: int, z: int, d: int) -> int:
    return (pow(s, -1, N) * (z + r * d)) % N


def x_from_k(k: int) -> int:
    sk = SigningKey.from_secret_exponent(k % N, curve=SECP256k1)
    return sk.verifying_key.pubkey.point.x()


def load_tdad() -> dict[int, int]:
    out: dict[int, int] = {}
    if not TDAD_TXT.exists():
        return out
    for line in TDAD_TXT.read_text(encoding="utf-8").splitlines():
        m = re.match(r"puzzle\s+(\d+):\s*(.*)", line.strip(), re.I)
        if not m:
            continue
        rest = m.group(2).strip()
        if not rest:
            continue
        val_s = rest.split("=")[0].strip().replace("\t", "")
        if val_s and val_s[0].isdigit():
            out[int(m.group(1))] = int(val_s)
    return out


def load_pubkey_map() -> dict[int, str]:
    m: dict[int, str] = {}
    keys53125 = parse_53125()
    for n, pk in keys53125.items():
        if pk.px:
            # rebuild compressed from 53125 coords is fragile; prefer RSZ pub field
            pass
    cat = load_catalog()
    for n, e in cat.items():
        if e.public_key:
            m[n] = e.public_key
    if PUB161.exists():
        for row in json.loads(PUB161.read_text(encoding="utf-8")):
            m[row["puzzle"]] = row["pubkey_compressed"]
    return m


def band(n: int) -> str:
    if n >= 161:
        return "161-256"
    if n >= 65:
        return "65-160"
    return "1-64"


def build_rows() -> list[dict]:
    rsz_rows = json.loads(DATA.read_text(encoding="utf-8"))
    keys53125 = parse_53125()
    cat = load_catalog()
    tdad = load_tdad()
    pub_map = load_pubkey_map()

    out: list[dict] = []
    for rec in rsz_rows:
        n = rec["puzzle"]
        r, s, z = rec["r"], rec["s"], rec["z"]
        d = None
        if n in keys53125 and keys53125[n].d:
            d = keys53125[n].d
        elif n in cat and cat[n].private_key:
            d = cat[n].private_key

        comp = rec.get("pub_compressed") or pub_map.get(n)
        px = py = None
        if comp:
            px, py = pubkey_xy(comp)

        row: dict = {
            "n": n,
            "band": band(n),
            "has_d": d is not None,
            "has_pubkey": px is not None,
            "source": rec.get("source", ""),
        }

        if px is not None:
            px_n = map_p_to_n(px)
            roof = (r - px_n) % N
            rem = (N * px) % p
            row.update(
                {
                    "roof_stitch_norm": norm_mod(roof),
                    "roof_stitch_signed": signed_norm_mod(roof),
                    "px_map_over_N": norm_mod(px_n),
                    "r_minus_px_map_over_N": (r / N) - norm_mod(px_n),
                    "rem_Nx_mod_p_over_p": rem / p,
                    "r_mod_p_over_p": (r % p) / p,
                    "rem_minus_r_mod_p_over_p": (rem - (r % p)) / p,
                    "defect_px_minus_p_times_map_over_N": norm_mod(px - px_n * p // N),
                }
            )

        if d is not None:
            k = recover_k(r, s, z, d)
            kinv = pow(k, -1, N)
            resid = (s * k - z - r * d) % N
            xk = x_from_k(k)
            row.update(
                {
                    "ecdsa_resid_zero": resid == 0,
                    "x_kG_eq_r": xk == r,
                    "k_over_N": norm_mod(k),
                    "k_inv_over_N": norm_mod(kinv),
                    "k_minus_d_signed": signed_norm_mod(k - d),
                    "kinv_minus_inv5_signed": signed_norm_mod(kinv - INV5),
                    "kd_mod_over_N": norm_mod(k * d),
                    "d_over_N": norm_mod(d),
                    "rz_minus_rd_over_N": norm_mod(z - r * d),  # should equal sk mod N
                    "k_over_d_ratio": k / d if d else None,
                }
            )
            T = tdad.get(n)
            if T is not None:
                row["tdad_T"] = T
                row["d_minus_T_over_N"] = signed_norm_mod(d - T)
                row["k_minus_T_signed"] = signed_norm_mod(k - T)

        out.append(row)
    return out


def corr_panel(rows: list[dict], features: list[str], label: str) -> dict:
    panel: dict = {"label": label, "n": len(rows), "correlations": {}, "perm_p": {}}
    ns = [float(r["n"]) for r in rows]
    for feat in features:
        vals = [r[feat] for r in rows if feat in r and r[feat] is not None]
        if len(vals) < len(rows):
            sub_ns = [float(r["n"]) for r in rows if feat in r and r[feat] is not None]
        else:
            sub_ns = ns
        if len(vals) < 5:
            continue
        panel["correlations"][feat] = pearson(sub_ns, vals)
        panel["perm_p"][feat] = perm_p(sub_ns, vals)
    return panel


def zscore(val: float, vals: list[float]) -> float:
    mu = statistics.mean(vals)
    sd = statistics.pstdev(vals) or 1.0
    return (val - mu) / sd


def main() -> None:
    rows = build_rows()
    n_d = sum(1 for r in rows if r["has_d"])
    n_pub = sum(1 for r in rows if r["has_pubkey"])
    ecdsa_ok = sum(1 for r in rows if r.get("ecdsa_resid_zero"))
    x_ok = sum(1 for r in rows if r.get("x_kG_eq_r"))

    roof_feats = [
        "roof_stitch_norm",
        "roof_stitch_signed",
        "r_minus_px_map_over_N",
        "rem_minus_r_mod_p_over_p",
        "defect_px_minus_p_times_map_over_N",
    ]
    k_feats = [
        "k_over_N",
        "k_inv_over_N",
        "k_minus_d_signed",
        "kinv_minus_inv5_signed",
        "kd_mod_over_N",
        "d_minus_T_over_N",
        "k_minus_T_signed",
    ]

    panels = {
        "all_roof": corr_panel([r for r in rows if "roof_stitch_norm" in r], roof_feats, "all with pubkey"),
        "161_256_roof": corr_panel(
            [r for r in rows if r["band"] == "161-256" and "roof_stitch_norm" in r],
            roof_feats,
            "161-256 roof",
        ),
        "solved_k": corr_panel([r for r in rows if r["has_d"]], k_feats, "solved with d (k recovered)"),
        "solved_roof": corr_panel(
            [r for r in rows if r["has_d"] and "roof_stitch_norm" in r],
            roof_feats,
            "solved roof stitch",
        ),
        "tdad_subset": corr_panel(
            [r for r in rows if "d_minus_T_over_N" in r],
            ["d_minus_T_over_N", "k_minus_T_signed", "kinv_minus_inv5_signed"],
            "TDAD transcript puzzles",
        ),
    }

    # P135 projection vs 161-256 cloud
    p135 = next((r for r in rows if r["n"] == 135), None)
    train161 = [r for r in rows if r["band"] == "161-256"]
    p135_z: dict[str, float] = {}
    if p135:
        for feat in roof_feats + k_feats:
            if feat not in p135:
                continue
            cloud = [r[feat] for r in train161 if feat in r]
            if cloud:
                p135_z[feat] = zscore(p135[feat], cloud)

    # Best coupled vs marginal baseline
    marginal_r = pearson(
        [float(r["n"]) for r in rows],
        [json.loads(DATA.read_text())[i]["r"] / N for i in range(len(rows))],
    )
    best_coupled = ("", 0.0, "")
    for pname, panel in panels.items():
        for feat, r_val in panel["correlations"].items():
            if math.isnan(r_val):
                continue
            if abs(r_val) > abs(best_coupled[1]):
                best_coupled = (feat, r_val, pname)

    # kd_mod vs n: d bit-length is ~ n by puzzle definition (r(n, log2 d) ~ 1)
    solved = [r for r in rows if r["has_d"]]
    log2_d_corr = None
    if len(solved) >= 10:
        import math as _math

        log2_d_corr = pearson(
            [float(r["n"]) for r in solved],
            [_math.log2(r["d_over_N"] * (2**256)) for r in solved],
        )

    report = {
        "n_rows": len(rows),
        "n_with_d": n_d,
        "n_with_pubkey": n_pub,
        "ecdsa_resid_zero_count": ecdsa_ok,
        "x_kG_eq_r_count": x_ok,
        "marginal_r_over_N_vs_n": marginal_r,
        "best_coupled": {
            "feature": best_coupled[0],
            "pearson_n": best_coupled[1],
            "panel": best_coupled[2],
        },
        "kd_mod_note": {
            "r_n_log2_d": log2_d_corr,
            "interpretation": "k*d mod N tracks n because d ~ 2^(n-1) by puzzle definition; not independent nonce structure",
        },
        "notes": {
            "d_minus_T_tautology": "double_and_add.txt final value equals d for solved puzzles — not an independent check",
        },
        "panels": panels,
        "p135_z_vs_161_256": p135_z,
        "p135_row": {k: v for k, v in (p135 or {}).items() if k != "source"},
    }

    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Genesis RSZ coupled invariants",
        "",
        f"Rows: **{len(rows)}** | with d: **{n_d}** | with pubkey: **{n_pub}**",
        f"ECDSA resid zero: **{ecdsa_ok}/{n_d}** | x([k]G)==r: **{x_ok}/{n_d}**",
        "",
        "## vs marginal baseline",
        "",
        f"| test | r(n, feature) |",
        f"|------|---------------|",
        f"| marginal r/N | {marginal_r:+.3f} |",
        f"| best coupled | {best_coupled[1]:+.3f} ({best_coupled[0]}, {best_coupled[2]}) |",
        "",
        "## Lane A — ECDSA system (solved, k recovered)",
        "",
        "| feature | r(n) | perm p |",
        "|---------|------|--------|",
    ]
    for feat, r_val in panels["solved_k"]["correlations"].items():
        pp = panels["solved_k"]["perm_p"].get(feat, float("nan"))
        lines.append(f"| {feat} | {r_val:+.3f} | {pp:.3f} |")

    if log2_d_corr is not None:
        lines += [
            "",
            f"**kd_mod artifact:** r(n, log2 d) = **{log2_d_corr:+.3f}** — k*d/N inherits index through d-scale, not k-structure.",
        ]

    lines += [
        "",
        "_Note: `d_minus_T` is tautological (transcript stores final d). Meaningful TDAD tests need operation-path intermediates, not final scalar._",
    ]

    lines += [
        "",
        "## Lane B — Roof stitch (r vs map_p_to_n(Px))",
        "",
        "| band | feature | r(n) | perm p |",
        "|------|---------|------|--------|",
    ]
    for band_name, key in [("all", "all_roof"), ("161-256", "161_256_roof"), ("solved", "solved_roof")]:
        p = panels[key]
        for feat, r_val in p["correlations"].items():
            pp = p["perm_p"].get(feat, float("nan"))
            lines.append(f"| {band_name} | {feat} | {r_val:+.3f} | {pp:.3f} |")

    lines += [
        "",
        "## Lane C — TDAD subset",
        "",
        "| feature | r(n) | perm p |",
        "|---------|------|--------|",
    ]
    for feat, r_val in panels["tdad_subset"]["correlations"].items():
        pp = panels["tdad_subset"]["perm_p"].get(feat, float("nan"))
        lines.append(f"| {feat} | {r_val:+.3f} | {pp:.3f} |")

    if p135_z:
        lines += [
            "",
            "## P135 vs 161-256 cloud (z-score on coupled features)",
            "",
            "| feature | z |",
            "|---------|---|",
        ]
        for feat, z in sorted(p135_z.items(), key=lambda x: -abs(x[1])):
            lines.append(f"| {feat} | {z:+.2f} |")

    lines += [
        "",
        "## Scope",
        "",
        "Coupled panel tests **multi-variable** structure. Null perm p > 0.05 means no index encoding in that invariant.",
        "Does **not** close TDAD recipe search or full f(r,s,z,k,d,p,N) algebra.",
        "",
        f"JSON: `{OUT_JSON.name}`",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print(f"ECDSA ok {ecdsa_ok}/{n_d}, x([k]G)==r {x_ok}/{n_d}")
    print(f"Best coupled: {best_coupled[0]} r={best_coupled[1]:+.3f}")


if __name__ == "__main__":
    main()
