#!/usr/bin/env python3
"""
Last-is-first proxy test (puzzles 1-160 only — 161-256 not public).

Question: do higher-index puzzle pubkeys predict lower-index
(P135/P160) hash160 / x-y features better than lower-index anchors?

If yes → checksum-trail hypothesis gets support within visible set.
If flat → removal of 161-256 likely irrelevant to lower entropy.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_catalog import load_catalog  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

getcontext().prec = 80
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F

TARGETS = [135, 140, 145, 150, 155, 160]


def hash160_from_comp(comp_hex: str) -> int:
    comp = bytes.fromhex(comp_hex)
    return int.from_bytes(
        hashlib.new("ripemd160", hashlib.sha256(comp).digest()).digest(), "big"
    )


def pubkey_xy(comp_hex: str) -> tuple[int, int]:
    prefix = comp_hex[:2]
    px = int(comp_hex[2:], 16)
    # y from even/odd
    y_sq = (pow(px, 3, p) + 7) % p
    y = pow(y_sq, (p + 1) // 4, p)
    if (y % 2 == 0) != (prefix == "02"):
        y = p - y
    return px, y


def left5(h: int) -> int:
    return int(str(h)[:5])


def echo_frac(val: int, num: int, den: int = 256) -> int:
    if val <= 0:
        return 0
    return int((Decimal(val).ln() * Decimal(num) / Decimal(den)).exp())


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else 0.0


def load_anchors() -> list[dict]:
    cat = load_catalog()
    keys = parse_53125()
    out = []
    for n, e in sorted(cat.items()):
        if not e.public_key:
            continue
        px, py = pubkey_xy(e.public_key)
        h = hash160_from_comp(e.public_key)
        rec = {
            "n": n,
            "solved": e.solved,
            "px": px,
            "py": py,
            "hash160": h,
            "left5": left5(h),
            "d": keys[n].d if n in keys and keys[n].d else None,
        }
        out.append(rec)
    return out


def target_features() -> dict[int, dict]:
    cat = load_catalog()
    out = {}
    for t in TARGETS:
        e = cat[t]
        px, py = pubkey_xy(e.public_key)
        h = hash160_from_comp(e.public_key)
        out[t] = {
            "px": px,
            "py": py,
            "hash160": h,
            "left5": left5(h),
            "x_echo": echo_frac(px, t),
            "y_echo": echo_frac(py, t),
            "curve_echo": echo_frac((pow(px, 3, p) + 7) % p, t),
        }
    return out


def score_anchor_to_target(a: dict, t: dict) -> dict:
    h_a, h_t = a["hash160"], t["hash160"]
    ratio_gap = abs((Decimal(h_a) / Decimal(1 << (a["n"] - 1))) - (Decimal(h_t) / Decimal(1 << (t["hash160"] and 0 or 0))))
    # simpler metrics
    return {
        "left5_gap": abs(a["left5"] - t["left5"]),
        "hash_log_dist": abs(math.log10(h_a + 1) - math.log10(h_t + 1)),
        "hash_abs_dist_norm": abs(h_a - h_t) / max(h_a, h_t),
        "ratio_gap_band": abs((Decimal(h_a) / Decimal(1 << (a["n"] - 1))) - (Decimal(h_t) / Decimal(1 << (160 - 1)))) if a["n"] >= 1 else 0,
        "px_mod_gap": abs(a["px"] - t["px"]) / p,
        "x_echo_gap": abs(echo_frac(a["px"], 160) - t["x_echo"]),
        "y_echo_gap": abs(echo_frac(a["py"], 160) - t["y_echo"]),
        "curve_echo_gap": abs(echo_frac((pow(a["px"], 3, p) + 7) % p, 160) - t["curve_echo"]),
        "prefix_match": len(str(h_a) if False else ""),  # placeholder fixed below
    }


def prefix_match_len(a: int, b: int) -> int:
    sa, sb = str(a), str(b)
    n = 0
    for x, y in zip(sa, sb):
        if x != y:
            break
        n += 1
    return n


def main() -> None:
    anchors = load_anchors()
    targets = target_features()
    t160 = targets[160]

    print(f"Anchors with pubkey: {len(anchors)} (puzzles 1-160)")
    print("NOTE: puzzles 161-256 not in public catalog — proxy test on 1-160 only")
    print()

    metrics = [
        "left5_gap",
        "hash_log_dist",
        "hash_abs_dist_norm",
        "ratio_gap_band",
        "x_echo_gap",
        "y_echo_gap",
        "curve_echo_gap",
        "prefix_match",
    ]

    rows = []
    for a in anchors:
        if a["n"] == 160:
            continue
        s = {
            "left5_gap": abs(a["left5"] - t160["left5"]),
            "hash_log_dist": abs(math.log10(a["hash160"] + 1) - math.log10(t160["hash160"] + 1)),
            "hash_abs_dist_norm": abs(a["hash160"] - t160["hash160"]) / t160["hash160"],
            "ratio_gap_band": float(
                abs(
                    Decimal(a["hash160"]) / Decimal(1 << (a["n"] - 1))
                    - Decimal(t160["hash160"]) / Decimal(1 << 159)
                )
            ),
            "x_echo_gap": abs(echo_frac(a["px"], 160) - t160["x_echo"]),
            "y_echo_gap": abs(echo_frac(a["py"], 160) - t160["y_echo"]),
            "curve_echo_gap": abs(
                echo_frac((pow(a["px"], 3, p) + 7) % p, 160) - t160["curve_echo"]
            ),
            "prefix_match": prefix_match_len(a["hash160"], t160["hash160"]),
        }
        s["n"] = a["n"]
        s["solved"] = a["solved"]
        rows.append(s)

    print("=== Does puzzle index n predict proximity to P160? (Pearson n vs score) ===")
    print("Negative r => higher n = closer (better predictor)")
    print(f"{'metric':22s} {'all':>8s} {'solved':>8s} {'unsolved':>8s}")
    for m in metrics:
        if m == "prefix_match":
            # higher is better — invert for distance-style correlation
            vals_all = [-r[m] for r in rows]
        else:
            vals_all = [r[m] for r in rows]
        ns = [float(r["n"]) for r in rows]
        r_all = pearson(ns, vals_all)
        rs = [r for r in rows if r["solved"]]
        ru = [r for r in rows if not r["solved"]]
        r_s = pearson([float(r["n"]) for r in rs], [vals_all[i] for i, r in enumerate(rows) if r["solved"]])
        r_u = pearson([float(r["n"]) for r in ru], [vals_all[i] for i, r in enumerate(rows) if not r["solved"]])
        print(f"{m:22s} {r_all:8.4f} {r_s:8.4f} {r_u:8.4f}")

    print()
    print("=== Band comparison: mean distance to P160 hash160 ===")
    bands = [(1, 60, "low 1-60"), (61, 120, "mid 61-120"), (121, 159, "high 121-159")]
    for lo, hi, name in bands:
        sub = [r for r in rows if lo <= r["n"] <= hi]
        if not sub:
            continue
        print(
            f"  {name:14s} n={len(sub):2d}  "
            f"left5_gap={sum(r['left5_gap'] for r in sub)/len(sub):.1f}  "
            f"prefix_match={sum(r['prefix_match'] for r in sub)/len(sub):.2f}  "
            f"hash_norm={sum(r['hash_abs_dist_norm'] for r in sub)/len(sub):.4f}"
        )

    print()
    print("=== Top 10 closest to P160 left5 by puzzle index ===")
    by_l5 = sorted(rows, key=lambda r: r["left5_gap"])[:10]
    for r in by_l5:
        print(f"  P{r['n']:3d}  left5_gap={r['left5_gap']:5d}  prefix_match={r['prefix_match']:2d}  solved={r['solved']}")

    print()
    print("=== Top 10 closest ratio_gap_band to P160 ===")
    by_ratio = sorted(rows, key=lambda r: r["ratio_gap_band"])[:10]
    for r in by_ratio:
        print(f"  P{r['n']:3d}  ratio_gap={r['ratio_gap_band']:.6e}  left5_gap={r['left5_gap']}")

    # random baseline: shuffle n labels
    print()
    print("=== NULL: mean left5_gap for random 88 vs structured bands ===")
    mean_all = sum(r["left5_gap"] for r in rows) / len(rows)
    import random

    random.seed(0)
    random_means = []
    l5_pool = [a["left5"] for a in anchors if a["n"] != 160]
    for _ in range(5000):
        random_means.append(abs(random.choice(l5_pool) - t160["left5"]))
    print(f"  observed mean left5_gap (anchors to P160): {mean_all:.1f}")
    print(f"  random left5_gap null mean: {sum(random_means)/len(random_means):.1f}")

    # multi-target: high band vs low band for all unsolved targets
    print()
    print("=== Multi-target: high (121-159) vs low (1-60) anchors ===")
    high = [a for a in anchors if 121 <= a["n"] <= 159]
    low = [a for a in anchors if 1 <= a["n"] <= 60]
    for t in TARGETS:
        tg = targets[t]
        def mean_gap(group):
            return sum(abs(a["left5"] - tg["left5"]) for a in group) / len(group)
        hg, lg = mean_gap(high), mean_gap(low)
        print(f"  P{t}: high_band left5_gap={hg:.1f}  low_band={lg:.1f}  ratio={hg/lg if lg else 0:.2f}x")

    # permutation: is high band closer than low band by chance?
    print()
    print("=== Permutation: high(121-159) vs low(1-60) left5_gap to each target ===")
    high_ns = set(range(121, 160))
    low_ns = set(range(1, 61))
    high_a = [a for a in anchors if a["n"] in high_ns]
    low_a = [a for a in anchors if a["n"] in low_ns]
    perm_trials = 10000
    random.seed(42)
    for t in [135, 160]:
        tg = targets[t]
        obs = (
            sum(abs(a["left5"] - tg["left5"]) for a in high_a) / len(high_a)
            - sum(abs(a["left5"] - tg["left5"]) for a in low_a) / len(low_a)
        )
        pool = [a for a in anchors if a["n"] != t]
        better = 0
        for _ in range(perm_trials):
            sh = random.sample(pool, len(high_a) + len(low_a))
            h = sh[: len(high_a)]
            l = sh[len(high_a) :]
            delta = sum(abs(x["left5"] - tg["left5"]) for x in h) / len(h) - sum(
                abs(x["left5"] - tg["left5"]) for x in l
            ) / len(l)
            if delta <= obs:
                better += 1
        p_perm = better / perm_trials
        print(
            f"  P{t}: high-low delta={obs:+.1f}  "
            f"high wins if negative; p_perm={p_perm:.3f}  "
            f"({'high closer' if obs < 0 else 'low closer'})"
        )

    # same-bit-band ratio (128-160): removes denominator artifact
    print()
    print("=== Same-band ratio h/2^159 (puzzles 128-159 only) vs P160 ===")
    band_rows = [r for r in rows if 128 <= r["n"] <= 159]
    if band_rows:
        for r in sorted(band_rows, key=lambda x: x["ratio_gap_band"])[:8]:
            print(f"  P{r['n']:3d}  ratio_gap={r['ratio_gap_band']:.6e}  left5_gap={r['left5_gap']}")
        r_band = pearson(
            [float(r["n"]) for r in band_rows],
            [r["left5_gap"] for r in band_rows],
        )
        print(f"  Pearson n vs left5_gap within 128-159 band: {r_band:.4f}")

    # TDAD lane: solved high d values vs lower target hash160
    print()
    print("=== TDAD lane (solved d from 53125): high index vs P135/P160 features ===")
    keys = parse_53125()
    tdad_path = ROOT / "02_Research" / "notes" / "double_and_add.txt"
    tdad_vals: dict[int, int] = {}
    if tdad_path.exists():
        for line in tdad_path.read_text(encoding="utf-8").splitlines():
            m = __import__("re").match(r"puzzle\s+(\d+):\s*(\d+)", line.strip(), __import__("re").I)
            if m:
                tdad_vals[int(m.group(1))] = int(m.group(2))
    solved_high = [n for n in sorted(keys) if n >= 120 and n in tdad_vals]
    if solved_high and 135 in targets:
        t135 = targets[135]
        cor_tdad_l5 = pearson(
            [float(n) for n in solved_high],
            [abs(tdad_vals[n] - t135["left5"]) for n in solved_high],
        )
        cor_d_l5 = pearson(
            [float(n) for n in solved_high],
            [abs(keys[n].d - t135["hash160"]) / t135["hash160"] for n in solved_high],
        )
        print(f"  solved n>=120: Pearson n vs |TDAD-left5(P135)| = {cor_tdad_l5:.4f}")
        print(f"  solved n>=120: Pearson n vs |d-hash160(P135)|/H = {cor_d_l5:.4f}")
        best = min(solved_high, key=lambda n: abs(tdad_vals[n] - t135["left5"]))
        print(f"  closest TDAD to P135 left5: P{best} gap={abs(tdad_vals[best]-t135['left5'])}")
    else:
        print("  (TDAD table unavailable or no solved high puzzles)")

    # ruling
    r_n_l5 = pearson([float(r["n"]) for r in rows], [r["left5_gap"] for r in rows])
    print()
    if abs(r_n_l5) > 0.15:
        print(f"RULING: weak index gradient detected (r={r_n_l5:.3f}) — inspect, not proof")
    else:
        print(f"RULING: no index gradient to P160 (r={r_n_l5:.3f}) — 161-256 removal likely irrelevant")
        print("Higher puzzles do NOT systematically constrain lower hash160 bands in visible 1-160 set.")

    out = ROOT / "ARCHIVE" / "last_is_first_proxy_test.json"
    out.write_text(
        json.dumps(
            {
                "note": "161-256 not public; proxy on puzzles 1-160",
                "n_anchors": len(rows),
                "pearson_n_left5_gap": r_n_l5,
                "top10_left5": [{k: r[k] for k in ("n", "left5_gap", "prefix_match", "solved")} for r in by_l5],
                "bands": {
                    name: {
                        "mean_left5_gap": sum(r["left5_gap"] for r in rows if lo <= r["n"] <= hi)
                        / max(1, len([r for r in rows if lo <= r["n"] <= hi])),
                    }
                    for lo, hi, name in bands
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
