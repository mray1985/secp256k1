#!/usr/bin/env python3
"""
Regress (d - shelf2) mod LO on solved high puzzles, then hunt P135.

1. Find pair-term formulas offset = (t_a ± t_b) mod LO that recover solved d.
2. Apply surviving row-specific formulas to P135 (row=2).
3. EC gate + tight ±scroll on hits-near-misses.
"""

from __future__ import annotations

import itertools
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import build_config
from ecdlp_full_pipeline import (
    N,
    PuzzleConfig,
    apply_puzzle_defaults,
    band_representative,
    build_bridge_offset_terms,
    p,
    puzzle_band,
    pubkey_from_scalar,
)
from gap_tier_common import d_candidates_from_offset, observed_offset
from genesis_calibration import bridge_state
from puzzle_keys_53125 import parse_53125

try:
    from ecdsa import SECP256k1

    G = SECP256k1.generator
    _HAS_G = True
except ImportError:
    _HAS_G = False

PX135 = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY135 = 46351506704828816385393879789131775975171267756561783641521771795450741674800
ROW_DELTA = {0: (7, 8, 9), 1: (8, 9), 2: (7, 8)}
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_offset_regress_hunt.log"
SCROLL = 250_000


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def build_p135_cfg() -> PuzzleConfig:
    cfg = PuzzleConfig(puzzle_num=135)
    apply_puzzle_defaults(cfg)
    keys = parse_53125()
    pk = keys[135]
    cfg.Py = pk.py
    return cfg


def bridge_terms_for_cfg(cfg: PuzzleConfig) -> tuple[dict, dict]:
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(cfg.puzzle_num)
    lam_p = (cfg.Px[cfg.row] * pow(cfg.rx[cfg.row], -1, p)) % p
    terms = build_bridge_offset_terms(
        oitc=st["oitc"],
        sim=st["sim"],
        lambda_ns=st["lambda_ns"],
        lo=lo,
        hi=hi,
        gap=st["gap"],
        lambda_p=lam_p,
        lambda_n_target=lam_p,
    )
    return st, dict(terms)


def offset_bits_ok(n: int, row: int, off: int, gap_bits: int) -> bool:
    if off <= 0:
        return False
    ob = off.bit_length()
    pred = {n - 10 + d for d in ROW_DELTA.get(row, (7, 8, 9))}
    return ob in pred or ob in {gap_bits, max(1, gap_bits - 1), gap_bits + 1}


def ec_hit_scalar(d: int, px: int, py: int) -> bool:
    try:
        x, y = pubkey_from_scalar(d)
        return x == px and y == py
    except Exception:
        return False


def ec_hit_fast(d: int, px: int, py: int) -> bool:
    if not _HAS_G:
        return ec_hit_scalar(d, px, py)
    pt = d * G
    return pt.x() == px and pt.y() == py


def scroll(center: int, px: int, py: int, lo: int, hi: int, label: str) -> int | None:
    if ec_hit_fast(center, px, py):
        log(f"  *** HIT d={center} [{label}] direct ***")
        return center
    pt = center * G
    p_fwd = pt
    for i in range(1, SCROLL + 1):
        d = center + i
        if d >= hi:
            break
        p_fwd = p_fwd + G
        if p_fwd.x() == px and p_fwd.y() == py:
            log(f"  *** HIT d={d} [{label}] +{i} ***")
            return d
    p_bwd = pt
    for i in range(1, SCROLL + 1):
        d = center - i
        if d < lo:
            break
        p_bwd = p_bwd + (-G)
        if p_bwd.x() == px and p_bwd.y() == py:
            log(f"  *** HIT d={d} [{label}] -{i} ***")
            return d
    return None


def regress_pair_formulas(keys: dict) -> dict[int, list[tuple[str, str]]]:
    """Return row -> list of (formula_name, op) that hit solved puzzles in that row."""
    row_hits: dict[int, dict[str, int]] = {0: {}, 1: {}, 2: {}}
    row_total: dict[int, int] = {0: 0, 1: 0, 2: 0}

    for n in sorted(keys):
        pk = keys[n]
        if pk.d == 0 or n < 70:
            continue
        try:
            cfg = build_config(pk)
        except Exception:
            continue
        st, term_map = bridge_terms_for_cfg(cfg)
        lo, hi, _ = puzzle_band(n)
        shelf2 = st["oitc"].shelf2
        o_true = observed_offset(pk.d, shelf2, lo)
        items = list(term_map.items())
        row = cfg.row
        row_total[row] = row_total.get(row, 0) + 1

        for (na, va), (nb, vb) in itertools.combinations(items, 2):
            for op_name, off in (
                (f"{na}+{nb}", (va + vb) % lo),
                (f"{na}-{nb}", (va - vb) % lo),
                (f"{nb}-{na}", (vb - va) % lo),
            ):
                for d in (shelf2 + off, shelf2 - off, shelf2 + off - lo, shelf2 - off + lo):
                    if lo <= d < hi and d == pk.d:
                        row_hits[row][op_name] = row_hits[row].get(op_name, 0) + 1

        # single terms too
        for name, off in term_map.items():
            for d in (shelf2 + off, shelf2 - off, shelf2 + off - lo, shelf2 - off + lo):
                if lo <= d < hi and d == pk.d:
                    row_hits[row][f"single:{name}"] = row_hits[row].get(f"single:{name}", 0) + 1

    out: dict[int, list[tuple[str, str]]] = {}
    for row in (0, 1, 2):
        total = row_total.get(row, 0)
        ranked = sorted(row_hits[row].items(), key=lambda x: -x[1])
        out[row] = [(name, f"{cnt}/{total}") for name, cnt in ranked if cnt >= 2]
    return out


def hunt_p135(formulas_by_row: dict[int, list[tuple[str, str]]]) -> int:
    cfg = build_p135_cfg()
    st, term_map = bridge_terms_for_cfg(cfg)
    lo, hi, _ = puzzle_band(135)
    shelf2 = st["oitc"].shelf2
    row = cfg.row
    gap_bits = (st["gap"] % lo).bit_length()
    px, py = cfg.Px[row], cfg.Py

    log(f"P135 row={row} shelf2_bits={shelf2.bit_length()} gap_bits={gap_bits}")
    log(f"  row-2 regression formulas (≥2 hits): {formulas_by_row.get(2, [])[:12]}")

    seen: set[int] = set()
    candidates: list[tuple[str, int]] = []

    def add(name: str, d: int) -> None:
        if lo <= d < hi and d not in seen:
            seen.add(d)
            candidates.append((name, d))

    # Apply top row-2 pair formulas
    for formula, score in formulas_by_row.get(2, [])[:40]:
        if formula.startswith("single:"):
            off = term_map.get(formula[7:])
            if off is None:
                continue
            for d, _dir in d_candidates_from_offset(shelf2, off, lo, hi):
                if offset_bits_ok(135, row, observed_offset(d, shelf2, lo), gap_bits):
                    add(f"{formula} ({score})", d)
        else:
            if "+" in formula and not formula.startswith("single"):
                na, nb = formula.split("+", 1)
                if na in term_map and nb in term_map:
                    off = (term_map[na] + term_map[nb]) % lo
                else:
                    continue
            elif "-" in formula:
                na, nb = formula.split("-", 1)
                if na in term_map and nb in term_map:
                    off = (term_map[na] - term_map[nb]) % lo
                else:
                    continue
            else:
                continue
            if not offset_bits_ok(135, row, off, gap_bits):
                continue
            for d, _dir in d_candidates_from_offset(shelf2, off, lo, hi):
                add(f"{formula} ({score})", d)

    # Carry band reps from carry_joint
    from p135_carry_joint import bridge_ints

    b = bridge_ints(cfg)
    for i in range(3):
        sh = b["shifts"][i]
        if sh:
            add(f"carry_row{i+1}", band_representative(sh[0], lo, hi))

    # lift68
    add("lift68", int("68805bb705259f04f28b88cf897c603c9", 16))

    log(f"  candidates after regression: {len(candidates)}")

    for name, d in candidates:
        if ec_hit_fast(d, px, py):
            log(f"  *** HIT d={d} [{name}] ***")
            return 0
        if ec_hit_fast((N - d) % N, px, py):
            log(f"  *** HIT mirror N-d={(N-d)%N} from d={d} [{name}] ***")
            return 0

    # Scroll top 12 by name priority
    priority = [c for c in candidates if "lift68" in c[0] or "carry" in c[0]]
    priority += [c for c in candidates if c not in priority][:12 - len(priority)]
    log(f"  scrolling {len(priority)} anchors ±{SCROLL}")
    for name, d in priority[:12]:
        hit = scroll(d, px, py, lo, hi, name)
        if hit:
            return 0

    return 1


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    keys = parse_53125()
    log("=== pair-term regression on solved P70+ ===")
    formulas = regress_pair_formulas(keys)
    for row in (0, 1, 2):
        log(f"  row {row}: {formulas[row][:8]}")
    log("")
    rc = hunt_p135(formulas)
    log(f"done in {time.perf_counter() - t0:.1f}s")
    return rc


if __name__ == "__main__":
    sys.exit(main())
