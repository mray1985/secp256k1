#!/usr/bin/env python3
"""
Structured P + kG → ECDLP walk for P135 / P160.

k is NOT brute 0..N. It is drawn from shelf2/gap offset geometry:
  - bridge offset terms (mod LO)
  - predicted offset-bit boundaries (n-10+{7,8,9} for row 0)
  - gap_mod_lo and gap±1 bit anchors
  - solved-puzzle offset transfers (P110–P130)
  - band D/8 lane spacing (ChatSieve)
  - alignment raw−shelf2 deltas

Backtrack: d = (d_k − k) mod N, certify [d]G == P.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from genesis_calibration import bridge_state  # noqa: E402
from gap_tier_common import observed_offset, offset_bits_to_interval  # noqa: E402
from p135_160_shelf2_offset_hunt import (  # noqa: E402
    ROW_DELTA,
    build_cfg,
    offset_bits_ok,
    predicted_offset_bits,
)
from probe_plus_g_ecdlp_walk import (  # noqa: E402
    WalkHit,
    gate_shifted,
    pubkey_for_puzzle,
)
from puzzle_catalog import load_catalog  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402
from unsolved_batch import offset_law_row  # noqa: E402
from ecdlp_full_pipeline import (  # noqa: E402
    N,
    build_alignment_candidates,
    build_bridge_offset_terms,
    p,
    puzzle_band,
)

OUT = ROOT / "ARCHIVE" / "plus_g_structured_walk.json"
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "plus_g_structured_walk.log"

# Solved high puzzles for offset transfer
TRANSFER_SOLVED = (110, 115, 120, 125, 130)


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def bit_boundary_samples(ob: int, *, cap: int = 16) -> list[int]:
    """Sample k at offset-bit boundaries without enumerating 2^ob."""
    if ob <= 0:
        return [0, 1]
    lo, hi = offset_bits_to_interval(ob)  # [2^(ob-1), 2^ob)
    if hi - lo <= cap:
        return list(range(lo, hi))
    mid = (lo + hi) // 2
    return sorted(
        {
            lo,
            lo + 1,
            lo + 2,
            mid - 1,
            mid,
            mid + 1,
            hi - 3,
            hi - 2,
            hi - 1,
        }
    )


def band_lane_k(n: int) -> list[int]:
    """ChatSieve D/8 lane spacing as k candidates."""
    lower = 1 << (n - 1)
    D = 1 << (n - 1)
    D8 = D // 8
    mid = lower + D // 2
    return [D8, mid - lower, mid + D8 - mid, (mid + D8) - (mid - D8)]


def structured_k_set(n: int, keys: dict) -> tuple[list[int], dict]:
    """Build deduped k list + metadata for puzzle n."""
    cfg = build_cfg(n, keys)
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(n)
    oitc = st["oitc"]
    sim = st["sim"]
    af = st["af"]
    lns = st["lambda_ns"]
    gap_val = st["gap"]
    gap_lo = gap_val % lo
    gap_bits = gap_lo.bit_length()
    shelf2 = oitc.shelf2
    law_row = offset_law_row(n, cfg.row)
    pred_obs = predicted_offset_bits(n, law_row)

    lam_p = (cfg.Px[cfg.row] * pow(cfg.rx[cfg.row], -1, p)) % p

    meta: dict = {
        "n": n,
        "shelf2_bits": shelf2.bit_length(),
        "gap_bits": gap_bits,
        "predicted_offset_bits": sorted(pred_obs),
        "law_row": law_row,
    }

    ks: set[int] = set()
    sources: dict[int, list[str]] = {}

    def add(k: int, src: str) -> None:
        k = int(k) % N
        if k == 0:
            return
        ks.add(k)
        sources.setdefault(k, []).append(src)

    # 1) Bridge offset terms
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
        add(off, f"bridge:{tname}")
        add(lo - off, f"bridge:LO-{tname}")
        if offset_bits_ok(off, n, law_row, gap_bits):
            add(off, f"bridge_filtered:{tname}")

    # 2) Alignment candidate deltas from shelf2
    align = build_alignment_candidates(
        af=af,
        oitc=oitc,
        sim=sim,
        lambda_ns=lns,
        gap=gap_val,
        lambda_p=lam_p,
        lambda_n_target=lam_p,
    )
    for name, d, raw in align:
        delta_k = (raw - shelf2) % lo
        if delta_k:
            add(delta_k, f"align_delta:{name[:40]}")
        add((d - shelf2) % lo, f"align_d:{name[:40]}")

    # 3) Predicted offset-bit boundaries + gap tier
    obs_set = set(pred_obs) | {gap_bits, max(1, gap_bits - 1), gap_bits + 1}
    for ob in sorted(obs_set):
        for k in bit_boundary_samples(ob):
            add(k, f"bit_boundary:ob={ob}")

    add(gap_lo, "gap_mod_lo")
    add((N - gap_lo) % lo, "N-gap_mod_lo")

    # 4) Solved-puzzle offset transfer
    for sn in TRANSFER_SOLVED:
        if sn not in keys or keys[sn].d == 0:
            continue
        scfg = build_cfg(sn, keys)
        sst = bridge_state(scfg)
        slo, _, _ = puzzle_band(sn)
        off = observed_offset(keys[sn].d, sst["oitc"].shelf2, slo)
        add(off, f"transfer:P{sn}_offset")
        add(off % lo, f"transfer:P{sn}_offset_mod_lo")

    # 5) Band lane spacing
    for k in band_lane_k(n):
        add(k, "band_D8")

    # 6) Small belt
    for k in range(1, 65):
        add(k, "small_k")

    ordered = sorted(ks)
    meta["n_k"] = len(ordered)
    meta["sources_sample"] = {str(k): sources[k][:3] for k in ordered[:20]}
    return ordered, meta


def walk_structured(n: int, keys: dict, cat: dict) -> tuple[list[WalkHit], dict]:
    px, py = pubkey_for_puzzle(n, cat, keys)
    ks, meta = structured_k_set(n, keys)
    log(f"=== P{n} structured walk: {len(ks)} k values ===")
    log(f"  shelf2_bits={meta['shelf2_bits']} gap_bits={meta['gap_bits']} pred_ob={meta['predicted_offset_bits']}")

    hits: list[WalkHit] = []
    t0 = time.time()
    for i, k in enumerate(ks):
        for h in gate_shifted(n, px, py, k):
            hits.append(h)
            log(f"*** HIT P{n} k={k} d={h.d_backtrack} [{h.candidate_name}] ***")
            meta["hit_k"] = k
            return hits, meta
        if (i + 1) % 100 == 0:
            log(f"  P{n} {i+1}/{len(ks)} k scanned ({time.time()-t0:.1f}s)")
    log(f"  P{n} done: {len(ks)} k, 0 hits ({time.time()-t0:.1f}s)")
    return hits, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puzzle", type=int, nargs="+", default=[135, 160])
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    LOG.write_text("", encoding="utf-8")
    keys = parse_53125()
    cat = load_catalog()
    report: dict = {"puzzles": {}}

    for n in args.puzzle:
        hits, meta = walk_structured(n, keys, cat)
        report["puzzles"][str(n)] = {
            "meta": meta,
            "hits": [h.__dict__ for h in hits],
            "solved": bool(hits),
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log(f"Wrote {args.out}")
    return 0 if any(report["puzzles"][str(n)]["solved"] for n in args.puzzle) else 2


if __name__ == "__main__":
    raise SystemExit(main())
