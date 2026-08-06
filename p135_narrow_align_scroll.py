#!/usr/bin/env python3
"""Narrow align scroll: shelf2 + top Phase 17c alignment residues (P135)."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (
    PuzzleConfig,
    apply_puzzle_defaults,
    band_representative,
    puzzle_band,
    pubkey_from_scalar,
)
from genesis_calibration import bridge_state

H = 135

# Top alignment residues mod LO from Phase 17c (offset_bits ascending)
TOP_RESIDUES: list[tuple[str, int]] = [
    ("matrix_t2_col2-col1", 5827839706377974604948484932062754122065),
    ("matrix_t0_col2-col1", 28587384099128612907648717725605660317377),
    ("N-GAP_mod_LO", 37614910932706401536723864036151746034614),
    ("L3-L1_mod_LO", 9777142835765674041031253627315487188207),
    ("L2-L1_mod_LO", 14180930785895064200032004282967808855361),
    ("d2_shelf2^3_mod_LO", 4728769865121412001070816144258391676865),
    ("shelf_y-shelf2", 7051956541651937603812048681062545476470),
    ("C_plus1-C_floor", 1),
    ("GAP_mod_LO", 19689742432503126329767669131687425741516),
    ("dy_residue_shelf_y^3", 16408222683124163822850024034818345257831),
]


def ec_hit(d: int, px: int, py: int) -> bool:
    x, y = pubkey_from_scalar(d)
    return x == px and y == py


def band_d(raw: int, lo: int, hi: int) -> int:
    d = raw % hi  # keep in reasonable range first
    if lo <= d < hi:
        return d
    return band_representative(raw, lo, hi)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--radius", type=int, default=2_000_000)
    ap.add_argument("--step", type=int, default=1)
    args = ap.parse_args()

    cfg = PuzzleConfig(puzzle_num=H, row=2)
    apply_puzzle_defaults(cfg)
    lo, hi, _ = puzzle_band(H)
    st = bridge_state(cfg)
    shelf2 = st["oitc"].shelf2
    cube_lift2 = 26506841348061473662726791019891557210049
    residues = list(TOP_RESIDUES) + [
        ("d_cube_lift2-shelf2", (cube_lift2 - shelf2) % lo),
    ]
    px, py = cfg.Px[cfg.row], cfg.Py
    assert py is not None

    seeds: list[tuple[str, int]] = [("shelf2", shelf2)]
    for name, residue in residues:
        seeds.append((f"shelf2+{name}", shelf2 + residue))
        seeds.append((f"shelf2-{name}", shelf2 - residue))

    # Dedupe band representatives
    seen: set[int] = set()
    unique: list[tuple[str, int]] = []
    for name, raw in seeds:
        d = band_d(raw, lo, hi)
        if d in seen:
            continue
        seen.add(d)
        unique.append((name, d))

    lines = [
        "P135 NARROW ALIGN SCROLL",
        f"radius=±{args.radius:,}  step={args.step}  seeds={len(unique)}",
        f"shelf2={shelf2}",
        "",
    ]

    t0 = time.time()
    tested = 0
    hit: tuple[str, int] | None = None

    for name, center in unique:
        start = max(lo, center - args.radius)
        end = min(hi - 1, center + args.radius)
        if start > end:
            lines.append(f"  skip [{name}] center out of band window")
            continue
        width = end - start + 1
        lines.append(f"  [{name}] center={center}  window width={width:,}")
        print(f"  [{name}] center={center}  width={width:,}", flush=True)
        d = start
        while d <= end:
            tested += 1
            if ec_hit(d, px, py):
                hit = (name, d)
                break
            d += args.step
        if hit:
            break

    elapsed = time.time() - t0
    lines.append("")
    lines.append(f"tested={tested:,}  elapsed={elapsed:.1f}s  rate={tested/max(elapsed,1e-9):,.0f}/s")
    if hit:
        lines.append(f"HIT [{hit[0]}] d={hit[1]}")
    else:
        lines.append("no hit")

    report = "\n".join(lines) + "\n"
    print(report)
    out = ROOT / "ARCHIVE" / "p135_narrow_align_scroll_report.txt"
    out.write_text(report, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
