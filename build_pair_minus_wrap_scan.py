#!/usr/bin/env python3
"""
Pair-minus-wrap scan — residue lane under shared p^2 roof.

  P_pair  = (x*p + y) / p^2
  wrap    = m / p^2       where m = (x^3 + 7 - y^2) // p
  residue = P_pair - wrap = (x*p + y - m) / p^2

Compare residue against beta-slot residues, RSZ r/s/z over N,
N/p, DELTA normalized, solved d/N and (N-d)/N.

Writes: ARCHIVE/briefcase/The Real Decimal/exhibit_pair_minus_wrap_scan.*
"""

from __future__ import annotations

import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

from build_complexity_operations_ledger import BETA, BETA_SQ, DELTA, N, inv, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog
from puzzle_rsz_blockchain import CACHE_PATH

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "The Real Decimal"
P2 = p * p


def pair_minus_wrap(px: int, y_limb: int) -> dict:
    m = (px**3 + 7 - y_limb**2) // p
    num = px * p + y_limb - m
    U = Fraction(px, p)
    W = Fraction(y_limb, P2)
    P_pair = U + W
    wrap = Fraction(m, P2)
    residue = Fraction(num, P2)
    assert residue == P_pair - wrap
    return {
        "U_x_over_p": str(float(U)),
        "W_y_over_p2": str(float(W)),
        "P_pair": str(float(P_pair)),
        "m": str(m),
        "wrap_m_over_p2": str(float(wrap)),
        "residue_numerator": str(num),
        "residue_num_int": num,
        "residue": str(float(residue)),
        "residue_fraction": f"{num}/{P2}",
        "ratio_P_pair_to_wrap": str(float(P_pair / wrap)) if wrap else None,
    }


def beta_slots(px: int) -> dict[int, int]:
    return {
        1: (px * inv(BETA_SQ, p)) % p,
        2: (px * inv(BETA, p)) % p,
        3: px,
    }


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


def global_refs(d: int | None = None, nd: int | None = None) -> dict[str, Fraction]:
    refs = {
        "N_over_p": Fraction(N, p),
        "DELTA_over_p2": Fraction(DELTA, P2),
        "DELTA_over_N": Fraction(DELTA, N),
        "one_over_p": Fraction(1, p),
        "seven_over_p3": Fraction(7, p**3),
    }
    if d is not None:
        refs["d_over_N"] = Fraction(d, N)
    if nd is not None:
        refs["N_minus_d_over_N"] = Fraction(nd, N)
    return refs


def compare_residue(R: Fraction, refs: dict[str, Fraction]) -> dict:
    exact = [k for k, v in refs.items() if R == v]
    dists = {k: abs(float(R - v)) for k, v in refs.items()}
    nearest = min(dists, key=dists.get)
    return {
        "exact_hits": exact,
        "nearest": nearest,
        "nearest_distance": dists[nearest],
        "distances": dists,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()
    rsz = load_rsz()

    rows: list[dict] = []
    exact_hit_counter: Counter[str] = Counter()
    nearest_counter: Counter[str] = Counter()
    beta_same_as_slot3 = 0
    beta_total = 0

    for n in range(1, 161):
        e = catalog[n]
        if not e.public_key:
            continue
        px, py = pubkey_xy(e.public_key)
        pmy = (p - py) % p

        branches = {}
        for label, yd in (("y", py), ("p_minus_y", pmy)):
            blk = pair_minus_wrap(px, yd)
            refs = global_refs()
            if n in rsz and rsz[n].get("r") is not None:
                rv = rsz[n]["r"]
                sv = rsz[n]["s"]
                zv = rsz[n]["z"]
                if isinstance(rv, str):
                    rv = int(rv, 16)
                if isinstance(sv, str):
                    sv = int(sv, 16)
                refs["r_over_N"] = Fraction(rv % N, N)
                refs["s_over_N"] = Fraction(sv % N, N)
                refs["z_over_N"] = Fraction(zv % N, N)
            if e.solved and e.private_key > 0:
                d = e.private_key
                nd = (N - d) % N
                refs["d_over_N"] = Fraction(d, N)
                refs["N_minus_d_over_N"] = Fraction(nd, N)

            R = Fraction(blk["residue_num_int"], P2)
            cmp = compare_residue(R, refs)
            for h in cmp["exact_hits"]:
                exact_hit_counter[h] += 1
            nearest_counter[cmp["nearest"]] += 1

            branches[label] = {**blk, "compare": cmp}

        # beta-slot residues (p−y branch, slot 3 is pubkey x)
        slots = beta_slots(px)
        slot_res = {}
        R3 = Fraction(pair_minus_wrap(px, pmy)["residue_num_int"], P2)
        for si, sx in slots.items():
            sr = pair_minus_wrap(sx, pmy)
            R = Fraction(sr["residue_num_int"], P2)
            beta_total += 1
            if si == 3:
                beta_same_as_slot3 += 1
            elif R == R3:
                beta_same_as_slot3 += 1
            slot_res[f"slot_{si}"] = {
                "residue": sr["residue"],
                "residue_numerator": sr["residue_numerator"],
                "delta_from_slot_3": str(float(R - R3)),
            }

        rec = {
            "puzzle": n,
            "Px": str(px),
            "primary_branch": "p_minus_y",
            "branches": branches,
            "beta_slot_residues_pmy": slot_res,
            "beta_residue_equals_slot3": all(
                slot_res[f"slot_{i}"]["residue"] == slot_res["slot_3"]["residue"]
                for i in (1, 2, 3)
            ),
        }
        rows.append(rec)

    # --- P135 headline ---
    p135 = next(r for r in rows if r["puzzle"] == 135)
    p135_pmy = p135["branches"]["p_minus_y"]

    # --- aggregate nearest (primary pmy branch only) ---
    nearest_pmy: Counter[str] = Counter()
    for r in rows:
        nearest_pmy[r["branches"]["p_minus_y"]["compare"]["nearest"]] += 1

    exhibit = {
        "exhibit": "pair_minus_wrap_scan",
        "builds_on": "exhibit_field_native_pair_packet",
        "formula": {
            "P_pair": "(x*p + y) / p^2",
            "wrap": "m / p^2",
            "m": "(x^3 + 7 - y^2) // p",
            "residue": "(x*p + y - m) / p^2 = P_pair - wrap",
        },
        "aggregates": {
            "pubkey_puzzles": len(rows),
            "exact_equality_hits": dict(exact_hit_counter),
            "total_exact_hits": sum(exact_hit_counter.values()),
            "nearest_reference_pmy_branch": dict(nearest_pmy),
            "beta_residue_equals_slot3_count": beta_same_as_slot3,
            "beta_residue_total": beta_total,
        },
        "P135": {
            "P_pair": p135_pmy["P_pair"],
            "wrap_m_over_p2": p135_pmy["wrap_m_over_p2"],
            "residue": p135_pmy["residue"],
            "ratio_P_pair_to_wrap": p135_pmy["ratio_P_pair_to_wrap"],
            "beta_slots": p135["beta_slot_residues_pmy"],
        },
        "puzzles": rows,
        "verdict": {
            "factual_structure": True,
            "is_d": False,
            "better_missing_term_target": True,
            "exact_hits_to_refs": sum(exact_hit_counter.values()) == 0,
            "note": "residue places coordinate limbs and curve wrap under same p^2 roof; identity is structural not scalar",
        },
        "ruling": "Point limbs and curve wrap now share p^2 denominator. Residue can testify; still not d.",
        "judge_popcorn": "We finally put the point limbs and the curve wrap under the same roof. Now the residue can testify.",
    }

    json_path = OUT / "exhibit_pair_minus_wrap_scan.json"
    json_path.write_text(json.dumps(exhibit, indent=2), encoding="utf-8")

    md = f"""# EXHIBIT: pair-minus-wrap scan

## Residue lane

```text
P_pair  = (x*p + y) / p^2
wrap    = m / p^2        m = (x^3 + 7 - y^2) // p
residue = P_pair - wrap  = (x*p + y - m) / p^2
```

Coordinate limbs and curve wrap share the **same p² roof**.

## Aggregates ({len(rows)} pubkey puzzles)

```text
exact equality hits to refs:  {sum(exact_hit_counter.values())}
beta residue == slot_3:       {beta_same_as_slot3} / {beta_total}
```

### Nearest reference (p−y branch, float distance)

```text
{chr(10).join(f"  {k}: {v}" for k, v in nearest_pmy.most_common())}
```

No exact hits to `d/N`, `r/N`, `N/p`, or `DELTA/p²` — residue is its own object.

## P135

```text
P_pair   = {p135_pmy['P_pair'][:55]}...
m/p²     = {p135_pmy['wrap_m_over_p2'][:55]}...
residue  = {p135_pmy['residue'][:55]}...
ratio    = {p135_pmy['ratio_P_pair_to_wrap'][:40]}...
```

β-slot residues (p−y):

| Slot | residue (head) | Δ from slot 3 |
|------|----------------|---------------|
| 1 | {p135['beta_slot_residues_pmy']['slot_1']['residue'][:40]}… | {p135['beta_slot_residues_pmy']['slot_1']['delta_from_slot_3'][:20]}… |
| 2 | {p135['beta_slot_residues_pmy']['slot_2']['residue'][:40]}… | {p135['beta_slot_residues_pmy']['slot_2']['delta_from_slot_3'][:20]}… |
| 3 | {p135['beta_slot_residues_pmy']['slot_3']['residue'][:40]}… | 0 |

## Clean ruling

```text
This is factual structure: yes
This is d:                 no
Better missing-term target: yes
```

Judge Popcorn: **We finally put the point limbs and the curve wrap under the same roof. Now the residue can testify.**
"""

    md_path = OUT / "exhibit_pair_minus_wrap_scan.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"exact hits: {sum(exact_hit_counter.values())}")
    print(f"nearest pmy: {dict(nearest_pmy.most_common(3))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
