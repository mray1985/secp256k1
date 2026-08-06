#!/usr/bin/env python3
"""
BSGS from Tax Math P135 d anchors — Python pass + KeyHunt export.

For each unique band-folded d from tax_math_falsify trials:
  - EC BSGS on a 2^32-wide window centered on the anchor (clipped to P135 band)
  - Export KeyHunt .bat launchers for the same windows

KeyHunt profile (user): -k 512, range 0x100000000 (2^32), 4 threads.
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from dump_tax_math_hex import fold_d_to_band, r_true  # noqa: E402
from ecdlp_full_pipeline import puzzle_band  # noqa: E402
from p135_common import load_target, save_hit  # noqa: E402
from puzzle135_bucket_bsgs.ec_bsgs import bsgs_pubkey_range  # noqa: E402
from tax_math_falsify import hunt_puzzle  # noqa: E402

PUZZLE = 135
WINDOW = 1 << 32  # 0x100000000 — user KeyHunt tile width
HALF = WINDOW // 2
EXPORT_DIR = ROOT / "puzzle135_keyhunt_bsgs" / "tax_math_exports"
REPORT = ROOT / "ARCHIVE" / "tax_math_bsgs_p135.txt"
PATHS_BAT = ROOT / "puzzle135_keyhunt_bsgs" / "paths.bat"
# KeyHunt default BSGS_N; user runs 2^32 tiles — pad only when exporting if needed.
MIN_KEYHUNT_SPAN = 0x100000000000


@dataclass
class AnchorWindow:
    d0: int
    stages: list[str]
    lo: int
    hi: int
  # inclusive hi for KeyHunt -r lo:hi

    @property
    def span(self) -> int:
        return self.hi - self.lo + 1

    @property
    def band_pos(self) -> float:
        lo_band, hi_band, _ = puzzle_band(PUZZLE)
        return 100.0 * (self.d0 - lo_band) / (hi_band - lo_band)


def clip_window(d0: int, band_lo: int, band_top: int) -> tuple[int, int]:
    """Center 2^32 window on d0; clip to [band_lo, band_top]."""
    lo = d0 - HALF
    hi = lo + WINDOW - 1
    if lo < band_lo:
        lo = band_lo
        hi = min(band_top, lo + WINDOW - 1)
    if hi > band_top:
        hi = band_top
        lo = max(band_lo, hi - WINDOW + 1)
    return lo, hi


def collect_anchors() -> list[AnchorWindow]:
    band_lo, band_hi, band_top = puzzle_band(PUZZLE)
    rt = r_true(PUZZLE)
    if rt is None:
        raise SystemExit("P135: no R_true")
    rx, ry = rt
    trials, _ = hunt_puzzle(PUZZLE, None, rx, ry)
    by_d: dict[int, list[str]] = {}
    for t in trials:
        d = fold_d_to_band(t.k, PUZZLE)
        by_d.setdefault(d, []).append(t.stage)

    anchors: list[AnchorWindow] = []
    for d0 in sorted(by_d):
        lo, hi = clip_window(d0, band_lo, band_top)
        anchors.append(AnchorWindow(d0=d0, stages=by_d[d0], lo=lo, hi=hi))
    return anchors


def export_keyhunt_bats(anchors: list[AnchorWindow], *, limit: int = 0) -> list[Path]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    subset = anchors if limit <= 0 else anchors[:limit]

    for i, aw in enumerate(subset, start=1):
        label = aw.stages[0][:40].replace(" ", "_").replace("/", "_")
        bat = EXPORT_DIR / f"run_p135_tax_{i:03d}_{label}.bat"
        span_note = ""
        if aw.span < MIN_KEYHUNT_SPAN:
            span_note = (
                f"echo NOTE: span={aw.span:x} < KeyHunt default min {MIN_KEYHUNT_SPAN:x}; "
                "use -n 0x100000000 or your 2^32 profile\n"
            )
        bat.write_text(
            f"""@echo off
setlocal
call "%~dp0..\\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #{i}
echo d0={aw.d0:x}  band_pos={aw.band_pos:.2f}%  stages={len(aw.stages)}
echo Range {aw.lo:x}:{aw.hi:x}  span={aw.span:x}
{span_note}REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r {aw.lo:x}:{aw.hi:x} -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
""",
            encoding="utf-8",
        )
        written.append(bat)

    manifest = EXPORT_DIR / "tax_math_manifest.txt"
    total_keys = sum(a.span for a in subset)
    manifest.write_text(
        "\n".join(
            [
                "Puzzle 135 tax-math anchor KeyHunt BSGS exports",
                f"window=0x{WINDOW:x}  anchors={len(subset)}  total_keys~2^{total_keys.bit_length()-1}",
                f"count_bats={len(written)}",
                "",
                *[
                    f"{p.name}  d0={a.d0:x}  pos={a.band_pos:.1f}%  {a.lo:x}:{a.hi:x}  span={a.span:x}"
                    for p, a in zip(written, subset)
                ],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(manifest)
    return written


def run_python_bsgs(
    anchors: list[AnchorWindow],
    *,
    limit: int = 0,
    progress: bool = True,
) -> tuple[int | None, list[str]]:
    px, py, _, _, _ = load_target()
    subset = anchors if limit <= 0 else anchors[:limit]
    lines: list[str] = [
        "TAX MATH BSGS — Puzzle 135",
        f"anchors={len(subset)}  window=0x{WINDOW:x}",
        "",
    ]
    hit_d: int | None = None
    t_all = time.perf_counter()

    for i, aw in enumerate(subset, start=1):
        width = aw.hi - aw.lo + 1
        m = int(math.isqrt(width)) + 1
        t0 = time.perf_counter()
        hit = bsgs_pubkey_range(px, py, aw.lo, aw.hi + 1, m=m, progress=False)
        dt = time.perf_counter() - t0
        status = f"HIT d={hex(hit)} delta={hit - aw.d0}" if hit else "none"
        line = (
            f"[{i:3d}/{len(subset)}] d0={aw.d0:x} pos={aw.band_pos:5.1f}%  "
            f"span=2^{width.bit_length()-1}  m=2^{m.bit_length()-1}  {dt:5.2f}s  {status}"
        )
        lines.append(line)
        if progress:
            print(line, flush=True)
        if hit is not None:
            hit_d = hit
            save_hit(hit, source=f"tax_math_bsgs:{aw.stages[0]}")
            lines.append(f"  SOLVED via anchor stage={aw.stages[0]}")
            break

    elapsed = time.perf_counter() - t_all
    lines.extend(["", f"wall={elapsed:.1f}s  result={'SOLVED' if hit_d else 'not found'}"])
    return hit_d, lines


def main() -> int:
    ap = argparse.ArgumentParser(description="BSGS from Tax Math P135 d anchors")
    ap.add_argument("--export-only", action="store_true", help="write KeyHunt bats only")
    ap.add_argument("--limit", type=int, default=0, help="max anchors (0 = all)")
    ap.add_argument("--no-run", action="store_true", help="skip Python BSGS pass")
    args = ap.parse_args()

    anchors = collect_anchors()
    band_lo, band_hi, _ = puzzle_band(PUZZLE)
    print(
        f"P135 band [{hex(band_lo)}, {hex(band_hi)})  "
        f"unique anchors={len(anchors)}  window=0x{WINDOW:x}",
        flush=True,
    )

    bats = export_keyhunt_bats(anchors, limit=args.limit)
    print(f"exported {len(bats)} files -> {EXPORT_DIR}", flush=True)

    if args.export_only:
        return 0

    if not args.no_run:
        hit, lines = run_python_bsgs(anchors, limit=args.limit)
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nreport: {REPORT}", flush=True)
        return 0 if hit else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
