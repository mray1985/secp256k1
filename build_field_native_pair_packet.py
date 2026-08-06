#!/usr/bin/env python3
"""
Field-native coordinate-pair packet — flattened 0.x_y in base p.

Packet:
  P_pair = x/p + y/p^2 = (x*p + y) / p^2

Not decimal stitch. Field-native two-limb witness:
  U = x/p          (first-order field placement)
  V = y/p          (y normalized to field roof)
  W = y/p^2        (second-order field-tail pressure)
  P_pair = U + W   = 0.x_y in base p

Curve wrap:
  y^2 = x^3 + 7 - m*p
  m = (x^3 + 7 - y^2) // p

Normalized (exact, all 88 pubkey puzzles):
  y^2/p^3 = x^3/p^3 + 7/p^3 - m/p^2

Compare P_pair against m/p^2, curve limbs, sqrt/defect roof terms.

Writes: ARCHIVE/briefcase/The Real Decimal/exhibit_field_native_pair_packet.*
"""

from __future__ import annotations

import json
import math
from fractions import Fraction
from pathlib import Path

from build_complexity_operations_ledger import DELTA, N, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "The Real Decimal"
B = (1 << 32) + 977  # 2^256 - p


def frac_str(f: Fraction) -> str:
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}={float(f):.60f}"


def carry_roof(x: int, y: int) -> int:
    """x.(y/p) carry into N."""
    rem = (N * x) % p
    return 1 if rem + y >= p else 0


def field_native_block(px: int, y_limb: int, label: str) -> dict:
    num = px * p + y_limb
    U = Fraction(px, p)
    V = Fraction(y_limb, p)
    W = Fraction(y_limb, p * p)
    P = U + W
    m = (px**3 + 7 - y_limb**2) // p
    curve_ok = (
        Fraction(y_limb**2, p**3)
        == Fraction(px**3, p**3) + Fraction(7, p**3) - Fraction(m, p**2)
    )
    return {
        "branch": label,
        "limbs": {
            "U_x_over_p": str(float(U)),
            "V_y_over_p": str(float(V)),
            "W_y_over_p2": str(float(W)),
            "P_pair": str(float(P)),
        },
        "exact": {
            "numerator_xp_plus_y": str(num),
            "denominator": str(p**2),
            "P_pair_fraction": f"{num}/{p**2}",
            "base_p_notation": f"0.{px}_{y_limb} (base p)",
        },
        "curve_wrap": {
            "m": str(m),
            "m_over_p2": str(float(Fraction(m, p**2))),
            "m_bit_length": m.bit_length(),
            "curve_normalized_ok": curve_ok,
            "identity": "y^2/p^3 = x^3/p^3 + 7/p^3 - m/p^2",
        },
        "pair_minus_wrap": {
            "numerator": str(num - m),
            "over_p2": str(float(Fraction(num - m, p**2))),
            "formula": "(x*p + y - m) / p^2 = P_pair - m/p^2",
        },
        "carry_roof": carry_roof(px, y_limb),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()

    rows: list[dict] = []
    curve_fail = 0
    p135_row: dict | None = None

    for n in range(1, 161):
        e = catalog[n]
        if not e.public_key:
            continue
        px, py = pubkey_xy(e.public_key)
        pmy = (p - py) % p

        by = field_native_block(px, py, "y")
        bp = field_native_block(px, pmy, "p_minus_y")
        if not by["curve_wrap"]["curve_normalized_ok"] or not bp["curve_wrap"]["curve_normalized_ok"]:
            curve_fail += 1

        rec = {
            "puzzle": n,
            "Px": str(px),
            "Py": str(py),
            "p_minus_y": str(pmy),
            "primary_branch": "p_minus_y",
            "branch_y": by,
            "branch_p_minus_y": bp,
            "P_pair_y": by["limbs"]["P_pair"],
            "P_pair_pmy": bp["limbs"]["P_pair"],
        }
        rows.append(rec)
        if n == 135:
            p135_row = rec

    # --- global reference terms (P135 primary branch for headline compare) ---
    px135, py135 = pubkey_xy(catalog[135].public_key)
    pmy135 = (p - py135) % p
    m135 = (px135**3 + 7 - pmy135**2) // p
    P135 = Fraction(px135 * p + pmy135, p**2)
    M135 = Fraction(m135, p**2)

    sqrt_p = math.isqrt(p)
    sqrt_N = math.isqrt(N)
    ref_terms = {
        "P_pair_p135_pmy": str(float(P135)),
        "m_over_p2_p135_pmy": str(float(M135)),
        "pair_minus_wrap_p135": str(float(P135 - M135)),
        "ratio_P_pair_to_m_over_p2": str(float(P135 / M135)) if M135 else None,
        "V_squared_over_p_p135": str(float(Fraction(pmy135**2, p**3))),
        "U_cubed_p135": str(float(Fraction(px135**3, p**3))),
        "seven_over_p3": str(float(Fraction(7, p**3))),
        "DELTA_over_p2": str(float(Fraction(DELTA, p**2))),
        "DELTA_over_p3": str(float(Fraction(DELTA, p**3))),
        "N_over_p": str(float(Fraction(N, p))),
        "B_over_p2": str(float(Fraction(B, p**2))),
        "sqrt_p_over_p": str(float(Fraction(sqrt_p, p))),
        "sqrt_N_over_p": str(float(Fraction(sqrt_N, p))),
        "sqrt_p_over_p2": str(float(Fraction(sqrt_p, p**2))),
        "note": "sqrt terms are integer isqrt roof witnesses, not curve sqrt",
    }

    # --- structural checks across all puzzles ---
    ratios = []
    for r in rows:
        bp = r["branch_p_minus_y"]
        P = float(bp["limbs"]["P_pair"])
        M = float(bp["curve_wrap"]["m_over_p2"])
        if M:
            ratios.append(P / M)

    exhibit = {
        "exhibit": "field_native_pair_packet",
        "builds_on": "exhibit_stitch_roof_comparison",
        "keeper": "0.x_y in base p — not human decimal stitch",
        "packet": {
            "formula": "(x*p + y) / p^2 = x/p + y/p^2",
            "name": "flattened coordinate-pair witness",
            "base_p": "0.x_y means x at p^-1 limb, y at p^-2 limb",
            "not": "x + y/10^digits(y)",
        },
        "limbs": {
            "U": "x/p — first-order field placement",
            "V": "y/p — y under field roof",
            "W": "y/p^2 — second-order tail pressure",
            "P_pair": "U + W",
        },
        "curve_wrap": {
            "integer": "y^2 = x^3 + 7 - m*p",
            "m": "(x^3 + 7 - y^2) // p",
            "normalized": "y^2/p^3 = x^3/p^3 + 7/p^3 - m/p^2",
            "verified_all_pubkeys": curve_fail == 0,
            "failures": curve_fail,
            "missing_term_candidate": "m/p^2 is the wrap limb at same denominator as P_pair",
        },
        "pair_vs_wrap": {
            "difference": "P_pair - m/p^2 = (x*p + y - m) / p^2",
            "same_denominator_p2": True,
            "P_pair_equals_m_over_p2": False,
            "note": "P_pair and m/p^2 share p^2 denominator but different numerators",
        },
        "reference_terms_p135_pmy": ref_terms,
        "ratio_P_to_m_pmy": {
            "min": min(ratios) if ratios else None,
            "max": max(ratios) if ratios else None,
            "p135": float(P135 / M135) if M135 else None,
        },
        "sqrt_caution": {
            "rejected_as_written": "x/p = -y*sqrt(p) — unit mismatch",
            "reframe": "x/p + y/p^2 exposes linear field placements; sqrt belongs to 128-bit midpoint roof after normalization",
        },
        "puzzles": rows,
        "ruling": (
            "x/p + y/p^2 is the field-native coordinate-pair packet (0.x_y in base p). "
            "m/p^2 is the curve wrap limb at the same denominator. "
            "Sqrt relations need normalized units before they are factual."
        ),
        "judge_popcorn": (
            "We stopped spelling coordinates in human decimal and started spelling them "
            "in the field's own alphabet. That's where the floorboards finally line up."
        ),
    }

    json_path = OUT / "exhibit_field_native_pair_packet.json"
    json_path.write_text(json.dumps(exhibit, indent=2), encoding="utf-8")

    md = f"""# EXHIBIT: field-native coordinate-pair packet

## Keeper

```text
0.x_y in base p  =  x/p + y/p^2  =  (x*p + y) / p^2
```

Not human decimal stitch. **Field-native two-limb witness.**

| Limb | Formula | Role |
|------|---------|------|
| U | `x/p` | first-order field placement |
| V | `y/p` | y under field roof |
| W | `y/p^2` | second-order tail pressure |
| P_pair | `U + W` | flattened coordinate-pair packet |

## Curve wrap (exact, all {len(rows)} pubkey puzzles)

```text
y^2 = x^3 + 7 - m*p
m   = (x^3 + 7 - y^2) // p

y^2/p^3 = x^3/p^3 + 7/p^3 - m/p^2     verified: {curve_fail == 0} failures
```

`m/p^2` is the **wrap limb** at the same `p^2` denominator as P_pair.

```text
P_pair - m/p^2 = (x*p + y - m) / p^2
```

P_pair and m/p^2 are **not equal** — different numerators, shared denominator.

## P135 (p−y primary branch)

```text
P_pair   = {ref_terms['P_pair_p135_pmy'][:60]}...
m/p^2    = {ref_terms['m_over_p2_p135_pmy'][:60]}...
P - m/p^2 = {ref_terms['pair_minus_wrap_p135'][:60]}...
ratio    = {ref_terms['ratio_P_pair_to_m_over_p2'][:40]}...
```

## Reference roof terms (P135 context)

```text
V^2/p = y^2/p^3 = {ref_terms['V_squared_over_p_p135'][:50]}...
U^3   = x^3/p^3  = {ref_terms['U_cubed_p135'][:50]}...
7/p^3           = {ref_terms['seven_over_p3'][:50]}...
DELTA/p^2       = {ref_terms['DELTA_over_p2'][:50]}...
sqrt(p)/p       = {ref_terms['sqrt_p_over_p'][:50]}...
sqrt(N)/p       = {ref_terms['sqrt_N_over_p'][:50]}...
```

## Sqrt caution

```text
REJECT (as written):  x/p = -y*sqrt(p)   — unit mismatch

REFRAME: x/p + y/p^2 are linear field placements.
         Curve relation lives in y^2 = x^3 + 7 - m*p.
         sqrt belongs to 128-bit midpoint roof after normalization.
```

## Ratio P_pair / (m/p^2) across puzzles

```text
min  = {exhibit['ratio_P_to_m_pmy']['min']}
max  = {exhibit['ratio_P_to_m_pmy']['max']}
P135 = {exhibit['ratio_P_to_m_pmy']['p135']}
```

Point-specific — not a universal constant.

## Clean ruling

```text
x/p + y/p^2 is the right field-native coordinate-pair packet.
It is a flattened ECC point witness (0.x_y in base p).
m/p^2 is the curve wrap limb at the same denominator.
Sqrt relations need normalized units before they are factual.
```

Judge Popcorn: **We stopped spelling coordinates in human decimal and started spelling them in the field's own alphabet. That's where the floorboards finally line up.**
"""

    md_path = OUT / "exhibit_field_native_pair_packet.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"curve normalized ok: {curve_fail == 0} / {len(rows)}")
    print(f"P135 ratio P/m: {float(P135/M135):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
