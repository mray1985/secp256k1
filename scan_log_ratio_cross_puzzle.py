#!/usr/bin/env python3
"""Cross-puzzle scan of change-of-base log features.

Seed observation (Puzzle 60):
  d * log(Py) / log(Px) ≈ 1.1418e18

Family (locked for this probe):
  F(scalar, a, b) = scalar * ln(a) / ln(b)   for a,b > 1

Scalars: d, k (when known), n, 1
Limbs:   Px, Py, p-y, r, s, z, Rx(=r), Ry (y of [k]G when k known)

Correlation checks (honest, not promotion):
  * Spearman(F, n), Spearman(F, log2(d)), Spearman(F / 2^n, n)
  * Pairing shuffle: re-pair scalar from puzzle i with limbs from π(i)
  * Report whether real |ρ| exceeds shuffle null

0 verified bits unless pairing gate passes (it is not expected to).
"""

from __future__ import annotations

import json
import math
import random
import statistics
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any, Callable

from ecdsa import SECP256k1
from ecdsa.ellipticcurve import Point
from ecdsa.numbertheory import square_root_mod_prime

from puzzle_catalog import load_catalog

getcontext().prec = 80

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "logs" / "log_ratio_scan"
P = SECP256k1.curve.p()
N = int(SECP256k1.order)
G = SECP256k1.generator
CURVE = SECP256k1.curve


def ln(x: int) -> Decimal:
    return Decimal(x).ln()


def feature(scalar: int, a: int, b: int) -> float | None:
    if scalar is None or a is None or b is None:
        return None
    if scalar <= 0 or a <= 1 or b <= 1:
        return None
    try:
        return float(Decimal(scalar) * ln(a) / ln(b))
    except Exception:
        return None


def spearman(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 5:
        return None

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
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    denx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    deny = math.sqrt(sum((b - my) ** 2 for b in ry))
    if denx == 0 or deny == 0:
        return None
    return num / (denx * deny)


@dataclass
class Row:
    n: int
    d: int | None
    k: int | None
    Px: int | None
    Py: int | None
    Pmy: int | None
    r: int | None
    s: int | None
    z: int | None
    Ry: int | None  # y of [k]G when k known


def recover_xy_from_pubkey(comp_hex: str) -> tuple[int, int]:
    raw = bytes.fromhex(comp_hex)
    px = int.from_bytes(raw[1:], "big")
    y2 = (pow(px, 3, P) + 7) % P
    y = square_root_mod_prime(y2, P)
    if (raw[0] == 0x02 and (y & 1)) or (raw[0] == 0x03 and not (y & 1)):
        y = P - y
    return px, y


def load_rows() -> list[Row]:
    cat = load_catalog()
    rsz = json.loads((ROOT / "ARCHIVE" / "puzzle_rsz_cache.json").read_text(encoding="utf-8"))
    rows: list[Row] = []
    for n, e in sorted(cat.items()):
        if not e.solved and not e.has_pubkey:
            continue
        d = e.private_key or None
        px = py = None
        if d:
            pt = G * d
            px, py = pt.x(), pt.y()
        elif e.public_key:
            px, py = recover_xy_from_pubkey(e.public_key)
        info = rsz.get(str(n)) or rsz.get(n) or {}
        if not isinstance(info, dict):
            info = {}
        r = int(info["r"]) if info.get("r") not in (None, "") else None
        s = int(info["s"]) if info.get("s") not in (None, "") else None
        z = int(info["z"]) if info.get("z") not in (None, "") else None
        k = int(info["k"]) if info.get("k") not in (None, "") else None
        # Derive k when d,r,s,z known: k ≡ s^{-1}(z + r d) (mod N)
        if k is None and d and r and s and z is not None:
            try:
                k = (pow(s, -1, N) * ((z + r * d) % N)) % N
                if k == 0:
                    k = None
            except ValueError:
                k = None
        ry = None
        if k:
            try:
                rpt = G * k
                # r should equal rpt.x() mod N (actually x mod N for ECDSA)
                ry = rpt.y()
            except Exception:
                ry = None
        rows.append(
            Row(
                n=n,
                d=d,
                k=k,
                Px=px,
                Py=py,
                Pmy=(P - py) if py is not None else None,
                r=r,
                s=s,
                z=z,
                Ry=ry,
            )
        )
    return rows


def limb_map(row: Row) -> dict[str, int | None]:
    return {
        "Px": row.Px,
        "Py": row.Py,
        "Pmy": row.Pmy,
        "r": row.r,
        "s": row.s,
        "z": row.z,
        "Ry": row.Ry,
    }


def scalar_map(row: Row) -> dict[str, int | None]:
    return {
        "d": row.d,
        "k": row.k,
        "n": row.n,
        "one": 1,
    }


def collect_feature(
    rows: list[Row],
    scalar_name: str,
    a_name: str,
    b_name: str,
    *,
    shuffle_limbs: bool = False,
    seed: int = 0,
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    order = list(range(len(rows)))
    if shuffle_limbs:
        rng.shuffle(order)
    out: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        donor = rows[order[i]] if shuffle_limbs else row
        sc = scalar_map(row).get(scalar_name)
        limbs = limb_map(donor)
        a, b = limbs.get(a_name), limbs.get(b_name)
        # For shuffle: keep scalar from row, limbs from donor
        f = feature(sc, a, b) if sc is not None else None
        if f is None or not math.isfinite(f):
            continue
        out.append(
            {
                "n": row.n,
                "d": row.d,
                "feature": f,
                "log2_d": math.log2(row.d) if row.d else None,
                "feature_over_2n": f / (2**row.n),
                "feature_over_d": (f / row.d) if row.d else None,
            }
        )
    return out


def summarize(points: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(points) < 5:
        return {"label": label, "n": len(points), "status": "insufficient"}
    fs = [p["feature"] for p in points]
    ns = [float(p["n"]) for p in points]
    logd = [p["log2_d"] for p in points if p["log2_d"] is not None]
    fs_d = [p["feature"] for p in points if p["log2_d"] is not None]
    f2n = [p["feature_over_2n"] for p in points]
    fod = [p["feature_over_d"] for p in points if p["feature_over_d"] is not None]
    return {
        "label": label,
        "n": len(points),
        "feature_mean": statistics.mean(fs),
        "feature_stdev": statistics.pstdev(fs) if len(fs) > 1 else 0.0,
        "feature_min": min(fs),
        "feature_max": max(fs),
        "spearman_F_vs_n": spearman(fs, ns),
        "spearman_F_vs_log2d": spearman(fs_d, logd) if len(logd) >= 5 else None,
        "spearman_F_over_2n_vs_n": spearman(f2n, ns),
        "spearman_F_over_d_vs_n": spearman(fod, [float(p["n"]) for p in points if p["feature_over_d"] is not None])
        if len(fod) >= 5
        else None,
        "mean_F_over_d": statistics.mean(fod) if fod else None,
        # F/d ≈ log(a)/log(b) — the pure change-of-base ratio
        "stdev_F_over_d": statistics.pstdev(fod) if len(fod) > 1 else None,
    }


def shuffle_null(
    rows: list[Row],
    scalar_name: str,
    a_name: str,
    b_name: str,
    *,
    trials: int = 200,
    metric: str = "spearman_F_vs_n",
) -> dict[str, Any]:
    real = summarize(collect_feature(rows, scalar_name, a_name, b_name), "real")
    real_v = real.get(metric)
    if real_v is None:
        return {"real": real, "null": None}
    null_vals: list[float] = []
    for t in range(trials):
        pts = collect_feature(rows, scalar_name, a_name, b_name, shuffle_limbs=True, seed=10_000 + t)
        s = summarize(pts, f"shuffle_{t}")
        v = s.get(metric)
        if v is not None:
            null_vals.append(v)
    if not null_vals:
        return {"real": real, "null": None}
    # two-sided: how often |null| >= |real|
    thr = abs(real_v)
    exceed = sum(1 for v in null_vals if abs(v) >= thr)
    return {
        "metric": metric,
        "real_value": real_v,
        "null_mean": statistics.mean(null_vals),
        "null_stdev": statistics.pstdev(null_vals),
        "null_p90_abs": sorted(abs(v) for v in null_vals)[int(0.9 * (len(null_vals) - 1))],
        "empirical_p": exceed / len(null_vals),
        "trials": len(null_vals),
        "real_summary": real,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    solved = [r for r in rows if r.d]
    print(f"rows={len(rows)} solved={len(solved)} with_k={sum(1 for r in rows if r.k)}")

    # Seed identity check (puzzle 60)
    r60 = next(r for r in rows if r.n == 60)
    seed = feature(r60.d, r60.Py, r60.Px)
    print(f"seed P60 d*log(Py)/log(Px) = {seed}")

    scalars = ["d", "k", "n", "one"]
    limbs = ["Px", "Py", "Pmy", "r", "s", "z", "Ry"]
    # ordered pairs a!=b
    pairs = [(a, b) for a in limbs for b in limbs if a != b]

    results: list[dict[str, Any]] = []
    for sc in scalars:
        for a, b in pairs:
            pts = collect_feature(solved if sc == "d" else rows, sc, a, b)
            # k features only where k exists
            if sc == "k":
                pts = collect_feature([r for r in rows if r.k and r.d], sc, a, b)
            summ = summarize(pts, f"{sc}*log({a})/log({b})")
            if summ.get("status") == "insufficient":
                continue
            results.append(
                {
                    "scalar": sc,
                    "a": a,
                    "b": b,
                    "formula": f"{sc}*log({a})/log({b})",
                    **{k: v for k, v in summ.items() if k != "label"},
                }
            )

    # Rank by |spearman F vs n| and by |spearman F/d vs n| (structure beyond d-scale)
    by_n = sorted(
        [r for r in results if r.get("spearman_F_vs_n") is not None],
        key=lambda r: abs(r["spearman_F_vs_n"]),
        reverse=True,
    )
    by_fod = sorted(
        [r for r in results if r.get("spearman_F_over_d_vs_n") is not None],
        key=lambda r: abs(r["spearman_F_over_d_vs_n"]),
        reverse=True,
    )
    # F/d ≈ log(a)/log(b): correlation of pure ratio with n
    pure_ratio = sorted(
        [r for r in results if r["scalar"] == "one" and r.get("spearman_F_vs_n") is not None],
        key=lambda r: abs(r["spearman_F_vs_n"]),
        reverse=True,
    )

    # Pairing gates on top candidates + the seed formula
    gate_targets = [
        ("d", "Py", "Px"),  # seed
        ("d", "Px", "Py"),
        ("d", "r", "s"),
        ("d", "Px", "r"),
        ("k", "Px", "Py"),
        ("k", "r", "s"),
        ("one", "Py", "Px"),
        ("one", "r", "s"),
    ]
    # add top-5 by |ρ(F,n)| for d-scalar
    for r in by_n:
        if r["scalar"] == "d":
            t = (r["scalar"], r["a"], r["b"])
            if t not in gate_targets:
                gate_targets.append(t)
            if len([x for x in gate_targets if x[0] == "d"]) >= 8:
                break

    gates = []
    for sc, a, b in gate_targets:
        base_rows = [r for r in solved] if sc in ("d", "one", "n") else [r for r in rows if r.k and r.d]
        g_n = shuffle_null(base_rows, sc, a, b, metric="spearman_F_vs_n")
        g_fod = shuffle_null(base_rows, sc, a, b, metric="spearman_F_over_d_vs_n")
        gates.append(
            {
                "formula": f"{sc}*log({a})/log({b})",
                "gate_F_vs_n": g_n,
                "gate_F_over_d_vs_n": g_fod,
            }
        )

    # Per-puzzle table for seed formula
    seed_table = collect_feature(solved, "d", "Py", "Px")

    payload = {
        "seed": {
            "puzzle": 60,
            "formula": "d * log(Py) / log(Px)",
            "value": seed,
            "expected_approx": 1.141812980483051e18,
            "match": abs(seed - 1.141812980483051e18) / 1.141812980483051e18 < 1e-12,
        },
        "n_formulas_evaluated": len(results),
        "top_by_abs_spearman_F_vs_n": by_n[:15],
        "top_by_abs_spearman_F_over_d_vs_n": by_fod[:15],
        "top_pure_log_ratio_one_star": pure_ratio[:10],
        "pairing_gates": gates,
        "seed_formula_per_puzzle": seed_table,
        "ruling": None,
        "verified_bits": 0,
    }

    # Ruling: any gate with empirical_p < 0.01 on F/d vs n (non-scale) and real |ρ|>0.3?
    survivors = []
    for g in gates:
        gf = g["gate_F_over_d_vs_n"]
        if not gf or gf.get("real_value") is None:
            continue
        if abs(gf["real_value"]) >= 0.3 and gf.get("empirical_p", 1) < 0.01:
            survivors.append(g["formula"])
    payload["ruling"] = {
        "survivors_pairing_gate_F_over_d": survivors,
        "conclusion": (
            "PASS pairing gate"
            if survivors
            else "NULL — no log-ratio feature beats shuffle pairing at p<0.01 on F/d vs n"
        ),
    }

    out_json = OUT / "log_ratio_cross_puzzle.json"
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Markdown summary
    lines = [
        "# Cross-puzzle log-ratio scan",
        "",
        "**Status:** probe complete — **0 verified bits** (unless survivors listed).",
        "",
        "## Seed (Puzzle 60)",
        "",
        r"\[",
        r"d\cdot\log(P_y)/\log(P_x)\approx 1.141812980483051\times 10^{18}",
        r"\]",
        "",
        f"Recomputed: `{seed}` match={payload['seed']['match']}",
        "",
        "## Family",
        "",
        "`F = scalar * ln(a) / ln(b)` over scalars `{d,k,n,1}` and limbs "
        "`{Px,Py,p−y,r,s,z,Ry}`.",
        "",
        f"Formulas evaluated: **{len(results)}** on {len(solved)} solved puzzles.",
        "",
        "## Top |Spearman(F, n)|",
        "",
        "| Formula | n | ρ(F,n) | ρ(F/d,n) | mean(F/d) |",
        "|---------|--:|-------:|---------:|----------:|",
    ]
    for r in by_n[:12]:
        lines.append(
            f"| `{r['formula']}` | {r['n']} | {r['spearman_F_vs_n']:.4f} | "
            f"{(r['spearman_F_over_d_vs_n'] if r['spearman_F_over_d_vs_n'] is not None else float('nan')):.4f} | "
            f"{(r['mean_F_over_d'] if r['mean_F_over_d'] is not None else float('nan')):.6f} |"
        )
    lines += [
        "",
        "## Pairing gates (shuffle limbs, keep scalar)",
        "",
        "| Formula | ρ(F,n) | p_emp | ρ(F/d,n) | p_emp |",
        "|---------|-------:|------:|---------:|------:|",
    ]
    for g in gates:
        gn, gf = g["gate_F_vs_n"], g["gate_F_over_d_vs_n"]
        lines.append(
            f"| `{g['formula']}` | "
            f"{gn.get('real_value') if gn else None} | {gn.get('empirical_p') if gn else None} | "
            f"{gf.get('real_value') if gf else None} | {gf.get('empirical_p') if gf else None} |"
        )
    lines += [
        "",
        "## Ruling",
        "",
        f"**{payload['ruling']['conclusion']}**",
        "",
        "Note: raw `d*log(a)/log(b)` tracks `d` (hence puzzle size) almost by construction; "
        "the informative object is `F/d = log(a)/log(b)` and whether it pairs with the correct "
        "`[d]G` under shuffle.",
        "",
        f"Artifact: `{out_json}`",
    ]
    out_md = OUT / "LOG_RATIO_CROSS_PUZZLE.md"
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")
    print("ruling:", payload["ruling"]["conclusion"])
    if by_n:
        print("top F vs n:", by_n[0]["formula"], by_n[0]["spearman_F_vs_n"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
