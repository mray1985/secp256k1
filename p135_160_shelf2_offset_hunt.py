#!/usr/bin/env python3
"""
Shelf2 + offset hunt for unsolved batch P135, P140, P145, P150, P155, P160.

Preferred entry: solve_batch.py (always runs all six).

Uses row-calibrated offset bit windows from solved high puzzles:
  row 0: offset_bits ~ (n-10) + {7,8,9}  ← all six (n≡0 mod 5)
  row 1: offset_bits ~ (n-10) + {8,9}
  row 2: offset_bits ~ (n-10) + {7,8}
Also accepts gap_mod_lo_bits ± 1.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (
    DEFAULT_GX,
    DEFAULT_RX,
    DEFAULT_RY,
    N,
    PuzzleConfig,
    all_cube_roots_mod_p,
    apply_puzzle_defaults,
    band_representative,
    build_alignment_candidates,
    build_bridge_offset_terms,
    p,
    puzzle_band,
    pubkey_from_scalar,
)
from genesis_calibration import bridge_state
from gap_tier_common import observed_offset
from puzzle_keys_53125 import parse_53125

try:
    from ecdsa import SECP256k1  # noqa: F401

    _HAS_ECDSA = True
except ImportError:
    _HAS_ECDSA = False

from unsolved_batch import UNSOLVED_PUZZLES, offset_law_row  # noqa: E402

LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_160_shelf2_offset_hunt.log"
ROW_DELTA = {0: (7, 8, 9), 1: (8, 9), 2: (7, 8)}
PUZZLES = list(UNSOLVED_PUZZLES)


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def predicted_offset_bits(n: int, row: int) -> set[int]:
    return {n - 10 + d for d in ROW_DELTA.get(row, (7, 8, 9))}


def build_cfg(n: int, keys: dict) -> PuzzleConfig:
    """P135: notebook DEFAULT_PX + row 2. P160: OITC block. Others: sorted Px cube roots."""
    pk = keys.get(n)
    if n == 160:
        cfg = PuzzleConfig(puzzle_num=160)
        apply_puzzle_defaults(cfg)
        return cfg
    if n == 135:
        cfg = PuzzleConfig(puzzle_num=135)
        apply_puzzle_defaults(cfg)
        if pk:
            cfg.Py = pk.py
            if cfg.Px[cfg.row] != pk.px:
                for i, px in enumerate(cfg.Px):
                    if px == pk.px:
                        cfg.row = i
                        break
        return cfg
    cfg = PuzzleConfig(puzzle_num=n)
    apply_puzzle_defaults(cfg)
    if pk and pk.px and pk.py:
        px_roots = sorted(all_cube_roots_mod_p((pk.py * pk.py - 7) % p, witness=pk.px))
        if pk.px not in px_roots:
            px_roots = sorted(all_cube_roots_mod_p((pk.py * pk.py - 7) % p))
        cfg.Px = px_roots
        cfg.rx = list(DEFAULT_RX)
        cfg.Py = pk.py
        cfg.ry = DEFAULT_RY
        cfg.Gx = list(DEFAULT_GX)
        cfg.row = px_roots.index(pk.px)
    return cfg


def ec_hit(d: int, px: int, py: int) -> bool:
    if not _HAS_ECDSA:
        return False
    try:
        x, y = pubkey_from_scalar(d)
        return x == px and y == py
    except Exception:
        return False


def offset_bits_ok(off: int, n: int, row: int, gap_bits: int) -> bool:
    if off <= 0:
        return False
    ob = off.bit_length()
    if ob in predicted_offset_bits(n, row):
        return True
    return ob in {gap_bits, max(1, gap_bits - 1), gap_bits + 1}


def hunt_one(n: int, keys: dict, *, offset_row: int | None = None) -> list[dict]:
    cfg = build_cfg(n, keys)
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(n)
    af = st["af"]
    oitc = st["oitc"]
    sim = st["sim"]
    lns = st["lambda_ns"]
    px_slot = cfg.row
    law_row = offset_row if offset_row is not None else offset_law_row(n, px_slot)
    px = cfg.Px[px_slot]
    py = cfg.Py
    lam_p = (cfg.Px[px_slot] * pow(cfg.rx[px_slot], -1, p)) % p
    gap_val = st["gap"]
    gap_lo = gap_val % lo
    gap_bits = gap_lo.bit_length()
    shelf2 = oitc.shelf2
    pred = sorted(predicted_offset_bits(n, law_row))

    log(
        f"=== P{n} px_slot={px_slot} offset_law_row={law_row} "
        f"shelf2_bits={shelf2.bit_length()} gap_bits={gap_bits} ==="
    )
    log(f"  predicted offset_bits: {pred} (+ gap±1)")

    seen: set[int] = set()
    results: list[dict] = []

    def try_d(name: str, d: int) -> None:
        if not (lo <= d < hi):
            d2 = band_representative(d, lo, hi)
            if lo <= d2 < hi:
                d = d2
            else:
                return
        if d in seen:
            return
        off = observed_offset(d, shelf2, lo)
        if not offset_bits_ok(off, n, law_row, gap_bits):
            return
        seen.add(d)
        hit = ec_hit(d, px, py)
        if not hit:
            hit = ec_hit((N - d) % N, px, py)
        rec = {
            "n": n,
            "d": d,
            "d_hex": format(d, "064x"),
            "offset_bits": off.bit_length(),
            "gap_bits": gap_bits,
            "px_slot": px_slot,
            "offset_law_row": law_row,
            "ec_hit": hit,
            "source": name,
        }
        results.append(rec)
        if hit:
            log(f"  *** HIT P{n} d={d} [{name}] ***")

    # Alignment lattice
    for name, d, _raw in build_alignment_candidates(
        af=af,
        oitc=oitc,
        sim=sim,
        lambda_ns=lns,
        gap=gap_val,
        lambda_p=lam_p,
        lambda_n_target=lam_p,
    ):
        try_d(f"align:{name}", d)

    # shelf2 + bridge terms filtered by bit window
    terms = build_bridge_offset_terms(
        oitc=oitc,
        sim=sim,
        lambda_ns=lns,
        lo=lo,
        hi=hi,
        gap=gap_val,
        lambda_p=lam_p,
        lambda_n_target=lam_p,
        calibrated_offset=None,
    )
    for tname, off in terms:
        if not offset_bits_ok(off, n, law_row, gap_bits):
            continue
        d = shelf2 + off
        try_d(f"shelf2+({tname})", d)
        d2 = shelf2 - off
        try_d(f"shelf2-({tname})", d2)

    # P135 lane-68 lift anchor if available
    if n == 135:
        try:
            from p135_f97_nibble_lift import (
                calibrate_f97_nibbles,
                calibrate_segment_offsets,
                f97_pattern,
                lift_with_f97_nibbles,
            )

            k130 = keys[130]
            priv130 = format(k130.d, "x").lower().lstrip("0")
            seg_offs = calibrate_segment_offsets(
                format(k130.px, "x"), format(k130.py, "x"), priv130
            )
            f97_offs, _ = calibrate_f97_nibbles(
                format(px, "x"), format(py, "x"), f97_pattern(), "f897c603"
            )
            lift = lift_with_f97_nibbles(
                format(px, "x"), format(py, "x"), seg_offs, f97_pattern(), f97_offs
            )
            sig = ("68" + lift[2:])[:34].ljust(34, "0")
            try_d("lift68", int(sig, 16))
        except Exception as exc:
            log(f"  lift68 skip: {exc}")

    log(f"  filtered candidates: {len(results)}  hits: {sum(1 for r in results if r['ec_hit'])}")
    log("")
    return results


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    keys = parse_53125()
    all_results: list[dict] = []
    any_hit = False

    log("Unsolved batch shelf2+offset hunt (P135–P160, row-0 offset law for n≡0 mod 5)")
    log(f"ECDSA: {_HAS_ECDSA}")
    log("")

    for n in PUZZLES:
        all_results.extend(hunt_one(n, keys))

    csv_path = ROOT / "ARCHIVE" / "p135_160_shelf2_offset_hunt.csv"
    if all_results:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(all_results[0].keys()))
            w.writeheader()
            w.writerows(all_results)

    for n in PUZZLES:
        sub = [r for r in all_results if r["n"] == n]
        hits = [r for r in sub if r["ec_hit"]]
        log(f"P{n}: {len(sub)} candidates, {len(hits)} hit(s)")
        if hits:
            any_hit = True
            for h in hits:
                log(f"  HIT {h['d_hex']} {h['source']}")

    log(f"wrote {csv_path}")
    return 0 if any_hit else 1


if __name__ == "__main__":
    sys.exit(main())
