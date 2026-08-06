#!/usr/bin/env python3
"""
Carry threshold ledger — exact integer formula + beta-slot ladder + ledger wrap.

Admitted fact (from y_tail_carry_scan):
  carry = floor((x.y/p)*N) - floor((x/p)*N)  in {0, 1}

Exact threshold (integer, no Decimal):
  rem = (N * x) % p
  carry = 1  iff  rem * 10^d + N * y >= p * 10^d
  carry = 0  otherwise

  margin = p * 10^d - (rem * 10^d + N * y)   # >0 no carry, <=0 carry

Wraps:
  - all pubkey puzzles: beta-slot carry ladder
  - branch differential (carry_y != carry_pmy)
  - ledger objects x puzzle y-tail
  - RSZ r carry with stitched tails (when available)

Writes: ARCHIVE/briefcase/The Real Decimal/exhibit_carry_threshold_ledger.*
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from decimal import Decimal, getcontext
from pathlib import Path

from build_complexity_operations_ledger import (
    BETA,
    BETA_SQ,
    DELTA,
    Gx,
    LAMBDA,
    LAMBDA1,
    N,
    Px as P135_PX_SLOTS,
    inv,
    p,
    rx,
)
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog
from puzzle_rsz_blockchain import CACHE_PATH

getcontext().prec = 120

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "The Real Decimal"


def carry_int(x: int, y: int) -> int:
    d = len(str(y))
    scale = 10**d
    a = (N * x) // p
    b = (N * (x * scale + y)) // (p * scale)
    return b - a


def carry_threshold(x: int, y: int) -> dict:
    d = len(str(y))
    scale = 10**d
    rem = (N * x) % p
    lhs = rem * scale + N * y
    rhs = p * scale
    margin = rhs - lhs
    c = 1 if lhs >= rhs else 0
    return {
        "rem_Nx_mod_p": str(rem),
        "lhs": str(lhs),
        "rhs": str(rhs),
        "margin": str(margin),
        "carry": c,
        "threshold": "carry=1 iff (N*x mod p)*10^d + N*y >= p*10^d",
    }


def carry_decimal(x: int, y: int) -> int:
    stitched = Decimal(f"{x}.{y}")
    a = (N * x) // p
    b = int(stitched / Decimal(p) * Decimal(N))
    return b - a


def beta_slots(px: int) -> dict[int, int]:
    return {
        1: (px * inv(BETA_SQ, p)) % p,
        2: (px * inv(BETA, p)) % p,
        3: px,
    }


def ledger_objects() -> dict[str, int]:
    objs: dict[str, int] = {
        "BETA": BETA,
        "BETA_SQ": BETA_SQ,
        "LAMBDA": LAMBDA,
        "LAMBDA1": LAMBDA1,
        "DELTA": DELTA,
        "p": p,
        "N": N % p,
    }
    for i, v in enumerate(Gx, 1):
        objs[f"Gx_slot_{i}"] = v
    for i, v in enumerate(P135_PX_SLOTS, 1):
        objs[f"P135_Px_slot_{i}"] = v
    for i, v in enumerate(rx, 1):
        objs[f"P135_rx_slot_{i}"] = v % p
    return objs


def load_rsz() -> dict[int, dict]:
    if not CACHE_PATH.exists():
        return {}
    raw = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    out: dict[int, dict] = {}
    for k, v in raw.items():
        if isinstance(v, dict):
            try:
                out[int(k)] = v
            except ValueError:
                pass
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()
    rsz = load_rsz()
    ledger = ledger_objects()

    # --- verify threshold formula ---
    verify_mismatch = []
    threshold_mismatch = []
    rows: list[dict] = []

    for n in range(1, 161):
        e = catalog[n]
        if not e.public_key:
            continue
        px, py = pubkey_xy(e.public_key)
        pmy = (p - py) % p

        for label, yd in (("y", py), ("p_minus_y", pmy)):
            if carry_int(px, yd) != carry_decimal(px, yd):
                verify_mismatch.append((n, label))
            th = carry_threshold(px, yd)
            if th["carry"] != carry_int(px, yd):
                threshold_mismatch.append((n, label))

        slots = beta_slots(px)
        slot_carries = {}
        for si, sx in slots.items():
            slot_carries[f"slot_{si}"] = {
                "x": str(sx),
                "carry_y": carry_int(sx, py),
                "carry_pmy": carry_int(sx, pmy),
                "threshold_pmy": carry_threshold(sx, pmy),
            }

        rec = {
            "puzzle": n,
            "Px": str(px),
            "carry_y": carry_int(px, py),
            "carry_pmy": carry_int(px, pmy),
            "carries_match": carry_int(px, py) == carry_int(px, pmy),
            "threshold_y": carry_threshold(px, py),
            "threshold_pmy": carry_threshold(px, pmy),
            "beta_slot_ladder": slot_carries,
            "all_slots_same_carry_pmy": len({carry_int(sx, pmy) for sx in slots.values()}) == 1,
        }

        # branch differential detail
        if not rec["carries_match"]:
            rec["branch_differential"] = {
                "pattern": f"y={rec['carry_y']}, pmy={rec['carry_pmy']}",
                "y_margin": rec["threshold_y"]["margin"],
                "pmy_margin": rec["threshold_pmy"]["margin"],
                "winner": "y" if rec["carry_y"] == 1 else "p_minus_y",
            }

        # RSZ r stitched with puzzle tails (N-scale witness, not EC x)
        if n in rsz and rsz[n].get("r") is not None:
            rv = rsz[n]["r"]
            if isinstance(rv, str):
                rv = int(rv, 16)
            r_mod = rv % N
            rec["rsz_r_carry"] = {
                "r_mod_N": str(r_mod),
                "carry_y": carry_int(r_mod, py),
                "carry_pmy": carry_int(r_mod, pmy),
                "matches_Px_carry_pmy": carry_int(r_mod, pmy) == rec["carry_pmy"],
            }

        rows.append(rec)

    # --- ledger wrap: each ledger object x each puzzle p-y tail ---
    ledger_wrap_hits: Counter[str] = Counter()
    ledger_wrap_rows: list[dict] = []
    for name, v in ledger.items():
        wrap_carries = Counter()
        for r in rows:
            n = r["puzzle"]
            e = catalog[n]
            _, py = pubkey_xy(e.public_key)
            pmy = (p - py) % p
            c = carry_int(v % p, pmy)
            wrap_carries[c] += 1
            if c == r["carry_pmy"]:
                ledger_wrap_hits[name] += 1
        ledger_wrap_rows.append({
            "object": name,
            "value_head": str(v % p),
            "carry_pmy_distribution": dict(wrap_carries),
            "matches_puzzle_carry_pmy": ledger_wrap_hits[name],
        })

    # --- aggregates ---
    diff_rows = [r for r in rows if not r["carries_match"]]
    diff_patterns = Counter(
        (r["carry_y"], r["carry_pmy"]) for r in diff_rows
    )
    slot_same = sum(1 for r in rows if r["all_slots_same_carry_pmy"])
    rsz_match = sum(
        1 for r in rows
        if r.get("rsz_r_carry", {}).get("matches_Px_carry_pmy")
    )
    rsz_total = sum(1 for r in rows if "rsz_r_carry" in r)

    exhibit = {
        "exhibit": "carry_threshold_ledger",
        "builds_on": "exhibit_y_tail_carry_scan (admissible fact)",
        "exact_formula": {
            "rem": "(N * x) % p",
            "carry": "1 if rem * 10^d + N * y >= p * 10^d else 0",
            "margin": "p * 10^d - (rem * 10^d + N * y)",
            "y_job": "N*y term is the carry pressure added to field remainder",
        },
        "verification": {
            "int_vs_decimal_mismatch": len(verify_mismatch),
            "threshold_vs_int_mismatch": len(threshold_mismatch),
            "all_ok": len(verify_mismatch) == 0 and len(threshold_mismatch) == 0,
        },
        "aggregates": {
            "pubkey_puzzles": len(rows),
            "branch_differential_count": len(diff_rows),
            "branch_differential_patterns": {f"y={a},pmy={b}": c for (a, b), c in diff_patterns.items()},
            "beta_all_slots_same_carry_pmy": slot_same,
            "beta_slots_differ": len(rows) - slot_same,
            "rsz_r_carry_matches_Px_carry_pmy": rsz_match,
            "rsz_r_total": rsz_total,
        },
        "ledger_wrap": {
            "objects": len(ledger_wrap_rows),
            "rows": ledger_wrap_rows,
            "best_match": max(ledger_wrap_rows, key=lambda x: x["matches_puzzle_carry_pmy"]),
            "note": "ledger head stitched with each puzzle p-y tail; checks carry agreement",
        },
        "puzzles": rows,
        "ruling": (
            "Carry threshold is exact integer law. y enters as N*y in the boundary test. "
            "Beta slots and ledger objects inherit the same rule but carry is point-specific."
        ),
        "judge_popcorn": (
            "The pressure has a formula now: rem*10^d + N*y vs p*10^d. "
            "Cross the line, N hears +1."
        ),
    }

    json_path = OUT / "exhibit_carry_threshold_ledger.json"
    json_path.write_text(json.dumps(exhibit, indent=2), encoding="utf-8")

    best = exhibit["ledger_wrap"]["best_match"]
    md = f"""# EXHIBIT: carry threshold ledger

Builds on **y-tail carry** (admissible fact).

## Exact formula

```text
rem   = (N * x) % p
d     = decimal digits of y

carry = 1  iff  rem * 10^d + N * y  >=  p * 10^d
carry = 0  otherwise

margin = p * 10^d - (rem * 10^d + N * y)
         > 0  no carry
         <= 0 carry event
```

`N * y` is the **carry pressure term**. `rem` is the field residue before the tail pushes.

## Verification

```text
int vs Decimal mismatch:     {len(verify_mismatch)}
threshold vs int mismatch:   {len(threshold_mismatch)}
all_ok:                      {exhibit['verification']['all_ok']}
```

## Branch differential ({len(diff_rows)} puzzles)

When `carry_y != carry_pmy`, one tail crosses the threshold and one does not:

```text
y=1, pmy=0: {diff_patterns.get((1, 0), 0)} puzzles
y=0, pmy=1: {diff_patterns.get((0, 1), 0)} puzzles
```

These are the puzzles where **y vs p−y pick different sides of the floorboard**.

## Beta-slot ladder

```text
all three slots same carry (p−y):  {slot_same} / {len(rows)}
slots differ:                    {len(rows) - slot_same} / {len(rows)}
```

β-rotation changes `rem`; same y-tail can flip carry at different slots.

## Ledger wrap ({len(ledger)} objects × {len(rows)} puzzles)

Each ledger integer head stitched with each puzzle's `p−y` tail.

Best carry agreement with puzzle `carry_pmy`:

```text
{best['object']}: {best['matches_puzzle_carry_pmy']} / {len(rows)} matches
```

No universal ledger carry mask — agreement is object-specific and weak.

## RSZ r carry ({rsz_total} puzzles)

```text
r stitched carry_pmy == Px carry_pmy:  {rsz_match} / {rsz_total}
```

## Clean ruling

```text
Carry is an exact integer threshold law.
y is not ornament — it is the N*y term in rem*10^d + N*y >= p*10^d.
Still not d. Still admissible structure.
```

Judge Popcorn: **The pressure has a formula now: rem*10^d + N*y vs p*10^d. Cross the line, N hears +1.**
"""

    md_path = OUT / "exhibit_carry_threshold_ledger.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"verify ok: {exhibit['verification']['all_ok']}")
    print(f"branch diff: {len(diff_rows)}  slot same: {slot_same}/{len(rows)}")
    print(f"best ledger match: {best['object']} {best['matches_puzzle_carry_pmy']}/{len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
