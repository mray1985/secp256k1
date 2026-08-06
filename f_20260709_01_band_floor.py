#!/usr/bin/env python3
"""
F-20260709-01 — Band-floor translation pairing test.

PRE-REGISTERED before evaluation (see logs/prereg/F-20260709-01*).
Does NOT verify Q=[u]G. Scores phi(u) vs phi((Qx+Qy) mod p) only.
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
CANDIDATE_ID = "F-20260709-01"
OUT = OUT_DIR / "F-20260709-01_band_floor_result.txt"
PREREG_MD = OUT_DIR / "prereg" / "F-20260709-01_band_floor_translation.md"


def floor_point(n: int) -> Point:
    return (1 << (n - 1)) * G


def translate(px: int, py: int, n: int) -> tuple[int, int] | None:
    """Q = P - [2^{n-1}]G. Returns None if Q is the point at infinity (u=0)."""
    P = Point(CURVE, px, py)
    Q = P + (-floor_point(n))
    if Q.x() is None or Q.y() is None:
        return None
    return int(Q.x()), int(Q.y())


def to_band_rows(raw: list[PuzzleRow]) -> list[PuzzleRow]:
    """
    Encode band-floor view into PuzzleRow:
      d  <- u = d - 2^{n-1}
      px,py <- Q = P - [2^{n-1}]G
    Original n kept. Score/nulls operate on (u, Q).
    Skips n<2 and u=0 (Q = O, no affine coords).
    """
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
        qx, qy = t
        out.append(PuzzleRow(n=r.n, d=u, px=qx, py=qy))
    return out


def score_band_floor(rows) -> float:
    """Locked feature: Pearson(phi(u), phi((Qx+Qy) mod p))."""
    u_phi = [lead_frac(r.d) for r in rows]
    g_phi = [lead_frac((r.px + r.py) % P_FIELD) for r in rows]
    return pearson(u_phi, g_phi)


def shuffle_Q(rows, rng: random.Random) -> list[PuzzleRow]:
    """Keep u_i, assign Q_π(i)."""
    pts = [(r.px, r.py) for r in rows]
    rng.shuffle(pts)
    return [PuzzleRow(n=r.n, d=r.d, px=px, py=py) for r, (px, py) in zip(rows, pts)]


def rand_nm1_field(rows, rng: random.Random) -> list[PuzzleRow]:
    """Random (n-1)-bit payload with random field-like coords."""
    out = []
    for r in rows:
        width = r.n - 1
        u = rng.randrange(1 << width) if width > 0 else 0
        out.append(
            PuzzleRow(
                n=r.n,
                d=u,
                px=rng.randrange(P_FIELD),
                py=rng.randrange(P_FIELD),
            )
        )
    return out


def rand_nm1_ec(rows, rng: random.Random) -> list[PuzzleRow]:
    """Random (n-1)-bit u' with true Q'=[u']G."""
    out = []
    for r in rows:
        width = r.n - 1
        u = rng.randrange(1 << width) if width > 0 else 0
        if u == 0:
            # identity has no affine coords in ecdsa; use 1
            u = 1 if width >= 1 else 1
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


def fill_prereg_results(res) -> None:
    """Append evaluation block to the markdown prereg (results section only)."""
    block = f"""
## Result (evaluated {date.today().isoformat()})

| Metric | Value |
|--------|------:|
| score_real | {res.score_real:+.4f} |
| score_shuffled | {res.score_shuffled_mean:+.4f} |
| Δ (advantage) | {res.advantage:+.4f} |
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
        else:
            text = text.rstrip() + "\n\n" + block
        # update evaluated date in header
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
    print(f"Band-floor rows: {len(rows)} (skipped n<2)")

    # Construction sanity only (NOT the score F): confirm Q=[u]G after translation.
    ok = 0
    for r in rows:
        qx, qy = pub_xy(r.d)  # r.d is already u
        if (r.px, r.py) == (qx, qy):
            ok += 1
    print(f"Construction check Q=[u]G holds for {ok}/{len(rows)} (not used as score)")
    print()

    res = evaluate(
        "F-20260709-01 band_floor_translation",
        score_band_floor,
        rows,
        prereg=prereg,
        make_shuffle=shuffle_Q,
        make_rand_nbit=rand_nm1_field,
        make_rand_ec=rand_nm1_ec,
        make_nearby=nearby_Q,
        control_rows=raw,  # sawtooth control on original (d, Px)
        shuffle_trials=1000,
        rand_trials=200,
        ec_trials=40,
    )
    print(format_result(res))

    prereg.evaluated_date = date.today().isoformat()
    save_prereg(prereg)

    payload = {
        "candidate_id": CANDIDATE_ID,
        "question": (
            "After removing 2^{n-1} band floor, does correct private payload "
            "leave a compact fingerprint on translated public point that "
            "disappears under wrong attachment?"
        ),
        "prereg": asdict(prereg),
        "result": asdict(res),
    }
    text = format_result(res) + "\n\n" + json.dumps(payload, indent=2)
    OUT.write_text(text, encoding="utf-8")
    (ARCHIVE / OUT.name).write_text(text, encoding="utf-8")
    fill_prereg_results(res)
    print()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
