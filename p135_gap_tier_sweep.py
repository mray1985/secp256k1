#!/usr/bin/env python3
"""
P135 gap-tier interval sweep.

Searches offset INTERVALS (not power-of-two endpoints) for gap=1 then gap=2:
  gap=1: o in [2^133, 2^134), offset_bits=134
  gap=2: o in [2^132, 2^133), offset_bits=133

Lifts d from shelf2 +/- o (with LO wrap), filters to puzzle band, gates on d*G==P.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    PuzzleConfig,
    apply_puzzle_defaults,
    pubkey_from_scalar,
    puzzle_band,
)
from gap_tier_common import (  # noqa: E402
    d_candidates_from_offset,
    gap_interval,
    observed_offset,
    sample_offsets_in_interval,
)
from genesis_calibration import bridge_state  # noqa: E402

try:
    from ecdsa import SECP256k1  # noqa: F401

    _HAS_ECDSA = True
except ImportError:
    _HAS_ECDSA = False

H = 135


def ec_hit(d: int, px: int, py: int) -> bool:
    if not _HAS_ECDSA:
        return False
    try:
        x, y = pubkey_from_scalar(d)
        return x == px and y == py
    except Exception:
        return False


def collect_bridge_offsets_in_interval(
    terms: list[tuple[str, int]], o_lo: int, o_hi: int
) -> list[tuple[str, int]]:
    return [(name, off) for name, off in terms if o_lo <= off < o_hi]


def run_sweep(samples_per_tier: int) -> None:
    cfg = PuzzleConfig(puzzle_num=H, row=2)
    apply_puzzle_defaults(cfg)
    st = bridge_state(cfg)
    lo, hi, top = puzzle_band(H)
    shelf2 = st["oitc"].shelf2
    px = cfg.Px[cfg.row]
    py = cfg.Py

    pool: dict[int, dict] = {}
    lines = [
        "P135 GAP-TIER INTERVAL SWEEP",
        f"H={H}  band d in [{lo}, {hi})  shelf2 bits={shelf2.bit_length()}",
        f"ecdsa: {_HAS_ECDSA}",
        "",
        "Convention: gap = H - offset_bits; offset = (d-shelf2) mod LO",
        "  gap=1 -> offset_bits=134 -> o in [2^133, 2^134)",
        "  gap=2 -> offset_bits=133 -> o in [2^132, 2^133)",
        "",
        "NOT testing o=2^132 or 2^133 alone — sampling full bit-length intervals.",
        "",
    ]

    def register(
        d: int,
        source: str,
        gap: int,
        o: int,
        direction: str,
    ) -> None:
        if d in pool:
            pool[d]["source"] += f";{source}"
            return
        off = observed_offset(d, shelf2, lo)
        ob = off.bit_length() if off else 0
        g = H - ob
        pool[d] = {
            "d": d,
            "d_bits": d.bit_length(),
            "gap_target": gap,
            "gap_observed": g,
            "offset": off,
            "offset_bits": ob,
            "o_probe": o,
            "direction": direction,
            "source": source,
            "ec_hit": ec_hit(d, px, py),
            "in_gap_tier": g == gap,
        }

    for gap in (1, 2):
        ob, o_lo, o_hi = gap_interval(H, gap)
        width = o_hi - o_lo
        lines.append("=" * 72)
        lines.append(
            f"GAP={gap}  offset_bits={ob}  interval [{o_lo}, {o_hi})  "
            f"width=2^{width.bit_length()-1} (~{width:.3e})"
        )

        # Bridge terms landing in this interval
        bridge_hits = collect_bridge_offsets_in_interval(st["terms"], o_lo, o_hi)
        lines.append(f"  bridge terms in interval: {len(bridge_hits)}")
        for name, off in bridge_hits:
            for d, direction in d_candidates_from_offset(shelf2, off, lo, hi):
                register(d, f"bridge:{name}", gap, off, direction)

        # Interval samples: boundaries, midpoint, log-spread
        probes = sample_offsets_in_interval(o_lo, o_hi, samples_per_tier)
        lines.append(f"  sampled offset probes: {len(probes)}")
        for o in probes:
            for d, direction in d_candidates_from_offset(shelf2, o, lo, hi):
                register(
                    d,
                    f"sample:g{gap}:{direction}:o={o}",
                    gap,
                    o,
                    direction,
                )

        # Report how many band d lifted per tier
        tier_rows = [r for r in pool.values() if r["gap_target"] == gap]
        in_band_obs = sum(1 for r in tier_rows if r["in_gap_tier"])
        lines.append(
            f"  unique d candidates from tier: {len(tier_rows)}  "
            f"observed gap matches target: {in_band_obs}"
        )
        lines.append("")

    ec_hits = [r for r in pool.values() if r["ec_hit"]]
    rows = sorted(
        pool.values(),
        key=lambda r: (not r["ec_hit"], r["gap_target"], r["gap_observed"], r["d"]),
    )

    lines.append("=" * 72)
    lines.append(f"TOTAL unique d in band: {len(rows)}")
    lines.append(f"EC hits (d*G==P): {len(ec_hits)}")
    lines.append("")
    hdr = (
        f"{'ec':>2} {'gT':>2} {'gO':>2} {'ob':>3} {'dir':>3}  "
        f"{'o_probe bits':>12}  source"
    )
    lines.append(hdr)
    lines.append("-" * len(hdr))
    for r in rows[:50]:
        lines.append(
            f"{'Y' if r['ec_hit'] else 'N':>2} {r['gap_target']:2d} {r['gap_observed']:2d} "
            f"{r['offset_bits']:3d} {r['direction']:>3}  "
            f"{r['o_probe'].bit_length():12d}  {r['source'][:55]}"
        )
    if len(rows) > 50:
        lines.append(f"  ... +{len(rows)-50} more (see CSV)")

    if ec_hits:
        lines.append("")
        for r in ec_hits:
            lines.append(f"  HIT d={r['d']}")

    report = "\n".join(lines) + "\n"
    print(report)

    out_txt = ROOT / "ARCHIVE" / "p135_gap_tier_sweep_report.txt"
    out_csv = ROOT / "ARCHIVE" / "p135_gap_tier_sweep.csv"
    out_txt.write_text(report, encoding="utf-8")
    if rows:
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print(f"wrote {out_txt}")
    print(f"wrote {out_csv}")


def main() -> None:
    ap = argparse.ArgumentParser(description="P135 gap-tier interval sweep")
    ap.add_argument(
        "--samples",
        type=int,
        default=48,
        help="offset samples per gap tier (plus bridge terms in interval)",
    )
    args = ap.parse_args()
    run_sweep(args.samples)


if __name__ == "__main__":
    main()
