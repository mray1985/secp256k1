#!/usr/bin/env python3
"""
Decimal-side correlation on SOLVED scalar triples (calibration only).

Representation (digit strings only — NOT packed U arithmetic):
  0.x.y  :=  0.<x padded to 78 digits>.<y padded to 78 digits>

Protocol:
  From solved puzzles, take (d_a, d_b), set d_c = (d_a + d_b) mod N.
  Compute P_a, P_b, P_c ONCE as calibration truth (EC used only to label).
  Compare decimal forms 0.xa.ya , 0.xb.yb , 0.xc.yc directly.

Measure digitwise add/carry vs truth; hold out triples for prediction.
Do NOT train on Puzzle 135.
Do NOT unpack/EC-add/repack as a decimal procedure.
Do NOT study packed Delta-U (that branch is a closed negative).
"""
from __future__ import annotations

import csv
import random
from collections import Counter
from pathlib import Path

from ecdsa import SECP256k1

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\DECIMAL_SIDE_SOLVED_TRIPLES.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\decimal_side_solved_triples.csv")

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = SECP256k1.generator
WIDTH = 78  # fixed decimal width for one coordinate
EXCLUDE_PUZZLES = {135}  # never train/validate on P135

# Sample budget (all-pairs is fine at ~3k; keep deterministic)
RNG = random.Random(13501)
N_TRAIN = 400
N_HOLD = 100


def dec_0xy(x: int, y: int) -> str:
    """Exact 0.x.y display: 0.<78>.<78> — strings only."""
    return f"0.{int(x):0{WIDTH}d}.{int(y):0{WIDTH}d}"


def split_0xy(s: str) -> tuple[str, str]:
    # 0.<x>.<y>
    body = s[2:]
    xdig, ydig = body.split(".")
    if len(xdig) != WIDTH or len(ydig) != WIDTH:
        raise ValueError(f"bad 0.x.y width: {len(xdig)},{len(ydig)}")
    return xdig, ydig


def digitwise_add(a: str, b: str) -> tuple[str, list[int]]:
    """Schoolbook digit add from right; return digit string + carry-out list per position (L->R after)."""
    assert len(a) == len(b)
    out = []
    carries = []  # carry INTO each position from the right (index 0 = leftmost)
    carry = 0
    tmp = []
    for i in range(len(a) - 1, -1, -1):
        s = int(a[i]) + int(b[i]) + carry
        tmp.append(str(s % 10))
        carry = s // 10
        carries.append(carry)  # carry going further left; collect then reverse
    tmp.reverse()
    # carries currently right-to-left final outgoing; rebuild per-position carry-in
    # Recompute carry-in left display order:
    cin = [0] * len(a)
    c = 0
    for i in range(len(a) - 1, -1, -1):
        cin[i] = c
        s = int(a[i]) + int(b[i]) + c
        c = s // 10
    final_carry = c
    return "".join(tmp), cin + [final_carry]  # last entry = overflow past MSB


def match_stats(pred: str, truth: str) -> dict:
    assert len(pred) == len(truth)
    eq = sum(p == t for p, t in zip(pred, truth))
    return {"eq": eq, "n": len(truth), "rate": eq / len(truth)}


def load_solved() -> list[tuple[int, int]]:
    rows = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            n = int(r["puzzle"])
            if n in EXCLUDE_PUZZLES:
                continue
            rows.append((n, int(r["private_key"])))
    rows.sort()
    return rows


def point_xy(d: int) -> tuple[int, int]:
    pt = d * G
    return int(pt.x()), int(pt.y())


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    solved = load_solved()
    w("=" * 88)
    w("DECIMAL-SIDE SOLVED TRIPLES  (0.x.y strings; EC = calibration only)")
    w("=" * 88)
    w()
    w("Closed branches")
    w("  - packed U = x*10^78+y with unpack/EC/repack Delta-U: NEGATIVE (no reusable delta)")
    w("  - n.C / A+=10^L prefix counter: REJECTED (wrong object)")
    w()
    w("Representation")
    w(f"  0.x.y = 0.<x {WIDTH} digits>.<y {WIDTH} digits>")
    w("  Arithmetic under test: digitwise decimal add/carry on those strings.")
    w("  Not: curve addition inside a packed integer.")
    w()
    w(f"Solved keys loaded: {len(solved)}  (excluded puzzles={sorted(EXCLUDE_PUZZLES)})")
    w()

    # Cache P decimals for solved keys
    cache: dict[int, tuple[str, int, int]] = {}
    for n, d in solved:
        x, y = point_xy(d)
        cache[d] = (dec_0xy(x, y), x, y)

    # Closed triples inside solved set (rare)
    dset = {d: n for n, d in solved}
    closed = []
    for i, (na, da) in enumerate(solved):
        for nb, db in solved[i:]:
            dc = (da + db) % N
            if dc in dset:
                closed.append((na, nb, dset[dc], da, db, dc))
    w(f"Fully solved closed additive triples: {len(closed)}")
    for t in closed[:5]:
        w(f"  puzzles {t[0]}+{t[1]}->{t[2]}  d: {t[3]}+{t[4]}={t[5]}")
    w()

    # Build pair list
    pairs: list[tuple[int, int, int, int]] = []  # na,nb,da,db
    for i, (na, da) in enumerate(solved):
        for nb, db in solved[i:]:  # include 2*da
            pairs.append((na, nb, da, db))
    RNG.shuffle(pairs)

    hold_n = min(N_HOLD, len(pairs) // 5)
    train_n = min(N_TRAIN, len(pairs) - hold_n)
    train = pairs[:train_n]
    hold = pairs[train_n : train_n + hold_n]
    w(f"Pair sample: train={len(train)}  holdout={len(hold)}  (from {len(pairs)} pairs)")
    w()

    def eval_split(name: str, sample: list[tuple[int, int, int, int]]) -> dict:
        x_rates = []
        y_rates = []
        x_exact = 0
        y_exact = 0
        both_exact = 0
        overflow_x = Counter()
        overflow_y = Counter()
        pos_x_hits = [0] * WIDTH
        pos_y_hits = [0] * WIDTH
        rows_out = []

        for na, nb, da, db in sample:
            dc = (da + db) % N
            Da, xa, ya = cache[da]
            Db, xb, yb = cache[db]
            # calibration truth for Pc (once per triple)
            xc, yc = point_xy(dc)
            Dc = dec_0xy(xc, yc)

            xa_s, ya_s = split_0xy(Da)
            xb_s, yb_s = split_0xy(Db)
            xc_s, yc_s = split_0xy(Dc)

            pred_x, cin_x = digitwise_add(xa_s, xb_s)
            pred_y, cin_y = digitwise_add(ya_s, yb_s)
            ox = cin_x[-1]
            oy = cin_y[-1]
            overflow_x[ox] += 1
            overflow_y[oy] += 1

            # If overflow, keep only WIDTH digits (drop MSB carry) — schoolbook mod 10^WIDTH
            if len(pred_x) != WIDTH:
                pred_x = pred_x[-WIDTH:].rjust(WIDTH, "0")
            if len(pred_y) != WIDTH:
                pred_y = pred_y[-WIDTH:].rjust(WIDTH, "0")
            # digitwise_add returns exactly WIDTH digits; overflow separate
            assert len(pred_x) == WIDTH and len(pred_y) == WIDTH

            sx = match_stats(pred_x, xc_s)
            sy = match_stats(pred_y, yc_s)
            x_rates.append(sx["rate"])
            y_rates.append(sy["rate"])
            if sx["eq"] == WIDTH:
                x_exact += 1
            if sy["eq"] == WIDTH:
                y_exact += 1
            if sx["eq"] == WIDTH and sy["eq"] == WIDTH and ox == 0 and oy == 0:
                both_exact += 1
            for i, (p, t) in enumerate(zip(pred_x, xc_s)):
                if p == t:
                    pos_x_hits[i] += 1
            for i, (p, t) in enumerate(zip(pred_y, yc_s)):
                if p == t:
                    pos_y_hits[i] += 1

            rows_out.append(
                {
                    "split": name,
                    "puzzle_a": na,
                    "puzzle_b": nb,
                    "d_a": da,
                    "d_b": db,
                    "d_c": dc,
                    "x_match": sx["eq"],
                    "y_match": sy["eq"],
                    "x_rate": f"{sx['rate']:.4f}",
                    "y_rate": f"{sy['rate']:.4f}",
                    "overflow_x": ox,
                    "overflow_y": oy,
                    "Da": Da,
                    "Db": Db,
                    "Dc": Dc,
                    "pred_x": pred_x,
                    "pred_y": pred_y,
                }
            )

        n = len(sample)
        summary = {
            "n": n,
            "x_mean_rate": sum(x_rates) / n if n else 0.0,
            "y_mean_rate": sum(y_rates) / n if n else 0.0,
            "x_exact": x_exact,
            "y_exact": y_exact,
            "both_exact": both_exact,
            "overflow_x": dict(overflow_x),
            "overflow_y": dict(overflow_y),
            "pos_x_rate": [h / n for h in pos_x_hits] if n else [],
            "pos_y_rate": [h / n for h in pos_y_hits] if n else [],
            "rows": rows_out,
        }
        return summary

    train_s = eval_split("train", train)
    hold_s = eval_split("hold", hold)

    w("-" * 88)
    w("Hypothesis under test")
    w("  digitwise:  x_c digits ?= schoolbook_add(x_a, x_b)")
    w("              y_c digits ?= schoolbook_add(y_a, y_b)")
    w("  (i.e. whether 0.xa.ya 'decimal-add' 0.xb.yb predicts 0.xc.yc)")
    w("-" * 88)
    for label, s in (("TRAIN", train_s), ("HOLDOUT", hold_s)):
        w(f"{label}: n={s['n']}")
        w(f"  mean digit match  x={s['x_mean_rate']:.4f}  y={s['y_mean_rate']:.4f}")
        w(
            f"  exact block match x={s['x_exact']}/{s['n']}  "
            f"y={s['y_exact']}/{s['n']}  both+no overflow={s['both_exact']}/{s['n']}"
        )
        w(f"  overflow_x counts={s['overflow_x']}  overflow_y={s['overflow_y']}")
        # chance baseline ~0.1 per digit
        w(f"  chance baseline per digit ~ 0.10")
        if s["pos_x_rate"]:
            best_x = max(range(WIDTH), key=lambda i: s["pos_x_rate"][i])
            worst_x = min(range(WIDTH), key=lambda i: s["pos_x_rate"][i])
            w(
                f"  x position hit rates: best pos {best_x}={s['pos_x_rate'][best_x]:.3f}  "
                f"worst pos {worst_x}={s['pos_x_rate'][worst_x]:.3f}  "
                f"mean={sum(s['pos_x_rate'])/WIDTH:.3f}"
            )
            best_y = max(range(WIDTH), key=lambda i: s["pos_y_rate"][i])
            worst_y = min(range(WIDTH), key=lambda i: s["pos_y_rate"][i])
            w(
                f"  y position hit rates: best pos {best_y}={s['pos_y_rate'][best_y]:.3f}  "
                f"worst pos {worst_y}={s['pos_y_rate'][worst_y]:.3f}  "
                f"mean={sum(s['pos_y_rate'])/WIDTH:.3f}"
            )
        w()

    # Null: shuffle digits of xb and remeasure on holdout (same xa)
    w("-" * 88)
    w("Null: digit-shuffle of x_b/y_b on holdout (destroys pair structure)")
    w("-" * 88)
    null_x = []
    null_y = []
    for na, nb, da, db in hold:
        Da, _, _ = cache[da]
        Db, _, _ = cache[db]
        dc = (da + db) % N
        xc, yc = point_xy(dc)
        Dc = dec_0xy(xc, yc)
        xa_s, ya_s = split_0xy(Da)
        xb_s, yb_s = split_0xy(Db)
        xc_s, yc_s = split_0xy(Dc)
        xb_n = "".join(RNG.sample(list(xb_s), len(xb_s)))
        yb_n = "".join(RNG.sample(list(yb_s), len(yb_s)))
        px, _ = digitwise_add(xa_s, xb_n)
        py, _ = digitwise_add(ya_s, yb_n)
        null_x.append(match_stats(px, xc_s)["rate"])
        null_y.append(match_stats(py, yc_s)["rate"])
    w(f"  null mean digit match x={sum(null_x)/len(null_x):.4f}  y={sum(null_y)/len(null_y):.4f}")
    w(f"  hold mean digit match x={hold_s['x_mean_rate']:.4f}  y={hold_s['y_mean_rate']:.4f}")
    w(
        f"  lift vs null x={hold_s['x_mean_rate']-sum(null_x)/len(null_x):+.4f}  "
        f"y={hold_s['y_mean_rate']-sum(null_y)/len(null_y):+.4f}"
    )
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    # Falsify if holdout near chance and no exact matches
    near_chance = hold_s["x_mean_rate"] < 0.15 and hold_s["y_mean_rate"] < 0.15
    no_exact = hold_s["both_exact"] == 0
    if near_chance and no_exact:
        w("  Schoolbook digitwise add on 0.x.y does NOT predict P_c for d_a+d_b.")
        w("  Correlation falsified for this rule (held-out).")
    else:
        w("  Residual signal present — inspect position rates / CSV before claiming a rule.")
    w("  Next rules (if any) must beat holdout + null on solved triples only.")
    w("  Puzzle 135 remains unused.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "split",
            "puzzle_a",
            "puzzle_b",
            "d_a",
            "d_b",
            "d_c",
            "x_match",
            "y_match",
            "x_rate",
            "y_rate",
            "overflow_x",
            "overflow_y",
        ]
        wr = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        wr.writeheader()
        for row in train_s["rows"] + hold_s["rows"]:
            wr.writerow(row)

    w()
    w(f"Wrote {OUT}")
    w(f"Wrote {CSV_OUT}")


if __name__ == "__main__":
    main()
