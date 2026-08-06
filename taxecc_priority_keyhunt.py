#!/usr/bin/env python3
"""Top-10 priority KeyHunt exports for k=512 / 2^32 hardware profile."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import puzzle_band  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from taxecc_zero_keyhunt_export import SpanJob, parse_jobs, trailing_zeros  # noqa: E402

PACKET = ROOT / "ARCHIVE" / "tax_math_trials_P135_P160_full_hex.txt"
EXPORT_DIR = ROOT / "puzzle135_keyhunt_bsgs" / "priority_k512"
MANIFEST = EXPORT_DIR / "priority_manifest.txt"
K512 = 512
WINDOW = 1 << 32  # 0x100000000 — user's runnable tile width

# One canonical raw pivot per puzzle + four P135/P145 form56 variants
PRIORITY_STAGES = [
    (135, "SE_pivot198.95_raw"),
    (140, "SE_pivot198.95_raw"),
    (145, "SE_pivot198.95_raw"),
    (150, "SE_pivot198.95_raw"),
    (155, "SE_pivot198.95_raw"),
    (160, "SE_pivot198.95_raw"),
    (135, "SE_pivot198.95_raw+form56_mul_2^H2"),
    (135, "SE_pivot198.95_raw+form56_div_2^H2"),
    (145, "SE_pivot198.95_raw+form56_mul_sqrt_pN_frac"),
    (135, "SE_pivot198.95_raw+form56_mul_sqrt_pN_frac"),
]


@dataclass
class PriorityJob:
    span: SpanJob
    lo: int
    hi: int
    profile: str

    @property
    def keys(self) -> int:
        return self.hi - self.lo + 1


def pick_priority(jobs: list[SpanJob]) -> list[SpanJob]:
    by_key = {(j.puzzle, j.stage): j for j in jobs}
    picked: list[SpanJob] = []
    for key in PRIORITY_STAGES:
        if key in by_key:
            picked.append(by_key[key])
    return picked


def k512_window(job: SpanJob) -> tuple[int, int]:
    """First 2^32 keys of zero span — fits k=512 KeyHunt."""
    band_lo, _, band_top = puzzle_band(job.puzzle)
    lo = max(band_lo, job.lo)
    hi = min(band_top, lo + WINDOW - 1, job.hi)
    return lo, hi


def export(priority: list[SpanJob]) -> list[PriorityJob]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out: list[PriorityJob] = []

    for i, job in enumerate(priority, 1):
        lo, hi = k512_window(job)
        pj = PriorityJob(job, lo, hi, "k512_first_2^32")
        out.append(pj)
        label = job.stage[:28].replace(" ", "_")
        bat = EXPORT_DIR / f"prio_{i:02d}_p{job.puzzle}_{label}.bat"
        bat.write_text(
            f"""@echo off
setlocal
call "%~dp0..\\paths.bat"
cd /d "%WORKDIR%"
echo PRIORITY {i}/10  P{job.puzzle}  [{job.stage}]
echo anchor_top={hex(job.top)}  full_zero_span=2^{job.tz}
echo k512 profile: FIRST 2^32 of zero corridor (anchor tile)
echo range {lo:x}:{hi:x}  keys=2^{pj.keys.bit_length()-1}
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P{job.puzzle}_compressed.pub" -r {lo:x}:{hi:x} -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
""",
            encoding="utf-8",
        )

    lines = [
        "PRIORITY KeyHunt — k=512 / 2^32 anchor tile (10 jobs)",
        f"K_FACTOR={K512}  WINDOW=0x{WINDOW:x}",
        "",
        "Each job: first 2^32 keys from zero span at anchor top.",
        "Full 2^tz single-span bats: ../single_span_exports/",
        "",
    ]
    for i, pj in enumerate(out, 1):
        j = pj.span
        lines.append(
            f"{i:2d}. P{j.puzzle}  top={hex(j.top)}  tz=2^{j.tz}  "
            f"tile={pj.lo:x}:{pj.hi:x}  [{j.stage}]"
        )
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> int:
    jobs = parse_jobs(PACKET)
    priority = pick_priority(jobs)
    if len(priority) < 10:
        print(f"warning: only {len(priority)} priority jobs matched")
    export(priority)
    print(f"wrote {len(priority)} bats -> {EXPORT_DIR}")
    print(f"manifest: {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
