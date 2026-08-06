#!/usr/bin/env python3
"""
Walk P + k*G through the ECDLP alignment gate.

If P_k = P + k*G yields pipeline hit d_k with [d_k]G = P_k,
backtrack: d = (d_k - k) mod N, certify [d]G == P and d in puzzle band.

Calibration: P5 (solved tiny puzzle) — walk must backtrack to true d at each k.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdsa import SECP256k1
from ecdsa.ellipticcurve import Point

from ecdlp_full_pipeline import (  # noqa: E402
    DEFAULT_GX,
    DEFAULT_RX,
    DEFAULT_RY,
    N,
    PuzzleConfig,
    add_c_bracket_candidates,
    add_matrix_candidates,
    apply_puzzle_defaults,
    build_alignment_candidates,
    build_d_candidates,
    carry,
    compute_alignment_frame,
    compute_order_in_the_court,
    compute_shelf_iteration_matrix,
    delta,
    oitc_notebook_d_cong,
    p,
    pubkey_from_scalar,
    puzzle_band,
    y_even,
    all_cube_roots_mod_p,
)
from puzzle_catalog import load_catalog
from puzzle_keys_53125 import parse_53125

CURVE = SECP256k1.curve
ORDER = SECP256k1.order
G_PT = SECP256k1.generator


@dataclass
class WalkHit:
    puzzle: int
    k_shift: int
    d_found: int
    d_backtrack: int
    in_band: bool
    candidate_name: str
    px_shift: int
    py_shift: int


def point_plus_kG(px: int, py: int, k: int) -> tuple[int, int]:
    P = Point(CURVE, px, py, ORDER)
    R = P + (k % N) * G_PT
    return int(R.x()), int(R.y())


def build_cfg_for_point(n: int, px: int, py: int) -> PuzzleConfig:
    cfg = PuzzleConfig(puzzle_num=n)
    apply_puzzle_defaults(cfg)
    px_roots = sorted(all_cube_roots_mod_p((py * py - 7) % p, witness=px))
    if px not in px_roots:
        px_roots = sorted(all_cube_roots_mod_p((py * py - 7) % p))
    cfg.Px = px_roots
    cfg.row = px_roots.index(px)
    cfg.Py = py
    if n in (135, 160):
        cfg.rx = list(DEFAULT_RX)
        cfg.ry = DEFAULT_RY
        cfg.Gx = list(DEFAULT_GX)
    cfg.known_d = None
    return cfg


def pipeline_hits(cfg: PuzzleConfig) -> list[tuple[str, int]]:
    """Scorecard-aligned candidate pool; skip scalar 0."""
    lo, hi, _ = puzzle_band(cfg.puzzle_num)
    py, ry = cfg.Py, cfg.ry
    row = cfg.row
    px, rx = cfg.Px, cfg.rx

    lam_p = (px[row] * pow(rx[row], -1, p)) % p
    lam_n = (px[row] * pow(rx[row], -1, N)) % N
    lam_ns = [(px[i] * pow(rx[i], -1, N)) % N for i in range(3)]
    lam_y_n = (py * pow(ry, -1, N)) % N
    gap = (lam_ns[row] - lam_p) % N
    qx = [(x * delta) % N for x in rx]
    qx_s = [(x * delta) % N for x in px]

    oitc = compute_order_in_the_court(
        lo=lo,
        qx=qx,
        qy=(ry * delta) % N,
        qx_scaled=qx_s,
        qy_scaled=(py * delta) % N,
        lambda_ns=lam_ns,
        lam_y_n=lam_y_n,
    )
    sim = compute_shelf_iteration_matrix(lo, [oitc.shelf2, oitc.shelf3, oitc.shelf_y])
    af = compute_alignment_frame(oitc=oitc, sim=sim, lo=lo, hi=hi, known_d=None)

    b_x_own: list[int | None] = []
    for i in range(3):
        ok, _, b = carry(lam_ns[i] * qx[i] - qx_s[i], N)
        b_x_own.append(b if ok else None)

    candidates = build_d_candidates(
        lo=lo,
        hi=hi,
        lambda_p=lam_p,
        lambda_ns=lam_ns,
        lam_y_n=lam_y_n,
        lambda_n_target=lam_n,
        b_x_own=b_x_own,
    )
    add_c_bracket_candidates(candidates, oitc.c_floor, oitc.c_plus1, oitc.c_minus1, oitc.c_minus2)
    for track, d_cong in oitc_notebook_d_cong(oitc):
        if d_cong not in {c[1] for c in candidates}:
            candidates.append((f"d congruent ({track})", d_cong, d_cong))
    add_matrix_candidates(candidates, sim)
    seen = {c[1] for c in candidates}
    for name, d, raw in build_alignment_candidates(
        af=af,
        oitc=oitc,
        sim=sim,
        lambda_ns=lam_ns,
        gap=gap,
        lambda_p=lam_p,
        lambda_n_target=lam_n,
    ):
        if d not in seen:
            candidates.append((name, d, raw))
            seen.add(d)

    hits: list[tuple[str, int]] = []
    for name, d, _raw in candidates:
        if d % N == 0:
            continue
        pub_x, pub_y = pubkey_from_scalar(d)
        if any(pub_x == px[i] and pub_y == py for i in range(3)):
            hits.append((name, d))
    return hits


def gate_shifted(n: int, px0: int, py0: int, k: int) -> list[WalkHit]:
    px_k, py_k = point_plus_kG(px0, py0, k)
    cfg = build_cfg_for_point(n, px_k, py_k)
    lo, hi = cfg.lo, cfg.hi
    out: list[WalkHit] = []
    for name, d in pipeline_hits(cfg):
        d_back = (d - k) % N
        if not (lo <= d_back < hi):
            continue
        bx, by = pubkey_from_scalar(d_back)
        if bx == px0 and by == py0:
            out.append(
                WalkHit(
                    puzzle=n,
                    k_shift=k,
                    d_found=d,
                    d_backtrack=d_back,
                    in_band=True,
                    candidate_name=name,
                    px_shift=px_k,
                    py_shift=py_k,
                )
            )
    return out


def pubkey_for_puzzle(n: int, cat: dict, keys: dict) -> tuple[int, int]:
    if n in keys and keys[n].px and keys[n].py:
        return keys[n].px, keys[n].py
    entry = cat[n]
    comp = entry.public_key
    px = int(comp[2:], 16)
    prefix = comp[:2]
    py = y_even(px) if prefix == "02" else (p - y_even(px)) % p
    return px, py


def calibrate_p5(k_max: int = 7) -> dict:
    keys = parse_53125()
    pk = keys[5]
    rows = []
    for k in range(0, min(k_max, 7) + 1):
        hits = gate_shifted(5, pk.px, pk.py, k)
        back_ok = any(h.d_backtrack == pk.d for h in hits)
        rows.append({"k": k, "n_hits": len(hits), "backtrack_ok": back_ok})
    return {
        "puzzle": 5,
        "true_d": pk.d,
        "rows": rows,
        "walk_viable_small": all(r["backtrack_ok"] for r in rows),
    }


def walk_puzzle(n: int, k_max: int, *, stride: int = 1) -> list[WalkHit]:
    cat = load_catalog()
    keys = parse_53125()
    px, py = pubkey_for_puzzle(n, cat, keys)
    hits: list[WalkHit] = []
    t0 = time.time()
    tested = 0
    for k in range(0, k_max + 1, stride):
        tested += 1
        for h in gate_shifted(n, px, py, k):
            hits.append(h)
            print(
                f"*** HIT P{n} k={k} d={h.d_backtrack} via {h.candidate_name} "
                f"({time.time() - t0:.1f}s) ***",
                flush=True,
            )
            return hits
        if tested % 64 == 0:
            print(f"  P{n} k={k} ({tested} shifts, {time.time() - t0:.1f}s)", flush=True)
    print(f"  P{n} done: {tested} shifts, 0 certified hits ({time.time() - t0:.1f}s)", flush=True)
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description="P + kG ECDLP walk with backtrack")
    ap.add_argument("--puzzle", type=int, nargs="+", default=[135, 160])
    ap.add_argument("--k-max", type=int, default=2048)
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--calibrate", action="store_true", help="Run P5 sanity first")
    ap.add_argument("--out", type=Path, default=ROOT / "ARCHIVE" / "plus_g_ecdlp_walk.json")
    args = ap.parse_args()

    report: dict = {"k_max": args.k_max, "stride": args.stride, "puzzles": {}}

    if args.calibrate:
        print("=== P5 calibration (tiny solved puzzle) ===", flush=True)
        cal = calibrate_p5(args.k_max)
        report["calibration_p5"] = cal
        print(f"  walk backtracks on P5: {cal['walk_viable_small']}", flush=True)

    for n in args.puzzle:
        print(f"=== P{n} walk P + kG, k=0..{args.k_max} ===", flush=True)
        hits = walk_puzzle(n, args.k_max, stride=args.stride)
        report["puzzles"][str(n)] = {
            "hits": [asdict(h) for h in hits],
            "solved": len(hits) > 0,
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}", flush=True)
    return 0 if any(report["puzzles"][str(n)]["solved"] for n in args.puzzle) else 2


if __name__ == "__main__":
    raise SystemExit(main())
