#!/usr/bin/env python3
"""
G-20260710-01 — Creator-side 64-bit LCG on five-step chain.

Preregistered before eval.
u = d - 2^{n-1}
w = floor(2^{64} * u / 2^{n-1})
w_{n+5} ≡ a*w_n + c (mod 2^{64})
Infer a,c from 75,80,85; exact predict 90..130.
"""
from __future__ import annotations

import csv
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
MOD = 1 << 64
CHAIN = list(range(75, 131, 5))  # 75..130 step 5
INFER = [75, 80, 85]
HOLDOUT = list(range(90, 131, 5))
OUT = OUT_DIR / "G-20260710-01_creator_lcg64_result.txt"
OUT_JSON = OUT_DIR / "G-20260710-01_creator_lcg64_result.json"
PREREG_MD = OUT_DIR / "prereg" / "G-20260710-01_creator_lcg64.md"
LEDGER = ARCHIVE / "LEDGER_G01_CREATOR_LCG64.md"


def inv_odd_mod_2k(a: int, k: int = 64) -> int | None:
    """Modular inverse mod 2^k exists iff a is odd."""
    a %= 1 << k
    if a % 2 == 0:
        return None
    return pow(a, -1, 1 << k)


def load_keys() -> dict[int, int]:
    keys = {}
    with KEYS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            keys[int(row["puzzle"])] = int(row["private_key"])
    return keys


def band_u(d: int, n: int) -> int:
    return d - (1 << (n - 1))


def w_of(d: int, n: int) -> int:
    """Locked: floor(2^{64} * u / 2^{n-1})."""
    u = band_u(d, n)
    shift = n - 1  # band width exponent
    # floor(2^{64} * u / 2^{shift}) = floor(u * 2^{64-shift}) or u >> (shift-64)
    if shift <= 64:
        return u << (64 - shift)
    return u >> (shift - 64)


def main() -> None:
    prereg = load_prereg("G-20260710-01")
    prereg.assert_ready()
    print(f"Prereg LOCKED: {prereg.candidate_id} — {prereg.short_name}")
    print()

    keys = load_keys()
    for n in CHAIN:
        if n not in keys:
            raise SystemExit(f"Missing key for puzzle {n}")

    ws = {n: w_of(keys[n], n) for n in CHAIN}
    us = {n: band_u(keys[n], n) for n in CHAIN}

    print("w_n (locked 64-bit band location):")
    for n in CHAIN:
        print(f"  n={n:3d}  w=0x{ws[n]:016x}  ({ws[n]})")

    w75, w80, w85 = ws[75], ws[80], ws[85]
    denom = (w80 - w75) % MOD
    inv = inv_odd_mod_2k(denom, 64)
    if inv is None:
        verdict = "FAIL"
        reason = (
            f"(w_80 - w_75) = {denom} is even => not invertible mod 2^64. "
            "Locked LCG hypothesis fails immediately (no alternate modulus)."
        )
        a = c = None
        holdout_results = []
        print(reason)
        print(f"VERDICT: {verdict}")
        payload = {
            "candidate_id": "G-20260710-01",
            "question": "Do the normalized puzzle payloads follow a fixed creator-side recurrence?",
            "verdict": verdict,
            "reason": reason,
            "w": {str(n): ws[n] for n in CHAIN},
            "u": {str(n): us[n] for n in CHAIN},
            "w80_minus_w75": denom,
            "holdout_matches": 0,
            "holdout_total": len(HOLDOUT),
            "w_135_pred": None,
            "keyspace_note": "Branch closed at inference; no keyspace reduction.",
        }
    else:
        a = ((w85 - w80) % MOD) * inv % MOD
        c = (w80 - a * w75) % MOD
        # sanity: reproduce w85 from w80
        check85 = (a * w80 + c) % MOD
        print()
        print(f"Inferred a = 0x{a:016x}")
        print(f"Inferred c = 0x{c:016x}")
        print(f"Check a*w80+c == w85: {check85 == w85}")

        holdout_results = []
        all_ok = True
        print()
        print("Holdout predictions (exact):")
        for n in HOLDOUT:
            prev = n - 5
            pred = (a * ws[prev] + c) % MOD
            actual = ws[n]
            ok = pred == actual
            all_ok = all_ok and ok
            holdout_results.append(
                {"n": n, "pred": pred, "actual": actual, "match": ok}
            )
            mark = "OK" if ok else "MISS"
            print(f"  n={n}: pred=0x{pred:016x} actual=0x{actual:016x} [{mark}]")

        n_ok = sum(1 for h in holdout_results if h["match"])
        if all_ok and check85 == w85:
            verdict = "PROMOTE"
            reason = (
                f"All {n_ok}/{len(HOLDOUT)} holdout predictions exact. "
                "Predict w_135 for top-64 bits of 134-bit payload."
            )
            # w_135 from w_130
            w135 = (a * ws[130] + c) % MOD
        else:
            verdict = "FAIL"
            reason = (
                f"Holdout exact matches {n_ok}/{len(HOLDOUT)}. "
                "One miss closes the 64-bit normalized LCG branch."
            )
            w135 = None

        print()
        print(f"VERDICT: {verdict}")
        print(reason)
        if w135 is not None:
            print(f"w_135 prediction = 0x{w135:016x}")

        payload = {
            "candidate_id": "G-20260710-01",
            "question": "Do the normalized puzzle payloads follow a fixed creator-side recurrence?",
            "a": a,
            "c": c,
            "a_hex": f"0x{a:016x}",
            "c_hex": f"0x{c:016x}",
            "w": {str(n): ws[n] for n in CHAIN},
            "u": {str(n): us[n] for n in CHAIN},
            "holdout": holdout_results,
            "holdout_matches": n_ok,
            "holdout_total": len(HOLDOUT),
            "w_135_pred": w135,
            "verdict": verdict,
            "reason": reason,
            "keyspace_note": (
                "If promoted: top 64 bits of 134-bit payload fixed ⇒ ~2^70 remaining"
                if verdict == "PROMOTE"
                else "Branch closed; no keyspace reduction from this LCG."
            ),
        }

    text = "\n".join(
        [
            "G-20260710-01 Creator-side 64-bit LCG",
            f"VERDICT: {payload['verdict']}",
            payload.get("reason", ""),
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
| a, c | {payload.get('a_hex', 'n/a')}, {payload.get('c_hex', 'n/a')} |
| holdout exact matches | {payload.get('holdout_matches', 0)}/{payload.get('holdout_total', 9)} |
| Verdict | {payload['verdict']} |
| w_135 (if promoted) | {payload.get('w_135_pred')} |

{payload.get('reason', '')}
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

    ledger = f"""# Ledger: G-01 Creator-side 64-bit LCG

## Question

$$
\\boxed{{\\text{{Do the normalized puzzle payloads follow a fixed creator-side recurrence?}}}}
$$

## Result

**Verdict: {payload['verdict']}**

{payload.get('reason', '')}

| | |
|--|--|
| chain | n=75,80,...,130 |
| infer | w75,w80,w85 → (a,c) |
| holdout | {payload.get('holdout_matches', 0)}/{payload.get('holdout_total', 9)} exact |
| a | {payload.get('a_hex', 'n/a')} |
| c | {payload.get('c_hex', 'n/a')} |

Promotion required every holdout prediction exact. One miss closes this branch.
No width/modulus/encoding reopen.

Artifacts: `G-20260710-01_creator_lcg64_result.*`, `g01_creator_lcg64.py`.
"""
    LEDGER.write_text(ledger, encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Wrote {LEDGER}")


if __name__ == "__main__":
    main()
