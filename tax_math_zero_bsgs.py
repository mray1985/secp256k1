#!/usr/bin/env python3
"""
BSGS through trailing-zero spans from tax_math packet hex.

Anchor = top (significant) part of d; low tz bits are free.
  d_anchor = d with trailing zeros  (already the printed hex)
  scan     [d_anchor, d_anchor + 2^tz)  clipped to puzzle band
  tiles    0x100000000 (2^32) KeyHunt windows through the zero run
"""

from __future__ import annotations

import argparse
import hashlib
import math
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle135_bucket_bsgs.ec_bsgs import bsgs_pubkey_range  # noqa: E402
from puzzle135_bucket_bsgs.p135_common import G, point_add, point_neg, scalar_mult  # noqa: E402

PACKET = ROOT / "ARCHIVE" / "tax_math_trials_P135_P160_full_hex.txt"
WINDOW = 1 << 32
REPORT = ROOT / "ARCHIVE" / "tax_math_zero_bsgs.txt"
EXPORT_DIR = ROOT / "puzzle135_keyhunt_bsgs" / "zero_span_exports"
PUZZLES = (135, 140, 145, 150, 155, 160)


@dataclass
class ZeroJob:
    puzzle: int
    stage: str
    d_anchor: int
    tz: int
    lo: int
    hi: int  # inclusive end

    @property
    def span(self) -> int:
        return self.hi - self.lo + 1

    @property
    def anchor_hex(self) -> str:
        return hex(self.d_anchor >> self.tz << self.tz)

    def tile_count(self) -> int:
        return (self.span + WINDOW - 1) // WINDOW

    def tile_at(self, index: int) -> tuple[int, int]:
        lo = self.lo + index * WINDOW
        if lo > self.hi:
            raise IndexError(index)
        return lo, min(lo + WINDOW - 1, self.hi)

    def iter_tiles(self, limit: int = 0):
        n = self.tile_count() if limit <= 0 else min(self.tile_count(), limit)
        for i in range(n):
            yield i, self.tile_at(i)


def load_pubkey(n: int) -> tuple[int, int]:
    rsz = PUZZLE_RSZ[n]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    comp = bytes.fromhex(rsz.pub_compressed)
    py = yp if comp[0] == 2 else yn
    return px, py


def trailing_zeros(d: int) -> int:
    if d == 0:
        return 0
    return (d & -d).bit_length() - 1


def parse_packet(path: Path, puzzles: tuple[int, ...]) -> list[ZeroJob]:
    text = path.read_text(encoding="utf-8")
    jobs: list[ZeroJob] = []
    seen: set[tuple[int, int]] = set()

    for n in puzzles:
        m = re.search(rf"=== P{n} .*?===(.*?)(?=\n=== P|\Z)", text, re.S)
        if not m:
            continue
        band_lo, band_hi, band_top = puzzle_band(n)
        for stage, hx in re.findall(r"\[([^\]]+)\]\s*\n\s*d = (0x[0-9a-f]+)", m.group(1)):
            d = int(hx, 16)
            tz = trailing_zeros(d)
            if tz < 32:
                continue
            key = (n, d)
            if key in seen:
                continue
            seen.add(key)
            lo = d
            hi = min(band_top, d + (1 << tz) - 1)
            if lo > band_top or hi < band_lo:
                continue
            lo = max(lo, band_lo)
            jobs.append(ZeroJob(puzzle=n, stage=stage, d_anchor=d, tz=tz, lo=lo, hi=hi))
    return jobs


def export_keyhunt(jobs: list[ZeroJob], *, tiles_per_job: int = 1) -> int:
    """Export first N tiles per job (default 1 = anchor 2^32 window)."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    manifest_lines = [
        "Tax math zero-span KeyHunt exports",
        f"window=0x{WINDOW:x}  tiles_exported_per_job={tiles_per_job}",
        "",
    ]
    for ji, job in enumerate(jobs, 1):
        for ti, (lo, hi) in job.iter_tiles(tiles_per_job):
            label = job.stage[:28].replace(" ", "_")
            bat = EXPORT_DIR / f"p{job.puzzle}_{ji:03d}_t{ti:04d}_{label}.bat"
            bat.write_text(
                f"""@echo off
setlocal
call "%~dp0..\\paths.bat"
cd /d "%WORKDIR%"
echo P{job.puzzle} zero-span BSGS  top={hex(job.d_anchor >> job.tz)}  tz=2^{job.tz}
echo stage={job.stage}
echo tile {ti}/{job.tile_count()-1}  range {lo:x}:{hi:x}
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P{job.puzzle}_compressed.pub" -r {lo:x}:{hi:x} -k %K_FACTOR% -t %THREADS% -s %STATS% -q
""",
                encoding="utf-8",
            )
            count += 1
        manifest_lines.append(
            f"P{job.puzzle}  top={hex(job.d_anchor >> job.tz)}  d={hex(job.d_anchor)}  "
            f"tz=2^{job.tz}  span=2^{job.span.bit_length()-1}  tiles_total={job.tile_count()}  "
            f"[{job.stage}]"
        )
    (EXPORT_DIR / "zero_span_manifest.txt").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    return count


def run_bsgs(jobs: list[ZeroJob], *, tile_limit: int = 1) -> tuple[int | None, list[str]]:
    lines: list[str] = [
        "TAX MATH ZERO-SPAN BSGS",
        f"jobs={len(jobs)}  window=0x{WINDOW:x}  tile_limit_per_job={tile_limit}",
        "",
    ]
    hit_d: int | None = None
    hit_puzzle = 0
    t_all = time.perf_counter()

    for ji, job in enumerate(jobs, 1):
        px, py = load_pubkey(job.puzzle)
        lines.append(
            f"--- P{job.puzzle} [{ji}/{len(jobs)}] tz=2^{job.tz} "
            f"anchor_top={hex(job.d_anchor >> job.tz)}  span=2^{job.span.bit_length()-1} "
            f"tiles_total={job.tile_count()}  [{job.stage}]"
        )
        for ti, (lo, hi) in job.iter_tiles(tile_limit):
            width = hi - lo + 1
            m = int(math.isqrt(width)) + 1
            t0 = time.perf_counter()
            found = bsgs_pubkey_range(px, py, lo, hi + 1, m=m, progress=False)
            dt = time.perf_counter() - t0
            status = f"HIT {hex(found)}" if found else "none"
            line = f"  tile{ti} [{lo:x},{hi:x}] w=2^{width.bit_length()-1} {dt:.2f}s {status}"
            lines.append(line)
            print(f"P{job.puzzle} {ji}/{len(jobs)} tile{ti} {dt:.1f}s {status}", flush=True)
            if found:
                hit_d = found
                hit_puzzle = job.puzzle
                lines.append(f"  SOLVED P{job.puzzle} d={found}")
                break
        if hit_d:
            break

    elapsed = time.perf_counter() - t_all
    summary = f"wall={elapsed:.1f}s  result={'SOLVED P'+str(hit_puzzle)+' d='+hex(hit_d) if hit_d else 'not found'}"
    lines.extend(["", summary])
    print(summary, flush=True)
    return hit_d, lines


def write_pub_files() -> None:
    out = ROOT / "puzzle135_keyhunt_bsgs"
    out.mkdir(parents=True, exist_ok=True)
    for n in PUZZLES:
        pub = PUZZLE_RSZ[n].pub_compressed + "\n"
        (out / f"P{n}_compressed.pub").write_text(pub, encoding="ascii")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packet", type=Path, default=PACKET)
    ap.add_argument("--export-only", action="store_true")
    ap.add_argument("--tile-limit", type=int, default=1, help="BSGS tiles per job (1=first 2^32)")
    ap.add_argument("--full-tiles", action="store_true", help="run every 2^32 tile (slow)")
    args = ap.parse_args()

    if not args.packet.is_file():
        raise SystemExit(f"missing packet: {args.packet}")

    jobs = parse_packet(args.packet, PUZZLES)
    total_tiles = sum(j.tile_count() for j in jobs)
    tile_limit = 10**9 if args.full_tiles else args.tile_limit
    print(
        f"zero-span jobs={len(jobs)}  total_zero_tiles={total_tiles}  "
        f"running_tiles_per_job={tile_limit}",
        flush=True,
    )

    write_pub_files()
    n_bats = export_keyhunt(jobs, tiles_per_job=min(tile_limit, max(1, tile_limit)))
    print(f"exported {n_bats} KeyHunt bats -> {EXPORT_DIR}", flush=True)

    if args.export_only:
        return 0

    hit, lines = run_bsgs(jobs, tile_limit=tile_limit)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"report: {REPORT}", flush=True)
    return 0 if hit else 1


if __name__ == "__main__":
    raise SystemExit(main())
