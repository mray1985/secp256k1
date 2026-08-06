#!/usr/bin/env python3
"""
Single-span KeyHunt BSGS export for tax_math zero anchors.

One job per anchor: full [d_anchor, d_anchor + 2^tz) clipped to band.
BSGS m = 2^(tz/2)  —  average tz~84 => m=2^42 (not sequential 2^32 tiles).
"""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import puzzle_band  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402

PACKET = ROOT / "ARCHIVE" / "tax_math_trials_P135_P160_full_hex.txt"
EXPORT_DIR = ROOT / "puzzle135_keyhunt_bsgs" / "single_span_exports"
MANIFEST = EXPORT_DIR / "single_span_manifest.txt"
PUZZLES = (135, 140, 145, 150, 155, 160)
AVG_ZERO_SPAN = 1 << 84  # 19342813113834066795298816


@dataclass
class SpanJob:
    puzzle: int
    stage: str
    d_anchor: int
    top: int
    tz: int
    lo: int
    hi: int

    @property
    def span(self) -> int:
        return self.hi - self.lo + 1

    @property
    def m_bits(self) -> int:
        return (self.tz + 1) // 2

    @property
    def k_factor_hint(self) -> int:
        """Rough KeyHunt -k scale: 512 at m=2^16, scale by 2^(m_bits-16)."""
        return max(512, 512 << max(0, self.m_bits - 16))


def trailing_zeros(d: int) -> int:
    if d == 0:
        return 0
    return (d & -d).bit_length() - 1


def parse_jobs(path: Path) -> list[SpanJob]:
    text = path.read_text(encoding="utf-8")
    jobs: list[SpanJob] = []
    seen: set[tuple[int, int]] = set()

    for n in PUZZLES:
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
            lo = max(band_lo, d)
            hi = min(band_top, d + (1 << tz) - 1)
            if lo > hi:
                continue
            top = d >> tz
            jobs.append(SpanJob(n, stage, d, top, tz, lo, hi))
    return jobs


def write_pub_files() -> None:
    out = ROOT / "puzzle135_keyhunt_bsgs"
    out.mkdir(parents=True, exist_ok=True)
    for n in PUZZLES:
        (out / f"P{n}_compressed.pub").write_text(
            PUZZLE_RSZ[n].pub_compressed + "\n", encoding="ascii"
        )


def export_bats(jobs: list[SpanJob]) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "Single-span KeyHunt BSGS — one MITM per zero anchor",
        f"avg_digit_span_decimal={AVG_ZERO_SPAN} = 2^84",
        f"jobs={len(jobs)}",
        "",
        f"{'file':<40} {'P':>4} {'tz':>4} {'m':>6} {'k_hint':>10} {'range'}",
    ]

    for i, job in enumerate(jobs, 1):
        label = job.stage[:24].replace(" ", "_")
        bat = EXPORT_DIR / f"p{job.puzzle}_{i:03d}_{label}.bat"
        m_bits = job.m_bits
        k_hint = job.k_factor_hint
        bat.write_text(
            f"""@echo off
setlocal
call "%~dp0..\\paths.bat"
cd /d "%WORKDIR%"
echo P{job.puzzle} SINGLE-SPAN BSGS  top={hex(job.top)}  tz=2^{job.tz}
echo stage={job.stage}
echo span=2^{job.tz}  m=2^{m_bits}  suggested -k {k_hint}
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P{job.puzzle}_compressed.pub" -r {job.lo:x}:{job.hi:x} -k {k_hint} -t %THREADS% -s %STATS% -q
pause
""",
            encoding="utf-8",
        )
        lines.append(
            f"{bat.name:<40} P{job.puzzle:>3} 2^{job.tz:<3} 2^{m_bits:<4} {k_hint:>10}  "
            f"{job.lo:x}:{job.hi:x}"
        )

    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if not PACKET.is_file():
        raise SystemExit(f"missing {PACKET}")
    jobs = parse_jobs(PACKET)
    write_pub_files()
    export_bats(jobs)
    tz_avg = sum(j.tz for j in jobs) / len(jobs) if jobs else 0
    print(f"exported {len(jobs)} single-span bats -> {EXPORT_DIR}")
    print(f"mean tz={tz_avg:.1f}  mean m_bits~{sum(j.m_bits for j in jobs)/len(jobs):.1f}")
    print(f"manifest: {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
