#!/usr/bin/env python3
"""Leave-one-out F-ordering sieve.

Hypothesis (illogical-but-valid path):
  F_n = d_n * q_n with q_n = log(Px)/log(Py) (or other limb pair)
  rho(F,n)=1 on solved set => F increases with puzzle height.
  For held-out m, assume ordering continues:
    max_{i: n_i < n_m} F_i / q_m  <  d_m  <  min_{j: n_j > n_m} F_j / q_m
  Intersect with known band [2^{n-1}, 2^n).

Falsifiable metrics:
  coverage = fraction of held-out d that land in the derived interval
  bits_cut = log2(band_width / intersect_width) when intersect is strictly tighter

0 verified bits unless coverage stays high AND mean bits_cut > 0 on LOO.
"""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path

from scan_log_ratio_cross_puzzle import load_rows, ln

getcontext().prec = 80
OUT = Path("logs/log_ratio_scan")


@dataclass
class PuzzleFeat:
    n: int
    d: int
    Px: int
    Py: int
    q: Decimal  # log(a)/log(b)
    F: Decimal  # d * q


def band(n: int) -> tuple[int, int]:
    """Inclusive puzzle-n private-key band [2^{n-1}, 2^n - 1]."""
    return 1 << (n - 1), (1 << n) - 1


def make_feats(a_name: str, b_name: str) -> list[PuzzleFeat]:
    rows = sorted(
        [r for r in load_rows() if r.d and r.Px and r.Py],
        key=lambda r: r.n,
    )
    out: list[PuzzleFeat] = []
    for r in rows:
        a = r.Px if a_name == "Px" else r.Py
        b = r.Py if b_name == "Py" else r.Px
        if a_name == "Py" and b_name == "Px":
            a, b = r.Py, r.Px
        elif a_name == "Px" and b_name == "Py":
            a, b = r.Px, r.Py
        else:
            raise ValueError(f"unsupported pair {a_name}/{b_name}")
        q = ln(a) / ln(b)
        F = Decimal(r.d) * q
        out.append(PuzzleFeat(n=r.n, d=r.d, Px=r.Px, Py=r.Py, q=q, F=F))
    return out


def loo_interval(
    feats: list[PuzzleFeat], hold: PuzzleFeat
) -> tuple[Decimal | None, Decimal | None, list[PuzzleFeat], list[PuzzleFeat]]:
    below = [f for f in feats if f.n < hold.n]
    above = [f for f in feats if f.n > hold.n]
    lo = max((f.F for f in below), default=None)
    hi = min((f.F for f in above), default=None)
    # Convert F-bounds to d-bounds via public q_hold
    d_lo = (lo / hold.q) if lo is not None else None
    d_hi = (hi / hold.q) if hi is not None else None
    return d_lo, d_hi, below, above


def intersect_band(
    n: int, d_lo: Decimal | None, d_hi: Decimal | None
) -> tuple[int, int] | None:
    b_lo, b_hi = band(n)
    lo = b_lo if d_lo is None else max(b_lo, math.ceil(float(d_lo)))
    # strict inequality F_i < F_m => d > F_i/q; use ceil of exclusive lower
    if d_lo is not None:
        # d > d_lo  =>  d >= floor(d_lo)+1
        lo = max(b_lo, math.floor(float(d_lo)) + 1)
    hi = b_hi if d_hi is None else min(b_hi, math.floor(float(d_hi)))
    # d < d_hi => d <= ceil(d_hi)-1 = floor(d_hi-eps)
    if d_hi is not None:
        hi = min(b_hi, math.ceil(float(d_hi)) - 1)
    if lo > hi:
        return None
    return lo, hi


def bits_of_width(lo: int, hi: int) -> float:
    w = hi - lo + 1
    if w <= 0:
        return float("-inf")
    return math.log2(w)


def run_loo(feats: list[PuzzleFeat], label: str) -> dict:
    rows_out = []
    covered = 0
    empty = 0
    tighter = 0
    bits_cuts: list[float] = []
    raw_beats_floor = 0  # d_lo > 2^{n-1} before intersect

    for hold in feats:
        d_lo, d_hi, below, above = loo_interval(feats, hold)
        b_lo, b_hi = band(hold.n)
        band_bits = bits_of_width(b_lo, b_hi)

        if d_lo is not None and float(d_lo) > b_lo:
            raw_beats_floor += 1

        inter = intersect_band(hold.n, d_lo, d_hi)
        if inter is None:
            empty += 1
            hit = False
            cut = None
            new_bits = None
        else:
            ilo, ihi = inter
            hit = ilo <= hold.d <= ihi
            if hit:
                covered += 1
            new_bits = bits_of_width(ilo, ihi)
            cut = band_bits - new_bits
            if cut > 1e-12:
                tighter += 1
                bits_cuts.append(cut)

        rows_out.append(
            {
                "n": hold.n,
                "d": hold.d,
                "q": float(hold.q),
                "F": float(hold.F),
                "n_below": len(below),
                "n_above": len(above),
                "d_lo_raw": float(d_lo) if d_lo is not None else None,
                "d_hi_raw": float(d_hi) if d_hi is not None else None,
                "band_lo": b_lo,
                "band_hi": b_hi,
                "inter_lo": inter[0] if inter else None,
                "inter_hi": inter[1] if inter else None,
                "covered": hit,
                "empty": inter is None,
                "bits_band": band_bits,
                "bits_inter": new_bits,
                "bits_cut": cut,
                "raw_lo_beats_floor": bool(d_lo is not None and float(d_lo) > b_lo),
                "raw_hi_beats_ceil": bool(
                    d_hi is not None and float(d_hi) < b_hi
                ),
            }
        )

    n = len(feats)
    summary = {
        "formula": label,
        "cohort": n,
        "coverage": covered / n,
        "covered": covered,
        "empty_intervals": empty,
        "tighter_than_band": tighter,
        "raw_lo_beats_floor_count": raw_beats_floor,
        "mean_bits_cut_when_tighter": (
            statistics.mean(bits_cuts) if bits_cuts else 0.0
        ),
        "max_bits_cut": max(bits_cuts) if bits_cuts else 0.0,
        "median_bits_cut_when_tighter": (
            statistics.median(bits_cuts) if bits_cuts else 0.0
        ),
    }
    return {"summary": summary, "rows": rows_out}


def probe_unsolved_lower(
    feats: list[PuzzleFeat], n_target: int, Px: int, Py: int, a_name: str, b_name: str
) -> dict:
    """Lower-bound only when no solved neighbor above (e.g. P135)."""
    if a_name == "Px" and b_name == "Py":
        q = ln(Px) / ln(Py)
    else:
        q = ln(Py) / ln(Px)
    below = [f for f in feats if f.n < n_target]
    d_lo = max(f.F for f in below) / q if below else None
    b_lo, b_hi = band(n_target)
    beats = d_lo is not None and float(d_lo) > b_lo
    inter_lo = b_lo
    if d_lo is not None:
        inter_lo = max(b_lo, math.floor(float(d_lo)) + 1)
    return {
        "n": n_target,
        "q": float(q),
        "d_lo_raw": float(d_lo) if d_lo else None,
        "band_lo": b_lo,
        "band_hi": b_hi,
        "inter_lo": inter_lo,
        "raw_lo_beats_floor": beats,
        "bits_cut_if_beats": (
            math.log2(b_hi - b_lo + 1) - math.log2(b_hi - inter_lo + 1)
            if beats and inter_lo <= b_hi
            else 0.0
        ),
        "n_below": len(below),
        "max_below_n": max((f.n for f in below), default=None),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    for a, b, label in [
        ("Px", "Py", "d*log(Px)/log(Py)"),
        ("Py", "Px", "d*log(Py)/log(Px)"),
    ]:
        feats = make_feats(a, b)
        # Verify full-set F ordering vs n
        Fs = [float(f.F) for f in feats]
        ns = [float(f.n) for f in feats]
        mono = all(Fs[i] < Fs[i + 1] for i in range(len(Fs) - 1))
        # also check F order matches n order (same as sorted by n already)
        order_ok = all(feats[i].F < feats[i + 1].F for i in range(len(feats) - 1))
        loo = run_loo(feats, label)
        loo["summary"]["full_set_F_strictly_increasing_with_n"] = order_ok
        loo["summary"]["full_set_mono"] = mono

        # P135 lower-bound probe if pubkey in catalog
        p135 = None
        try:
            from puzzle_catalog import load_catalog
            from scan_log_ratio_cross_puzzle import recover_xy_from_pubkey

            cat = load_catalog()
            e135 = cat.get(135)
            if e135 is not None and e135.has_pubkey:
                px, py = recover_xy_from_pubkey(e135.public_key)
                p135 = probe_unsolved_lower(feats, 135, px, py, a, b)
        except Exception as e:
            p135 = {"error": str(e)}

        results[label] = {"loo": loo["summary"], "p135": p135, "detail_rows": loo["rows"]}

        s = loo["summary"]
        print(f"\n=== {label} ===")
        print(f"cohort={s['cohort']}  F mono with n={s['full_set_F_strictly_increasing_with_n']}")
        print(f"LOO coverage={s['coverage']:.4f}  empty={s['empty_intervals']}")
        print(
            f"tighter_than_band={s['tighter_than_band']}  "
            f"raw_lo_beats_floor={s['raw_lo_beats_floor_count']}"
        )
        print(
            f"mean_bits_cut_when_tighter={s['mean_bits_cut_when_tighter']:.6f}  "
            f"max={s['max_bits_cut']:.6f}"
        )
        if p135 and "error" not in p135:
            print(
                f"P135: raw_lo_beats_floor={p135['raw_lo_beats_floor']}  "
                f"bits_cut={p135['bits_cut_if_beats']:.6f}  "
                f"d_lo_raw={p135['d_lo_raw']}  band_lo={p135['band_lo']}"
            )

    # Control: same LOO but with q=1 (pure d ordering) — should match "no extra bits"
    feats_d = make_feats("Py", "Px")
    for f in feats_d:
        f.q = Decimal(1)
        f.F = Decimal(f.d)
    ctrl = run_loo(feats_d, "d only (q=1)")
    results["control_d_only"] = {"loo": ctrl["summary"]}
    print("\n=== control q=1 (pure d order) ===")
    print(ctrl["summary"])

    path = OUT / "ordering_sieve_loo.json"
    # trim detail for control-less bulk: keep both formulas' details
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nwrote {path}")

    # Ruling
    # Ruling: require meaningful, repeatable cut (not sub-bit edge noise)
    meaningful = any(
        results[k]["loo"]["tighter_than_band"] >= 5
        and results[k]["loo"]["mean_bits_cut_when_tighter"] >= 1.0
        for k in results
        if k != "control_d_only"
    )
    print(
        "\nRULING:",
        "candidate bit removal — review LOO" if meaningful else "0 verified bits (no usable band tightening)",
    )


if __name__ == "__main__":
    main()
