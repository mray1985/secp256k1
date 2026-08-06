#!/usr/bin/env python3
"""
F-20260709-05 — GLV order-3 orbit mutual information.

Preregistered before eval.
  a = argmin_j (lam^j * d mod N)
  b = argmin_j (beta^j * Px mod p)
  S = I(a;b) bits
"""
from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import asdict
from datetime import date
from typing import Sequence

from pairing_advantage_filter import (
    ARCHIVE,
    ARCHIVE_PREREG,
    N_ORDER,
    OUT_DIR,
    P_FIELD,
    PuzzleRow,
    evaluate,
    format_result,
    load_prereg,
    load_puzzles,
    save_prereg,
)

CANDIDATE_ID = "F-20260709-05"
OUT = OUT_DIR / "F-20260709-05_glv_orbit_mi_result.txt"
PREREG_MD = OUT_DIR / "prereg" / "F-20260709-05_glv_orbit_mi.md"

LAM = 0x5363ad4cc05c30e0a5261c028812645a122e22ea20816678df02967c1b23bd72
BETA = 0x7ae96a2b657c07106e64479eac3434e99cf0497512f58995c1396c28719501ee
LAM_POW = [1, LAM % N_ORDER, (LAM * LAM) % N_ORDER]
BETA_POW = [1, BETA % P_FIELD, (BETA * BETA) % P_FIELD]


def argmin_orbit(vals: list[int]) -> int:
    """argmin with ties -> smallest j."""
    best_j, best_v = 0, vals[0]
    for j in range(1, 3):
        if vals[j] < best_v:
            best_j, best_v = j, vals[j]
    return best_j


def label_a(d: int) -> int:
    return argmin_orbit([(LAM_POW[j] * (d % N_ORDER)) % N_ORDER for j in range(3)])


def label_b(px: int) -> int:
    return argmin_orbit([(BETA_POW[j] * (px % P_FIELD)) % P_FIELD for j in range(3)])


def mutual_information(pairs: Sequence[tuple[int, int]]) -> float:
    """I(a;b) in bits over empirical joint. Empty -> 0."""
    n = len(pairs)
    if n == 0:
        return 0.0
    joint = Counter(pairs)
    marg_a = Counter(a for a, _ in pairs)
    marg_b = Counter(b for _, b in pairs)
    mi = 0.0
    for (a, b), c in joint.items():
        p_ab = c / n
        p_a = marg_a[a] / n
        p_b = marg_b[b] / n
        mi += p_ab * math.log2(p_ab / (p_a * p_b))
    return mi


def score_glv_mi(rows: Sequence[PuzzleRow]) -> float:
    pairs = [(label_a(r.d), label_b(r.px)) for r in rows]
    return mutual_information(pairs)


def fill_prereg(res) -> None:
    block = f"""
## Result (evaluated {date.today().isoformat()})

| Metric | Value |
|--------|------:|
| I_real | {res.score_real:+.4f} |
| I_shuffled mean | {res.score_shuffled_mean:+.4f} |
| Δ | {res.advantage:+.4f} |
| p_shuffle | {res.p_shuffled:.4f} |
| train / test I | {res.score_train:+.4f} / {res.score_test:+.4f} |
| train / test Δ | {res.advantage_train:+.4f} / {res.advantage_test:+.4f} |
| Verdict | {res.verdict} |

Notes: {'; '.join(res.notes)}
"""
    if PREREG_MD.exists():
        text = PREREG_MD.read_text(encoding="utf-8")
        marker = "## Result (fill only after evaluation)"
        if marker in text:
            text = text.split(marker)[0] + block.lstrip()
        text = text.replace(
            "| Date first evaluated | *(pending)* |",
            f"| Date first evaluated | {date.today().isoformat()} |",
        )
        PREREG_MD.write_text(text, encoding="utf-8")
        (ARCHIVE_PREREG / PREREG_MD.name).write_text(text, encoding="utf-8")


def main() -> None:
    assert pow(LAM, 3, N_ORDER) == 1
    assert pow(BETA, 3, P_FIELD) == 1

    prereg = load_prereg(CANDIDATE_ID)
    prereg.assert_ready()
    print(f"Prereg LOCKED: {prereg.candidate_id} — {prereg.short_name}")
    print(f"Formula: {prereg.formula}")
    print()

    rows = load_puzzles(70)
    print(f"N puzzles: {len(rows)}")

    # 3x3 table snapshot (real only — for log, not for tuning)
    pairs = [(label_a(r.d), label_b(r.px)) for r in rows]
    table = Counter(pairs)
    print("3x3 counts (a,b):")
    for a in range(3):
        print(" ", [table[(a, b)] for b in range(3)])
    print(f"I_real preview: {mutual_information(pairs):.4f} bits")
    print()

    res = evaluate(
        "F-20260709-05 glv_orbit_mutual_information",
        score_glv_mi,
        rows,
        prereg=prereg,
        control_rows=rows,
        shuffle_trials=1000,
        rand_trials=200,
        ec_trials=40,
    )
    print(format_result(res))

    prereg.evaluated_date = date.today().isoformat()
    save_prereg(prereg)
    fill_prereg(res)

    payload = {
        "candidate_id": CANDIDATE_ID,
        "closed_branch": "translated-point/doubling-feature F-01..F-04 CLOSED",
        "question": (
            "Does d<->Px attachment preserve categorical alignment under "
            "secp256k1 shared order-3 endomorphism?"
        ),
        "table_counts": {f"{a},{b}": table[(a, b)] for a in range(3) for b in range(3)},
        "result": asdict(res),
        "prereg": asdict(prereg),
    }
    text = format_result(res) + "\n\n" + json.dumps(payload, indent=2)
    OUT.write_text(text, encoding="utf-8")
    (ARCHIVE / OUT.name).write_text(text, encoding="utf-8")
    print()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
