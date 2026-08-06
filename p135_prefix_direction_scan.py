#!/usr/bin/env python3
"""
Lightweight prefix scan: 02 + x hex digit-by-digit (no string format per step).

Hot path per scroll step:
  1) y&1 -> skip (not compressed 02)
  2) compare x nibbles MSB->LSB via shifts (no f"{x:064x}")
  3) bail on first nibble mismatch
  4) x==px and y==py -> HIT (no re-multiply verify)

One scalar mult at anchor, then +G / -G only.
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from harvester_endless_scroll import three_rail_anchors  # noqa: E402
from p135_common import G, save_hit, scalar_mult  # noqa: E402
from p135_fold_from_P import fold_candidates_from_P  # noqa: E402
from scroll_g_table import fill_scroll_window, px_nibbles, scroll_chunk_table  # noqa: E402

REPORT = ROOT / "ARCHIVE" / "p135_prefix_direction_scan.txt"


def build_tasks(
    anchor: str,
    d0: int,
    radius: int,
    px: int,
    py: int,
    nibbles: tuple[int, ...],
    lo: int,
    hi: int,
    chunk: int,
) -> list[dict]:
    d0 = max(lo, min(hi - 1, d0))
    base = {"px": px, "py": py, "nibbles": nibbles, "anchor": anchor, "table_size": chunk}
    tasks: list[dict] = []

    def add_range(mode: str, start: int, count: int) -> None:
        if count <= 0:
            return
        pos = start
        rem = count
        while rem > 0:
            n = min(chunk, rem)
            tasks.append({**base, "mode": mode, "d_start": pos, "steps": n})
            pos += n if mode == "fwd" else -n
            rem -= n

    add_range("fwd", d0 + 1, min(radius, hi - 1 - d0))
    add_range("bwd", d0 - 1, min(radius, d0 - lo))
    return tasks


def collect_anchors(px: int, py: int, lo: int, hi: int, top: int) -> list[tuple[str, int]]:
    seen: dict[int, str] = {}
    for a in fold_candidates_from_P(px, py, 135, lo, top, hi):
        seen[a.d] = a.name
    for a in three_rail_anchors(px, py, 135):
        if a.d not in seen:
            seen[a.d] = a.name
    return sorted(((n, d) for d, n in seen.items()), key=lambda x: x[1])


def scan_anchor(
    name: str,
    d0: int,
    radius: int,
    px: int,
    py: int,
    nibbles: tuple[int, ...],
    lo: int,
    hi: int,
    chunk: int,
    workers: int,
) -> tuple[int | None, int, int]:
    d0 = max(lo, min(hi - 1, d0))
    p0 = scalar_mult(d0, G)
    if p0 and not (p0[1] & 1) and p0[0] == px and p0[1] == py:
        return d0, 1, 66

    tasks = build_tasks(name, d0, radius, px, py, nibbles, lo, hi, chunk)
    total = best = 0
    if workers <= 1:
        for t in tasks:
            r = scroll_chunk_table(t)
            total += r["checked"]
            best = max(best, r["best"])
            if r["hit"]:
                return r["hit"], total, best
        return None, total, best

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(scroll_chunk_table, t) for t in tasks]
        for fut in as_completed(futs):
            r = fut.result()
            total += r["checked"]
            best = max(best, r["best"])
            if r["hit"]:
                for f in futs:
                    f.cancel()
                return r["hit"], total, best
    return None, total, best


def bench(steps: int = 100_000) -> None:
    from scroll_g_table import init_scroll_table, prefix_scan_arrays

    px = 9210836494447108270027136741376870869791784014198948301625976867708124077590
    nib = px_nibbles(px)
    lo, _, _ = puzzle_band(135)
    d0 = lo + 999_999

    init_scroll_table(steps)
    t0 = time.perf_counter()
    ds, xs, ys, _ = fill_scroll_window(d0, steps, forward=True)
    t1 = time.perf_counter()
    _, _ = prefix_scan_arrays(ds, xs, ys, px, 0, nib)
    t2 = time.perf_counter()
    print(f"EC table build {steps:,}: {steps / (t1 - t0):,.0f}/s")
    print(f"prefix filter only:      {steps / (t2 - t1):,.0f}/s")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--radius", type=int, default=10_000_000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--chunk", type=int, default=200_000)
    ap.add_argument("--bench", action="store_true")
    args = ap.parse_args()

    if args.bench:
        bench()
        return 0

    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn
    lo, hi, top = puzzle_band(135)
    nibbles = px_nibbles(px)
    target_comp = "02" + "".join(f"{n:x}" for n in nibbles)

    anchors = collect_anchors(px, py, lo, hi, top)
    lines = [
        "P135 PRECOMPUTED SCROLL + PREFIX FILTER (02 + x nibbles)",
        f"target: {target_comp[:18]}...",
        f"anchors={len(anchors)} radius=+/-{args.radius:,} workers={args.workers}",
        "EC: 1x mult + G-table; filter: integer-only on prebuilt x/y",
        "",
    ]
    print("\n".join(lines[:4]), flush=True)

    hit_d: int | None = None
    hit_name = ""
    t_all = time.perf_counter()
    grand = 0

    for i, (name, d0) in enumerate(anchors, 1):
        t0 = time.perf_counter()
        hit, n, best = scan_anchor(
            name, d0, args.radius, px, py, nibbles, lo, hi, args.chunk, args.workers
        )
        dt = time.perf_counter() - t0
        grand += n
        rate = n / dt if dt else 0
        line = (
            f"[{i}/{len(anchors)}] {name:28s} {n:,} pts {dt:.1f}s ({rate:,.0f}/s) "
            f"best_nib={max(0,best-1)} {'HIT '+str(hit) if hit else ''}"
        )
        lines.append(line)
        print(line, flush=True)
        if hit:
            hit_d = hit
            hit_name = name
            break

    elapsed = time.perf_counter() - t_all
    summary = f"total={grand:,} wall={elapsed:.1f}s avg={grand/elapsed:,.0f}/s result={'SOLVED' if hit_d else 'not found'}"
    lines.extend(["", summary])
    print(summary, flush=True)
    if hit_d:
        save_hit(hit_d, source=f"prefix_light:{hit_name}")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if hit_d else 1


if __name__ == "__main__":
    raise SystemExit(main())
