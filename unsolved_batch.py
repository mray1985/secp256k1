#!/usr/bin/env python3
"""Shared config for unsolved puzzle batch P135–P160 (step 5)."""

from __future__ import annotations

# Always run all six when attempting to solve.
UNSOLVED_PUZZLES: tuple[int, ...] = (135, 140, 145, 150, 155, 160)

# Offset-law row (shelf2+offset bit window): n ≡ 0 (mod 5) cluster → row 0
# (P110, P115, P130 pattern). Px slot index may still differ per puzzle.
OFFSET_LAW_ROW: dict[int, int] = {n: 0 for n in UNSOLVED_PUZZLES}


def offset_law_row(n: int, px_slot: int) -> int:
    """Return offset-calibration row; default px_slot for puzzles outside batch."""
    return OFFSET_LAW_ROW.get(n, px_slot)


def is_unsolved_batch(n: int) -> bool:
    return n in UNSOLVED_PUZZLES
