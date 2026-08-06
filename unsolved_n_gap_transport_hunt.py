#!/usr/bin/env python3
"""
N-gap transport hunt for unsolved batch P135, P140, P145, P150, P155, P160.

Law:
  px^3 + 4 == py^2 - 3  (mod p, on-curve)

N displacement:
  gap(px,py) = (py^2 - 3) - (px^3 + 4) mod N

Per puzzle, anchor gap from (true rx via RSZ, bridge DEFAULT_RY).
Hunt shelf2 ± offset candidates whose pubkey gap matches anchor (exact or head).
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    DEFAULT_RY,
    N,
    resolve_true_r_xy,
    puzzle_band,
    pubkey_from_scalar,
)
from genesis_calibration import bridge_state  # noqa: E402
from gap_tier_common import gap_interval, sample_offsets_in_interval  # noqa: E402
from p135_160_shelf2_offset_hunt import build_cfg, ec_hit  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402
from unsolved_batch import UNSOLVED_PUZZLES  # noqa: E402

LOG = ROOT / "ARCHIVE" / "cloud_pages" / "unsolved_n_gap_transport_hunt.log"
CSV = ROOT / "ARCHIVE" / "unsolved_n_gap_transport_hunt.csv"


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def n_gap(px: int, py: int) -> int:
    return ((pow(py, 2, N) - 3) - (pow(px, 3, N) + 4)) % N


def head_dec(value: int, digits: int) -> str:
    s = str(value)
    return s[:digits] if len(s) >= digits else s


@dataclass(frozen=True)
class PuzzleAnchor:
    n: int
    rx: int
    ry_bridge: int
    gap: int
    lhs_n: int
    rhs_n: int
    r_source: str
    target_px: int
    target_py: int
    shelf2: int


def build_anchor(n: int, keys: dict) -> PuzzleAnchor:
    cfg = build_cfg(n, keys)
    st = bridge_state(cfg)
    rx, _ry_true, src = resolve_true_r_xy(cfg)
    ry_b = DEFAULT_RY
    pk = keys.get(n)
    px_t = pk.px if pk else cfg.Px[cfg.row]
    py_t = pk.py if pk else cfg.Py
    g = n_gap(rx, ry_b)
    return PuzzleAnchor(
        n=n,
        rx=rx,
        ry_bridge=ry_b,
        gap=g,
        lhs_n=(pow(rx, 3, N) + 4) % N,
        rhs_n=(pow(ry_b, 2, N) - 3) % N,
        r_source=src,
        target_px=px_t,
        target_py=py_t,
        shelf2=st["oitc"].shelf2,
    )


def gap_match(g: int, anchor: PuzzleAnchor, head: int) -> bool:
    if head > 0:
        return head_dec(g, head) == head_dec(anchor.gap, head)
    return g == anchor.gap


def hunt_one(
    anchor: PuzzleAnchor,
    *,
    samples: int,
    head: int,
    max_pass: int,
) -> list[dict]:
    n = anchor.n
    lo, hi, _top = puzzle_band(n)
    _, o_lo, o_hi = gap_interval(n, 1)
    rows: list[dict] = []
    tested = 0
    passed = 0

    log(f"=== P{n} N-GAP HUNT ===")
    log(f"  rx tail ...{str(anchor.rx)[-3:]}  ({anchor.r_source})")
    log(f"  lhs (x^3+4) mod N tail ...{str(anchor.lhs_n)[-3:]}")
    log(f"  rhs (y^2-3) mod N tail ...{str(anchor.rhs_n)[-3:]}")
    log(f"  anchor gap tail ...{str(anchor.gap)[-3:]} head2={head_dec(anchor.gap,2)} head3={head_dec(anchor.gap,3)}")
    log(f"  shelf2 bits {anchor.shelf2.bit_length()}  band [{lo}, {hi})")
    log(f"  filter: {'exact gap' if head == 0 else f'gap head{head}'}")

    for off in sample_offsets_in_interval(o_lo, o_hi, samples):
        for sign in (+1, -1):
            d = anchor.shelf2 + sign * off
            if not (lo <= d < hi):
                continue
            tested += 1
            x, y = pubkey_from_scalar(d)
            g = n_gap(x, y)
            if not gap_match(g, anchor, head):
                continue
            hit = ec_hit(d, anchor.target_px, anchor.target_py)
            if not hit:
                hit = ec_hit((N - d) % N, anchor.target_px, anchor.target_py)
            passed += 1
            row = {
                "n": n,
                "d": d,
                "d_hex": format(d, "064x"),
                "offset": sign * off,
                "gap_tail": str(g)[-3:],
                "gap_head2": head_dec(g, 2),
                "gap_head3": head_dec(g, 3),
                "px_tail": str(x)[-3:],
                "py_tail": str(y)[-3:],
                "ec_hit": hit,
            }
            rows.append(row)
            if hit:
                log(f"  *** EC HIT d={d} off={sign * off} ***")
            elif passed <= 5:
                log(f"  pass d={d} off={sign * off} gap_tail={row['gap_tail']}")
            if passed >= max_pass:
                break
        if passed >= max_pass:
            break

    log(f"  tested={tested} passed={passed} ec_hits={sum(1 for r in rows if r['ec_hit'])}")
    log("")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Unsolved batch N-gap transport hunt")
    ap.add_argument("--samples", type=int, default=200_000, help="offsets sampled per sign")
    ap.add_argument("--head", type=int, default=2, help="0=exact gap, else match first N decimal digits")
    ap.add_argument("--max-pass", type=int, default=30, help="max candidates per puzzle")
    args = ap.parse_args()

    LOG.write_text("", encoding="utf-8")
    keys = parse_53125()
    all_rows: list[dict] = []
    any_hit = False

    log("=== UNSOLVED BATCH N-GAP TRANSPORT HUNT ===")
    log(f"puzzles: {list(UNSOLVED_PUZZLES)}")
    log(f"samples/sign: {args.samples}  head: {args.head if args.head else 'exact'}")
    log("")

    for n in UNSOLVED_PUZZLES:
        anchor = build_anchor(n, keys)
        all_rows.extend(
            hunt_one(anchor, samples=args.samples, head=args.head, max_pass=args.max_pass)
        )

    if all_rows:
        with CSV.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            w.writeheader()
            w.writerows(all_rows)

    any_hit = any(r["ec_hit"] for r in all_rows)
    log("=== SUMMARY ===")
    for n in UNSOLVED_PUZZLES:
        sub = [r for r in all_rows if r["n"] == n]
        log(f"  P{n}: passed={len(sub)} ec_hits={sum(1 for r in sub if r['ec_hit'])}")
    log(f"csv -> {CSV}")
    log(f"log -> {LOG}")
    return 0 if any_hit else 1


if __name__ == "__main__":
    raise SystemExit(main())
