#!/usr/bin/env python3
"""
F-20260709-03 — Band-floor + tangent slope T(Q).

Preregistered before eval. Replaces feature (not offset):
  T(Q) = 3 Qx^2 * (2 Qy)^{-1} mod p
score = Pearson(phi(u), phi(T(Q)))
"""
from __future__ import annotations

import json
import random
from dataclasses import asdict
from datetime import date
from pathlib import Path

from ecdsa import SECP256k1
from ecdsa.ellipticcurve import Point

from pairing_advantage_filter import (
    ARCHIVE,
    ARCHIVE_PREREG,
    OUT_DIR,
    P_FIELD,
    PuzzleRow,
    evaluate,
    format_result,
    lead_frac,
    load_prereg,
    load_puzzles,
    pearson,
    pub_xy,
    save_prereg,
)

G = SECP256k1.generator
CURVE = SECP256k1.curve
CANDIDATE_ID = "F-20260709-03"
OUT = OUT_DIR / "F-20260709-03_band_floor_tangent_result.txt"
PREREG_MD = OUT_DIR / "prereg" / "F-20260709-03_band_floor_tangent.md"


def modinv(a: int, p: int = P_FIELD) -> int | None:
    a %= p
    if a == 0:
        return None
    return pow(a, -1, p)


def tangent_T(qx: int, qy: int) -> int | None:
    """T(Q) = 3 Qx^2 * (2 Qy)^{-1} mod p. None if 2Qy = 0."""
    inv = modinv((2 * qy) % P_FIELD)
    if inv is None:
        return None
    return (3 * qx * qx * inv) % P_FIELD


def translate(px: int, py: int, n: int) -> tuple[int, int] | None:
    P = Point(CURVE, px, py)
    Q = P + (-((1 << (n - 1)) * G))
    if Q.x() is None:
        return None
    return int(Q.x()), int(Q.y())


def to_band_rows(raw: list[PuzzleRow]) -> list[PuzzleRow]:
    """d<-u, px/py<-Q. Skip n<2, u<=0, Q=O."""
    out = []
    for r in raw:
        if r.n < 2:
            continue
        u = r.d - (1 << (r.n - 1))
        if u <= 0:
            continue
        t = translate(r.px, r.py, r.n)
        if t is None:
            continue
        out.append(PuzzleRow(n=r.n, d=u, px=t[0], py=t[1]))
    return out


def score_tangent(rows) -> float:
    """Locked: Pearson(phi(u), phi(T(Q))). Skip rows with Qy=0."""
    xs, ys = [], []
    for r in rows:
        T = tangent_T(r.px, r.py)
        if T is None:
            continue
        xs.append(lead_frac(r.d))
        ys.append(lead_frac(T))
    if len(xs) < 8:
        return 0.0
    return pearson(xs, ys)


def shuffle_Q(rows, rng: random.Random) -> list[PuzzleRow]:
    pts = [(r.px, r.py) for r in rows]
    rng.shuffle(pts)
    return [PuzzleRow(n=r.n, d=r.d, px=px, py=py) for r, (px, py) in zip(rows, pts)]


def rand_nm1_field(rows, rng: random.Random) -> list[PuzzleRow]:
    out = []
    for r in rows:
        width = r.n - 1
        u = rng.randrange(1 << width) if width > 0 else 0
        # ensure 2*qy invertible almost surely
        qx, qy = rng.randrange(P_FIELD), rng.randrange(1, P_FIELD)
        out.append(PuzzleRow(n=r.n, d=u, px=qx, py=qy))
    return out


def rand_nm1_ec(rows, rng: random.Random) -> list[PuzzleRow]:
    out = []
    for r in rows:
        width = r.n - 1
        u = rng.randrange(1, 1 << width) if width >= 1 else 1
        qx, qy = pub_xy(u)
        out.append(PuzzleRow(n=r.n, d=u, px=qx, py=qy))
    return out


def nearby_Q(rows, rng: random.Random) -> list[PuzzleRow]:
    by_n = {r.n: r for r in rows}
    ns = [r.n for r in rows]
    out = []
    for r in rows:
        cands = [n for n in ns if 1 <= abs(n - r.n) <= 3] or [n for n in ns if n != r.n]
        j = by_n[rng.choice(cands)]
        out.append(PuzzleRow(n=r.n, d=r.d, px=j.px, py=j.py))
    return out


def fill_prereg(res) -> None:
    block = f"""
## Result (evaluated {date.today().isoformat()})

| Metric | Value |
|--------|------:|
| score_real | {res.score_real:+.4f} |
| score_shuffled | {res.score_shuffled_mean:+.4f} |
| Δ | {res.advantage:+.4f} |
| p_shuffle | {res.p_shuffled:.4f} |
| train / test score | {res.score_train:+.4f} / {res.score_test:+.4f} |
| train / test advantage | {res.advantage_train:+.4f} / {res.advantage_test:+.4f} |
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
    prereg = load_prereg(CANDIDATE_ID)
    prereg.assert_ready()
    print(f"Prereg LOCKED: {prereg.candidate_id} — {prereg.short_name}")
    print(f"Formula: {prereg.formula}")
    print()

    raw = load_puzzles(70)
    rows = to_band_rows(raw)
    # drop rows where T undefined
    rows = [r for r in rows if tangent_T(r.px, r.py) is not None]
    print(f"Band-floor rows with T defined: {len(rows)}")

    ok = sum(1 for r in rows if (r.px, r.py) == pub_xy(r.d))
    print(f"Construction Q=[u]G: {ok}/{len(rows)} (not used as score)")
    print()

    res = evaluate(
        "F-20260709-03 band_floor_tangent_slope",
        score_tangent,
        rows,
        prereg=prereg,
        make_shuffle=shuffle_Q,
        make_rand_nbit=rand_nm1_field,
        make_rand_ec=rand_nm1_ec,
        make_nearby=nearby_Q,
        control_rows=raw,
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
        "closed_branch": "wrong offset same feature (Qx+Qy) — FALSIFIED by F-01/F-02",
        "this_fork": "replace feature with T(Q); keep band floor",
        "sibling_not_evaluated": "X2(Q)=T^2-2Qx",
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
