#!/usr/bin/env python3
"""
F-20260709-06 — Adjacent Hamming coupling (preregistered before eval).

h_d = HW(pad_{n_{i+1}}(d_i) XOR d_{i+1}) / n_{i+1}
h_P = HW(SEC_compressed(P_i) XOR SEC_compressed(P_{i+1})) / 264
S = SpearmanCorr(h_d, h_P)
"""
from __future__ import annotations

import json
import random
import statistics
from dataclasses import asdict
from datetime import date
from typing import Sequence

from pairing_advantage_filter import (
    ADVANTAGE_FLOOR,
    ARCHIVE,
    ARCHIVE_PREREG,
    OUT_DIR,
    P_SHUFFLE_MAX,
    PuzzleRow,
    load_prereg,
    load_puzzles,
    pub_xy,
    save_prereg,
    score_native_lead_corr,
    shuffle_points,
)

CANDIDATE_ID = "F-20260709-06"
OUT = OUT_DIR / "F-20260709-06_adjacent_hamming_result.txt"
PREREG_MD = OUT_DIR / "prereg" / "F-20260709-06_adjacent_hamming.md"
B_SHUF = 1000
B_RAND = 200
B_EC = 40
RNG = random.Random(20260709)


def popcount(x: int) -> int:
    return x.bit_count()


def sec_compressed(px: int, py: int) -> bytes:
    prefix = b"\x02" if (py % 2 == 0) else b"\x03"
    return prefix + px.to_bytes(32, "big")


def hamming_bytes(a: bytes, b: bytes) -> int:
    return sum(popcount(x ^ y) for x, y in zip(a, b))


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Spearman rank correlation (average ranks for ties)."""
    n = len(xs)
    if n < 3:
        return 0.0

    def ranks(vals: Sequence[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = 0.5 * (i + j) + 1.0  # 1-based average rank
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    denx = sum((a - mx) ** 2 for a in rx) ** 0.5
    deny = sum((b - my) ** 2 for b in ry) ** 0.5
    return num / (denx * deny) if denx and deny else 0.0


def edge_rates(rows: Sequence[PuzzleRow]) -> tuple[list[float], list[float]]:
    """Compute h_d, h_P for consecutive edges. rows must be sorted by n."""
    hd, hp = [], []
    for i in range(len(rows) - 1):
        a, b = rows[i], rows[i + 1]
        n1 = b.n
        pad = a.d  # zero-extend is free for int XOR into n1-bit width
        # mask to n1 bits for pad and d_{i+1}
        mask = (1 << n1) - 1
        hd.append(popcount((pad & mask) ^ (b.d & mask)) / n1)
        sa, sb = sec_compressed(a.px, a.py), sec_compressed(b.px, b.py)
        hp.append(hamming_bytes(sa, sb) / 264.0)
    return hd, hp


def score_spearman(rows: Sequence[PuzzleRow]) -> float:
    hd, hp = edge_rates(rows)
    return spearman(hd, hp)


def shuffle_public_order(rows: Sequence[PuzzleRow], rng: random.Random) -> list[PuzzleRow]:
    """Keep d sequence; permute (px,py) among rows."""
    return shuffle_points(rows, rng)


def circular_shift_P(rows: Sequence[PuzzleRow], k: int) -> list[PuzzleRow]:
    pts = [(r.px, r.py) for r in rows]
    n = len(pts)
    k %= n
    pts = pts[k:] + pts[:k]
    return [PuzzleRow(n=r.n, d=r.d, px=px, py=py) for r, (px, py) in zip(rows, pts)]


def random_nbit_ec(rows: Sequence[PuzzleRow], rng: random.Random) -> list[PuzzleRow]:
    out = []
    for r in rows:
        lo, hi = 1 << (r.n - 1), (1 << r.n) - 1
        d = rng.randrange(lo, hi + 1)
        px, py = pub_xy(d)
        out.append(PuzzleRow(n=r.n, d=d, px=px, py=py))
    return out


def unrelated_random_ec(rows: Sequence[PuzzleRow], rng: random.Random) -> list[PuzzleRow]:
    """Random n-bit d' for h_d; independent random EC points (not [d']G)."""
    out = []
    for r in rows:
        lo, hi = 1 << (r.n - 1), (1 << r.n) - 1
        d = rng.randrange(lo, hi + 1)
        # random valid-ish point: use random scalar's point but different scalar for d
        d_pt = rng.randrange(lo, hi + 1)
        px, py = pub_xy(d_pt)
        out.append(PuzzleRow(n=r.n, d=d, px=px, py=py))
    return out


def subset_by_edge_filter(rows: Sequence[PuzzleRow], pred) -> list[PuzzleRow]:
    """
    Keep consecutive rows that form edges satisfying pred(left, right).
    Returns a contiguous list of rows covering those edges (may drop gaps).
    Simpler: score only on edges where pred holds by building edge lists.
    """
    # Build filtered edge score directly
    return list(rows)  # unused; see score_edges_filtered


def score_edges_filtered(rows: Sequence[PuzzleRow], pred) -> float:
    hd, hp = [], []
    for i in range(len(rows) - 1):
        a, b = rows[i], rows[i + 1]
        if not pred(a, b):
            continue
        n1 = b.n
        mask = (1 << n1) - 1
        hd.append(popcount((a.d & mask) ^ (b.d & mask)) / n1)
        sa, sb = sec_compressed(a.px, a.py), sec_compressed(b.px, b.py)
        hp.append(hamming_bytes(sa, sb) / 264.0)
    return spearman(hd, hp)


def mean_null(score_fn, builder, rows, trials, rng) -> float:
    vals = [score_fn(builder(rows, rng)) for _ in range(trials)]
    return statistics.fmean(vals)


def main() -> None:
    prereg = load_prereg(CANDIDATE_ID)
    prereg.assert_ready()
    print(f"Prereg LOCKED: {prereg.candidate_id} — {prereg.short_name}")
    print(f"Formula: {prereg.formula}")
    print()

    rows = load_puzzles(70)
    rows = sorted(rows, key=lambda r: r.n)
    print(f"N puzzles: {len(rows)}  edges: {len(rows)-1}")

    S_real = score_spearman(rows)
    print(f"S_real (Spearman): {S_real:+.4f}")

    # shuffle public order
    shuf = [score_spearman(shuffle_public_order(rows, RNG)) for _ in range(B_SHUF)]
    shuf_mean = statistics.fmean(shuf)
    shuf_sd = statistics.pstdev(shuf)
    advantage = S_real - shuf_mean
    ge = sum(1 for s in shuf if abs(s) >= abs(S_real))
    # better: compare advantage magnitude vs null advantages from 0?
    # Gate uses p as fraction of shuffles with |S| >= |S_real| (same as harness)
    p_shuf = (ge + 1) / (B_SHUF + 1)

    # circular shifts
    circ = [score_spearman(circular_shift_P(rows, k)) for k in range(1, len(rows))]
    circ_mean = statistics.fmean(circ)

    # random n-bit EC
    rand_ec = [score_spearman(random_nbit_ec(rows, RNG)) for _ in range(B_EC)]
    rand_ec_mean = statistics.fmean(rand_ec)

    # unrelated random
    unrel = [score_spearman(unrelated_random_ec(rows, RNG)) for _ in range(B_RAND)]
    unrel_mean = statistics.fmean(unrel)

    # edge holdout per prereg: train (1,2)..(50,51); test edges with both n>=51
    S_train = score_edges_filtered(rows, lambda a, b: a.n <= 50 and b.n <= 51)
    S_test = score_edges_filtered(rows, lambda a, b: a.n >= 51)

    train_shuf = [
        score_edges_filtered(
            shuffle_public_order(rows, RNG), lambda a, b: a.n <= 50 and b.n <= 51
        )
        for _ in range(min(500, B_SHUF))
    ]
    test_shuf = [
        score_edges_filtered(shuffle_public_order(rows, RNG), lambda a, b: a.n >= 51)
        for _ in range(min(500, B_SHUF))
    ]
    adv_train = S_train - statistics.fmean(train_shuf)
    adv_test = S_test - statistics.fmean(test_shuf)

    S_lo = score_edges_filtered(rows, lambda a, b: b.n <= 35)
    S_hi = score_edges_filtered(rows, lambda a, b: a.n >= 36)

    # control
    ctrl_real = score_native_lead_corr(rows)
    ctrl_shuf = [score_native_lead_corr(shuffle_points(rows, RNG)) for _ in range(200)]
    ctrl_adv = ctrl_real - statistics.fmean(ctrl_shuf)

    def beats_null(null_mean: float) -> bool:
        if advantage >= 0:
            return S_real > null_mean + 0.02
        return S_real < null_mean - 0.02

    def sign(x: float) -> int:
        if x > 1e-12:
            return 1
        if x < -1e-12:
            return -1
        return 0

    gate = {
        "advantage_gt_floor": advantage > ADVANTAGE_FLOOR,
        "p_shuffle_ok": p_shuf < P_SHUFFLE_MAX,
        "beats_rand_nbit": beats_null(rand_ec_mean),
        "beats_rand_ec": beats_null(unrel_mean),
        "holds_oos": sign(adv_train) == sign(adv_test) != 0
        and abs(adv_train) > 0.05
        and abs(adv_test) > 0.05,
        "direction_consistent": sign(S_lo) == sign(S_hi) != 0,
    }
    beats_control = abs(advantage) > abs(ctrl_adv) + 0.02

    if all(gate.values()) and beats_control:
        verdict = "PROMOTE"
    elif abs(advantage) < 0.05 or p_shuf > 0.10:
        verdict = "FAIL"
    else:
        verdict = "BORDERLINE"

    lines = []

    def w(s=""):
        lines.append(s)
        print(s)

    w("=" * 72)
    w("F-20260709-06 Adjacent Hamming coupling")
    w("=" * 72)
    w(f"S_real (Spearman)     = {S_real:+.4f}")
    w(f"S_shuffled mean       = {shuf_mean:+.4f}  (sd={shuf_sd:.4f})")
    w(f"ADVANTAGE             = {advantage:+.4f}")
    w(f"p_shuffle             = {p_shuf:.4f}")
    w(f"circular-shift mean   = {circ_mean:+.4f}")
    w(f"random n-bit EC mean  = {rand_ec_mean:+.4f}")
    w(f"unrelated random mean = {unrel_mean:+.4f}")
    w(f"control sawtooth adv  = {ctrl_adv:+.4f}")
    w()
    w(f"train edges (n_left<=50): S={S_train:+.4f}  Delta={adv_train:+.4f}")
    w(f"test  edges (n_left>=51): S={S_test:+.4f}  Delta={adv_test:+.4f}")
    w(f"range early (n<=35):      S={S_lo:+.4f}")
    w(f"range late  (n>=36):      S={S_hi:+.4f}")
    w()
    w("PROMOTION GATE:")
    for k, v in gate.items():
        w(f"  [ {'OK' if v else 'NO'} ] {k}")
    w(f"  beats_control: {beats_control}")
    w(f"VERDICT: {verdict}")
    w()
    w("Question: Does any local similarity in the private-key sequence")
    w("          survive into local public-key similarity?")

    block = f"""
## Result (evaluated {date.today().isoformat()})

| Metric | Value |
|--------|------:|
| S_real | {S_real:+.4f} |
| S_shuffled mean | {shuf_mean:+.4f} |
| Δ | {advantage:+.4f} |
| p_shuffle | {p_shuf:.4f} |
| train / test S | {S_train:+.4f} / {S_test:+.4f} |
| train / test Δ | {adv_train:+.4f} / {adv_test:+.4f} |
| Verdict | {verdict} |

Notes: prereg locked; compressed SEC; Spearman only; edge holdout.
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

    prereg.evaluated_date = date.today().isoformat()
    save_prereg(prereg)

    payload = {
        "candidate_id": CANDIDATE_ID,
        "question": "Does any local similarity in the private-key sequence survive into local public-key similarity?",
        "S_real": S_real,
        "advantage": advantage,
        "p_shuffle": p_shuf,
        "circular_shift_mean": circ_mean,
        "rand_ec_mean": rand_ec_mean,
        "unrelated_mean": unrel_mean,
        "train": {"S": S_train, "delta": adv_train},
        "test": {"S": S_test, "delta": adv_test},
        "gate": gate,
        "verdict": verdict,
        "prereg": asdict(prereg),
    }
    text = "\n".join(lines) + "\n\n" + json.dumps(payload, indent=2)
    OUT.write_text(text, encoding="utf-8")
    (ARCHIVE / OUT.name).write_text(text, encoding="utf-8")
    w()
    w(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
