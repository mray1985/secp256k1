#!/usr/bin/env python3
"""
K-20260710-02 — RFC6979 deterministic nonce identification.

Preregistered before eval.
k_det = RFC6979_HMAC_SHA256(d, z)
match iff k_det in {k, N-k}
Results separated by source. No post-failure encoding variants.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
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
OUT = OUT_DIR / "K-20260710-02_rfc6979_result.txt"
OUT_JSON = OUT_DIR / "K-20260710-02_rfc6979_result.json"
PREREG_MD = OUT_DIR / "prereg" / "K-20260710-02_rfc6979.md"
LEDGER = ARCHIVE / "LEDGER_K02_RFC6979.md"


def int2octets32(x: int) -> bytes:
    """32-byte big-endian (secp256k1 scalar / hash width)."""
    return (x % (1 << 256)).to_bytes(32, "big")


def rfc6979_k(d: int, z: int) -> int:
    """
    Locked procedure:
      d as numeric secexp
      data = 32-byte BE of z (panel sighash integer; width 256)
      hash_func = SHA-256
      no extra_entropy
    python-ecdsa applies bits2octets internally per RFC6979.
    """
    return rfc6979.generate_k(
        N_ORDER,
        d % N_ORDER,
        hashlib.sha256,
        int2octets32(z),
        extra_entropy=b"",
    )


def is_match(k: int, k_det: int) -> bool:
    k %= N_ORDER
    k_det %= N_ORDER
    return k_det == k or k_det == (N_ORDER - k) % N_ORDER


def main() -> None:
    prereg = load_prereg("K-20260710-02")
    prereg.assert_ready()
    print(f"Prereg LOCKED: {prereg.candidate_id} — {prereg.short_name}")
    print(f"Formula: {prereg.formula}")
    print()

    panel = json.loads(PANEL.read_text(encoding="utf-8"))
    rsz = json.loads(RSZ.read_text(encoding="utf-8"))

    rows_out = []
    by_source = defaultdict(list)
    for row in panel:
        n = int(row["puzzle"])
        d, k, z = int(row["d"]), int(row["k"]), int(row["z"])
        rec = rsz.get(str(n)) or {}
        source = rec.get("source") or "unknown"
        k_det = rfc6979_k(d, z)
        matched = is_match(k, k_det)
        item = {
            "puzzle": n,
            "source": source,
            "match": matched,
            "k_det": k_det,
            "k": k,
            "matched_as": (
                "k"
                if k_det == k % N_ORDER
                else ("N-k" if k_det == (N_ORDER - k) % N_ORDER else None)
            ),
        }
        rows_out.append(item)
        by_source[source].append(item)

    n_all = len(rows_out)
    n_match = sum(1 for r in rows_out if r["match"])
    print(f"Overall: {n_match}/{n_all} exact RFC6979 matches")
    print()
    print("By source:")
    source_stats = {}
    for src, items in sorted(by_source.items()):
        m = sum(1 for x in items if x["match"])
        source_stats[src] = {"n": len(items), "matches": m, "rate": m / len(items)}
        print(f"  {src}: {m}/{len(items)} ({100*m/len(items):.1f}%)")
        if m:
            print("    matched puzzles:", [x["puzzle"] for x in items if x["match"]])

    # era descriptive only
    def era(n: int) -> str:
        if n <= 50:
            return "early"
        if n <= 100:
            return "mid"
        return "late"

    by_era = defaultdict(list)
    for r in rows_out:
        by_era[era(r["puzzle"])].append(r)
    print()
    print("By era_proxy (descriptive):")
    era_stats = {}
    for e, items in sorted(by_era.items()):
        m = sum(1 for x in items if x["match"])
        era_stats[e] = {"n": len(items), "matches": m, "rate": m / len(items)}
        print(f"  {e}: {m}/{len(items)}")

    # Interpretation per prereg
    if n_match == 0:
        verdict = "FAIL"
        interpretation = (
            "Zero exact matches: exact RFC6979(d,z) hypothesis fails on this panel. "
            "Do not tune encodings/entropy after looking."
        )
    elif n_match <= 2:
        verdict = "FAIL"
        interpretation = (
            f"Isolated matches only ({n_match}): treat as chance/edge cases, not a process. "
            "Do not tune after looking."
        )
    else:
        # many matches? check concentration in one source
        concentrated = [
            (s, st) for s, st in source_stats.items() if st["matches"] >= 5 and st["rate"] >= 0.5
        ]
        if concentrated:
            verdict = "ATTRIBUTION"
            interpretation = (
                "Many exact matches concentrated in source(s): "
                + ", ".join(s for s, _ in concentrated)
                + ". Those spends likely used RFC6979. Signer attribution only — "
                "not transferable to P135 unless P135 shares that signer."
            )
        else:
            verdict = "MIXED"
            interpretation = (
                "Mixed/scattered matches across sources. Split by signer/source; "
                "do not treat 82 rows as one process. Not a P135 nonce sieve."
            )

    print()
    print(f"VERDICT: {verdict}")
    print(interpretation)
    print()
    print("Boundary: No universal empirical k-rule may be transferred")
    print("from heterogeneous puzzle spends to P135.")

    payload = {
        "candidate_id": "K-20260710-02",
        "boundary": (
            "No universal empirical k-rule may be transferred from "
            "heterogeneous puzzle spends to P135."
        ),
        "overall": {"matches": n_match, "n": n_all, "rate": n_match / n_all},
        "by_source": source_stats,
        "by_era": era_stats,
        "matched_puzzles": [r["puzzle"] for r in rows_out if r["match"]],
        "verdict": verdict,
        "interpretation": interpretation,
        "procedure": {
            "lib": "ecdsa.rfc6979.generate_k",
            "hash": "SHA-256",
            "d": "numeric secexp mod N",
            "z_data": "32-byte big-endian of z mod 2^256",
            "extra_entropy": "",
            "match_orbit": "{k, N-k}",
        },
    }

    text_lines = [
        "K-20260710-02 RFC6979 deterministic generator identification",
        f"overall: {n_match}/{n_all}",
        f"by_source: {json.dumps(source_stats)}",
        f"VERDICT: {verdict}",
        interpretation,
        "",
        json.dumps(payload, indent=2),
    ]
    text = "\n".join(text_lines)
    OUT.write_text(text, encoding="utf-8")
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (ARCHIVE / OUT.name).write_text(text, encoding="utf-8")
    (ARCHIVE / OUT_JSON.name).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    block = f"""
## Result (evaluated {date.today().isoformat()})

| Metric | Value |
|--------|------:|
| matches overall | {n_match}/{n_all} |
| matches blockstream | {source_stats.get('blockstream spend tx', {}).get('matches', 0)}/{source_stats.get('blockstream spend tx', {}).get('n', 0)} |
| matches hashkeys | {source_stats.get('hashkeys.space partial spend', {}).get('matches', 0)}/{source_stats.get('hashkeys.space partial spend', {}).get('n', 0)} |
| Verdict | {verdict} |

{interpretation}

Matched puzzles: {payload['matched_puzzles']}
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

    ledger = f"""# Ledger: K-02 RFC6979 identification

## Strategic boundary

> A nonce pattern from solved-puzzle spending transactions describes the
> **people/software that spent those coins**, not necessarily the creator of
> the puzzle set.

$$
\\boxed{{\\text{{No universal empirical }}k\\text{{-rule may be transferred from heterogeneous puzzle spends to P135.}}}}
$$

## K-01 reminder

Byte-bin clustering FALSIFIED (holdout ≈ random).

## K-02 result ({date.today().isoformat()})

Exact RFC6979_SHA256(d,z) with match in {{k, N-k}}.

| | |
|--|--|
| overall | **{n_match}/{n_all}** |
| blockstream | {source_stats.get('blockstream spend tx', {})} |
| hashkeys | {source_stats.get('hashkeys.space partial spend', {})} |
| **Verdict** | **{verdict}** |

{interpretation}

Even success would be **signer attribution**, not key recovery for P135, unless
the P135 signature shares that signing process.

Artifacts: `K-20260710-02_rfc6979_result.*`, `k02_rfc6979_id.py`.
"""
    LEDGER.write_text(ledger, encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Wrote {LEDGER}")


if __name__ == "__main__":
    main()
