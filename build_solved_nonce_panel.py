#!/usr/bin/env python3
"""
Build solved ECDSA nonce panel: (d, k, r, s, z, P) for puzzles with known d + RSZ.

k = (z + r*d) * s^{-1}  mod N
Verified by [k]G.x ≡ ±r (mod N).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from ecdsa import SECP256k1

from pairing_advantage_filter import N_ORDER, pub_xy

ROOT = Path(r"C:\Users\mitch\Desktop\secp256k1")
RSZ = ROOT / "ARCHIVE" / "puzzle_rsz_cache.json"
KEYS = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT_JSON = ROOT / "logs" / "SOLVED_NONCE_PANEL.json"
OUT_CSV = ROOT / "logs" / "SOLVED_NONCE_PANEL.csv"
OUT_MD = ROOT / "logs" / "K_CONSTRAINT_LAB.md"
ARCHIVE = ROOT / "ARCHIVE" / "briefcase" / "factoradic_native_lead_falsified"
G = SECP256k1.generator


def verify_k(k: int, r: int) -> bool:
    R = (k % N_ORDER) * G
    rx = int(R.x()) % N_ORDER
    rr = r % N_ORDER
    return rx == rr or (N_ORDER - rx) % N_ORDER == rr


def main() -> None:
    rsz = json.loads(RSZ.read_text(encoding="utf-8"))
    keys = {}
    with KEYS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            keys[int(row["puzzle"])] = int(row["private_key"])

    rows = []
    for n, d in sorted(keys.items()):
        rec = rsz.get(str(n))
        if not rec:
            continue
        r, s, z = int(rec["r"]), int(rec["s"]), int(rec["z"])
        k = ((z + r * d) * pow(s, -1, N_ORDER)) % N_ORDER
        ok = verify_k(k, r)
        px, py = pub_xy(d)
        rows.append(
            {
                "puzzle": n,
                "d": d,
                "k": k,
                "r": r,
                "s": s,
                "z": z,
                "px": px,
                "py": py,
                "pub_compressed": rec.get("pub_compressed", ""),
                "txid": rec.get("txid", ""),
                "k_verifies": ok,
                "k_bit_length": k.bit_length(),
                "d_bit_length": d.bit_length(),
            }
        )

    n_ok = sum(1 for x in rows if x["k_verifies"])
    print(f"Solved nonce panel: {len(rows)} rows, k verifies: {n_ok}/{len(rows)}")

    OUT_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "puzzle",
            "d",
            "k",
            "r",
            "s",
            "z",
            "px",
            "py",
            "pub_compressed",
            "txid",
            "k_verifies",
            "k_bit_length",
            "d_bit_length",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)

    # holdout suggestion: chronological by puzzle n
    train = [x for x in rows if x["puzzle"] <= 50]
    test = [x for x in rows if x["puzzle"] > 50]
    bits = [x["k_bit_length"] for x in rows]

    lab = f"""# K-constraint laboratory

**Strategic pivot** (after F-06):

> Stop asking coordinates to resemble d; start testing constraints on k inside ECDSA.

## Identity

```text
s*k ≡ z + r*d  (mod N)
k ≡ (z + r*d) * s^{{-1}}  (mod N)
```

## Panel

| | |
|--|--|
| Source RSZ | `ARCHIVE/puzzle_rsz_cache.json` |
| Known keys | `factoradic_private_keys.csv` |
| Panel | `logs/SOLVED_NONCE_PANEL.{{json,csv}}` |
| Rows | **{len(rows)}** solved spends with known d |
| k verifies vs r | **{n_ok}/{len(rows)}** |

Suggested holdout: train puzzles n<=50 ({len(train)}), test n>50 ({len(test)}).

k bit-length: min={min(bits)}, median={sorted(bits)[len(bits)//2]}, max={max(bits)}.

## Promotion gate for a nonce rule R

A candidate constraint R (predicate / sieve on observables that may involve r,s,z,P,
and optionally hypothesized structure on k) promotes only if on **held-out** solved
signatures:

```text
retention of true k = 100%
surviving candidates / N  << 1
```

Also require:

* preregistration before peeking (`logs/prereg/K_CONSTRAINT_PREREG_TEMPLATE.md`)
* not DL recomputation of known d
* not vacuous curve membership
* shuffle / random-signature nulls where applicable
* same direction on train and holdout reduction factors

## What this lab is for

Calibrate constraints that **retain true historical nonces** while shrinking the
candidate set — then ask whether the same rule narrows Puzzle 135's equation
without claiming a solve from coordinate resemblance.

## Closed (do not reopen)

Coordinate-similarity branches F-01…F-06 (factoradic, offsets, doubling, GLV argmin MI,
adjacent Hamming). See archive ledgers under
`ARCHIVE/briefcase/factoradic_native_lead_falsified/`.
"""
    OUT_MD.write_text(lab, encoding="utf-8")
    (ARCHIVE / "SOLVED_NONCE_PANEL.json").write_text(OUT_JSON.read_text(encoding="utf-8"), encoding="utf-8")
    (ARCHIVE / "SOLVED_NONCE_PANEL.csv").write_text(OUT_CSV.read_text(encoding="utf-8"), encoding="utf-8")
    (ARCHIVE / "K_CONSTRAINT_LAB.md").write_text(lab, encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
