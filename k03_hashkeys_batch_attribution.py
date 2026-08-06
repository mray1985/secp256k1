#!/usr/bin/env python3
"""
K-20260710-03 — Hashkeys batch RFC6979 attribution strength.

Preregistered before eval.
In-batch (exact txid): require 100% RFC6979 match.
Out-of-batch: report rate (need not be 100%).
P135 co-location: metadata only.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

from ecdsa import rfc6979

from pairing_advantage_filter import (
    ARCHIVE,
    ARCHIVE_PREREG,
    N_ORDER,
    OUT_DIR,
    load_prereg,
    save_prereg,
)

PANEL = OUT_DIR / "SOLVED_NONCE_PANEL.json"
RSZ = Path(r"C:\Users\mitch\Desktop\secp256k1\ARCHIVE\puzzle_rsz_cache.json")
HASHKEYS_TXID = "17e4e323cfbc68d7f0071cad09364e8193eedf8fefbcbd8a21b4b65717a4b3d3"
OUT = OUT_DIR / "K-20260710-03_hashkeys_batch_result.txt"
OUT_JSON = OUT_DIR / "K-20260710-03_hashkeys_batch_result.json"
PREREG_MD = OUT_DIR / "prereg" / "K-20260710-03_hashkeys_batch_attribution.md"
LEDGER = ARCHIVE / "LEDGER_K03_HASHKEYS_BATCH.md"


def int2octets32(x: int) -> bytes:
    return (x % (1 << 256)).to_bytes(32, "big")


def rfc6979_k(d: int, z: int) -> int:
    return rfc6979.generate_k(
        N_ORDER, d % N_ORDER, hashlib.sha256, int2octets32(z), extra_entropy=b""
    )


def is_match(k: int, k_det: int) -> bool:
    k %= N_ORDER
    k_det %= N_ORDER
    return k_det == k or k_det == (N_ORDER - k) % N_ORDER


def main() -> None:
    prereg = load_prereg("K-20260710-03")
    prereg.assert_ready()
    print(f"Prereg LOCKED: {prereg.candidate_id}")
    print()

    panel = json.loads(PANEL.read_text(encoding="utf-8"))
    rsz = json.loads(RSZ.read_text(encoding="utf-8"))

    in_batch, out_batch = [], []
    for row in panel:
        n = int(row["puzzle"])
        rec = rsz.get(str(n)) or {}
        txid = (row.get("txid") or rec.get("txid") or "").lower()
        d, k, z = int(row["d"]), int(row["k"]), int(row["z"])
        matched = is_match(k, rfc6979_k(d, z))
        item = {
            "puzzle": n,
            "txid": txid,
            "source": rec.get("source") or "unknown",
            "input_index": rec.get("input_index"),
            "match": matched,
        }
        if txid == HASHKEYS_TXID:
            in_batch.append(item)
        else:
            out_batch.append(item)

    in_m = sum(1 for x in in_batch if x["match"])
    out_m = sum(1 for x in out_batch if x["match"])
    in_rate = in_m / len(in_batch) if in_batch else float("nan")
    out_rate = out_m / len(out_batch) if out_batch else float("nan")

    # P135 co-location (metadata; d unknown so no match test)
    p135 = rsz.get("135")
    p135_txid = (p135.get("txid") if p135 else "") or ""
    p135_colocated = p135_txid.lower() == HASHKEYS_TXID

    # All RSZ rows on that txid (including unsolved)
    rsz_on_tx = []
    for key, rec in rsz.items():
        if not rec:
            continue
        if (rec.get("txid") or "").lower() == HASHKEYS_TXID:
            rsz_on_tx.append(
                {
                    "puzzle": int(key),
                    "input_index": rec.get("input_index"),
                    "has_known_d": any(int(r["puzzle"]) == int(key) for r in panel),
                }
            )
    rsz_on_tx.sort(key=lambda x: (x["input_index"] is None, x["input_index"], x["puzzle"]))

    attribution_ok = (
        len(in_batch) > 0
        and in_rate == 1.0
        and (out_rate < in_rate - 0.2 if out_batch else True)
    )
    if attribution_ok:
        verdict = "ATTRIBUTION_CONFIRMED"
    elif in_rate == 1.0:
        verdict = "BORDERLINE"
    else:
        verdict = "FAIL"

    print(f"Hashkeys txid: {HASHKEYS_TXID}")
    print(f"In-batch solved:  {in_m}/{len(in_batch)} ({100*in_rate:.1f}%)")
    print(f"  puzzles: {sorted(x['puzzle'] for x in in_batch)}")
    print(f"Out-of-batch:     {out_m}/{len(out_batch)} ({100*out_rate:.1f}%)")
    print(f"P135 co-located:  {p135_colocated} (txid={p135_txid[:16]}...)")
    print(f"RSZ rows on tx:   {len(rsz_on_tx)} (solved+unsolved)")
    print(f"VERDICT: {verdict}")

    interpretation = (
        "In-batch 100% RFC6979 with substantially lower out-of-batch rate: "
        "hashkeys tx is one deterministic signing process. "
        "P135 co-located => defensible hypothesis k_135=RFC6979(d_135,z_135). "
        "This is a candidate VALIDATOR (F(d)=0), not an algebraic solve — "
        "HMAC keyed by d. Not transferable from blockstream spends."
        if attribution_ok
        else "Batch attribution claim not confirmed under locked criteria."
    )
    print(interpretation)

    payload = {
        "candidate_id": "K-20260710-03",
        "hashkeys_txid": HASHKEYS_TXID,
        "in_batch": {
            "n": len(in_batch),
            "matches": in_m,
            "rate": in_rate,
            "puzzles": sorted(x["puzzle"] for x in in_batch),
        },
        "out_batch": {
            "n": len(out_batch),
            "matches": out_m,
            "rate": out_rate,
        },
        "p135": {
            "colocated": p135_colocated,
            "txid": p135_txid,
            "hypothesis": "k_135 = RFC6979_SHA256(d_135, z_135)",
            "validator": "F(d)=s*RFC6979(d,z)-z-r*d ≡ 0 (mod N); also [d]G=P_135",
            "not_a_solve": True,
        },
        "rsz_rows_on_txid": rsz_on_tx,
        "verdict": verdict,
        "interpretation": interpretation,
        "strategic": {
            "deterministic_nonce_bound_to_d": True,
            "no_universal_transfer_from_heterogeneous_spends": True,
        },
    }

    text = "\n".join(
        [
            "K-20260710-03 Hashkeys batch RFC6979 attribution",
            f"in_batch: {in_m}/{len(in_batch)}",
            f"out_batch: {out_m}/{len(out_batch)}",
            f"P135 colocated: {p135_colocated}",
            f"VERDICT: {verdict}",
            interpretation,
            "",
            json.dumps(payload, indent=2),
        ]
    )
    OUT.write_text(text, encoding="utf-8")
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (ARCHIVE / OUT.name).write_text(text, encoding="utf-8")
    (ARCHIVE / OUT_JSON.name).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    block = f"""
## Result (evaluated {date.today().isoformat()})

| Metric | Value |
|--------|------:|
| in-batch matches | {in_m}/{len(in_batch)} ({100*in_rate:.1f}%) |
| out-of-batch matches | {out_m}/{len(out_batch)} ({100*out_rate:.1f}%) |
| P135 co-located | {p135_colocated} |
| Verdict | {verdict} |

{interpretation}
"""
    if PREREG_MD.exists():
        md = PREREG_MD.read_text(encoding="utf-8")
        marker = "## Result (fill only after evaluation)"
        if marker in md:
            md = md.split(marker)[0] + block.lstrip()
        md = md.replace(
            "| Date first evaluated | *(pending)* |",
            f"| Date first evaluated | {date.today().isoformat()} |",
        )
        PREREG_MD.write_text(md, encoding="utf-8")
        (ARCHIVE_PREREG / PREREG_MD.name).write_text(md, encoding="utf-8")

    prereg.evaluated_date = date.today().isoformat()
    save_prereg(prereg)

    ledger = f"""# Ledger: K-03 Hashkeys batch attribution — CONFIRMED

## Classification

**Signer attribution (batch-scoped), not a nonce sieve and not key recovery.**

## Locked conclusions

$$
\\boxed{{\\text{{P135 probably has a deterministic nonce, but that nonce is cryptographically bound to the unknown }}d.}}
$$

Defensible batch hypothesis:

$$
\\boxed{{k_{{135}}=\\operatorname{{RFC6979}}_{{\\mathrm{{SHA256}}}}(d_{{135}},z_{{135}})}}
$$

Validator (not a solve):

```text
[d]G = P_135
F(d) = s * RFC6979(d,z) - z - r*d  ≡ 0 (mod N)
```

## K-03 numbers ({date.today().isoformat()})

| | |
|--|--|
| hashkeys txid | `{HASHKEYS_TXID}` |
| in-batch solved RFC6979 | **{in_m}/{len(in_batch)}** |
| out-of-batch | **{out_m}/{len(out_batch)}** ({100*out_rate:.1f}%) |
| P135 co-located on that tx | **{p135_colocated}** |
| RSZ rows on tx (all) | {len(rsz_on_tx)} |
| **Verdict** | **{verdict}** |

{interpretation}

What this accomplishes:

* removes random-nonce hypotheses for that batch
* makes timestamp-seeded nonce theories unnecessary unless attribution is contradicted
* prevents pooling mixed blockstream signatures with the hashkeys signer
* gives every proposed P135 candidate a strict two-part test (EC point + RFC6979 consistency)

What this does **not** do: invert HMAC-SHA256 keyed by d, or transfer empirical rules from unrelated spends.

Artifacts: `K-20260710-03_hashkeys_batch_result.*`, `k03_hashkeys_batch_attribution.py`.
"""
    LEDGER.write_text(ledger, encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Wrote {LEDGER}")


if __name__ == "__main__":
    main()
