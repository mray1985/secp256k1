"""Shared gap-tier offset conventions for shelf2 alignment."""

from __future__ import annotations

import math
from typing import Literal

Direction = Literal["+", "-"]


def offset_bits_to_interval(offset_bits: int) -> tuple[int, int]:
    """bit_length(o) == offset_bits  <=>  2^(k-1) <= o < 2^k."""
    if offset_bits <= 0:
        return (0, 1)
    return (1 << (offset_bits - 1), 1 << offset_bits)


def gap_to_offset_bits(puzzle_h: int, gap: int) -> int:
    return puzzle_h - gap


def gap_interval(puzzle_h: int, gap: int) -> tuple[int, int, int]:
    """Return (offset_bits, o_lo inclusive, o_hi exclusive) for a gap tier."""
    ob = gap_to_offset_bits(puzzle_h, gap)
    lo, hi = offset_bits_to_interval(ob)
    return ob, lo, hi


def observed_offset(d: int, shelf2: int, lo_mod: int) -> int:
    return (d - shelf2) % lo_mod


def offset_in_gap_tier(
    o: int, puzzle_h: int, gap: int, *, lo_mod: int | None = None
) -> bool:
    _, o_lo, o_hi = gap_interval(puzzle_h, gap)
    if o <= 0:
        return False
    if o >= (lo_mod or o_hi):
        # still valid if bitlength matches even when o >= LO (residue wraps)
        pass
    return o_lo <= o < o_hi


def gap_from_observed(d: int, shelf2: int, puzzle_h: int, lo_mod: int) -> tuple[int, int]:
    """Return (gap, offset_bits) from solved d."""
    o = observed_offset(d, shelf2, lo_mod)
    ob = o.bit_length() if o else 0
    return puzzle_h - ob, ob


def d_candidates_from_offset(
    shelf2: int, o: int, lo: int, hi: int, *, mod_n: int | None = None
) -> list[tuple[int, Direction]]:
    """Lift offset o to puzzle-band d via + and - shelf2 (with LO wrap)."""
    if o <= 0:
        return []
    out: list[tuple[int, Direction]] = []
    seen: set[int] = set()

    def add(d: int, direction: Direction) -> None:
        if mod_n is not None:
            d = d % mod_n
        if lo <= d < hi and d not in seen:
            seen.add(d)
            out.append((d, direction))

    for direction, base in (("+", shelf2 + o), ("-", shelf2 - o)):
        add(base, direction)
        add(base - lo, direction)
        add(base + lo, direction)

    return out


def verify_convention_row(
    puzzle_h: int, d: int, shelf2: int, lo_mod: int
) -> dict:
    o = observed_offset(d, shelf2, lo_mod)
    ob = o.bit_length() if o else 0
    gap = puzzle_h - ob
    _, o_lo, o_hi = gap_interval(puzzle_h, gap) if gap > 0 else (0, 0, 0)
    return {
        "puzzle_h": puzzle_h,
        "d": d,
        "shelf2": shelf2,
        "offset": o,
        "offset_bits": ob,
        "gap": gap,
        "gap_eq_h_minus_offset_bits": gap == puzzle_h - ob,
        "offset_in_bit_interval": o_lo <= o < o_hi if o else False,
        "formula_offset_bits_eq_bitlength": ob == (o.bit_length() if o else 0),
    }


def uniform_lo_null_p_gap(puzzle_h: int, gap: int) -> float:
    """P(gap | o uniform on [0, LO)) with LO=2^(H-1), o>0."""
    if gap < 1 or gap >= puzzle_h:
        return 0.0
    return 2.0 ** (-gap)


def uniform_lo_null_p_gap12(puzzle_h: int) -> float:
    return uniform_lo_null_p_gap(puzzle_h, 1) + uniform_lo_null_p_gap(puzzle_h, 2)


def binomial_tail_ge(n: int, k: int, p: float) -> float:
    return sum(math.comb(n, i) * (p**i) * ((1 - p) ** (n - i)) for i in range(k, n + 1))


def sample_offsets_in_interval(o_lo: int, o_hi: int, n_samples: int) -> list[int]:
    """Sample offsets across [o_lo, o_hi) without enumerating the full interval."""
    if o_hi <= o_lo:
        return []
    width = o_hi - o_lo
    if width <= n_samples:
        return list(range(o_lo, o_hi))
    pts = {o_lo, o_hi - 1, (o_lo + o_hi - 1) // 2}
    if n_samples > 3:
        step = max(1, width // (n_samples - 1))
        for i in range(0, width, step):
            pts.add(o_lo + i)
    return sorted(pts)
