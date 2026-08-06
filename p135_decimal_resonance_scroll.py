#!/usr/bin/env python3
"""
Decimal-resonance scroll for P135.

Anchors:
  - barcode mean41 (64.2% band)
  - 2^134 floor (921 decimal lock on Px)
  - top-3 chunk cluster mean
  - individual in-band barcode chunks

Filter: decimal Px prefix depth + optional ratio Px/Px(2^134) ~ 0.1
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from p135_common import G, save_hit, scalar_mult  # noqa: E402
from scroll_g_table import (  # noqa: E402
    fill_scroll_window,
    init_scroll_table,
    prefix_depth_fast,
    px_nibbles,
    scroll_chunk_table,
)

CHUNKS41 = [
    36494447108270027136741376870869791784014,
    27002713674137687086979178401419894830162,
    27136741376870869791784014198948301625976,
    36741376870869791784014198948301625976867,
    41376870869791784014198948301625976867708,
    37687086979178401419894830162597686770812,
    33931356102403126543598669501169573955773,
    39313561024031265435986695011695739557734,
    31356102403126543598669501169573955773406,
    35610240312654359866950116957395577340649,
    34064768751455512905803656635953890300131,
    40647687514555129058036566359538903001312,
    29875763924304053419655647994379903175655,
    39243040534196556479943799031756551071842,
    24304053419655647994379903175655107184284,
    43040534196556479943799031756551071842849,
    30405341965564799437990317565510718428499,
    40534196556479943799031756551071842849986,
    34196556479943799031756551071842849986982,
    41965564799437990317565510718428499869821,
    43799031756551071842849986982126532884689,
    37990317565510718428499869821265328846898,
]

REPORT = ROOT / "ARCHIVE" / "p135_decimal_resonance_scroll.txt"


def dec_prefix_depth(x: int, target_dec: str) -> int:
    sx = str(x)
    k = 0
    for a, b in zip(target_dec, sx):
        if a == b:
            k += 1
        else:
            break
    return k


def dec_ratio_ok(x: int, x_anchor: int, lo_r: float, hi_r: float) -> bool:
    if x_anchor <= 0:
        return True
    r = x / x_anchor
    return lo_r <= r <= hi_r


def dec_scan_arrays(
    ds,
    xs,
    ys,
    px: int,
    py: int,
    target_dec: str,
    x_anchor: int,
    *,
    min_dec: int,
    ratio_band: tuple[float, float] | None,
) -> tuple[int | None, int, int]:
    best_dec = 0
    best_hex = 0
    nibbles = px_nibbles(px)
    for d, x, y in zip(ds, xs, ys):
        if y & 1:
            continue
        if x == px and y == py:
            return d, 999, 66
        if ratio_band and not dec_ratio_ok(x, x_anchor, *ratio_band):
            continue
        dep = dec_prefix_depth(x, target_dec)
        if dep < min_dec:
            continue
        if dep > best_dec:
            best_dec = dep
        hdep = prefix_depth_fast(x, y, nibbles)
        if hdep > best_hex:
            best_hex = hdep
    return None, best_dec, best_hex


def scroll_chunk_decimal(task: dict) -> dict:
    base = scroll_chunk_table(task)
    if base.get("hit"):
        return base

    px = task["px"]
    py = task["py"]
    target_dec = task["target_dec"]
    x_anchor = task["x_anchor"]
    min_dec = task.get("min_dec", 3)
    ratio_band = task.get("ratio_band")

    init_scroll_table(max(task.get("table_size", task["steps"]), task["steps"]))
    p0 = scalar_mult(task["d_start"], G)
    checked = 1
    best_dec = 0
    best_hex = base.get("best", 0)

    if p0:
        if not (p0[1] & 1) and p0[0] == px and p0[1] == py:
            return {"hit": task["d_start"], "checked": 1, "best_dec": 999, "best": 66, "anchor": task["anchor"]}
        if not ratio_band or dec_ratio_ok(p0[0], x_anchor, *ratio_band):
            best_dec = max(best_dec, dec_prefix_depth(p0[0], target_dec))

    forward = task["mode"] == "fwd"
    ds, xs, ys, _ = fill_scroll_window(task["d_start"], task["steps"], forward=forward)
    checked += len(ds)
    hit, bd, bh = dec_scan_arrays(
        ds, xs, ys, px, py, target_dec, x_anchor,
        min_dec=min_dec, ratio_band=ratio_band,
    )
    return {
        "hit": hit,
        "checked": checked,
        "best_dec": max(best_dec, bd),
        "best": max(best_hex, bh),
        "anchor": task["anchor"],
    }


def build_anchors(lo: int, hi: int, px_dec: str) -> list[tuple[str, int]]:
    in_band = [c for c in CHUNKS41 if lo <= c < hi]
    mean41 = sum(CHUNKS41) // len(CHUNKS41)
    top3 = sorted(in_band, key=lambda c: dec_prefix_depth(c, px_dec), reverse=True)[:3]
    top3_mean = sum(top3) // 3 if top3 else mean41
    median = sorted(in_band)[len(in_band) // 2]

    anchors: dict[int, str] = {
        lo: "band_floor_2^134",
        mean41: "barcode_mean41",
        top3_mean: "barcode_top3_mean",
        median: "barcode_median",
    }
    for i, c in enumerate(in_band[:8]):
        anchors.setdefault(c, f"chunk_{i}")

    return sorted((name, d) for d, name in anchors.items())


def build_tasks(
    anchor: str,
    d0: int,
    radius: int,
    px: int,
    py: int,
    nibbles: tuple[int, ...],
    target_dec: str,
    x_anchor: int,
    lo: int,
    hi: int,
    chunk: int,
    *,
    min_dec: int,
    ratio_band: tuple[float, float] | None,
) -> list[dict]:
    d0 = max(lo, min(hi - 1, d0))
    base = {
        "px": px,
        "py": py,
        "nibbles": nibbles,
        "anchor": anchor,
        "table_size": chunk,
        "target_dec": target_dec,
        "x_anchor": x_anchor,
        "min_dec": min_dec,
        "ratio_band": ratio_band,
    }
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
    target_dec: str,
    x_anchor: int,
    lo: int,
    hi: int,
    chunk: int,
    workers: int,
    *,
    min_dec: int,
    ratio_band: tuple[float, float] | None,
) -> tuple[int | None, int, int, int]:
    from concurrent.futures import ProcessPoolExecutor, as_completed

    tasks = build_tasks(
        name, d0, radius, px, py, nibbles, target_dec, x_anchor, lo, hi, chunk,
        min_dec=min_dec, ratio_band=ratio_band,
    )
    total = best_dec = best_hex = 0

    if workers <= 1:
        init_scroll_table(chunk)
        for t in tasks:
            r = scroll_chunk_decimal(t)
            total += r["checked"]
            best_dec = max(best_dec, r.get("best_dec", 0))
            best_hex = max(best_hex, r.get("best", 0))
            if r["hit"]:
                return r["hit"], total, best_dec, best_hex
        return None, total, best_dec, best_hex

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(scroll_chunk_decimal, t) for t in tasks]
        for fut in as_completed(futs):
            r = fut.result()
            total += r["checked"]
            best_dec = max(best_dec, r.get("best_dec", 0))
            best_hex = max(best_hex, r.get("best", 0))
            if r["hit"]:
                for f in futs:
                    f.cancel()
                return r["hit"], total, best_dec, best_hex
    return None, total, best_dec, best_hex


def main() -> int:
    ap = argparse.ArgumentParser(description="P135 decimal-resonance scroll")
    ap.add_argument("--radius", type=int, default=2_000_000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--chunk", type=int, default=200_000)
    ap.add_argument("--min-dec", type=int, default=3, help="min decimal Px prefix depth")
    ap.add_argument("--ratio", action="store_true", help="filter Px/Px(2^134) in [0.095,0.105]")
    ap.add_argument("--list-only", action="store_true")
    args = ap.parse_args()

    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn
    lo, hi, _ = puzzle_band(135)
    nibbles = px_nibbles(px)
    target_dec = str(px)
    x_anchor = scalar_mult(lo, G)[0]

    ratio_band = (0.095, 0.105) if args.ratio else None
    anchors = build_anchors(lo, hi, target_dec)

    lines = [
        "P135 DECIMAL-RESONANCE SCROLL",
        f"target Px dec: {target_dec[:20]}...",
        f"Px(2^134) dec: {str(x_anchor)[:20]}...",
        f"anchors={len(anchors)}  radius=+/-{args.radius:,}  min_dec={args.min_dec}",
        f"ratio_filter={ratio_band}",
        "",
    ]

    if args.list_only:
        for name, d in anchors:
            pos = 100 * (d - lo) / (hi - lo)
            lines.append(f"  {name:22s} pos={pos:6.2f}%  d...{str(d)[-12:]}")
        text = "\n".join(lines)
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(text + "\n", encoding="utf-8")
        print(text)
        return 0

    hit_d = None
    t_all = time.perf_counter()
    grand = 0

    for i, (name, d0) in enumerate(anchors, 1):
        t0 = time.perf_counter()
        hit, n, best_dec, best_hex = scan_anchor(
            name, d0, args.radius, px, py, nibbles, target_dec, x_anchor,
            lo, hi, args.chunk, args.workers,
            min_dec=args.min_dec, ratio_band=ratio_band,
        )
        dt = time.perf_counter() - t0
        grand += n
        rate = n / dt if dt else 0
        line = (
            f"[{i}/{len(anchors)}] {name:22s} {n:,} pts {dt:.1f}s ({rate:,.0f}/s) "
            f"best_dec={best_dec} best_hex_nib={max(0,best_hex-1)} "
            f"{'HIT '+str(hit) if hit else ''}"
        )
        lines.append(line)
        print(line, flush=True)
        if hit:
            hit_d = hit
            break

    elapsed = time.perf_counter() - t_all
    summary = (
        f"total={grand:,} wall={elapsed:.1f}s avg={grand/elapsed:,.0f}/s "
        f"result={'SOLVED' if hit_d else 'not found'}"
    )
    lines.extend(["", summary])
    print(summary, flush=True)
    if hit_d:
        save_hit(hit_d, source="decimal_resonance_scroll")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if hit_d else 1


if __name__ == "__main__":
    raise SystemExit(main())
