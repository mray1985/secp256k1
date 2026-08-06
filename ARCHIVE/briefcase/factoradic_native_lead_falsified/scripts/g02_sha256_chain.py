#!/usr/bin/env python3
"""
G-20260710-02 — SHA-256 chained puzzle keys.

Preregistered before eval.
h = SHA256(int32be(d_n))
u_hat = int(h) mod 2^{n+4}
d_hat = 2^{n+4} + u_hat
Exact: d_hat == d_{n+5}
One miss closes.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import date
from pathlib import Path

from pairing_advantage_filter import (
    ARCHIVE,
    ARCHIVE_PREREG,
    OUT_DIR,
    load_prereg,
    save_prereg,
)

KEYS = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
CHAIN = list(range(75, 131, 5))
OUT = OUT_DIR / "G-20260710-02_sha256_chain_result.txt"
OUT_JSON = OUT_DIR / "G-20260710-02_sha256_chain_result.json"
PREREG_MD = OUT_DIR / "prereg" / "G-20260710-02_sha256_chain.md"
LEDGER = ARCHIVE / "LEDGER_G02_SHA256_CHAIN.md"


def load_keys() -> dict[int, int]:
    keys = {}
    with KEYS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            keys[int(row["puzzle"])] = int(row["private_key"])
    return keys


def int32be(d: int) -> bytes:
    """Exactly 32-byte big-endian, zero-padded."""
    return d.to_bytes(32, "big")


def predict_next(d_n: int, n: int) -> int:
    """d_hat_{n+5} = 2^{n+4} + (SHA256(int32be(d_n)) as int mod 2^{n+4})."""
    h = hashlib.sha256(int32be(d_n)).digest()
    h_int = int.from_bytes(h, "big")
    u_hat = h_int % (1 << (n + 4))
    return (1 << (n + 4)) + u_hat


def main() -> None:
    prereg = load_prereg("G-20260710-02")
    prereg.assert_ready()
    print(f"Prereg LOCKED: {prereg.candidate_id} — {prereg.short_name}")
    print()

    keys = load_keys()
    for n in CHAIN:
        if n not in keys:
            raise SystemExit(f"Missing key for puzzle {n}")

    edges = []
    first_miss = None
    for n in CHAIN[:-1]:
        nxt = n + 5
        pred = predict_next(keys[n], n)
        actual = keys[nxt]
        ok = pred == actual
        edges.append(
            {
                "n": n,
                "n_next": nxt,
                "pred": pred,
                "actual": actual,
                "match": ok,
            }
        )
        mark = "OK" if ok else "MISS"
        print(f"  {n}->{nxt}: [{mark}]")
        if not ok and first_miss is None:
            first_miss = {"n": n, "n_next": nxt, "pred": pred, "actual": actual}

    n_ok = sum(1 for e in edges if e["match"])
    n_tot = len(edges)
    if n_ok == n_tot:
        verdict = "PROMOTE"
        reason = (
            f"All {n_tot}/{n_tot} edges exact. Predict d_135 from d_130."
        )
        d135 = predict_next(keys[130], 130)
    else:
        verdict = "FAIL"
        reason = (
            f"Exact matches {n_ok}/{n_tot}. First miss at "
            f"{first_miss['n']}->{first_miss['n_next']}. "
            "One mismatch closes this exact SHA-256 chain hypothesis."
        )
        d135 = None

    print()
    print(f"VERDICT: {verdict}")
    print(reason)
    if d135 is not None:
        print(f"d_135 prediction = {d135}")

    payload = {
        "candidate_id": "G-20260710-02",
        "question": (
            "d_{n+5} ?= 2^{n+4} + (SHA256(int32be(d_n)) mod 2^{n+4})"
        ),
        "edges": [
            {
                "n": e["n"],
                "n_next": e["n_next"],
                "match": e["match"],
                "pred_hex": hex(e["pred"]),
                "actual_hex": hex(e["actual"]),
            }
            for e in edges
        ],
        "exact_matches": n_ok,
        "edges_total": n_tot,
        "first_miss": first_miss,
        "d_135_pred": d135,
        "verdict": verdict,
        "reason": reason,
        "g01_note": (
            "G-01 FALSIFIED: a*Delta1 ≡ Delta2 (mod 2^64) has no solution "
            "because gcd(Delta1,2^64)=2 does not divide odd Delta2."
        ),
    }

    text = "\n".join(
        [
            "G-20260710-02 SHA-256 chained puzzle keys",
            f"exact matches: {n_ok}/{n_tot}",
            f"VERDICT: {verdict}",
            reason,
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
| edges tested | {n_tot} |
| exact matches | {n_ok}/{n_tot} |
| first miss | {first_miss['n']}->{first_miss['n_next'] if first_miss else 'n/a'} |
| Verdict | {verdict} |

{reason}
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

    ledger = f"""# Ledger: G-02 SHA-256 chained puzzle keys — {verdict}

## Question

$$
\\boxed{{
d_{{n+5}}
\\stackrel{{?}}{{=}}
2^{{n+4}}
+
\\left(
\\operatorname{{SHA256}}(\\operatorname{{int32be}}(d_n))
\\bmod 2^{{n+4}}
\\right)
}}
$$

## Result

**Verdict: {verdict}**

{reason}

| | |
|--|--|
| edges | {n_ok}/{n_tot} exact |
| first miss | {first_miss} |
| encoding | 32-byte BE, SHA-256 once, low n+4 bits |

No approximate scores, byte-order, high-bits, hex, or alternate-hash reopen.

## G-01 reminder (precise)

G-01 FALSIFIED: \(a\\Delta_1\\equiv\\Delta_2\\pmod{{2^{{64}}}}\) has no solution because
\(\\gcd(\\Delta_1,2^{{64}})=2\) does not divide the odd right-hand side.

Artifacts: `G-20260710-02_sha256_chain_result.*`, `g02_sha256_chain.py`.
"""
    LEDGER.write_text(ledger, encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Wrote {LEDGER}")


if __name__ == "__main__":
    main()
