#!/usr/bin/env python3
"""
Precomputed +G / -G offset table for Harvester endless scroll.

VanitySearch builds GTable[i] = i*G once; scroll uses P_i = P0 + table[i]
(one point add per step, table shared across all anchors in a worker).

Filter pass runs on prebuilt x/y arrays — no EC in the prefix loop.
"""

from __future__ import annotations

from typing import Sequence

from p135_common import G, N, P, point_add, point_neg, scalar_mult

GX, GY = G
NEG_G = point_neg(G)

# Process-local tables (built once per worker via init_worker)
_FWD: list[tuple[int, int] | None] | None = None
_BWD: list[tuple[int, int] | None] | None = None
_TABLE_SIZE = 0


def build_g_offsets(size: int) -> tuple[list[tuple[int, int] | None], list[tuple[int, int] | None]]:
    """i*G and i*(-G) for i in [0, size]. _fwd[0]=None (identity), _fwd[i]=i*G."""
    fwd: list[tuple[int, int] | None] = [None] * (size + 1)
    bwd: list[tuple[int, int] | None] = [None] * (size + 1)
    pt_f: tuple[int, int] | None = None
    pt_b: tuple[int, int] | None = None
    for i in range(1, size + 1):
        pt_f = point_add(pt_f, G)
        pt_b = point_add(pt_b, NEG_G)
        fwd[i] = pt_f
        bwd[i] = pt_b
    return fwd, bwd


def init_scroll_table(size: int) -> None:
    global _FWD, _BWD, _TABLE_SIZE
    if _FWD is not None and _TABLE_SIZE >= size:
        return
    _FWD, _BWD = build_g_offsets(size)
    _TABLE_SIZE = size


def ensure_table(size: int) -> None:
    if _FWD is None or _TABLE_SIZE < size:
        init_scroll_table(size)


def fill_scroll_window(
    d_anchor: int,
    steps: int,
    *,
    forward: bool = True,
) -> tuple[list[int], list[int], list[int], int]:
    """
    One scalar mult at d_anchor, then table[i]*G adds only.
    Returns (d_list, x_list, y_list, sign) where sign=+1 fwd / -1 bwd.
    """
    if steps <= 0:
        return [], [], [], 1 if forward else -1
    ensure_table(steps)
    assert _FWD is not None and _BWD is not None

    p0 = scalar_mult(d_anchor, G)
    if p0 is None:
        return [], [], [], 1 if forward else -1

    offsets = _FWD if forward else _BWD
    sign = 1 if forward else -1
    ds: list[int] = []
    xs: list[int] = []
    ys: list[int] = []

    for i in range(1, steps + 1):
        pt = point_add(p0, offsets[i])
        if pt is None:
            continue
        ds.append(d_anchor + sign * i)
        xs.append(pt[0])
        ys.append(pt[1])

    return ds, xs, ys, sign


def px_nibbles(px: int) -> tuple[int, ...]:
    return tuple((px >> (4 * (63 - i))) & 0xF for i in range(64))


def prefix_depth_fast(x: int, y: int, nibbles: Sequence[int]) -> int:
    if y & 1:
        return 0
    depth = 1
    for i, t in enumerate(nibbles):
        if ((x >> (4 * (63 - i))) & 0xF) != t:
            return depth
        depth = 2 + i
    return 66


def prefix_scan_arrays(
    ds: Sequence[int],
    xs: Sequence[int],
    ys: Sequence[int],
    px: int,
    py: int,
    nibbles: Sequence[int],
) -> tuple[int | None, int]:
    """Pure integer filter on precomputed coordinates. Returns (hit_d, best_depth)."""
    best = 0
    top = nibbles[0]
    for d, x, y in zip(ds, xs, ys):
        if y & 1:
            continue
        if x == px and y == py:
            return d, 66
        if ((x >> 252) & 0xF) != top:
            continue
        dep = prefix_depth_fast(x, y, nibbles)
        if dep > best:
            best = dep
    return None, best


def scroll_chunk_table(task: dict) -> dict:
    """Worker entry: build coordinate table, then lightweight prefix scan."""
    mode = task["mode"]
    d_start = task["d_start"]
    steps = task["steps"]
    px = task["px"]
    py = task["py"]
    nibbles = tuple(task["nibbles"])
    anchor = task["anchor"]
    table_size = task.get("table_size", steps)

    init_scroll_table(max(table_size, steps))

    # anchor point itself
    p0 = scalar_mult(d_start, G)
    checked = 1
    best = 0
    if p0 and not (p0[1] & 1) and p0[0] == px and p0[1] == py:
        return {"hit": d_start, "checked": 1, "best": 66, "anchor": anchor}
    if p0:
        best = prefix_depth_fast(p0[0], p0[1], nibbles)

    forward = mode == "fwd"
    ds, xs, ys, _ = fill_scroll_window(d_start, steps, forward=forward)
    checked += len(ds)
    hit, b2 = prefix_scan_arrays(ds, xs, ys, px, py, nibbles)
    best = max(best, b2)

    return {"hit": hit, "checked": checked, "best": best, "anchor": anchor}
