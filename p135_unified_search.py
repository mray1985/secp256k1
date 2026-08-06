#!/usr/bin/env python3
"""
P135 unified bridge search — best-effort priority stack:

1. Row-2 calibration (solved puzzles on epsilon row 2)
2. Gap-tier filter on shelf2 offset (gap 1 then 2 intervals)
3. Full alignment lattice (anchors + bridge terms) filtered by tier
4. k-lane direct d + k-implied offsets
5. EC gate d*G==P

Skips integer factorization / Pollard-rho on auxiliary Q (not bridge-aligned).
"""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import build_config  # noqa: E402
from ecdlp_full_pipeline import (  # noqa: E402
    PuzzleConfig,
    apply_puzzle_defaults,
    band_representative,
    build_alignment_candidates,
    build_bridge_offset_terms,
    pubkey_from_scalar,
    puzzle_band,
)
from gap_tier_common import (  # noqa: E402
    d_candidates_from_offset,
    gap_from_observed,
    gap_interval,
    observed_offset,
    offset_in_gap_tier,
)
from genesis_calibration import bridge_state  # noqa: E402
from k_xy_mod134_distance import bridge_k_pair, puzzle_k_transforms  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

try:
    from ecdsa import SECP256k1  # noqa: F401

    _HAS_ECDSA = True
except ImportError:
    _HAS_ECDSA = False

H = 135
ROW2_PUZZLES = [15, 35, 45, 50, 70, 90, 100, 120]


def ec_hit(d: int, px: int, py: int) -> bool:
    if not _HAS_ECDSA:
        return False
    try:
        x, y = pubkey_from_scalar(d)
        return x == px and y == py
    except Exception:
        return False


def min_k_gap_bits(d: int, kx: int, ky: int) -> tuple[int, str]:
    best = 1 << 300
    lbl = ""
    for prefix, k in (("kx", kx), ("ky", ky)):
        t = puzzle_k_transforms(H, k)
        for tag, val in (("r1", t["floor_lift"]), ("r2", t["height_residue"])):
            dist = abs(d - val)
            if dist < best:
                best = dist
                lbl = f"{prefix}_{tag}"
    return best.bit_length(), lbl


def tier_of_offset(o: int) -> int | None:
    if o <= 0:
        return None
    for gap in (1, 2):
        if offset_in_gap_tier(o, H, gap):
            return gap
    return None


def calibrate_row2(keys: dict) -> list[str]:
    lines = ["ROW-2 CALIBRATION (epsilon row = 2 solved puzzles)", ""]
    term_hits: Counter[str] = Counter()
    gap_ctr: Counter[int] = Counter()

    for n in ROW2_PUZZLES:
        if n not in keys:
            continue
        pk = keys[n]
        cfg = build_config(pk)
        st = bridge_state(cfg)
        lo, hi, _ = puzzle_band(n)
        shelf2 = st["oitc"].shelf2
        true_off = (pk.d - shelf2) % lo
        gap, ob = gap_from_observed(pk.d, shelf2, n, lo)
        gap_ctr[gap] += 1
        row_cfg = cfg.row
        from ecdlp_full_pipeline import p as FIELD_P

        lam_p = (cfg.Px[row_cfg] * pow(cfg.rx[row_cfg], -1, FIELD_P)) % FIELD_P
        raw_terms = build_bridge_offset_terms(
            oitc=st["oitc"],
            sim=st["sim"],
            lambda_ns=st["lambda_ns"],
            lo=lo,
            hi=hi,
            gap=st["gap"],
            lambda_p=lam_p,
            lambda_n_target=lam_p,
            calibrated_offset=None,
        )
        hits = [name for name, v in raw_terms if v == true_off]
        for h in hits:
            term_hits[h] += 1
        lines.append(
            f"  P{n}: gap={gap} offset_bits={ob}  term_exact={hits[:2] or 'none'}"
        )

    lines += [
        "",
        f"  gap distribution: {dict(sorted(gap_ctr.items()))}",
        "  top exact bridge terms across row-2:",
    ]
    for name, cnt in term_hits.most_common(8):
        lines.append(f"    {cnt}/{len(ROW2_PUZZLES)}  {name}")
    lines.append("")
    return lines


def generate_p135_candidates(st: dict, lo: int, hi: int) -> list[tuple[str, int, int | None]]:
    """name, d, gap_tier (None if outside gap 1/2 from shelf2)."""
    cfg = st["cfg"]
    af = st["af"]
    oitc = st["oitc"]
    sim = st["sim"]
    lns = st["lambda_ns"]
    row = cfg.row
    px = cfg.Px[row]
    from ecdlp_full_pipeline import p as FIELD_P

    lam_p = (cfg.Px[row] * pow(cfg.rx[row], -1, FIELD_P)) % FIELD_P
    gap_val = st["gap"]
    shelf2 = oitc.shelf2

    out: dict[int, tuple[str, int | None]] = {}

    def put(d: int, name: str, tier: int | None) -> None:
        d = d % hi  # keep canonical band rep when possible
        if not (lo <= d < hi):
            d2 = band_representative(d, lo, hi)
            if lo <= d2 < hi:
                d = d2
            else:
                return
        off = observed_offset(d, shelf2, lo)
        t = tier if tier is not None else tier_of_offset(off)
        prev = out.get(d)
        if prev is None:
            out[d] = (name, t)
        elif t is not None and prev[1] is None:
            out[d] = (name, t)

    # A) Pipeline alignment lattice
    for name, d, _raw in build_alignment_candidates(
        af=af,
        oitc=oitc,
        sim=sim,
        lambda_ns=lns,
        gap=gap_val,
        lambda_p=lam_p,
        lambda_n_target=lam_p,
    ):
        put(d, f"align:{name}", tier_of_offset(observed_offset(d, shelf2, lo)))

    # B) shelf2 ± o for every bridge term o in gap tiers
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
    for gap in (1, 2):
        _, o_lo, o_hi = gap_interval(H, gap)
        for name, off in terms:
            if not (o_lo <= off < o_hi):
                continue
            for d, direction in d_candidates_from_offset(shelf2, off, lo, hi):
                put(d, f"tier{gap}:shelf2{direction}({name})", gap)

    # C) k-lane
    kx, ky, _, _ = bridge_k_pair(cfg)
    for label, k in (
        ("k_x", kx),
        ("k_y_same", ky),
    ):
        t = puzzle_k_transforms(H, k)
        for tag, val in (("r1", t["floor_lift"]), ("r2", t["height_residue"])):
            put(val, f"k:{label}_{tag}", tier_of_offset(observed_offset(val, shelf2, lo)))
        off = (t["floor_lift"] - shelf2) % lo
        if tier_of_offset(off):
            for d, direction in d_candidates_from_offset(shelf2, off, lo, hi):
                put(d, f"koff:{label}_r1:{direction}", tier_of_offset(off))

    rows = [(d, name, tier) for d, (name, tier) in out.items()]
    rows.sort(key=lambda x: (x[2] is None, x[2] or 99, x[0]))
    return [(name, d, tier) for d, name, tier in rows]


def main() -> None:
    keys = parse_53125()
    lines = calibrate_row2(keys)
    lines += [
        "=" * 72,
        f"P135 UNIFIED SEARCH (H={H}, row=2)",
        f"ECDSA available: {_HAS_ECDSA}",
        "",
    ]

    cfg = PuzzleConfig(puzzle_num=H, row=2)
    apply_puzzle_defaults(cfg)
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(H)
    px = cfg.Px[cfg.row]
    py = cfg.Py
    shelf2 = st["oitc"].shelf2

    kx, ky, _, _ = bridge_k_pair(cfg)
    cands = generate_p135_candidates(st, lo, hi)

    tier1 = [c for c in cands if c[2] == 1]
    tier2 = [c for c in cands if c[2] == 2]
    other = [c for c in cands if c[2] is None]

    lines.append(f"Candidates: tier1={len(tier1)} tier2={len(tier2)} other={len(other)} total={len(cands)}")
    lines.append("")

    results: list[dict] = []
    ec_hits: list[dict] = []

    for tier_prio, batch, label in (
        (1, tier1, "gap-1"),
        (2, tier2, "gap-2"),
        (3, other[:200], "other"),
    ):
        lines.append(f"--- {label} ({len(batch)} tested) ---")
        for name, d, tier in batch:
            off = observed_offset(d, shelf2, lo)
            kg, kb = min_k_gap_bits(d, kx, ky)
            hit = ec_hit(d, px, py)
            rec = {
                "d": d,
                "d_bits": d.bit_length(),
                "tier": tier,
                "tier_prio": tier_prio,
                "offset_bits": off.bit_length() if off else 0,
                "gap_obs": H - (off.bit_length() if off else 0),
                "k_gap_bits": kg,
                "k_best": kb,
                "ec_hit": hit,
                "source": name,
            }
            results.append(rec)
            if hit:
                ec_hits.append(rec)
                lines.append(f"  *** EC HIT *** d={d}  {name}")
        if not any(r["ec_hit"] for r in results if r["tier_prio"] == tier_prio):
            lines.append(f"  no EC hit in {label}")
        lines.append("")

    # Top tier-1 by k-gap
    lines.append("Top gap-1 by k-lane proximity (no EC hit):")
    t1_sorted = sorted([r for r in results if r["tier"] == 1 and not r["ec_hit"]], key=lambda r: r["k_gap_bits"])
    for r in t1_sorted[:8]:
        lines.append(
            f"  k_gap={r['k_gap_bits']:3d}b  gap={r['gap_obs']}  {r['source'][:60]}"
        )

    lines += [
        "",
        f"EC hits total: {len(ec_hits)}",
        "Pollard-rho on closeclose Q: NOT RUN (not bridge-aligned; prior 24h run aborted).",
        "",
        "Next if still open: congruence inside gap-1 band from row-1/row-2 carry,",
        "or bounded kangaroo only if interval shrinks below ~2^60.",
    ]

    report = "\n".join(lines) + "\n"
    print(report)

    out_txt = ROOT / "ARCHIVE" / "p135_unified_search_report.txt"
    out_csv = ROOT / "ARCHIVE" / "p135_unified_search.csv"
    out_txt.write_text(report, encoding="utf-8")
    if results:
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            w.writeheader()
            w.writerows(results)
    print(f"wrote {out_txt}")
    print(f"wrote {out_csv}")


if __name__ == "__main__":
    main()
