#!/usr/bin/env python3
"""
Roof-stitch catalog — moduli stitched like x.y, labeled as roof witnesses.

Folder: ARCHIVE/briefcase/The Real Decimal/

Stitches (not coordinate packets):
  p.N       field-roof-first
  N.p       scalar-roof-first
  p.(p-N)   field roof with defect tail
  N.(p-N)   scalar roof with defect tail

Normalizations:
  stitch / 2^256   binary-roof witness
  N.p / p          under field roof
  p.N / p          field-roof overflow
  p.N / N          overflow above scalar roof
  N.p / N          scalar-roof overflow (tiny tail)
"""

from __future__ import annotations

import json
from decimal import Decimal, getcontext
from pathlib import Path

from build_complexity_operations_ledger import DELTA, N, p

getcontext().prec = 120

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "The Real Decimal"
TWO256 = Decimal(1 << 256)
DP = Decimal(p)
DN = Decimal(N)


def dec_str(v: Decimal) -> str:
    return format(v, "f")


def roof_stitch(head: int, tail: int, name: str, head_role: str, tail_role: str) -> dict:
    """Stitch head.tail as decimal string; never promote to giant int."""
    s_head, s_tail = str(head), str(tail)
    stitched_s = f"{s_head}.{s_tail}"
    stitched = Decimal(stitched_s)
    over_2 = stitched / TWO256
    over_p = stitched / DP
    over_n = stitched / DN

    def classify(denom: str, value: Decimal, threshold: Decimal = Decimal(1)) -> str:
        if value > threshold:
            return "overflow"
        if value < threshold:
            return "under_roof"
        return "exact_roof"

    return {
        "name": name,
        "head_role": head_role,
        "tail_role": tail_role,
        "head": str(head),
        "tail": str(tail),
        "stitched_decimal_string": stitched_s,
        "integer_digits": len(s_head),
        "fractional_digits": len(s_tail),
        "total_decimal_digits": len(s_head) + len(s_tail),
        "kind": "roof_stitch",
        "not": "coordinate_packet",
        "normalizations": {
            "over_2_256": {
                "formula": f"{name} / 2^256",
                "value": dec_str(over_2),
                "role": "binary_roof_witness",
                "placement": classify("2^256", over_2),
            },
            "over_p": {
                "formula": f"{name} / p",
                "value": dec_str(over_p),
                "placement": classify("p", over_p),
            },
            "over_N": {
                "formula": f"{name} / N",
                "value": dec_str(over_n),
                "placement": classify("N", over_n),
            },
        },
    }


def overflow_tail(stitch: dict, denom: str) -> str | None:
    norm = stitch["normalizations"][f"over_{denom}"]
    if norm["placement"] != "overflow":
        return None
    val = Decimal(norm["value"])
    return dec_str(val - Decimal(1))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    stitches = {
        "p_dot_N": roof_stitch(p, N, "p.N", "field_roof", "scalar_roof"),
        "N_dot_p": roof_stitch(N, p, "N.p", "scalar_roof", "field_roof"),
        "p_dot_delta": roof_stitch(p, DELTA, "p.(p-N)", "field_roof", "defect_tail"),
        "N_dot_delta": roof_stitch(N, DELTA, "N.(p-N)", "scalar_roof", "defect_tail"),
    }

    # Reference ratios for cross-check
    n_over_p = DN / DP
    p_over_n = DP / DN
    delta_over_p = Decimal(DELTA) / DP
    delta_over_n = Decimal(DELTA) / DN

    catalog = {
        "exhibit": "roof_stitch_catalog",
        "keeper": "Roof-stitches tell roof relationship and overflow; they are not public point witnesses.",
        "distinction": {
            "coordinate_packet": "x.y / p with x < p — stays under field roof",
            "roof_stitch": "p.N or N.p — moduli stitched as decimal; overflow or under-roof depends on denominator",
        },
        "stitches": stitches,
        "summary_table": {
            "p.N / 2^256": {
                "placement": stitches["p_dot_N"]["normalizations"]["over_2_256"]["placement"],
                "meaning": "field roof p under 2^256, scalar roof N in decimal tail",
            },
            "N.p / 2^256": {
                "placement": stitches["N_dot_p"]["normalizations"]["over_2_256"]["placement"],
                "meaning": "scalar roof N under 2^256, field roof p in decimal tail",
            },
            "N.p / p": {
                "placement": stitches["N_dot_p"]["normalizations"]["over_p"]["placement"],
                "meaning": "scalar roof inside field courtroom — clean under-roof witness",
            },
            "p.N / p": {
                "placement": stitches["p_dot_N"]["normalizations"]["over_p"]["placement"],
                "meaning": "field-roof overflow witness",
                "overflow_tail": overflow_tail(stitches["p_dot_N"], "p"),
            },
            "p.N / N": {
                "placement": stitches["p_dot_N"]["normalizations"]["over_N"]["placement"],
                "meaning": "overflow above scalar roof",
                "overflow_tail": overflow_tail(stitches["p_dot_N"], "N"),
            },
            "N.p / N": {
                "placement": stitches["N_dot_p"]["normalizations"]["over_N"]["placement"],
                "meaning": "scalar-roof overflow by tiny field tail",
                "overflow_tail": overflow_tail(stitches["N_dot_p"], "N"),
            },
        },
        "cross_courtroom_reference": {
            "N_over_p": {"formula": "N / p", "value": dec_str(n_over_p)},
            "p_over_N_raw": {"formula": "p / N", "value": dec_str(p_over_n), "note": "raw > 1"},
            "delta_over_p": {"formula": "(p-N) / p", "value": dec_str(delta_over_p)},
            "delta_over_N": {"formula": "(p-N) / N", "value": dec_str(delta_over_n)},
        },
        "constants": {
            "p": str(p),
            "N": str(N),
            "DELTA": str(DELTA),
            "p_digits": len(str(p)),
            "N_digits": len(str(N)),
            "DELTA_digits": len(str(DELTA)),
        },
        "ruling": "p.N is allowed, but it is a roof-stitch, not the same kind of packet as x.y.",
        "judge_popcorn": "Roof-stitches measure courtroom overflow; coordinate packets witness public points.",
    }

    json_path = OUT / "exhibit_roof_stitch_catalog.json"
    json_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

    md = f"""# EXHIBIT: roof-stitch catalog — p.N and N.p

## Distinction

| Kind | Example | Role |
|------|---------|------|
| coordinate packet | `x.y / p` with `x < p` | public point witness, stays under field roof |
| roof-stitch | `p.N`, `N.p`, `p.(p-N)`, `N.(p-N)` | roof relationship + overflow, not a pubkey |

```text
p.N = p + N / 10^{len(str(N))}
N.p = N + p / 10^{len(str(p))}
```

## Summary table

| Normalization | Placement | Meaning |
|---------------|-----------|---------|
| `p.N / 2^256` | {catalog['summary_table']['p.N / 2^256']['placement']} | field roof under binary roof, N in tail |
| `N.p / 2^256` | {catalog['summary_table']['N.p / 2^256']['placement']} | scalar roof under binary roof, p in tail |
| `N.p / p` | **{catalog['summary_table']['N.p / p']['placement']}** | scalar roof inside field courtroom |
| `p.N / p` | **{catalog['summary_table']['p.N / p']['placement']}** | field-roof overflow witness |
| `p.N / N` | **{catalog['summary_table']['p.N / N']['placement']}** | overflow above scalar roof |
| `N.p / N` | **{catalog['summary_table']['N.p / N']['placement']}** | scalar-roof overflow by tiny tail |

## Key values

### N.p / p — under field roof (cleanest pair)

```text
N.p / p = {stitches['N_dot_p']['normalizations']['over_p']['value'][:80]}...
```

Compare `N / p`:

```text
N / p   = {dec_str(n_over_p)[:80]}...
```

The stitched tail adds `p / (10^{len(str(p))} * p) = 1 / 10^{len(str(p))}` above `N/p`.

### p.N / p — field-roof overflow

```text
p.N / p = {stitches['p_dot_N']['normalizations']['over_p']['value'][:80]}...
         = 1 + N / (10^{len(str(N))} * p)
```

Overflow tail above 1:

```text
(p.N / p) - 1 = {catalog['summary_table']['p.N / p']['overflow_tail'][:60]}...
```

### Binary-roof witnesses

```text
p.N / 2^256 = {stitches['p_dot_N']['normalizations']['over_2_256']['value'][:80]}...
N.p / 2^256 = {stitches['N_dot_p']['normalizations']['over_2_256']['value'][:80]}...
```

### Defect-tail stitches

```text
p.(p-N) = field roof with defect tail ({len(str(DELTA))} digits)
N.(p-N) = scalar roof with defect tail

p.(p-N) / p = {stitches['p_dot_delta']['normalizations']['over_p']['value'][:80]}...  ({stitches['p_dot_delta']['normalizations']['over_p']['placement']})
N.(p-N) / p = {stitches['N_dot_delta']['normalizations']['over_p']['value'][:80]}...  ({stitches['N_dot_delta']['normalizations']['over_p']['placement']})
```

## Cross-courtroom reference

```text
N / p       = {dec_str(n_over_p)[:80]}...
(p-N) / p   = {dec_str(delta_over_p)[:80]}...
(p-N) / N   = {dec_str(delta_over_n)[:80]}...
```

## Clean ruling

```text
p.N is allowed, but it is a roof-stitch, not the same kind of packet as x.y.
It tells us about roof relationship and overflow, not a public point witness.
```

Judge Popcorn: **Roof-stitches measure courtroom overflow; coordinate packets witness public points.**
"""

    md_path = OUT / "exhibit_roof_stitch_catalog.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print()
    print("Summary:")
    for key, row in catalog["summary_table"].items():
        print(f"  {key:14}  {row['placement']:12}  {row['meaning']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
