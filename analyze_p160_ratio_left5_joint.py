#!/usr/bin/env python3
"""
P160 band combined filter:
  ratio_gap = |(h/d) - (H_P160/d)|
  left5_gap = |left5(h) - left5(H_P160)|

Test whether close ratio + close left5 co-occur more than independence expects.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_catalog import load_catalog  # noqa: E402

LO160 = 1 << 159
LEFT5_SPACE = 90_000
P160_LEFT5 = 13260


def hash160_compressed(d: int) -> int:
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1)
    pub = sk.get_verifying_key().to_string()
    x, y = pub[:32], pub[32:]
    comp = (b"\x02" if (y[-1] & 1) == 0 else b"\x03") + x
    h = hashlib.new("ripemd160", hashlib.sha256(comp).digest()).digest()
    return int.from_bytes(h, "big")


def left5(h: int) -> int:
    return int(str(h)[:5])


def p160_hash160() -> int:
    comp = bytes.fromhex(load_catalog()[160].public_key)
    return int.from_bytes(
        hashlib.new("ripemd160", hashlib.sha256(comp).digest()).digest(), "big"
    )


def build_rows(n: int, h_p160: int) -> list[dict]:
    rows = []
    for off in range(n):
        d = LO160 + off
        h = hash160_compressed(d)
        l5 = left5(h)
        ratio = Decimal(h) / Decimal(d)
        ratio_p160 = Decimal(h_p160) / Decimal(d)
        ratio_gap = float(abs(ratio - ratio_p160))
        # equivalent: |h - h_p160| / d
        l5_gap = abs(l5 - P160_LEFT5)
        rows.append(
            {
                "offset": off,
                "d": d,
                "h": h,
                "left5": l5,
                "ratio": float(ratio),
                "ratio_p160": float(ratio_p160),
                "ratio_gap": ratio_gap,
                "left5_gap": l5_gap,
                "log_ratio_gap": math.log10(ratio_gap + 1e-300),
            }
        )
    return rows


def rank(values: list[float], *, reverse: bool = False) -> list[int]:
    """Rank 0 = best (smallest gap unless reverse)."""
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=reverse)
    ranks = [0] * len(values)
    for r, i in enumerate(order):
        ranks[i] = r
    return ranks


def joint_enrichment(rows: list[dict]) -> dict:
    n = len(rows)
    ratio_gaps = [r["ratio_gap"] for r in rows]
    l5_gaps = [r["left5_gap"] for r in rows]

    ratio_rank = rank(ratio_gaps)
    l5_rank = rank(l5_gaps)
    for i, r in enumerate(rows):
        r["ratio_rank"] = ratio_rank[i]
        r["l5_rank"] = l5_rank[i]
        r["combined_rank"] = ratio_rank[i] + l5_rank[i]

    # percentile thresholds
    out = {"n": n, "joint_cells": []}
    ratio_pctiles = [100, 200, 500, 1000]  # top k closest
    l5_tols = [5, 10, 50, 100]

    for top_k in ratio_pctiles:
        if top_k > n:
            continue
        ratio_set = {i for i, r in enumerate(ratio_rank) if ratio_rank[i] < top_k}
        p_ratio = top_k / n
        for tol in l5_tols:
            l5_set = {i for i, r in enumerate(rows) if rows[i]["left5_gap"] <= tol}
            p_l5 = len(l5_set) / n
            joint = ratio_set & l5_set
            obs = len(joint)
            exp = p_ratio * p_l5 * n
            ratio_enrich = (obs / exp) if exp else 0
            out["joint_cells"].append(
                {
                    "top_ratio_k": top_k,
                    "left5_tol": tol,
                    "obs_joint": obs,
                    "exp_independent": exp,
                    "enrichment": ratio_enrich,
                    "p_ratio": p_ratio,
                    "p_left5": p_l5,
                }
            )

    # sorted by combined rank
    by_combined = sorted(rows, key=lambda r: (r["combined_rank"], r["ratio_gap"], r["left5_gap"]))
    out["top20_combined"] = [
        {
            "offset": r["offset"],
            "ratio_gap": r["ratio_gap"],
            "left5_gap": r["left5_gap"],
            "left5": r["left5"],
            "ratio": r["ratio"],
            "ratio_p160": r["ratio_p160"],
            "combined_rank": r["combined_rank"],
        }
        for r in by_combined[:20]
    ]
    return out


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=10_000)
    args = ap.parse_args()

    h_p160 = p160_hash160()
    print(f"P160 H = {h_p160}")
    print(f"P160 left5 = {P160_LEFT5}")
    print(f"Building {args.n} band rows...", flush=True)

    rows = build_rows(args.n, h_p160)
    stats = joint_enrichment(rows)

    print()
    print("=== RATIO GAP |(h/d)-(H_P160/d)| — top 15 closest ===")
    by_ratio = sorted(rows, key=lambda r: r["ratio_gap"])[:15]
    for r in by_ratio:
        print(
            f"  off={r['offset']:5d}  ratio_gap={r['ratio_gap']:.6e}  "
            f"h/d={r['ratio']:.6f}  H_P160/d={r['ratio_p160']:.6f}  "
            f"left5={r['left5']} dist={r['left5_gap']}"
        )

    print()
    print("=== JOINT: close ratio (top-k) AND close left5 (tol) ===")
    print(f"{'top_k':>6} {'l5_tol':>6} {'obs':>5} {'exp':>8} {'enrich':>8}")
    for cell in stats["joint_cells"]:
        print(
            f"{cell['top_ratio_k']:6d} {cell['left5_tol']:6d} "
            f"{cell['obs_joint']:5d} {cell['exp_independent']:8.2f} {cell['enrichment']:8.2f}x"
        )

    print()
    print("=== TOP 20 by combined rank (ratio_rank + left5_rank) ===")
    for r in stats["top20_combined"]:
        print(
            f"  off={r['offset']:5d}  ratio_gap={r['ratio_gap']:.4e}  "
            f"left5={r['left5']} l5_gap={r['left5_gap']}  "
            f"combined_rank={r['combined_rank']}"
        )

    # highlight offset 517
    r517 = next(r for r in rows if r["offset"] == 517)
    print()
    print("=== offset 517 (prior left5 exact hit) ===")
    print(
        f"  ratio_rank={r517['ratio_rank']} / {args.n}  "
        f"l5_rank={r517['l5_rank']}  combined_rank={r517['combined_rank']}"
    )
    print(f"  ratio_gap={r517['ratio_gap']:.6e}  left5={r517['left5']}")

    # ruling
    enrich_100_50 = next(
        (c for c in stats["joint_cells"] if c["top_ratio_k"] == 100 and c["left5_tol"] == 50),
        None,
    )
    print()
    if enrich_100_50 and enrich_100_50["enrichment"] > 1.5:
        print("RULING: joint enrichment > 1.5x — combined filter may beat independence")
    elif enrich_100_50 and enrich_100_50["enrichment"] > 1.1:
        print("RULING: weak joint enrichment (~1.1-1.5x) — marginal, not a compass")
    else:
        print("RULING: joint enrichment ~1x — ratio + left5 independent; no combined compass")

    out = ROOT / "ARCHIVE" / "p160_band_ratio_left5_joint.json"
    out.write_text(
        json.dumps(
            {
                "p160_hash160": str(h_p160),
                "p160_left5": P160_LEFT5,
                "n": args.n,
                "joint_cells": stats["joint_cells"],
                "top20_combined": stats["top20_combined"],
                "offset_517": {
                    k: r517[k]
                    for k in (
                        "offset",
                        "ratio_gap",
                        "left5",
                        "left5_gap",
                        "ratio_rank",
                        "l5_rank",
                        "combined_rank",
                    )
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
