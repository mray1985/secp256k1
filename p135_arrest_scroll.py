#!/usr/bin/env python3
"""
Arrest geometry -> anchor d0 -> precomputed endless scroll -> prefix filter.

Not "run scripts" — one pipeline:
  1) arrest formulas (frac(sqrt N), {Delta_y}) give d0
  2) fold-from-P anchors (floor/height)
  3) one scalar mult per chunk, G-offset table, integer prefix scan on x
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from harvester_endless_scroll import three_rail_anchors  # noqa: E402
from p135_common import G, N, P, save_hit, scalar_mult  # noqa: E402
from p135_fold_from_P import fold_candidates_from_P  # noqa: E402
from scroll_g_table import (  # noqa: E402
    fill_scroll_window,
    init_scroll_table,
    prefix_scan_arrays,
    prefix_depth_fast,
    px_nibbles,
    scroll_chunk_table,
)

getcontext().prec = 120
PN = P - N
REPORT = ROOT / "ARCHIVE" / "p135_arrest_scroll.txt"


def log2d(v: int | Decimal) -> float:
    return float((Decimal(v).ln() / Decimal(2).ln()))


def arrest_d(mult: float, k: int, spn: Decimal | None = None) -> int:
    spn = spn or Decimal(PN).sqrt()
    return int(
        (Decimal(str(mult)) * spn * (Decimal(2) ** k)).to_integral_value(rounding="ROUND_FLOOR")
    )


def arrest_anchors(px: int, py: int, n: int, lo: int, hi: int, top: int) -> list[tuple[str, int]]:
    spn = Decimal(PN).sqrt()
    sn = Decimal(N).sqrt()
    frac_sn = float(sn - sn.to_integral_value(rounding="ROUND_FLOOR"))

    h = log2d(PN)
    ly = log2d(Decimal(py).sqrt())
    fdy = (h - ly) - math.floor(h - ly)

    out: list[tuple[str, int]] = []

    # email arrest: frac(sqrt N) * sqrt(p-N) * 2^k
    for k, label in ((71, "arrest_frac_k71"), (72, "arrest_frac_k72")):
        d = arrest_d(frac_sn, k, spn)
        if lo <= d < hi:
            out.append((label, d))

    # log hinge arrest: {Delta_y} * sqrt(p-N) * 2^k  (P135 in-band k ~ n-57)
    k_dy = n - 57
    d_dy = arrest_d(fdy, k_dy, spn)
    if lo <= d < hi:
        out.append((f"arrest_Delta_y_k{k_dy}", d_dy))

    k_dy_lo = k_dy - 8
    d_dy_lo = arrest_d(fdy, k_dy_lo, spn)
    if lo <= d_dy_lo < hi:
        out.append((f"arrest_Delta_y_k{k_dy_lo}", d_dy_lo))

    # fold-from-P + formula rails
    seen = {d: name for name, d in out}
    for a in fold_candidates_from_P(px, py, n, lo, top, hi):
        if a.d not in seen:
            seen[a.d] = a.name
    for a in three_rail_anchors(px, py, n):
        if a.d not in seen:
            seen[a.d] = a.name

    return sorted(((n, d) for d, n in seen.items()), key=lambda x: x[0])


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
        pos, rem = start, count
        while rem > 0:
            n = min(chunk, rem)
            tasks.append({**base, "mode": mode, "d_start": pos, "steps": n})
            pos += n if mode == "fwd" else -n
            rem -= n

    add_range("fwd", d0 + 1, min(radius, hi - 1 - d0))
    add_range("bwd", d0 - 1, min(radius, d0 - lo))
    return tasks


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
    from concurrent.futures import ProcessPoolExecutor, as_completed

    d0 = max(lo, min(hi - 1, d0))
    p0 = scalar_mult(d0, G)
    if p0 and not (p0[1] & 1) and p0[0] == px and p0[1] == py:
        return d0, 1, 66

    tasks = build_tasks(name, d0, radius, px, py, nibbles, lo, hi, chunk)
    total = best = 0

    if workers <= 1:
        init_scroll_table(chunk)
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Arrest anchors + precomputed scroll + prefix filter")
    ap.add_argument("--radius", type=int, default=10_000_000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--chunk", type=int, default=250_000)
    ap.add_argument("--list-only", action="store_true")
    args = ap.parse_args()

    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn
    lo, hi, top = puzzle_band(135)
    nibbles = px_nibbles(px)

    spn = Decimal(PN).sqrt()
    sn = Decimal(N).sqrt()
    frac_sn = float(sn - sn.to_integral_value(rounding="ROUND_FLOOR"))
    h = log2d(PN)
    ly = log2d(Decimal(py).sqrt())
    fdy = (h - ly) - math.floor(h - ly)

    anchors = arrest_anchors(px, py, 135, lo, hi, top)

    lines = [
        "P135 ARREST + PRECOMPUTED ENDLESS SCROLL",
        "",
        "=== hinge / arrest constants ===",
        f"floor(sqrt N) = floor(sqrt p) = 2^128 - 1  (shared shell)",
        f"frac(sqrt N)) = {frac_sn:.12f}  (decimal tail — spatial)",
        f"{{H}} = {h - math.floor(h):.6f}  {{H/2}} = {(h/2) - math.floor(h/2):.6f}  (log hinge)",
        f"{{Delta_y}} = {fdy:.6f}  (live y-bridge on P)",
        f"sqrt(p-N) ~ {float(spn):.6e}",
        "",
        f"k=71 arrest (email): bits={arrest_d(frac_sn, 71, spn).bit_length()} "
        f"in_band={lo <= arrest_d(frac_sn, 71, spn) < hi}  (134-bit — below band)",
        f"k=72 arrest (frac):  ...{str(arrest_d(frac_sn, 72, spn))[-12:]}",
        f"k=78 arrest ({{Dy}}): ...{str(arrest_d(fdy, 78, spn))[-12:]}",
        "",
        f"anchors={len(anchors)}  radius=+/-{args.radius:,}  chunk={args.chunk:,}",
        "scroll: 1x scalar mult + G-table offset adds; filter on prebuilt x/y arrays",
        "",
    ]

    if args.list_only:
        for name, d in anchors:
            pos = 100 * (d - lo) / (hi - lo)
            lines.append(f"  {name:32s} d...{str(d)[-10:]}  pos={pos:.1f}%")
        text = "\n".join(lines)
        print(text)
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(text + "\n", encoding="utf-8")
        return 0

    print("\n".join(lines[:12]), flush=True)

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
            f"[{i}/{len(anchors)}] {name:32s} {n:,} pts {dt:.1f}s ({rate:,.0f}/s) "
            f"best_nib={max(0, best - 1)} {'HIT ' + str(hit) if hit else ''}"
        )
        lines.append(line)
        print(line, flush=True)
        if hit:
            hit_d = hit
            hit_name = name
            break

    elapsed = time.perf_counter() - t_all
    summary = (
        f"total={grand:,} wall={elapsed:.1f}s avg={grand / elapsed:,.0f}/s "
        f"result={'SOLVED' if hit_d else 'not found'}"
    )
    lines.extend(["", summary])
    print(summary, flush=True)
    if hit_d:
        save_hit(hit_d, source=f"arrest_scroll:{hit_name}")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if hit_d else 1


if __name__ == "__main__":
    raise SystemExit(main())
