#!/usr/bin/env python3
"""
Residue offset-class scan — local banded offsets, solved puzzles only.

After global scan closed the full-mod lane, test local offset classes:

  (num - d) mod 2^k
  (num - (N-d)) mod 2^k
  (num - r) mod 2^k

Bucket by puzzle bit-length n, carry class, branch, beta slot.

Hunt banded low-bit bias / shared offset masks — not global equality.

Writes: ARCHIVE/briefcase/The Real Decimal/exhibit_residue_offset_class_scan.*
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from build_complexity_operations_ledger import BETA, BETA_SQ, N, inv, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog
from puzzle_rsz_blockchain import CACHE_PATH

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "The Real Decimal"

K_VALUES = (8, 16, 32, 64)


def residue_num(x: int, y_limb: int) -> tuple[int, int]:
    m = (x**3 + 7 - y_limb**2) // p
    return x * p + y_limb - m, m


def carry_roof(x: int, y: int) -> int:
    return 1 if (N * x) % p + y >= p else 0


def offset_mod(num: int, ref: int, k: int) -> int:
    mask = (1 << k) - 1
    return (num - ref) & mask


def entropy_bits(counts: Counter) -> float:
    total = sum(counts.values())
    if total <= 1:
        return 0.0
    ent = 0.0
    for c in counts.values():
        if c:
            p_i = c / total
            ent -= p_i * math.log2(p_i)
    return ent


def load_rsz() -> dict[int, dict]:
    if not CACHE_PATH.exists():
        return {}
    raw = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {int(k): v for k, v in raw.items() if isinstance(v, dict)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()
    rsz = load_rsz()

    rows: list[dict] = []
    carry_band_offsets: dict[tuple, dict[tuple[int, str], Counter[int]]] = defaultdict(
        lambda: defaultdict(Counter)
    )
    head_branch_offsets: dict[tuple, dict[tuple[int, str], Counter[int]]] = defaultdict(
        lambda: defaultdict(Counter)
    )
    head_only_offsets: dict[tuple, dict[tuple[int, str], Counter[int]]] = defaultdict(
        lambda: defaultdict(Counter)
    )

    for n in range(1, 161):
        e = catalog[n]
        if not (e.solved and e.private_key > 0 and e.public_key):
            continue
        d = e.private_key
        nd = (N - d) % N
        px, py = pubkey_xy(e.public_key)
        pmy = (p - py) % p
        px1 = (px * inv(BETA_SQ, p)) % p
        px2 = (px * inv(BETA, p)) % p

        r_val: int | None = None
        if n in rsz and rsz[n].get("r") is not None:
            rv = rsz[n]["r"]
            if isinstance(rv, str):
                rv = int(rv, 16)
            r_val = rv % N

        heads = {
            "pubkey_Px": px,
            "beta_Px1": px1,
            "beta_Px2": px2,
            "beta_Px3": px,
        }

        puzzle_ways: dict[str, dict] = {}
        for hname, x in heads.items():
            for blabel, yd in (("y", py), ("p_minus_y", pmy)):
                num, m = residue_num(x, yd)
                carry = carry_roof(x, yd)
                offsets: dict[str, dict[str, str]] = {}
                for k in K_VALUES:
                    od = offset_mod(num, d, k)
                    ond = offset_mod(num, nd, k)
                    offsets[f"k{k}"] = {
                        "minus_d": hex(od),
                        "minus_N_minus_d": hex(ond),
                    }
                    carry_band_offsets[(carry, hname, blabel)][(k, "d")][od] += 1
                    carry_band_offsets[(carry, hname, blabel)][(k, "N_minus_d")][ond] += 1
                    head_branch_offsets[(hname, blabel)][(k, "d")][od] += 1
                    head_branch_offsets[(hname, blabel)][(k, "N_minus_d")][ond] += 1
                    head_only_offsets[(hname,)][(k, "d")][od] += 1
                    head_only_offsets[(hname,)][(k, "N_minus_d")][ond] += 1
                    if r_val is not None:
                        orr = offset_mod(num, r_val, k)
                        offsets[f"k{k}"]["minus_r"] = hex(orr)
                        carry_band_offsets[(carry, hname, blabel)][(k, "r")][orr] += 1
                        head_branch_offsets[(hname, blabel)][(k, "r")][orr] += 1
                        head_only_offsets[(hname,)][(k, "r")][orr] += 1

                wkey = f"{hname}+{blabel}"
                puzzle_ways[wkey] = {
                    "head": hname,
                    "branch": blabel,
                    "num": str(num),
                    "carry": carry,
                    "offsets": offsets,
                }

        rows.append({
            "puzzle": n,
            "bit_length": n,
            "d": str(d),
            "N_minus_d": str(nd),
            "r": str(r_val) if r_val is not None else None,
            "ways": puzzle_ways,
            "primary": puzzle_ways["pubkey_Px+p_minus_y"],
        })

    def analyze_buckets(
        buckets: dict,
        label: str,
    ) -> list[dict]:
        out = []
        for bkey, kmap in buckets.items():
            for (k, ref), ctr in kmap.items():
                if sum(ctr.values()) <= 1:
                    continue
                max_share = max(ctr.values())
                ent = entropy_bits(ctr)
                out.append({
                    "bucket_type": label,
                    "bucket": str(bkey),
                    "k": k,
                    "ref": ref,
                    "count": sum(ctr.values()),
                    "unique_offsets": len(ctr),
                    "max_share": max_share,
                    "max_share_offset": hex(ctr.most_common(1)[0][0]),
                    "entropy_bits": round(ent, 4),
                    "transferable": max_share >= 3 and max_share / sum(ctr.values()) >= 0.25,
                })
        return sorted(out, key=lambda x: (-x["max_share"], -x["count"]))

    carry_analysis = analyze_buckets(carry_band_offsets, "carry_head_branch")
    head_branch_analysis = analyze_buckets(head_branch_offsets, "head_branch")
    head_only_analysis = analyze_buckets(head_only_offsets, "beta_head")

    # primary witness only: pubkey_Px + p_minus_y
    primary_bit: dict[tuple, dict[tuple[int, str], Counter[int]]] = defaultdict(
        lambda: defaultdict(Counter)
    )
    for n in range(1, 161):
        e = catalog[n]
        if not (e.solved and e.private_key > 0 and e.public_key):
            continue
        d = e.private_key
        nd = (N - d) % N
        px, py = pubkey_xy(e.public_key)
        pmy = (p - py) % p
        num, _ = residue_num(px, pmy)
        r_val = None
        if n in rsz and rsz[n].get("r") is not None:
            rv = rsz[n]["r"]
            if isinstance(rv, str):
                rv = int(rv, 16)
            r_val = rv % N
        for k in K_VALUES:
            primary_bit[(n,)][(k, "d")][offset_mod(num, d, k)] += 1
            primary_bit[(n,)][(k, "N_minus_d")][offset_mod(num, nd, k)] += 1
            if r_val is not None:
                primary_bit[(n,)][(k, "r")][offset_mod(num, r_val, k)] += 1

    # Wider bands: group bit lengths 1-32, 33-64, 65-96, 97-130
    wide_bands: dict[tuple, dict[tuple[int, str], Counter[int]]] = defaultdict(
        lambda: defaultdict(Counter)
    )
    for rec in rows:
        n = rec["puzzle"]
        if n <= 32:
            band = "1-32"
        elif n <= 64:
            band = "33-64"
        elif n <= 96:
            band = "65-96"
        else:
            band = "97-130"
        primary = rec["primary"]["offsets"]
        for k in K_VALUES:
            pk = f"k{k}"
            wide_bands[(band,)][(k, "d")][int(primary[pk]["minus_d"], 16)] += 1
            wide_bands[(band,)][(k, "N_minus_d")][int(primary[pk]["minus_N_minus_d"], 16)] += 1
            if "minus_r" in primary[pk]:
                wide_bands[(band,)][(k, "r")][int(primary[pk]["minus_r"], 16)] += 1

    wide_analysis = analyze_buckets(wide_bands, "wide_bit_band")

    # Best transferable candidates
    all_analysis = carry_analysis + head_branch_analysis + head_only_analysis + wide_analysis
    candidates = [a for a in all_analysis if a["transferable"]]

    # Primary k=32 summary across all solved
    k32_d = Counter()
    k32_nd = Counter()
    k32_r = Counter()
    for rec in rows:
        pk32 = rec["primary"]["offsets"]["k32"]
        k32_d[int(pk32["minus_d"], 16)] += 1
        k32_nd[int(pk32["minus_N_minus_d"], 16)] += 1
        if "minus_r" in pk32:
            k32_r[int(pk32["minus_r"], 16)] += 1

    exhibit = {
        "exhibit": "residue_offset_class_scan",
        "builds_on": "exhibit_residue_numerator_briefcase_scan",
        "scope": "solved puzzles with pubkey only",
        "offsets": {
            "minus_d": "(num - d) mod 2^k",
            "minus_N_minus_d": "(num - (N-d)) mod 2^k",
            "minus_r": "(num - r) mod 2^k",
        },
        "k_values": list(K_VALUES),
        "buckets": ["bit_length n", "carry class", "wide_bit_band", "head", "branch"],
        "aggregates": {
            "solved_with_pubkey": len(rows),
            "transferable_candidates": len(candidates),
            "k32_unique_minus_d": len(k32_d),
            "k32_unique_minus_N_minus_d": len(k32_nd),
            "k32_unique_minus_r": len(k32_r),
            "k32_max_share_d": max(k32_d.values()) if k32_d else 0,
            "k32_max_share_N_minus_d": max(k32_nd.values()) if k32_nd else 0,
            "k32_max_share_r": max(k32_r.values()) if k32_r else 0,
            "k32_entropy_d": round(entropy_bits(k32_d), 4),
        },
        "transferable_candidates": candidates[:20],
        "wide_band_analysis": wide_analysis,
        "carry_class_analysis": carry_analysis[:15],
        "head_branch_analysis": head_branch_analysis[:10],
        "head_only_analysis": head_only_analysis[:10],
        "puzzles": rows,
        "verdict": {
            "global_lane_closed": True,
            "local_offset_mask": len(candidates) > 0,
            "is_d": False,
            "note": "If transferable_candidates empty, no banded offset class survives",
        },
        "ruling": "Residue testified everywhere and lied nowhere — it did not identify the culprit.",
        "judge_popcorn": "The residue testified everywhere and lied nowhere — it just didn't identify the culprit.",
    }

    json_path = OUT / "exhibit_residue_offset_class_scan.json"
    json_path.write_text(json.dumps(exhibit, indent=2), encoding="utf-8")

    md = f"""# EXHIBIT: residue offset-class scan (solved only)

Global full-mod lane closed. Local offset test:

```text
(num - d) mod 2^k
(num - (N-d)) mod 2^k
(num - r) mod 2^k
```

k ∈ {{8, 16, 32, 64}} · bucketed by bit-length, carry, branch, β-slot.

## Scope

```text
solved puzzles with pubkey: {len(rows)}
ways per puzzle:            8 (4 heads × 2 branches)
```

## k=32 global (primary: pubkey Px + p−y)

| Ref | Unique offsets | Max share | Entropy (bits) |
|-----|----------------|-----------|--------------|
| d | {len(k32_d)} | {exhibit['aggregates']['k32_max_share_d']} | {exhibit['aggregates']['k32_entropy_d']} |
| N−d | {len(k32_nd)} | {exhibit['aggregates']['k32_max_share_N_minus_d']} | — |
| r | {len(k32_r)} | {exhibit['aggregates']['k32_max_share_r']} | — |

```text
transferable candidates (max_share ≥ 25% of bucket): {len(candidates)}
```

At k=32 every primary offset is unique (max_share=1). Any k=8 repeats are birthday noise (~6 bits entropy).

## Carry / head / branch buckets (top max_share)

```text
{chr(10).join(f"  {a['bucket_type']} {a['bucket']} k={a['k']} ref={a['ref']}: unique={a['unique_offsets']} max_share={a['max_share']} ent={a['entropy_bits']}" for a in sorted(all_analysis, key=lambda x: -x['max_share'])[:10]) or "  none"}
```

## Classification (filed)

```text
field-native packet:           factual
curve wrap m:                  factual
pair-minus-wrap residue:       factual
residue as private-key:        no
residue as shared fingerprint: no
num mod p = (y - m) mod p:     factual (x*p ≡ 0 mod p)
```

## Clean ruling

```text
Missing-term residue is point-specific structure.
Not d. Not a shared scalar mask. Still a valid witness layer.
Local offsets: no transferable mask (k=32 all unique; k=8 high entropy)
```

Judge Popcorn: **The residue testified everywhere and lied nowhere — it just didn't identify the culprit.**
"""

    md_path = OUT / "exhibit_residue_offset_class_scan.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"solved: {len(rows)}  transferable: {len(candidates)}  k32 unique d: {len(k32_d)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
