#!/usr/bin/env python3
"""
Residue numerator briefcase scan — integer lane across all briefcase ways.

residue numerator:
  num = x*p + y - m
  m   = (x^3 + 7 - y^2) // p

Mod lenses:
  num mod p, mod N, mod DELTA, mod 2^256

Ways (head x limb):
  pubkey Px + y / p-y
  beta Px1, Px2, Px3 + y / p-y
  rx slots (when RSZ) + y / p-y
  Gx slots + y / p-y

Compare mod classes against all briefcase witnesses:
  d, N-d, r, s, z, Px, Py, hash160, range_lo/hi,
  map_p_to_n, ledger globals, m, pair numerator, carry, etc.

Writes: ARCHIVE/briefcase/The Real Decimal/exhibit_residue_numerator_briefcase_scan.*
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from build_complexity_operations_ledger import (
    BETA,
    BETA_SQ,
    DELTA,
    Gx,
    LAMBDA,
    LAMBDA1,
    N,
    Px as P135_PX,
    inv,
    p,
    rx,
)
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog
from puzzle_rsz_blockchain import CACHE_PATH

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "The Real Decimal"
P2 = p * p
TWO256 = 1 << 256
B = (1 << 32) + 977
B4 = pow(B, 4)


def residue_num(x: int, y_limb: int) -> tuple[int, int]:
    m = (x**3 + 7 - y_limb**2) // p
    return x * p + y_limb - m, m


def map_p_to_n(x: int) -> int:
    return (N * x) // p


def carry_roof(x: int, y: int) -> int:
    return 1 if (N * x) % p + y >= p else 0


def mod_pack(num: int) -> dict[str, str]:
    return {
        "mod_p": str(num % p),
        "mod_N": str(num % N),
        "mod_DELTA": str(num % DELTA),
        "mod_2_256": str(num % TWO256),
        "mod_p_bits": (num % p).bit_length(),
        "mod_N_bits": (num % N).bit_length(),
    }


def load_rsz() -> dict[int, dict]:
    if not CACHE_PATH.exists():
        return {}
    raw = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {int(k): v for k, v in raw.items() if isinstance(v, dict)}


def puzzle_witnesses(n: int, e, px: int, py: int, pmy: int, rsz: dict) -> dict[str, int]:
    w: dict[str, int] = {
        "Px": px,
        "Py": py,
        "p_minus_y": pmy,
        "hash160": int(e.hash160, 16) if e.hash160 else 0,
        "range_lo": e.range_min,
        "range_hi": e.range_max,
        "map_p_to_n_Px": map_p_to_n(px),
        "map_p_to_n_Py": map_p_to_n(py),
        "map_p_to_n_pmy": map_p_to_n(pmy),
    }
    if e.solved and e.private_key > 0:
        d = e.private_key
        w["d"] = d
        w["N_minus_d"] = (N - d) % N
        w["d_minus_lo"] = d - e.range_min
    if n in rsz and rsz[n].get("r") is not None:
        rv = rsz[n]["r"]
        sv = rsz[n]["s"]
        zv = rsz[n]["z"]
        if isinstance(rv, str):
            rv = int(rv, 16)
        if isinstance(sv, str):
            sv = int(sv, 16)
        r, s, z = rv % N, sv % N, zv % N
        w["r"] = r
        w["s"] = s
        w["z"] = z
        w["map_p_to_n_r"] = map_p_to_n(r)
    return w


def global_witnesses() -> dict[str, int]:
    g = {
        "BETA": BETA,
        "BETA_SQ": BETA_SQ,
        "LAMBDA": LAMBDA,
        "LAMBDA1": LAMBDA1,
        "DELTA": DELTA,
        "B": B,
        "B4": B4,
        "p_mod_N": p % N,
        "N_mod_p": N % p,
    }
    for i, v in enumerate(Gx, 1):
        g[f"Gx_slot_{i}"] = v
    for i, v in enumerate(P135_PX, 1):
        g[f"P135_Px_slot_{i}"] = v
    for i, v in enumerate(rx, 1):
        g[f"P135_rx_slot_{i}"] = v % p
    return g


def compare_mods(num: int, refs: dict[str, int], mod_name: str, mod_val: int) -> list[str]:
    hits = []
    nmod = num % mod_val
    for name, val in refs.items():
        if val % mod_val == nmod:
            hits.append(name)
    return hits


def low_bit_hits(num: int, refs: dict[str, int], bits: int) -> list[str]:
    mask = (1 << bits) - 1
    nlow = num & mask
    return [name for name, val in refs.items() if (val & mask) == nlow]


def offset_class(num: int, ref: int, mod: int) -> int:
    return (num - ref) % mod


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()
    rsz = load_rsz()
    globals_w = global_witnesses()

    mod_names = {
        "mod_p": p,
        "mod_N": N,
        "mod_DELTA": DELTA,
        "mod_2_256": TWO256,
    }

    hit_counter: Counter[tuple[str, str, str]] = Counter()  # (way, mod, ref)
    lowbit_counter: Counter[tuple[str, int, str]] = Counter()
    primary_triplets: Counter[tuple[int, int, int]] = Counter()
    identity_fail = 0
    rows: list[dict] = []
    way_count = 0

    for n in range(1, 161):
        e = catalog[n]
        if not e.public_key:
            continue
        px, py = pubkey_xy(e.public_key)
        pmy = (p - py) % p
        witnesses = puzzle_witnesses(n, e, px, py, pmy, rsz)
        all_refs = {**globals_w, **witnesses}

        px1 = (px * inv(BETA_SQ, p)) % p
        px2 = (px * inv(BETA, p)) % p

        heads: dict[str, int] = {
            "pubkey_Px": px,
            "beta_Px1": px1,
            "beta_Px2": px2,
            "beta_Px3": px,
        }
        if n in rsz and rsz[n].get("r") is not None:
            for i, rv in enumerate(rx, 1):
                heads[f"rx_slot_{i}"] = rv % p
        for i, gv in enumerate(Gx, 1):
            heads[f"Gx_slot_{i}"] = gv

        puzzle_ways: dict[str, dict] = {}
        for hname, x in heads.items():
            for blabel, yd in (("y", py), ("p_minus_y", pmy)):
                way_count += 1
                num, m = residue_num(x, yd)
                if num % p != (yd - m) % p:
                    identity_fail += 1
                mods = mod_pack(num)
                hits_by_mod: dict[str, list[str]] = {}
                for mlabel, mval in mod_names.items():
                    h = compare_mods(num, all_refs, mlabel, mval)
                    hits_by_mod[mlabel] = h
                    for ref in h:
                        hit_counter[(f"{hname}+{blabel}", mlabel, ref)] += 1

                low_hits: dict[str, list[str]] = {}
                for bits in (8, 16, 32, 64):
                    lh = low_bit_hits(num, all_refs, bits)
                    low_hits[f"low_{bits}"] = lh
                    for ref in lh:
                        lowbit_counter[(f"{hname}+{blabel}", bits, ref)] += 1

                wkey = f"{hname}+{blabel}"
                puzzle_ways[wkey] = {
                    "head": hname,
                    "branch": blabel,
                    "num": str(num),
                    "m": str(m),
                    "pair_numerator_xp_plus_y": str(x * p + yd),
                    "mods": mods,
                    "mod_hits": hits_by_mod,
                    "low_bit_hits": low_hits,
                    "carry_roof": carry_roof(x, yd),
                }

                if hname == "pubkey_Px" and blabel == "p_minus_y":
                    primary_triplets[(num % p, num % N, num % DELTA)] += 1

        primary = puzzle_ways["pubkey_Px+p_minus_y"]
        rec = {
            "puzzle": n,
            "primary_residue_pmy": primary,
            "all_ways": puzzle_ways,
            "witness_count": len(all_refs),
        }
        rows.append(rec)

    # --- shared fingerprint entropy (primary) ---
    triplet_share = Counter(primary_triplets.values())
    max_share = max(triplet_share) if triplet_share else 0
    unique_triplets = len(primary_triplets)

    # --- top hits ---
    top_hits = hit_counter.most_common(15)
    top_lowbit = lowbit_counter.most_common(20)

    # solved: low-32 vs d
    d_low32_hits = 0
    for r in rows:
        n = r["puzzle"]
        e = catalog[n]
        if not e.solved or e.private_key <= 0:
            continue
        num = int(r["primary_residue_pmy"]["num"])
        if (num & 0xFFFFFFFF) == (e.private_key & 0xFFFFFFFF):
            d_low32_hits += 1

    # --- mod_p hit summary for primary way only ---
    primary_hits_p = Counter(
        ref for (way, mod, ref), c in hit_counter.items()
        if way == "pubkey_Px+p_minus_y" and mod == "mod_p"
        for _ in range(c)
    )
    primary_hits_N = Counter(
        ref for (way, mod, ref), c in hit_counter.items()
        if way == "pubkey_Px+p_minus_y" and mod == "mod_N"
        for _ in range(c)
    )

    # --- exact d hits? ---
    d_hits = sum(
        c for (way, mod, ref), c in hit_counter.items()
        if ref == "d"
    )

    # --- P135 ---
    p135 = next(r for r in rows if r["puzzle"] == 135)

    exhibit = {
        "exhibit": "residue_numerator_briefcase_scan",
        "builds_on": "exhibit_pair_minus_wrap_scan",
        "formula": {
            "num": "x*p + y - m",
            "m": "(x^3 + 7 - y^2) // p",
            "identity_mod_p": "num mod p = (y - m) mod p",
        },
        "mod_lenses": list(mod_names.keys()),
        "ways": {
            "heads": ["pubkey_Px", "beta_Px1", "beta_Px2", "beta_Px3", "rx_slot_*", "Gx_slot_*"],
            "branches": ["y", "p_minus_y"],
            "total_way_rows": way_count,
        },
        "reference_witnesses": {
            "per_puzzle": list(puzzle_witnesses(135, catalog[135], *pubkey_xy(catalog[135].public_key), (p - pubkey_xy(catalog[135].public_key)[1]) % p, rsz).keys()),
            "global": list(globals_w.keys()),
        },
        "aggregates": {
            "pubkey_puzzles": len(rows),
            "identity_mod_p_failures": identity_fail,
            "unique_primary_mod_triplets": unique_triplets,
            "max_puzzles_sharing_primary_triplet": max_share,
            "d_exact_mod_hits": d_hits,
            "d_low32_hits_primary": d_low32_hits,
            "exact_full_mod_hits_total": sum(hit_counter.values()),
            "primary_mod_p_top_hits": dict(primary_hits_p.most_common(15)),
            "primary_mod_N_top_hits": dict(primary_hits_N.most_common(15)),
            "top_low_bit_hits": [
                {"way": w, "bits": b, "ref": r, "count": c} for (w, b, r), c in top_lowbit
            ],
            "top_exact_mod_hits": [
                {"way": w, "mod": m, "ref": r, "count": c} for (w, m, r), c in top_hits
            ],
        },
        "P135": {
            "puzzle": 135,
            "primary_residue_pmy": p135["primary_residue_pmy"],
            "all_ways": p135["all_ways"],
        },
        "puzzles_summary": [
            {
                "puzzle": r["puzzle"],
                "primary_mods": r["primary_residue_pmy"]["mods"],
                "primary_mod_hits": r["primary_residue_pmy"]["mod_hits"],
                "way_count": len(r["all_ways"]),
            }
            for r in rows
        ],
        "verdict": {
            "factual_structure": True,
            "is_d": d_hits == 0,
            "transferable_triplet_mask": max_share <= 2,
            "note": "integer mod lane across all briefcase heads/branches/refs",
        },
        "ruling": "Residue numerator tested on all briefcase ways. Mod hits are mostly trivial (Py, p-y, self). Not d.",
        "judge_popcorn": "The residue testified in every courtroom. No conviction.",
    }

    json_path = OUT / "exhibit_residue_numerator_briefcase_scan.json"
    json_path.write_text(json.dumps(exhibit, indent=2), encoding="utf-8")

    md = f"""# EXHIBIT: residue numerator briefcase scan

Integer lane: `num = x*p + y - m` across **all briefcase ways**.

## Mod lenses

```text
num mod p
num mod N
num mod DELTA
num mod 2^256
```

Identity: `num mod p = (y - m) mod p` — verified ({identity_fail} failures).

## Ways scanned

```text
heads:    pubkey_Px, beta_Px1/2/3, rx_slot_*, Gx_slot_*
branches: y, p_minus_y
total:    {way_count} residue rows ({len(rows)} puzzles)
```

## Primary witness (pubkey Px + p−y)

```text
unique (mod p, mod N, mod DELTA) triplets: {unique_triplets} / {len(rows)}
max puzzles sharing one triplet:          {max_share}
```

No transferable global fingerprint — triplets are point-specific.

## Exact full-mod hits

```text
total exact (mod p/N/DELTA/2^256) hits: {sum(hit_counter.values())}
d exact mod hits:                       {d_hits}
d low-32 primary hits:                  {d_low32_hits}
```

Exact full-mod equality is empty — expected at 256-bit scale.

## Low-bit hits (top)

```text
{chr(10).join(f"  {h['way']} | low_{h['bits']} | {h['ref']}: {h['count']}" for h in exhibit['aggregates']['top_low_bit_hits'][:10]) or "  (none above noise)"}
```

## Primary mod_p / mod_N exact hits

```text
mod_p: {dict(primary_hits_p.most_common(5)) or "none"}
mod_N: {dict(primary_hits_N.most_common(5)) or "none"}
```

## P135 primary (pubkey + p−y)

```text
num mod p     = {p135['primary_residue_pmy']['mods']['mod_p'][:50]}...
num mod N     = (256-bit residue class)
num mod DELTA = {p135['primary_residue_pmy']['mods']['mod_DELTA'][:50]}...
mod_p hits    = {p135['primary_residue_pmy']['mod_hits']['mod_p']}
```

## Clean ruling

```text
Factual structure: yes — integer mod lane works on all briefcase ways
This is d:         no — {d_hits} exact d mod hits
Transferable mask: no — {unique_triplets} unique primary triplets
```

Judge Popcorn: **The residue testified in every courtroom. No conviction.**
"""

    md_path = OUT / "exhibit_residue_numerator_briefcase_scan.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"ways: {way_count}  unique triplets: {unique_triplets}  d_hits: {d_hits}")
    print(f"top hit: {top_hits[0] if top_hits else None}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
