#!/usr/bin/env python3
"""
G-20260710-03 — Normalized payload serial-dependence gate (dCor).

Preregistered before eval.
q = (d - 2^{n-1}) / 2^{n-1}
S = dCor(q_t, q_{t+1})
Chains A=1..70 and B=75..130 step5 separately.
Permute q order for null. Promote only if p_perm<0.01 on BOTH.
"""
from __future__ import annotations

import csv
import json
import math
import random
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
B_PERM = 10000
RNG = random.Random(20260710)
P_MAX = 0.01
OUT = OUT_DIR / "G-20260710-03_serial_dcor_result.txt"
OUT_JSON = OUT_DIR / "G-20260710-03_serial_dcor_result.json"
PREREG_MD = OUT_DIR / "prereg" / "G-20260710-03_serial_dcor.md"
LEDGER = ARCHIVE / "LEDGER_G03_SERIAL_DCOR.md"


def load_keys() -> dict[int, int]:
    keys = {}
    with KEYS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            keys[int(row["puzzle"])] = int(row["private_key"])
    return keys


def q_of(d: int, n: int) -> float:
    """q = (d - 2^{n-1}) / 2^{n-1} in [0,1)."""
    band = 1 << (n - 1)
    return (d - band) / band


def distance_correlation(xs: list[float], ys: list[float]) -> float:
    """Empirical distance correlation (Székely–Rizzo–Bakirov)."""
    n = len(xs)
    if n < 3:
        return 0.0

    def dist_matrix(vals: list[float]) -> list[list[float]]:
        return [[abs(vals[i] - vals[j]) for j in range(n)] for i in range(n)]

    def center(A: list[list[float]]) -> list[list[float]]:
        row_mean = [sum(A[i]) / n for i in range(n)]
        col_mean = [sum(A[i][j] for i in range(n)) / n for j in range(n)]
        grand = sum(row_mean) / n
        return [
            [A[i][j] - row_mean[i] - col_mean[j] + grand for j in range(n)]
            for i in range(n)
        ]

    A = center(dist_matrix(xs))
    B = center(dist_matrix(ys))
    dcov2 = sum(A[i][j] * B[i][j] for i in range(n) for j in range(n)) / (n * n)
    dvarx = sum(A[i][j] * A[i][j] for i in range(n) for j in range(n)) / (n * n)
    dvary = sum(B[i][j] * B[i][j] for i in range(n) for j in range(n)) / (n * n)
    if dvarx <= 0.0 or dvary <= 0.0:
        return 0.0
    return math.sqrt(dcov2 / math.sqrt(dvarx * dvary))


def serial_dcor(qs: list[float]) -> float:
    """dCor on consecutive pairs (q_t, q_{t+1})."""
    if len(qs) < 3:
        return 0.0
    xs = qs[:-1]
    ys = qs[1:]
    return distance_correlation(xs, ys)


def perm_pvalue(qs: list[float], s_real: float, trials: int, rng: random.Random) -> tuple[float, float]:
    """Return (p_perm, p99 of null S)."""
    null = []
    for _ in range(trials):
        shuffled = list(qs)
        rng.shuffle(shuffled)
        null.append(serial_dcor(shuffled))
    null.sort()
    ge = sum(1 for s in null if s >= s_real)
    p = (ge + 1) / (trials + 1)
    p99 = null[int(0.99 * (trials - 1))]
    return p, p99


def main() -> None:
    prereg = load_prereg("G-20260710-03")
    prereg.assert_ready()
    print(f"Prereg LOCKED: {prereg.candidate_id} — {prereg.short_name}")
    print()

    keys = load_keys()

    # Chain A: 1..70 consecutive (only those present)
    chain_a_ns = [n for n in range(1, 71) if n in keys]
    qs_a = [q_of(keys[n], n) for n in chain_a_ns]

    # Chain B: 75,80,...,130
    chain_b_ns = list(range(75, 131, 5))
    for n in chain_b_ns:
        if n not in keys:
            raise SystemExit(f"Missing key for puzzle {n}")
    qs_b = [q_of(keys[n], n) for n in chain_b_ns]

    print(f"Chain A: n={chain_a_ns[0]}..{chain_a_ns[-1]}  len={len(qs_a)}  pairs={len(qs_a)-1}")
    print(f"Chain B: {chain_b_ns[0]}..{chain_b_ns[-1]} step5  len={len(qs_b)}  pairs={len(qs_b)-1}")
    print()

    results = {}
    for name, ns, qs in (("A_1_70", chain_a_ns, qs_a), ("B_75_130_step5", chain_b_ns, qs_b)):
        s_real = serial_dcor(qs)
        p_perm, p99 = perm_pvalue(qs, s_real, B_PERM, RNG)
        above_p99 = s_real > p99
        pass_gate = p_perm < P_MAX and above_p99
        results[name] = {
            "n_points": len(qs),
            "n_pairs": len(qs) - 1,
            "S_real": s_real,
            "p_perm": p_perm,
            "p99_null": p99,
            "above_p99": above_p99,
            "pass": pass_gate,
            "ns": ns,
        }
        print(f"{name}:")
        print(f"  S_real   = {s_real:.6f}")
        print(f"  p_perm   = {p_perm:.6f}")
        print(f"  p99_null = {p99:.6f}")
        print(f"  above p99: {above_p99}")
        print(f"  gate: {'PASS' if pass_gate else 'FAIL'}")
        print()

    both = results["A_1_70"]["pass"] and results["B_75_130_step5"]["pass"]
    if both:
        verdict = "PROMOTE"
        meaning = (
            "Serial dependence detected in BOTH chains. "
            "Predictive generator search is justified."
        )
    else:
        verdict = "FAIL"
        meaning = (
            "Solved payload locations behave like independently ordered draws "
            "at the detectable scale. Close invent-another-recurrence/hash cycle; "
            "prefer direct search-space engineering for Puzzle 135."
        )

    print(f"OVERALL VERDICT: {verdict}")
    print(meaning)

    payload = {
        "candidate_id": "G-20260710-03",
        "question": "Is there detectable serial dependence in normalized within-band payload locations?",
        "B_perm": B_PERM,
        "p_threshold": P_MAX,
        "chains": results,
        "both_pass": both,
        "verdict": verdict,
        "meaning": meaning,
        "boxed_if_fail": (
            "Solved payload locations behave like independently ordered draws at the detectable scale."
        ),
    }

    text = "\n".join(
        [
            "G-20260710-03 Normalized payload serial-dependence gate (dCor)",
            f"A: S={results['A_1_70']['S_real']:.6f} p={results['A_1_70']['p_perm']:.6f} "
            f"p99={results['A_1_70']['p99_null']:.6f} pass={results['A_1_70']['pass']}",
            f"B: S={results['B_75_130_step5']['S_real']:.6f} p={results['B_75_130_step5']['p_perm']:.6f} "
            f"p99={results['B_75_130_step5']['p99_null']:.6f} pass={results['B_75_130_step5']['pass']}",
            f"VERDICT: {verdict}",
            meaning,
            "",
            json.dumps(payload, indent=2),
        ]
    )
    OUT.write_text(text, encoding="utf-8")
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (ARCHIVE / OUT.name).write_text(text, encoding="utf-8")
    (ARCHIVE / OUT_JSON.name).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    a, b = results["A_1_70"], results["B_75_130_step5"]
    block = f"""
## Result (evaluated {date.today().isoformat()})

| Chain | S_real | p_perm | p99_null | Verdict |
|-------|-------:|-------:|---------:|---------|
| A 1..70 | {a['S_real']:.6f} | {a['p_perm']:.6f} | {a['p99_null']:.6f} | {'PASS' if a['pass'] else 'FAIL'} |
| B 75..130 step 5 | {b['S_real']:.6f} | {b['p_perm']:.6f} | {b['p99_null']:.6f} | {'PASS' if b['pass'] else 'FAIL'} |
| Overall | | | | **{verdict}** |

{meaning}
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

    ledger = f"""# Ledger: G-03 Serial dependence gate (dCor) — {verdict}

## Question

Is there detectable serial dependence in normalized within-band payload locations?

## Result

| Chain | S_real | p_perm | p99_null | Gate |
|-------|-------:|-------:|---------:|------|
| A 1..70 | {a['S_real']:.6f} | {a['p_perm']:.6f} | {a['p99_null']:.6f} | {'PASS' if a['pass'] else 'FAIL'} |
| B 75..130 step5 | {b['S_real']:.6f} | {b['p_perm']:.6f} | {b['p99_null']:.6f} | {'PASS' if b['pass'] else 'FAIL'} |

**Overall: {verdict}** (require p_perm < 0.01 on **both**)

{meaning}
"""
    if verdict == "FAIL":
        ledger += """
$$
\\boxed{\\text{Solved payload locations behave like independently ordered draws at the detectable scale.}}
$$

Close invent-another-recurrence/hash cycle. Prefer direct search-space engineering for Puzzle 135.
"""
    ledger += """
No lag sweep, Pearson/Spearman, or chain-combining reopen.

Artifacts: `G-20260710-03_serial_dcor_result.*`, `g03_serial_dcor.py`.
"""
    LEDGER.write_text(ledger, encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Wrote {LEDGER}")


if __name__ == "__main__":
    main()
