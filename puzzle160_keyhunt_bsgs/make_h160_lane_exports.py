#!/usr/bin/env python3
"""Export KeyHunt BSGS launchers for the P160 h160 shelf lane.

Lane lock:
  d = band_lo + q_h * 2^32 + eps
  q_h = (h160(P160) - band_lo) // 2^32
  eps in [0, 2^32)

KeyHunt requires span >= 0x100000000000 (2^44). The full lane (2^32) fits in one
padded window; this script also emits 256 sub-tiles (eps chunks of 2^24) for
parallel / resumable runs.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402

MIN_KEYHUNT_SPAN = 0x100000000000
D_LO, D_HI = 1 << 159, 1 << 160


def clip_d_range(center: int, half_window: int, min_span: int = MIN_KEYHUNT_SPAN) -> tuple[int, int, int]:
    """KeyHunt BSGS needs (hi-lo+1) >= min_span. Extend downward first when clipped at band top."""
    d_top = D_HI - 1
    lo = max(center - half_window, D_LO)
    hi = min(center + half_window, d_top)
    span = hi - lo + 1
    if span < min_span:
        need = min_span - span
        extend_lo = min(need, lo - D_LO)
        lo -= extend_lo
        need -= extend_lo
        if need > 0:
            hi = min(d_top, hi + need)
        span = hi - lo + 1
    if span < min_span:
        hi = d_top
        lo = max(D_LO, d_top - min_span + 1)
        span = hi - lo + 1
    # KeyHunt checks (hi - lo) >= min_span (exclusive end), not (hi - lo + 1).
    if hi - lo < min_span:
        hi = min(d_top, lo + min_span)
        span = hi - lo + 1
    return lo, hi, span

BSGS_DIR = Path(__file__).resolve().parent
EXPORT_DIR = BSGS_DIR / "h160_lane_exports"
MANIFEST = EXPORT_DIR / "h160_lane_manifest.txt"

TWO32 = 1 << 32
EPS_CHUNK = 1 << 24  # 256 tiles cover the lane
NUM_TILES = TWO32 // EPS_CHUNK


def h160_p160() -> tuple[int, int, int]:
    pub = (BSGS_DIR / "P160_compressed.pub").read_text(encoding="ascii").strip().splitlines()[0]
    raw = bytes.fromhex(pub)
    x = int(pub[2:], 16)
    yp, yn = y_roots(x)
    y = yp if (raw[0] == 2) == (yp % 2 == 0) else yn
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    digest = hashlib.new(
        "ripemd160",
        hashlib.sha256(pref + x.to_bytes(32, "big")).digest(),
    ).digest()
    h160 = int.from_bytes(digest, "big")
    lo, hi, _ = puzzle_band(160)
    q_h = (h160 - lo) // TWO32
    eps_h = (h160 - lo) % TWO32
    return h160, q_h, eps_h


def lane_bounds(q_h: int) -> tuple[int, int]:
    lo, _, _ = puzzle_band(160)
    lo_lane = lo + q_h * TWO32
    hi_lane = lo_lane + TWO32 - 1
    return lo_lane, hi_lane


def write_bat(
    path: Path,
    *,
    label: str,
    lo: int,
    hi: int,
    span: int,
    extra_echo: str = "",
) -> None:
    path.write_text(
        f"""@echo off
setlocal
call "%~dp0..\\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: {label}
{extra_echo}echo Range {lo:x}:{hi:x}  span={span}  (KeyHunt min span {MIN_KEYHUNT_SPAN:x})
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r {lo:x}:{hi:x} -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
""",
        encoding="utf-8",
    )


def main() -> None:
    h160, q_h, eps_h = h160_p160()
    lo_band, hi_band, _ = puzzle_band(160)
    lo_lane, hi_lane = lane_bounds(q_h)
    bf_h = (h160 - lo_band) / (hi_band - lo_band)
    priority_tile = eps_h // EPS_CHUNK

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # --- single padded window (entire lane) ---
    center_full = (lo_lane + hi_lane) // 2
    half_full = TWO32 // 2
    lo_f, hi_f, span_f = clip_d_range(center_full, half_full)
    single_bat = EXPORT_DIR / "run_p160_h160_lane_FULL.bat"
    write_bat(
        single_bat,
        label="FULL (one-shot entire lane)",
        lo=lo_f,
        hi=hi_f,
        span=span_f,
        extra_echo=(
            f"echo q_h={q_h}  eps_h={eps_h}  h160_bf={bf_h:.9f}\n"
            f"echo lo_lane={lo_lane}  hi_lane={hi_lane}\n"
        ),
    )

    # --- 256 sub-tiles ---
    tiles: list[str] = []
    for i in range(NUM_TILES):
        eps_lo = i * EPS_CHUNK
        eps_hi = min(eps_lo + EPS_CHUNK - 1, TWO32 - 1)
        core_lo = lo_lane + eps_lo
        core_hi = lo_lane + eps_hi
        center = (core_lo + core_hi) // 2
        half = max((core_hi - core_lo) // 2, 1)
        lo, hi, span = clip_d_range(center, half)
        name = f"run_p160_h160_lane_{i:03d}_eps_{eps_lo:08x}.bat"
        bat = EXPORT_DIR / name
        pri = " [PRIORITY h160 eps]" if i == priority_tile else ""
        write_bat(
            bat,
            label=f"tile {i:03d}/255  eps [{eps_lo:x},{eps_hi:x}]{pri}",
            lo=lo,
            hi=hi,
            span=span,
            extra_echo=(
                f"echo q_h={q_h}  core_eps=[{eps_lo},{eps_hi}]  tile={i}{pri}\n"
            ),
        )
        tiles.append(
            f"{name}  tile={i:03d}  eps=[{eps_lo:08x},{eps_hi:08x}]  "
            f"span={span}  {lo:x}:{hi:x}{pri}"
        )

    lines = [
        "Puzzle 160 h160 shelf lane — KeyHunt BSGS exports",
        f"h160={h160}",
        f"band_frac(h160)={bf_h:.9f}",
        f"q_h={q_h}",
        f"eps_h={eps_h}  (priority tile {priority_tile:03d})",
        f"lo_lane={lo_lane}",
        f"hi_lane={hi_lane}",
        f"lane_width=2^32={TWO32}",
        f"MIN_KEYHUNT_SPAN={MIN_KEYHUNT_SPAN:x} (2^44)",
        f"tiles={NUM_TILES}  eps_chunk=2^24={EPS_CHUNK}",
        "",
        "ONE-SHOT (entire lane, padded to min span):",
        f"  {single_bat.name}  span={span_f}  {lo_f:x}:{hi_f:x}",
        "",
        "TILES (256 parallel / resumable):",
        *tiles,
        "",
        "Queue: run_h160_lane_queue.bat  (priority tile first, then 000..255)",
        "Single: run_h160_lane_single.bat",
    ]
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {single_bat.name}  span={span_f}")
    print(f"wrote {NUM_TILES} tile bats in {EXPORT_DIR}")
    print(f"manifest: {MANIFEST}")
    print(f"priority tile (h160 eps): {priority_tile:03d}")


if __name__ == "__main__":
    main()
