#!/usr/bin/env python3
"""
Pubkey-rooted power ladder for P160.

Grid (per pubkey axis Px / Py as scalar anchors):
  anchor + k                         — mandatory pubkey ±k  (n=0)
  (anchor ± 2^n) + k   for n=1..158  — power structuring from pubkey

All candidate pubkeys land in a baby table; one Px hit + y-verify solves the puzzle.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parent


def grid_width(max_pow: int) -> int:
    """Bases per axis: pubkey center + ±2^1 .. ±2^max_pow."""
    return 1 + 2 * max_pow


def per_axis_count(fuzz: int, max_pow: int) -> int:
    return (2 * fuzz + 1) * grid_width(max_pow)


def fuzz_for_target(target: int, axes: int, max_pow: int) -> int:
    per = max(1, target // max(1, axes))
    width = grid_width(max_pow)
    half = (per + width - 1) // width
    return max(1, (half - 1) // 2)


def load_pubkey_target() -> tuple[int, int, int, int, int, list[tuple[str, int]]]:
    import sys

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "ECDLP"))
    from ecdlp_full_pipeline import PuzzleConfig, apply_puzzle_defaults, puzzle_band  # noqa: WPS433

    cfg = PuzzleConfig(puzzle_num=160)
    apply_puzzle_defaults(cfg)
    lo, hi, _ = puzzle_band(160)
    row = cfg.row
    target_x, target_y = cfg.Px[row], cfg.Py
    axes = [
        ("Px", target_x),
        ("Py", target_y),
    ]
    return lo, hi, row, target_x, target_y, axes


def iter_scalar_grid(
    anchor: int,
    lo: int,
    hi: int,
    fuzz: int,
    max_pow: int,
    in_band,
    lift,
) -> Iterator[tuple[int, int, int, str]]:
    """Yield (d, n, sign, tag) with sign in {0,+1,-1}, n=0 for pubkey ±k line."""
    seen: set[int] = set()

    def emit(raw: int, n: int, sign: int, tag: str):
        d = raw if in_band(raw, lo, hi) else lift(raw, lo, hi)
        if d in seen:
            return
        seen.add(d)
        yield d, n, sign, tag

    for k in range(-fuzz, fuzz + 1):
        yield from emit(anchor + k, 0, 0, f"pub{k:+d}")

    for n in range(1, max_pow + 1):
        step = 1 << n
        for sign, base in ((+1, anchor + step), (-1, anchor - step)):
            sign_name = "+" if sign > 0 else "-"
            for k in range(-fuzz, fuzz + 1):
                yield from emit(base + k, n, sign, f"{sign_name}2^{n}{k:+d}")
