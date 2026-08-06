#!/usr/bin/env python3
"""
Inspect first 2000 scalars in P160 band [2^159, 2^160):
  block A: d = 2^159 .. 2^159+999
  block B: d = 2^159+1000 .. 2^159+1999

Compare to P160 pubkey hash160 anchor and test correlations with band offset.
"""

from __future__ import annotations

import hashlib
import math
import sys
from collections import defaultdict
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_catalog import load_catalog  # noqa: E402

LO160 = 1 << 159
BAND_WIDTH = 1 << 159  # half-open [LO, LO+WIDTH)
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


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else float("nan")


def spearman(xs: list[int], ys: list[int]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")

    def ranks(vals: list[int]) -> list[float]:
        order = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    return pearson(ranks(xs), ranks(ys))


def p160_hash160() -> int:
    comp = bytes.fromhex(load_catalog()[160].public_key)
    return int.from_bytes(
        hashlib.new("ripemd160", hashlib.sha256(comp).digest()).digest(), "big"
    )


def analyze_block(ds: list[int], h160_p160: int, l5_p160: int) -> dict:
    rows = []
    for d in ds:
        h = hash160_compressed(d)
        l5 = left5(h)
        off = d - LO160
        rows.append(
            {
                "d": d,
                "offset": off,
                "hash160": h,
                "left5": l5,
                "dist_l5": abs(l5 - l5_p160),
                "dist_h": abs(h - h160_p160),
            }
        )

    offsets = [r["offset"] for r in rows]
    l5s = [r["left5"] for r in rows]
    dists = [r["dist_l5"] for r in rows]

    by_l5: dict[int, list[int]] = defaultdict(list)
    for r in rows:
        by_l5[r["left5"]].append(r["offset"])

    dups = {k: sorted(v) for k, v in by_l5.items() if len(v) > 1}
    spreads = []
    for ds_off in dups.values():
        for i in range(len(ds_off) - 1):
            spreads.append(ds_off[i + 1] - ds_off[i])

    near = {t: sum(1 for r in rows if r["dist_l5"] <= t) for t in (5, 10, 50, 100)}

    return {
        "rows": rows,
        "unique_l5": len(by_l5),
        "dup_prefixes": len(dups),
        "spreads": spreads,
        "near": near,
        "l5_min": min(l5s),
        "l5_max": max(l5s),
        "corr_offset_left5": pearson([float(o) for o in offsets], [float(l) for l in l5s]),
        "spearman_offset_left5": spearman(offsets, l5s),
        "corr_offset_dist_l5": pearson([float(o) for o in offsets], [float(d) for d in dists]),
        "spearman_offset_dist_l5": spearman(offsets, dists),
        "exact_p160_left5": [r for r in rows if r["left5"] == l5_p160],
        "exact_p160_hash160": [r for r in rows if r["hash160"] == h160_p160],
        "nearest5": sorted(rows, key=lambda r: (r["dist_l5"], r["offset"]))[:5],
    }


def expected_near(n: int, tol: int) -> float:
    return n * (2 * tol + 1) / LEFT5_SPACE


def main() -> None:
    h160_p160 = p160_hash160()
    l5_p160 = left5(h160_p160)
    print("P160 band LO = 2^159 =", LO160)
    print("P160 hash160  =", h160_p160)
    print("P160 left5    =", l5_p160)
    print()

    block_a = [LO160 + i for i in range(1000)]
    block_b = [LO160 + 1000 + i for i in range(1000)]

    print("Computing block A (first 1000 in band)...", flush=True)
    ra = analyze_block(block_a, h160_p160, l5_p160)
    print("Computing block B (next 1000 in band)...", flush=True)
    rb = analyze_block(block_b, h160_p160, l5_p160)

    for name, r in [("A first 1k", ra), ("B next 1k", rb)]:
        print(f"=== BLOCK {name} (offsets {r['rows'][0]['offset']}..{r['rows'][-1]['offset']}) ===")
        print(f"  unique left5: {r['unique_l5']} / 1000")
        print(f"  duplicate left5 prefixes: {r['dup_prefixes']}")
        if r["spreads"]:
            print(
                f"  dup offset spreads: min/mean/max = "
                f"{min(r['spreads'])}/{sum(r['spreads'])/len(r['spreads']):.1f}/{max(r['spreads'])}"
            )
        print(f"  left5 range: {r['l5_min']} .. {r['l5_max']}")
        for t in (5, 10, 50, 100):
            obs = r["near"][t]
            exp = expected_near(1000, t)
            print(f"  near P160 left5 tol<={t:3d}: obs={obs:3d} exp={exp:.2f} ratio={obs/exp:.2f}x")
        print(f"  Pearson(offset, left5):  {r['corr_offset_left5']:.6f}")
        print(f"  Spearman(offset, left5): {r['spearman_offset_left5']:.6f}")
        print(f"  Pearson(offset, |left5-13260|):  {r['corr_offset_dist_l5']:.6f}")
        print(f"  Spearman(offset, |left5-13260|): {r['spearman_offset_dist_l5']:.6f}")
        print(f"  exact left5==13260: {len(r['exact_p160_left5'])}")
        print(f"  exact hash160==P160: {len(r['exact_p160_hash160'])}")
        print("  nearest 5 to P160 left5:")
        for row in r["nearest5"]:
            print(
                f"    offset={row['offset']:4d} d=...{str(row['d'])[-8:]}  "
                f"left5={row['left5']} dist={row['dist_l5']}"
            )
        print()

    # cross-block same left5
    set_a = {r["left5"] for r in ra["rows"]}
    set_b = {r["left5"] for r in rb["rows"]}
    cross = sorted(set_a & set_b)
    print(f"Cross-block same left5 (A cap B): {len(cross)}")
    for p in cross[:15]:
        oa = [r["offset"] for r in ra["rows"] if r["left5"] == p]
        ob = [r["offset"] for r in rb["rows"] if r["left5"] == p]
        print(f"  {p}  A_offsets={oa}  B_offsets={ob}")

    # combined 2000 vs small-d baseline
    print()
    print("=== COMBINED 2000 @ 2^159 vs small-d baseline (from prior test) ===")
    comb = ra["rows"] + rb["rows"]
    for t in (5, 10, 50, 100):
        obs = sum(1 for r in comb if r["dist_l5"] <= t)
        exp = expected_near(2000, t)
        print(f"  tol<={t:3d}: obs={obs:3d} exp={exp:.2f} ratio={obs/exp:.2f}x")

    # linear trend: does dist to 13260 shrink as offset grows?
    all_off = [r["offset"] for r in comb]
    all_dist = [r["dist_l5"] for r in comb]
    print()
    print("=== TREND: band offset vs distance to P160 left5 (2000 points) ===")
    print(f"  Pearson:  {pearson([float(x) for x in all_off], [float(x) for x in all_dist]):.6f}")
    print(f"  Spearman: {spearman(all_off, all_dist):.6f}")
    first500 = [r for r in comb if r["offset"] < 500]
    last500 = [r for r in comb if r["offset"] >= 1500]
    m1 = sum(r["dist_l5"] for r in first500) / len(first500)
    m2 = sum(r["dist_l5"] for r in last500) / len(last500)
    print(f"  mean dist_l5 offsets 0-499:   {m1:.2f}")
    print(f"  mean dist_l5 offsets 1500-1999: {m2:.2f}")

    # write sample
    out = ROOT / "ARCHIVE" / "p160_band_first2000_left5.txt"
    with out.open("w", encoding="utf-8") as f:
        f.write("# offset_in_band\td\tleft5\thash160_decimal\tdist_l5_P160\n")
        for r in comb:
            f.write(f"{r['offset']}\t{r['d']}\t{r['left5']}\t{r['hash160']}\t{r['dist_l5']}\n")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
