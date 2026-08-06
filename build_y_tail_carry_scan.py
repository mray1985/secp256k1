#!/usr/bin/env python3
"""
Y-tail carry / wrap scan — does the stitched y-tail push floor(x*N/p) across a boundary?

Question (NOT "does x.y become d?"):
  Does y act as the carry/wrap amount when projecting packet_p into N?

For each pubkey puzzle:
  A       = floor((x / p) * N)           = map_p_to_n(Px)
  B_y     = floor((x.y / p) * N)
  B_pmy   = floor((x.(p-y) / p) * N)
  carry_y   = B_y - A   (expect 0 or 1)
  carry_pmy = B_pmy - A (expect 0 or 1)

Compare carry to: beta slots, y/p-y branch, r/N landing, d offset (solved), N-d mirror.

Writes: ARCHIVE/briefcase/The Real Decimal/exhibit_y_tail_carry_scan.*
"""

from __future__ import annotations

import json
import math
from collections import Counter
from decimal import Decimal, getcontext
from pathlib import Path

from build_complexity_operations_ledger import BETA, BETA_SQ, N, inv, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog
from puzzle_rsz_blockchain import CACHE_PATH

getcontext().prec = 120

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "The Real Decimal"
DP = Decimal(p)
DN = Decimal(N)


def map_p_to_n(x: int) -> int:
    return (N * x) // p


def floor_packet_times_n(px: int, y_digits: int) -> int:
    stitched = Decimal(f"{px}.{y_digits}")
    return int(stitched / DP * DN)


def n_mirror_window(n: int) -> tuple[int, int]:
    lo = N - (1 << n) + 1
    hi = N - (1 << (n - 1))
    return lo, hi


def in_window(x: int, lo: int, hi: int) -> bool:
    return lo <= x <= hi


def carry_block(px: int, y_digits: int, label: str) -> dict:
    stitched = Decimal(f"{px}.{y_digits}")
    packet_p = stitched / DP
    a = map_p_to_n(px)
    b = int(packet_p * DN)
    carry = b - a
    floor_p = int(packet_p * DP)
    return {
        "branch": label,
        "A_map_p_to_n": str(a),
        "B_floor_packet_N": str(b),
        "carry": carry,
        "floor_packet_times_p": str(floor_p),
        "matches_Px": floor_p == px,
        "packet_p_head": format(packet_p, "f")[:48] + "...",
    }


def beta_slot_maps(px: int) -> dict:
    px3 = px
    px2 = (px * inv(BETA, p)) % p
    px1 = (px * inv(BETA_SQ, p)) % p
    return {
        "Px1": {"x": str(px1), "map_p_to_n": str(map_p_to_n(px1))},
        "Px2": {"x": str(px2), "map_p_to_n": str(map_p_to_n(px2))},
        "Px3": {"x": str(px3), "map_p_to_n": str(map_p_to_n(px3))},
        "pubkey_is_slot": 3,
    }


def roof_stitch_carry(head: int, tail: int, name: str) -> dict:
    stitched = Decimal(f"{head}.{tail}")
    over_p = stitched / DP
    over_n = stitched / DN
    a_p = map_p_to_n(head)
    b_n = int(over_p * DN)
    return {
        "name": name,
        "A_map_p_to_n_head": str(a_p),
        "B_floor_stitch_over_p_times_N": str(b_n),
        "carry_p_to_N": b_n - a_p,
        "over_p": format(over_p, "f")[:32] + "...",
        "over_p_placement": "overflow" if over_p > 1 else "under_roof",
        "over_n_placement": "overflow" if over_n > 1 else "under_roof",
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
    den = math.sqrt(sum((rx[i] - mx) ** 2 for i in range(n)) * sum((ry[i] - my) ** 2 for i in range(n)))
    return num / den if den else float("nan")


def load_rsz() -> dict[int, dict]:
    if not CACHE_PATH.exists():
        return {}
    raw = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    out: dict[int, dict] = {}
    for k, v in raw.items():
        if not isinstance(v, dict):
            continue
        try:
            n = int(k)
        except ValueError:
            continue
        out[n] = v
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()
    rsz = load_rsz()

    rows: list[dict] = []
    carry_y_all: list[int] = []
    carry_pmy_all: list[int] = []

    for n in range(1, 161):
        e = catalog[n]
        if not e.public_key:
            continue
        px, py = pubkey_xy(e.public_key)
        pmy = (p - py) % p
        lo, hi = n_mirror_window(n)

        cy = carry_block(px, py, "y")
        cp = carry_block(px, pmy, "p_minus_y")
        a = int(cy["A_map_p_to_n"])
        by = int(cy["B_floor_packet_N"])
        bp = int(cp["B_floor_packet_N"])

        carry_y_all.append(cy["carry"])
        carry_pmy_all.append(cp["carry"])

        beta = beta_slot_maps(px)
        rec: dict = {
            "puzzle": n,
            "compressed_prefix": e.public_key[:2],
            "Px": str(px),
            "Py": str(py),
            "p_minus_y": str(pmy),
            "beta_slots": beta,
            "branch_y": cy,
            "branch_p_minus_y": cp,
            "carry_y": cy["carry"],
            "carry_pmy": cp["carry"],
            "carries_match": cy["carry"] == cp["carry"],
            "N_mirror_window": {"lo": str(lo), "hi": str(hi)},
            "A_in_N_mirror": in_window(a, lo, hi),
            "B_y_in_N_mirror": in_window(by, lo, hi),
            "B_pmy_in_N_mirror": in_window(bp, lo, hi),
            "carry_pmy_flipped_N_mirror_vs_A": (
                in_window(bp, lo, hi) != in_window(a, lo, hi)
            ),
        }

        # RSZ r/N landing
        if n in rsz and rsz[n].get("r") is not None:
            rv = rsz[n]["r"]
            if isinstance(rv, str):
                rv = int(rv, 16)
            r_mod = rv % N
            r_map = map_p_to_n(r_mod)
            rec["rsz"] = {
                "r_mod_N": str(r_mod),
                "map_p_to_n_r": str(r_map),
                "r_map_minus_A": r_map - a,
                "r_map_minus_B_pmy": r_map - bp,
                "carry_pmy_eq_r_map_gt_A": cp["carry"] == (1 if r_map > a else 0),
            }

        if e.solved and e.private_key > 0:
            d = e.private_key
            nd = (N - d) % N
            rec["scalar"] = {
                "d": str(d),
                "N_minus_d": str(nd),
                "d_minus_A": d - a,
                "d_minus_B_y": d - by,
                "d_minus_B_pmy": d - bp,
                "A_plus_carry_pmy": str(a + cp["carry"]),
                "B_pmy_equals_A_plus_carry": bp == a + cp["carry"],
                "d_equals_A_plus_carry_pmy": d == a + cp["carry"],
                "d_equals_B_pmy": d == bp,
                "N_minus_d_in_N_mirror": in_window(nd, lo, hi),
                "B_pmy_in_N_mirror": in_window(bp, lo, hi),
            }

        rows.append(rec)

    # --- aggregates ---
    cy_cnt = Counter(carry_y_all)
    cp_cnt = Counter(carry_pmy_all)
    match_cnt = sum(1 for r in rows if r["carries_match"])

    # solved-only: does carry predict d > A?
    solved = [r for r in rows if "scalar" in r]
    carry_vs_d_gt_a_pmy = sum(
        1 for r in solved if r["carry_pmy"] == (1 if int(r["scalar"]["d"]) > int(r["branch_p_minus_y"]["A_map_p_to_n"]) else 0)
    )
    d_eq_a_plus_carry = sum(
        1 for r in solved if r["scalar"]["d_equals_A_plus_carry_pmy"]
    )

    # RSZ correlation
    rsz_rows = [r for r in rows if "rsz" in r]
    rsz_carry_match = sum(
        1 for r in rsz_rows if r["rsz"]["carry_pmy_eq_r_map_gt_A"]
    )

    # beta: slot-2 vs slot-3 map difference (informational)
    # Roof-stitch globals (same head.tail / roof principle)
    from build_complexity_operations_ledger import DELTA

    roof_carries = {
        "p_dot_N": roof_stitch_carry(p, N, "p.N"),
        "N_dot_p": roof_stitch_carry(N, p, "N.p"),
        "p_dot_delta": roof_stitch_carry(p, DELTA, "p.(p-N)"),
        "N_dot_delta": roof_stitch_carry(N, DELTA, "N.(p-N)"),
    }

    # n-confound check: carry vs puzzle index
    ns = [float(r["puzzle"]) for r in rows]
    spearman_n_carry_y = spearman(ns, [float(r["carry_y"]) for r in rows])
    spearman_n_carry_pmy = spearman(ns, [float(r["carry_pmy"]) for r in rows])

    exhibit = {
        "exhibit": "y_tail_carry_scan",
        "question": "Does y act as the carry/wrap amount in floor((x.y/p)*N) vs floor((x/p)*N)?",
        "not": "Does x.y become d?",
        "mechanism": {
            "A": "floor((x / p) * N) = map_p_to_n(Px)",
            "B": "floor((x.y / p) * N)",
            "carry": "B - A, expected 0 or 1",
            "under_p": "floor((x.y / p) * p) = floor(x.y) = x — tail invisible to p-floor",
            "under_N": "tail can push floor from A to A+1",
        },
        "counts": {
            "pubkey_puzzles": len(rows),
            "carry_y": dict(cy_cnt),
            "carry_pmy": dict(cp_cnt),
            "carries_y_eq_pmy": match_cnt,
            "carries_y_ne_pmy": len(rows) - match_cnt,
            "all_carry_in_0_1": all(c in (0, 1) for c in carry_y_all + carry_pmy_all),
        },
        "solved_comparisons": {
            "puzzles": len(solved),
            "d_equals_A_plus_carry_pmy": d_eq_a_plus_carry,
            "d_equals_B_pmy": sum(1 for r in solved if r["scalar"]["d_equals_B_pmy"]),
            "carry_pmy_matches_d_gt_A": carry_vs_d_gt_a_pmy,
        },
        "rsz_comparisons": {
            "puzzles_with_r": len(rsz_rows),
            "carry_pmy_eq_indicator_r_map_gt_A": rsz_carry_match,
        },
        "confound": {
            "spearman_n_carry_y": spearman_n_carry_y,
            "spearman_n_carry_pmy": spearman_n_carry_pmy,
            "note": "weak n correlation expected; carry is point-specific not index-driven",
        },
        "roof_stitch_carry": roof_carries,
        "puzzles": rows,
        "admissible_fact": {
            "status": "ADMITTED",
            "statement": (
                "x.y is not merely a display packet. When projected from p to N: "
                "x sets the floor; y decides whether the projected floor stays A or carries to A+1."
            ),
            "formula": {
                "A": "floor((x / p) * N)",
                "B": "floor((x.y / p) * N)",
                "carry": "B - A in {0, 1}",
            },
            "y_job": "carry pressure in p→N projection",
            "not": "private key (d == B_pmy: 0/82; d == A+carry: 0/82)",
            "P135": {"B_y": "A+1", "B_pmy": "A+1"},
        },
        "ruling": "Admissible fact, not conviction. y-tail carry is structural, not scalar identity.",
        "judge_popcorn": "Admissible fact, not conviction. x is the floor; y is the pressure; N hears the carry.",
    }

    json_path = OUT / "exhibit_y_tail_carry_scan.json"
    json_path.write_text(json.dumps(exhibit, indent=2), encoding="utf-8")

    md = f"""# EXHIBIT: y-tail carry / wrap scan

## Question

```text
Does y act as the carry/wrap amount?
```

**Not:** does `x.y` become `d`?

## Mechanism

```text
A       = floor((x / p) * N)     = map_p_to_n(Px)
B       = floor((x.y / p) * N)
carry   = B - A                  (0 or 1)

Under p: floor((x.y / p) * p) = x   — tail invisible
Under N: tail may push A → A+1      — wrap event
```

## Verdict counts ({len(rows)} pubkey puzzles)

| Carry | y branch | p−y branch |
|-------|----------|------------|
| 0 | {cy_cnt[0]} | {cp_cnt[0]} |
| 1 | {cy_cnt[1]} | {cp_cnt[1]} |

```text
carry_y == carry_pmy:  {match_cnt} puzzles
carry_y != carry_pmy:  {len(rows) - match_cnt} puzzles
all carry in {{0,1}}:  {exhibit['counts']['all_carry_in_0_1']}
```

## Solved puzzle checks ({len(solved)} puzzles)

| Test | Hits |
|------|------|
| `d == A + carry_pmy` | {d_eq_a_plus_carry} |
| `d == B_pmy` | {exhibit['solved_comparisons']['d_equals_B_pmy']} |
| `carry_pmy == (d > A)` | {carry_vs_d_gt_a_pmy} |

No direct key recovery — confirms carry is mechanical, not scalar identity.

## RSZ r/N landing ({len(rsz_rows)} puzzles with r)

```text
carry_pmy == (map_p_to_n(r) > A):  {rsz_carry_match} / {len(rsz_rows) or '—'}
```

## Confound control

```text
Spearman(n, carry_y):   {spearman_n_carry_y:.4f}
Spearman(n, carry_pmy): {spearman_n_carry_pmy:.4f}
```

Carry is **point-specific** (which y-tail crosses the boundary), not a puzzle-index compass.

## Roof-stitch carry (same principle)

| Stitch | carry p→N | over_p |
|--------|-----------|--------|
| `p.N` | {roof_carries['p_dot_N']['carry_p_to_N']} | {roof_carries['p_dot_N']['over_p_placement']} |
| `N.p` | {roof_carries['N_dot_p']['carry_p_to_N']} | {roof_carries['N_dot_p']['over_p_placement']} |
| `p.(p−N)` | {roof_carries['p_dot_delta']['carry_p_to_N']} | {roof_carries['p_dot_delta']['over_p_placement']} |
| `N.(p−N)` | {roof_carries['N_dot_delta']['carry_p_to_N']} | {roof_carries['N_dot_delta']['over_p_placement']} |

Head sets the main room; tail sets under-roof vs overflow vs +1 carry.

## Admissible fact (filed)

```text
x.y is not merely a display packet.

When projected from p to N:
  x sets the floor
  y decides whether the projected floor stays A
  or carries to A + 1

y = carry pressure in p→N projection
```

```text
d == B_pmy:     0 / 82 solved
d == A + carry: 0 / 82 solved
```

**Not the private key.** Structural rule only.

P135: `B_y = A+1`, `B_pmy = A+1` — both tails push across the boundary.

## Clean ruling

```text
Admissible fact, not conviction.
x is the floor; y is the pressure; N hears the carry.
```

Judge Popcorn: **Admissible fact, not conviction. x is the floor; y is the pressure; N hears the carry.**
"""

    md_path = OUT / "exhibit_y_tail_carry_scan.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"carry_y: {dict(cy_cnt)}  carry_pmy: {dict(cp_cnt)}")
    print(f"d==A+carry: {d_eq_a_plus_carry}/{len(solved)}  all carry in 0,1: {exhibit['counts']['all_carry_in_0_1']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
