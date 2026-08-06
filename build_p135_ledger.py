#!/usr/bin/env python3
"""
P135 local courtroom ledger — every object under the correct roof.

Not a global scan. Single puzzle courtroom with field-native packets,
carry, curve wrap, residue, β-slots (Px and rx), RSZ, Λ bridges.

Writes: ARCHIVE/briefcase/The Real Decimal/P135/
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from build_complexity_operations_ledger import (
    BETA,
    BETA_SQ,
    DELTA,
    LAMBDA,
    LAMBDA1,
    N,
    Px as CS_PX,
    rx as CS_RX,
    inv,
    p,
)
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog
from puzzle_rsz_blockchain import CACHE_PATH

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "The Real Decimal" / "P135"
P2 = p * p
TWO256 = 1 << 256


def frac(f: Fraction) -> dict:
    return {
        "numerator": str(f.numerator),
        "denominator": str(f.denominator),
        "value": format(float(f), ".60f"),
    }


def over_p(v: int) -> dict:
    return {"formula": "v / p", **frac(Fraction(v, p))}


def over_n(v: int) -> dict:
    return {"formula": "v / N", **frac(Fraction(v, N))}


def over_p2(v: int) -> dict:
    return {"formula": "v / p²", **frac(Fraction(v, P2))}


def over_2_256(v: int) -> dict:
    return {"formula": "v / 2^256", **frac(Fraction(v, TWO256))}


def map_p_to_n(x: int) -> int:
    return (N * x) // p


def carry_roof(x: int, y: int) -> int:
    return 1 if (N * x) % p + y >= p else 0


def field_native(x: int, y_limb: int, label: str) -> dict:
    m = (x**3 + 7 - y_limb**2) // p
    num_pair = x * p + y_limb
    num_res = num_pair - m
    U = Fraction(x, p)
    V = Fraction(y_limb, p)
    W = Fraction(y_limb, P2)
    P_pair = U + W
    wrap = Fraction(m, P2)
    residue = Fraction(num_res, P2)
    return {
        "branch": label,
        "x": str(x),
        "y_limb": str(y_limb),
        "field_courtroom": {
            "x_over_p": over_p(x),
            "y_over_p": over_p(y_limb),
            "P_pair": {
                "formula": "(x*p + y) / p² = x/p + y/p²",
                "base_p": f"0.{x}_{y_limb}",
                **frac(P_pair),
            },
            "m_over_p2": over_p2(m),
            "residue_over_p2": {
                "formula": "(x*p + y - m) / p²",
                "numerator": str(num_res),
                **frac(residue),
            },
            "num_mod_p": str(num_res % p),
            "identity": "num mod p = (y - m) mod p",
        },
        "curve_wrap": {
            "m": str(m),
            "y_sq_eq": "y² = x³ + 7 - m*p",
            "normalized": "y²/p³ = x³/p³ + 7/p³ - m/p²",
            "verified": (
                Fraction(y_limb**2, p**3)
                == Fraction(x**3, p**3) + Fraction(7, p**3) - Fraction(m, P2)
            ),
        },
        "carry_p_to_N": {
            "A_map_p_to_n": str(map_p_to_n(x)),
            "B_floor_pair_N": str(int(P_pair * N)),
            "carry": carry_roof(x, y_limb),
            "threshold": "(N*x mod p) + y >= p",
        },
        "scalar_shadow": {
            "map_p_to_n_x": str(map_p_to_n(x)),
            "map_p_to_n_y": str(map_p_to_n(y_limb)),
        },
    }


def beta_x_slots(px: int) -> dict[str, int]:
    return {
        "Px1": (px * inv(BETA_SQ, p)) % p,
        "Px2": (px * inv(BETA, p)) % p,
        "Px3": px,
    }


def beta_rx_slots() -> dict[str, int]:
    return {
        "rx1": CS_RX[0] % p,
        "rx2": CS_RX[1] % p,
        "rx3": CS_RX[2] % p,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()
    e = catalog[135]
    px, py = pubkey_xy(e.public_key)
    pmy = (p - py) % p

    rsz = {}
    if CACHE_PATH.exists():
        raw = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        rsz = raw.get("135") or raw.get(135) or {}

    r = int(rsz.get("r", CS_RX[1]))
    s = int(rsz.get("s", 0))
    z = int(rsz.get("z", 0))

    n_lo = N - (1 << 135) + 1
    n_hi = N - (1 << 134)

    branches = {
        "y": field_native(px, py, "y"),
        "p_minus_y": field_native(px, pmy, "p_minus_y"),
    }
    primary = branches["p_minus_y"]

    px_slots = beta_x_slots(px)
    px_slot_blocks = {}
    for name, x in px_slots.items():
        px_slot_blocks[name] = {
            "x": str(x),
            "Px2_times_beta_eq_Px3": (px_slots["Px2"] * BETA) % p == px_slots["Px3"],
            "branches": {
                "y": field_native(x, py, "y"),
                "p_minus_y": field_native(x, pmy, "p_minus_y"),
            },
        }

    rx_slots = beta_rx_slots()
    rx_slot_blocks = {}
    for name, x in rx_slots.items():
        rx_slot_blocks[name] = {
            "x": str(x),
            "rx3_eq_rx2_beta": (rx_slots["rx2"] * BETA) % p == rx_slots["rx3"],
            "over_p": over_p(x),
            "over_N": over_n(x % N),
            "branches": {
                "y": field_native(x, py, "y"),
                "p_minus_y": field_native(x, pmy, "p_minus_y"),
            },
        }

    ledger = {
        "puzzle": 135,
        "courtroom": "P135 local ledger — every object under correct roof",
        "status": "UNSOLVED_PUBKEY",
        "residue_lane": "closed — point-specific witness, not d extractor",
        "identity": {
            "address": e.address,
            "hash160": e.hash160,
            "compressed_pubkey": e.public_key,
            "btc_value": e.btc_value,
            "d_window": f"[2^134, 2^135)",
            "range_lo": str(e.range_min),
            "range_hi": str(e.range_max),
            "N_mirror_window": f"[N-2^135+1, N-2^134]",
            "N_mirror_lo": str(n_lo),
            "N_mirror_hi": str(n_hi),
        },
        "roofs": {
            "p": {"value": str(p), "over_p": "1", "over_2_256": over_2_256(p)},
            "N": {"value": str(N), "over_p": over_p(N), "over_2_256": over_2_256(N)},
            "DELTA": {"value": str(DELTA), "over_p2": over_p2(DELTA), "over_N": over_n(DELTA)},
            "N_over_p": frac(Fraction(N, p)),
            "cross_courtroom": "N/p = scalar roof seen from field courtroom",
        },
        "pubkey": {
            "Px": str(px),
            "Py": str(py),
            "p_minus_y": str(pmy),
            "Px_over_p": over_p(px),
            "Py_over_p": over_p(py),
            "p_minus_y_over_p": over_p(pmy),
        },
        "field_native_primary": {
            "primary_branch": "p_minus_y",
            "branches": branches,
        },
        "beta_Px_slots": px_slot_blocks,
        "rsz": {
            "source": rsz.get("source", "hashkeys.space partial spend"),
            "txid": rsz.get("txid"),
            "input_index": rsz.get("input_index"),
            "equation": "s*k ≡ z + r*d (mod N)",
            "r": {"value": str(r), "hex": hex(r), **over_n(r % N)},
            "s": {"value": str(s), "hex": hex(s), **over_n(s % N)},
            "z": {"value": str(z), "hex": hex(z), **over_n(z % N)},
            "k": "unknown (d unknown)",
            "map_p_to_n_r": str(map_p_to_n(r % N)),
        },
        "beta_rx_slots": rx_slot_blocks,
        "lambda_bridges": {
            "LAMBDA": {
                "value": str(LAMBDA),
                "formula": "Px3 / rx3 mod p",
                "verified": (px * inv(rx_slots["rx3"], p)) % p == LAMBDA,
                **over_p(LAMBDA),
            },
            "LAMBDA1": {
                "value": str(LAMBDA1),
                "formula": "Px3 / rx2 mod p",
                "verified": (px * inv(rx_slots["rx2"], p)) % p == LAMBDA1,
                **over_p(LAMBDA1),
            },
            "LAMBDA_over_LAMBDA1_eq_BETA_SQ": (LAMBDA * inv(LAMBDA1, p)) % p == BETA_SQ,
        },
        "carry_summary": {
            "pubkey_y": branches["y"]["carry_p_to_N"]["carry"],
            "pubkey_pmy": branches["p_minus_y"]["carry_p_to_N"]["carry"],
            "admitted_fact": "y = carry pressure in p→N; not d",
        },
        "residue_summary": {
            "primary_residue_over_p2": primary["field_courtroom"]["residue_over_p2"],
            "wrap_over_p2": primary["field_courtroom"]["m_over_p2"],
            "P_pair": primary["field_courtroom"]["P_pair"],
            "ratio_P_pair_to_wrap": format(
                float(Fraction(
                    int(primary["field_courtroom"]["P_pair"]["numerator"]),
                    int(primary["field_courtroom"]["P_pair"]["denominator"]),
                ))
                / float(Fraction(
                    int(primary["field_courtroom"]["m_over_p2"]["numerator"]),
                    int(primary["field_courtroom"]["m_over_p2"]["denominator"]),
                )),
                ".6f",
            ),
            "num_mod_DELTA": str(int(primary["field_courtroom"]["residue_over_p2"]["numerator"]) % DELTA),
            "classification": "point-specific structure; not shared mask; not d",
        },
        "gained_ground": [
            "decimal stitch found carry mechanism",
            "x.(y/p) corrected the gauge",
            "0.x_y base-p packet corrected coordinate witness",
            "curve wrap m aligned missing term under p²",
            "residue scans proved point-specific not scalar-transferable",
        ],
        "next_lanes_open": [
            "A: carry as gate around candidate equations",
            "B: RSZ s*k = z + r*d mod N",
            "C: field-native packets vs RSZ r/s/z/k maps",
        ],
        "ruling": "Residue is evidence of structure, not evidence of extraction. Bring in RSZ.",
        "judge_popcorn": "The residue is dismissed as suspect, but retained as a witness. Bring in RSZ.",
    }

    json_path = OUT / "ledger.json"
    json_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")

    md = f"""# P135 local courtroom ledger

Single puzzle courtroom. Every object under the correct roof.

## Status

```text
UNSOLVED · pubkey exposed · RSZ from hashkeys partial spend
Residue lane: CLOSED (witness only, not extractor)
```

## Identity

| Field | Value |
|-------|-------|
| address | `{e.address}` |
| d-window | `[2^134, 2^135)` |
| N-mirror | `[N-2^135+1, N-2^134]` |

## Pubkey (field roof /p)

```text
Px / p  = {over_p(px)['value'][:50]}...
Py / p  = {over_p(py)['value'][:50]}...
(p−y)/p = {over_p(pmy)['value'][:50]}...
```

## Field-native packet (primary: p−y)

```text
P_pair     = (x*p + y) / p²  = 0.x_y in base p
m / p²     = curve wrap limb
residue/p² = (x*p + y − m) / p²

P_pair   ≈ {primary['field_courtroom']['P_pair']['value'][:55]}...
m/p²     ≈ {primary['field_courtroom']['m_over_p2']['value'][:55]}...
residue  ≈ {primary['field_courtroom']['residue_over_p2']['value'][:55]}...
ratio    ≈ {ledger['residue_summary']['ratio_P_pair_to_wrap']}
```

## Carry (admitted fact)

```text
carry_y   = {ledger['carry_summary']['pubkey_y']}
carry_pmy = {ledger['carry_summary']['pubkey_pmy']}
threshold = (N*x mod p) + y >= p
```

## RSZ (scalar roof /N)

```text
s*k ≡ z + r*d (mod N)

r/N = {over_n(r % N)['value'][:50]}...
s/N = {over_n(s % N)['value'][:50]}...
z/N = {over_n(z % N)['value'][:50]}...
k   = unknown
```

## Λ bridges

```text
Λ  = Px3/rx3 mod p  verified={ledger['lambda_bridges']['LAMBDA']['verified']}
Λ1 = Px3/rx2 mod p  verified={ledger['lambda_bridges']['LAMBDA1']['verified']}
Λ/Λ1 = β² mod p      verified={ledger['lambda_bridges']['LAMBDA_over_LAMBDA1_eq_BETA_SQ']}
```

## β-slots

**Px:** Px1, Px2, Px3 — see `ledger.json` → `beta_Px_slots`  
**rx:** rx1, rx2, rx3 — rx3 = rx2·β — see `beta_rx_slots`

## Residue classification (filed)

```text
field-native packet:     factual
curve wrap m:            factual
pair-minus-wrap:         factual
num mod p = (y−m) mod p: factual
residue as d:            no
shared fingerprint:      no
offset class mask:       no
```

## Ruling

```text
Residue is evidence of structure, not extraction.
Next open lane: RSZ — s*k = z + r*d mod N
```

Judge Popcorn: **The residue is dismissed as suspect, but retained as a witness. Bring in RSZ.**
"""

    md_path = OUT / "index.md"
    md_path.write_text(md, encoding="utf-8")

    manifest = {
        "folder": "ARCHIVE/briefcase/The Real Decimal/P135/",
        "puzzle": 135,
        "files": ["ledger.json", "index.md"],
        "build": "python build_p135_ledger.py",
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"carry y/pmy: {ledger['carry_summary']['pubkey_y']}/{ledger['carry_summary']['pubkey_pmy']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
