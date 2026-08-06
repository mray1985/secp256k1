#!/usr/bin/env python3
"""P71 scaled TDAD: 2^29 subset combinations via meet-in-the-middle."""

from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path

from ecdsa import SECP256k1, SigningKey
from puzzle_catalog import load_catalog

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ARCHIVE" / "briefcase" / "The Real Decimal" / "P71"

M = 536870912
LO = 1 << 70
HI = (1 << 71) - 1
T71_FILED = 1411488254391826260559
TARGET = bytes.fromhex("f6f5431d25bbf7b12e8add9af5e3475c44a0a5b8")


def h160(d: int) -> bytes:
    sk = SigningKey.from_secret_exponent(d % int(SECP256k1.order), curve=SECP256k1)
    pt = sk.verifying_key.pubkey.point
    x, y = pt.x(), pt.y()
    comp = (b"\x02" if y % 2 == 0 else b"\x03") + x.to_bytes(32, "big")
    return hashlib.new("ripemd160", hashlib.sha256(comp).digest()).digest()


def half_sums(pool: list[int], d: dict[int, int]) -> dict[int, list[list[int]]]:
    """mask over pool -> sum -> list of index lists (keep all for small half)."""
    contrib = [(i, M * d[i]) for i in pool]
    out: dict[int, list[list[int]]] = defaultdict(list)
    n = len(contrib)
    for mask in range(1 << n):
        s = 0
        chosen: list[int] = []
        for bit, (idx, c) in enumerate(contrib):
            if mask & (1 << bit):
                s += c
                chosen.append(idx)
        if chosen:
            out[s].append(chosen)
    return out


def combine_halves(
    left: dict[int, list[list[int]]],
    right: dict[int, list[list[int]]],
    lo: int,
    hi: int,
    cap: int = 200,
) -> list[dict]:
    hits: list[dict] = []
    right_items = sorted(right.items())
    right_sums = [rs for rs, _ in right_items]

    def rs_range(need_lo: int, need_hi: int) -> list[tuple[int, list[list[int]]]]:
        import bisect
        i0 = bisect.bisect_left(right_sums, need_lo)
        i1 = bisect.bisect_right(right_sums, need_hi)
        return right_items[i0:i1]

    for ls, lsets in left.items():
        need_lo, need_hi = lo - ls, hi - ls
        for rs, rsets in rs_range(need_lo, need_hi):
            total = ls + rs
            if lo <= total <= hi:
                hits.append({"d": str(total), "indices": lsets[0] + rsets[0]})
                if len(hits) >= cap:
                    return hits
    return hits


def combine_for_target(
    left: dict[int, list[list[int]]],
    right: dict[int, list[list[int]]],
    target_lo: int,
    target_hi: int,
) -> list[dict]:
    import bisect

    hits: list[dict] = []
    right_items = sorted(right.items())
    right_sums = [rs for rs, _ in right_items]

    for ls, lsets in left.items():
        need_lo, need_hi = target_lo - ls, target_hi - ls
        i0 = bisect.bisect_left(right_sums, need_lo)
        i1 = bisect.bisect_right(right_sums, need_hi)
        for rs, rsets in right_items[i0:i1]:
            total = ls + rs
            if target_lo <= total <= target_hi:
                rem = T71_FILED - total
                hits.append({
                    "sum": str(total),
                    "remainder": rem,
                    "d_filed": str(total + rem) if 0 <= rem < M else None,
                    "indices": lsets[0] + rsets[0],
                })
    return hits


def main() -> int:
    cat = load_catalog()
    d = {n: cat[n].private_key for n in range(1, 161) if cat[n].solved and cat[n].private_key > 0}

    pool = list(range(14, 43))  # 29 slots: P71 first ceiling 42 => n-29 .. 42
    mid = 14
    left_pool, right_pool = pool[:mid], pool[mid:]

    t0 = time.time()
    left = half_sums(left_pool, d)
    right = half_sums(right_pool, d)
    t_build = time.time() - t0

    in_band = combine_halves(left, right, LO, HI)
    filed_band = combine_for_target(left, right, T71_FILED - M + 1, T71_FILED)

    h160_hits: list[dict] = []
    checked = set()

    def gate(val: int, meta: dict) -> None:
        if val in checked or not (LO <= val <= HI):
            return
        checked.add(val)
        if h160(val) == TARGET:
            h160_hits.append({"d": str(val), **meta})

    for row in in_band:
        gate(int(row["d"]), {"indices": row["indices"], "kind": "bare_in_band"})
    for row in filed_band:
        if row.get("d_filed"):
            gate(int(row["d_filed"]), {
                "indices": row["indices"],
                "sum": row["sum"],
                "remainder": row["remainder"],
                "kind": "filed_T71_decomp",
            })

    summary = {
        "hypothesis": "2^29 combinations = subset of 29 index slots (14..42), optional remainder < 2^29",
        "pool": pool,
        "combinations": 2 ** len(pool),
        "half_sizes": [len(left_pool), len(right_pool)],
        "half_sum_counts": [len(left), len(right)],
        "build_s": round(t_build, 3),
        "in_band_samples": in_band[:20],
        "filed_T71_sum_hits": len(filed_band),
        "filed_T71_samples": filed_band[:10],
        "hash160_hits": h160_hits,
        "hash160_checked": len(checked),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "p71_2p29_combination_scan.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md = [
        "# P71 2^29 combination scan (MITM)",
        "",
        f"Pool: indices **14..42** (29 slots) → **2^29 = {2**29}** subsets",
        f"Remainder bucket: **< 2^29 = {M}**",
        "",
        f"- Half-sum build: {t_build:.2f}s",
        f"- Bare sums in `[2^70,2^71)`: sampled **{len(in_band)}** (capped)",
        f"- Subset sums where `T71_filed - sum < 2^29`: **{len(filed_band)}**",
        f"- Hash160 checked: **{len(checked)}**",
        f"- Hash160 hits: **{len(h160_hits)}**",
        "",
    ]
    if filed_band:
        md.append("## Filed T71 remainder hits (sample)")
        for row in filed_band[:5]:
            md.append(f"- sum={row['sum']} rem={row['remainder']} n_terms={len(row['indices'])}")
    (OUT / "p71_2p29_combination_scan.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(json.dumps({k: summary[k] for k in ("combinations", "filed_T71_sum_hits", "hash160_hits", "hash160_checked")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
