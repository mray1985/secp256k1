#!/usr/bin/env python3
"""
Puzzle 71 — bridge shelf2 + gap-tier offset hunt, gated on hash160(compress(d*G)).

Uses P68–P70 bridge shelf2 to extrapolate P71 shelf2 anchors, scans gap-tier
offset intervals (ob ≈ 69–70), verifies with Bitcoin hash160 (not RIPEMD160(d)).

Harvester scroll (P += G) on anchor hits and near-misses.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import build_config  # noqa: E402
from ecdlp_full_pipeline import N, pubkey_from_scalar, puzzle_band  # noqa: E402
from gap_tier_common import (  # noqa: E402
    d_candidates_from_offset,
    gap_interval,
    sample_offsets_in_interval,
)
from genesis_calibration import bridge_state  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

P71_H = 71
P71_LO = 1 << 70
P71_HI = 1 << 71
P71_TOP = P71_HI - 1
TARGET_H160 = bytes.fromhex("F6F5431D25BBF7B12E8ADD9AF5E3475C44A0A5B8")
TARGET_ADDR = "1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU"
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p71_hash160_hunt.log"


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def hash160_point(x: int, y: int) -> bytes:
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    return hashlib.new(
        "ripemd160",
        hashlib.sha256(pref + x.to_bytes(32, "big")).digest(),
    ).digest()


def verify_d_hash160(d: int) -> bool:
    if not (P71_LO <= d < P71_HI):
        return False
    try:
        x, y = pubkey_from_scalar(d)
        return hash160_point(x, y) == TARGET_H160
    except Exception:
        return False


def shelf2_guesses(keys: dict) -> list[tuple[str, int]]:
    """Extrapolate P71 shelf2 from P68–P70 bridge (not P68–P70 d themselves)."""
    shelves: dict[int, int] = {}
    for n in (68, 69, 70):
        cfg = build_config(keys[n])
        st = bridge_state(cfg)
        shelves[n] = st["oitc"].shelf2

    s68, s69, s70 = shelves[68], shelves[69], shelves[70]
    lo71 = P71_LO
    out: list[tuple[str, int]] = []
    formulas = [
        ("P70_shelf2_mod_LO", lo71 + (s70 % lo71)),
        ("2*s70 - s69", lo71 + ((2 * s70 - s69) % lo71)),
        ("s70 + (s70-s69)", lo71 + ((s70 + (s70 - s69)) % lo71)),
        ("s70 + (s69-s68)", lo71 + ((s70 + (s69 - s68)) % lo71)),
        ("avg(s68,s69,s70)", lo71 + ((s68 + s69 + s70) // 3 % lo71)),
        ("P70_d_mod_LO", lo71 + (keys[70].d % lo71)),
    ]
    for name, val in formulas:
        if P71_LO <= val < P71_HI:
            out.append((name, val))
    return out


def offset_tiers() -> list[tuple[str, int, int, int, int]]:
    """(label, gap, offset_bits, o_lo, o_hi)."""
    tiers: list[tuple[str, int, int, int, int]] = []
    for gap in (1, 2, 4):
        ob, o_lo, o_hi = gap_interval(P71_H, gap)
        tiers.append((f"gap{gap}_ob{ob}", gap, ob, o_lo, o_hi))
    return tiers


@dataclass(frozen=True)
class Candidate:
    d: int
    source: str


def puzzle_offset_rows(keys: dict, p: int) -> set[int]:
    """Return lit offset rows k where d = sum(2**((p-1)-k))."""
    d = keys[p].d
    top = p - 1
    return {top - i for i in range(d.bit_length()) if d & (1 << i)}


def offset_rows_to_d(rows: set[int]) -> int:
    return sum(1 << (70 - k) for k in rows)


def stack_bracket_anchors(keys: dict) -> list[Candidate]:
    """
    Build P71 anchors by meeting P70 forward and P75 backward on the k-stack.

    Forward side:
      P70 union gains shared by both prior +1 hops (P65->P66, P69->P70)
    Backward side:
      P75∩P70 persist bits union lane-1 anchor bits from P61∩P66
    """
    o61 = puzzle_offset_rows(keys, 61)
    o65 = puzzle_offset_rows(keys, 65)
    o66 = puzzle_offset_rows(keys, 66)
    o69 = puzzle_offset_rows(keys, 69)
    o70 = puzzle_offset_rows(keys, 70)
    o75 = puzzle_offset_rows(keys, 75)

    gain_65_66 = o66 - o65
    gain_69_70 = o70 - o69
    lane1_anchor = o61 & o66
    back_core = o75 & o70
    forward = o70 | (gain_65_66 & gain_69_70)
    backward = back_core | lane1_anchor
    meet = forward & backward

    anchors = [
        Candidate(offset_rows_to_d(meet), "stack:meet_fwd_back"),
        Candidate(offset_rows_to_d(forward), "stack:forward_from_p70"),
        Candidate(offset_rows_to_d(backward), "stack:backward_from_p75"),
        Candidate(offset_rows_to_d(back_core), "stack:back_core_p75_p70"),
    ]

    # Keep the old minimal cross inside the new bidirectional meet.
    cross = {0, 12, 19, 24, 27, 58, 59}
    anchors.append(Candidate(offset_rows_to_d(cross), "stack:cross_core"))

    seen: set[int] = set()
    out: list[Candidate] = []
    for cand in anchors:
        if P71_LO <= cand.d < P71_HI and cand.d not in seen:
            seen.add(cand.d)
            out.append(cand)
    return out


def discrete_candidates(shelf2: int, label: str) -> list[Candidate]:
    """Shelf2 + offset endpoints/midpoints per gap tier (+/- directions)."""
    out: list[Candidate] = []
    seen: set[int] = set()
    lo, hi = P71_LO, P71_HI

    def add(d: int, src: str) -> None:
        if lo <= d < hi and d not in seen:
            seen.add(d)
            out.append(Candidate(d, f"{label}:{src}"))

    for tier_label, _gap, ob, o_lo, o_hi in offset_tiers():
        mid = (o_lo + o_hi - 1) // 2
        for off in (o_lo, mid, o_hi - 1):
            for d, dr in d_candidates_from_offset(shelf2, off, lo, hi):
                add(d, f"{tier_label}/{dr}/off{off.bit_length()}b")

    return out


def sampled_candidates(
    shelf2: int,
    label: str,
    n_samples: int,
) -> list[Candidate]:
    out: list[Candidate] = []
    seen: set[int] = set()
    lo, hi = P71_LO, P71_HI

    for tier_label, _gap, _ob, o_lo, o_hi in offset_tiers():
        for off in sample_offsets_in_interval(o_lo, o_hi, n_samples):
            for d, dr in d_candidates_from_offset(shelf2, off, lo, hi):
                if d not in seen:
                    seen.add(d)
                    out.append(Candidate(d, f"{label}:{tier_label}/{dr}/sample"))
    return out


def harvester_scroll(d0: int, radius: int, label: str) -> tuple[int, str] | None:
    """P = d0*G then P += G / P -= G, check hash160."""
    from ecdsa import SECP256k1, SigningKey

    if not (P71_LO <= d0 <= P71_TOP):
        return None

    def pt(d: int) -> tuple[int, int]:
        sk = SigningKey.from_secret_exponent(d % N, curve=SECP256k1)
        p = sk.get_verifying_key().pubkey.point
        return int(p.x()), int(p.y())

    x0, y0 = pt(d0)
    if hash160_point(x0, y0) == TARGET_H160:
        return d0, f"{label} exact"

    # walk forward
    d = d0
    x, y = x0, y0
    for i in range(1, radius + 1):
        d += 1
        if d > P71_TOP:
            break
        x, y = pt(d)
        if hash160_point(x, y) == TARGET_H160:
            return d, f"{label} +{i}"

    # walk backward
    d = d0
    for i in range(1, radius + 1):
        d -= 1
        if d < P71_LO:
            break
        x, y = pt(d)
        if hash160_point(x, y) == TARGET_H160:
            return d, f"{label} -{i}"

    return None


def calibrate_p70(keys: dict) -> bool:
    """Sanity: P70 d must NOT match P71 hash160; hash160 pipeline works."""
    d70 = keys[70].d
    x, y = pubkey_from_scalar(d70)
    h = hash160_point(x, y)
    ok_not_p71 = h != TARGET_H160
    log(f"  calibrate P70: hash160={h.hex()} != P71 target: {ok_not_p71}")
    return ok_not_p71


def main() -> int:
    ap = argparse.ArgumentParser(description="P71 bridge + hash160 hunt")
    ap.add_argument("--samples", type=int, default=25_000, help="offsets sampled per tier per shelf2")
    ap.add_argument("--radius", type=int, default=50_000, help="harvester scroll radius from each anchor")
    ap.add_argument("--no-scroll", action="store_true")
    ap.add_argument("--discrete-only", action="store_true")
    args = ap.parse_args()

    LOG.write_text("", encoding="utf-8")
    keys = parse_53125()
    t0 = time.perf_counter()

    log("=== P71 BRIDGE + HASH160 HUNT ===")
    log(f"target hash160: {TARGET_H160.hex()}")
    log(f"target address: {TARGET_ADDR}")
    log(f"band: [{P71_LO}, {P71_HI})")
    log(f"predicted row: {P71_H % 3}  offset tiers: gap1→ob70, gap2→ob69, gap4→ob67")
    log("")

    log("--- calibration ---")
    if not calibrate_p70(keys):
        log("FAIL: calibration")
        return 1
    log("")

    shelves = shelf2_guesses(keys)
    log(f"shelf2 / anchor guesses: {len(shelves)}")
    for name, s2 in shelves:
        log(f"  {name}: {s2} ({s2.bit_length()}b)")
    log("")

    stack_anchors = stack_bracket_anchors(keys)
    log(f"stack bracket anchors: {len(stack_anchors)}")
    for cand in stack_anchors:
        log(f"  {cand.source}: d={cand.d} hex=0x{cand.d:x}")
    log("")

    tested = 0
    hit_d: int | None = None
    hit_src = ""

    # Phase 1: discrete
    log("--- phase 1: discrete shelf2 + gap-tier endpoints ---")
    for sname, shelf2 in shelves:
        for cand in discrete_candidates(shelf2, sname):
            tested += 1
            if verify_d_hash160(cand.d):
                hit_d, hit_src = cand.d, cand.source
                log(f"*** HIT d={cand.d} [{cand.source}] ***")
                break
        if hit_d:
            break
    log(f"  tested {tested} discrete candidates")
    log("")

    # Phase 1b: exact stack anchors
    if not hit_d:
        log("--- phase 1b: exact stack anchors ---")
        for cand in stack_anchors:
            tested += 1
            if verify_d_hash160(cand.d):
                hit_d, hit_src = cand.d, cand.source
                log(f"*** HIT d={cand.d} [{cand.source}] ***")
                break
        log(f"  tested {len(stack_anchors)} stack anchors")
        log("")

    # Phase 2: sampled intervals
    if not hit_d and not args.discrete_only and args.samples > 0:
        log(f"--- phase 2: sampled offsets ({args.samples}/tier/shelf2) ---")
        t1 = time.perf_counter()
        for sname, shelf2 in shelves:
            batch = sampled_candidates(shelf2, sname, args.samples)
            for i, cand in enumerate(batch):
                tested += 1
                if verify_d_hash160(cand.d):
                    hit_d, hit_src = cand.d, cand.source
                    log(f"*** HIT d={cand.d} [{cand.source}] ***")
                    break
                if tested % 100_000 == 0:
                    elapsed = time.perf_counter() - t1
                    log(f"  ... tested={tested} rate={tested/max(elapsed,1e-9):,.0f}/s")
            if hit_d:
                break
        log(f"  phase 2 total tested so far: {tested}")
        log("")

    # Phase 3: harvester scroll from shelf2 centers + pattern anchors
    if not hit_d and not args.no_scroll and args.radius > 0:
        log(f"--- phase 3: harvester scroll radius={args.radius} ---")
        scroll_anchors: list[tuple[str, int]] = list(shelves)
        scroll_anchors.extend((cand.source, cand.d) for cand in stack_anchors)
        # pattern-report d candidates (P70 shelf2 + gap offsets)
        s70 = bridge_state(build_config(keys[70]))["oitc"].shelf2
        for ob in (69, 70, 67):
            gap = P71_H - ob
            _, o_lo, _ = gap_interval(P71_H, gap)
            for d, dr in d_candidates_from_offset(s70, o_lo, P71_LO, P71_HI):
                if dr == "+":
                    scroll_anchors.append((f"P70s2+ob{ob}", d))

        seen_a: set[int] = set()
        for label, d0 in scroll_anchors:
            if d0 in seen_a:
                continue
            seen_a.add(d0)
            res = harvester_scroll(d0, args.radius, label)
            tested += 2 * args.radius + 1
            if res:
                hit_d, hit_src = res
                log(f"*** HIT d={hit_d} [{hit_src}] ***")
                break
        log(f"  scroll anchors tried: {len(seen_a)}")
        log("")

    elapsed = time.perf_counter() - t0
    log("=== SUMMARY ===")
    log(f"tested≈{tested}  elapsed={elapsed:.1f}s  rate≈{tested/max(elapsed,1e-9):,.0f}/s")
    if hit_d is not None:
        x, y = pubkey_from_scalar(hit_d)
        log(f"SOLVED P71")
        log(f"  d = {hit_d}")
        log(f"  d_hex = {hit_d:064x}")
        log(f"  hash160 = {hash160_point(x, y).hex()}")
        log(f"  source = {hit_src}")
        log(f"log -> {LOG}")
        return 0

    log("P71 OPEN — no hash160 hit in this run")
    log("  widen: --samples 500000 --radius 500000")
    log("  or run puzzle71_bsgs/ for full-band BSGS")
    log(f"log -> {LOG}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
