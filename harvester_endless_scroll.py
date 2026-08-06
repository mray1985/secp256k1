#!/usr/bin/env python3
"""
Harvester endless scroll for Puzzle 135 — fast path.

One scalar mult at each anchor (or chunk start), then only P += G / P -= G.
No verify_candidate in the hot loop (no re-multiply per step).
Optional parallel chunk workers for wide radius scans.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
import sys
import time
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from p135_common import N, P, save_hit  # noqa: E402
from puzzle_keys_53125 import parse_53125

REPORT = ROOT / "ARCHIVE" / "harvester_endless_scroll.txt"
CHECKED_KEYS = Path(r"C:\Users\mitch\Desktop\harvester\checkedkeys.txt")
ROW0_HUNT = ROOT / "ARCHIVE" / "p135_row0_hunt.csv"

PN = P - N
SQRT_N_INT = 340282366920938463463374607431768211455
A3 = 21882023022690643225957990962827778287572171943979549177037792017938914896823
LAM = 0xD773B315F9871CF943F6F886AD1243BBE9D2130DB214DD8EF0504CFEDAE1049D

# secp256k1 generator (module-level for pickling workers)
GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
NEG_GY = (-GY) % P
_MAX_POOL = 61  # Windows cap for ProcessPoolExecutor (Python 3.14)


class MultiExecutor:
    """Fan-out across multiple ProcessPoolExecutors to exceed the 61-worker OS cap."""

    def __init__(self, workers: int) -> None:
        self.pools: list[ProcessPoolExecutor] = []
        left = max(1, workers)
        while left > 0:
            w = min(_MAX_POOL, left)
            self.pools.append(ProcessPoolExecutor(max_workers=w))
            left -= w
        self._i = 0

    def submit(self, fn, *args, **kwargs) -> Future:
        pool = self.pools[self._i % len(self.pools)]
        self._i += 1
        return pool.submit(fn, *args, **kwargs)

    def shutdown(self) -> None:
        for pool in self.pools:
            pool.shutdown(wait=True)

    def __enter__(self) -> MultiExecutor:
        return self

    def __exit__(self, *exc) -> None:
        self.shutdown()


def frac(x: float) -> float:
    return x - math.floor(x)


def f2s(v: int) -> float:
    getcontext().prec = 80
    v = int(v) % P
    if v <= 0:
        return float("nan")
    ln = float(Decimal(v).ln() / Decimal(2).ln()) / 2
    return ln - math.floor(ln)


def d_from_band_frac(bf: float) -> int:
    return int(round(2 ** (134 + bf)))


def clamp_band(d: int, lo: int, hi: int) -> int | None:
    if lo <= d < hi:
        return d
    return None


def pubkey_at(d: int) -> tuple[int, int]:
    """One-time multiply at anchor / chunk boundary."""
    from ecdsa import SECP256k1, SigningKey

    sk = SigningKey.from_secret_exponent(int(d) % N, curve=SECP256k1)
    pt = sk.get_verifying_key().pubkey.point
    return int(pt.x()), int(pt.y())


def add_g(x1: int, y1: int, x2: int, y2: int) -> tuple[int, int]:
    """P += G (or += arbitrary affine point). Inlined for scroll speed."""
    if x1 == x2:
        lam = (3 * x1 * x1) * pow(2 * y1, -1, P) % P
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, P) % P
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return x3, y3


def scroll_forward(
    d_start: int,
    steps: int,
    px: int,
    py: int,
) -> tuple[int | None, int]:
    """One multiply at d_start, then `steps` additions of +G."""
    if steps <= 0:
        return None, 0
    x, y = pubkey_at(d_start)
    checked = 1
    if x == px and y == py:
        return d_start, checked
    for i in range(1, steps + 1):
        x, y = add_g(x, y, GX, GY)
        checked += 1
        if x == px and y == py:
            return d_start + i, checked
    return None, checked


def scroll_backward(
    d_start: int,
    steps: int,
    px: int,
    py: int,
) -> tuple[int | None, int]:
    """One multiply at d_start, then `steps` additions of -G."""
    if steps <= 0:
        return None, 0
    x, y = pubkey_at(d_start)
    checked = 1
    if x == px and y == py:
        return d_start, checked
    for i in range(1, steps + 1):
        x, y = add_g(x, y, GX, NEG_GY)
        checked += 1
        if x == px and y == py:
            return d_start - i, checked
    return None, checked


def scroll_chunk(task: dict) -> dict:
    """Worker: one multiply + add-only scroll on a d interval."""
    mode = task["mode"]
    d0 = task["d0"]
    steps = task["steps"]
    px = task["px"]
    py = task["py"]
    if mode == "fwd":
        hit, n = scroll_forward(d0, steps, px, py)
    else:
        hit, n = scroll_backward(d0, steps, px, py)
    return {"hit": hit, "checked": n, "anchor": task["anchor"], "chunk": task["chunk"]}


def parallel_scroll(
    anchor: str,
    d_center: int,
    radius: int,
    lo: int,
    hi: int,
    px: int,
    py: int,
    chunk: int,
    pool: MultiExecutor | None = None,
) -> tuple[int | None, int]:
    """Split +/- radius into chunks; each chunk = 1 multiply + add-only scroll."""
    d_center = max(lo, min(hi - 1, d_center))
    tasks: list[dict] = []

    # forward chunks: [d_center+1, d_center+radius]
    d_lo_f = d_center + 1
    d_hi_f = min(hi - 1, d_center + radius)
    pos = d_lo_f
    ci = 0
    while pos <= d_hi_f:
        end = min(d_hi_f, pos + chunk - 1)
        tasks.append(
            {
                "mode": "fwd",
                "d0": pos,
                "steps": end - pos,
                "px": px,
                "py": py,
                "anchor": anchor,
                "chunk": f"f{ci}",
            }
        )
        pos = end + 1
        ci += 1

    # backward chunks: [d_center-radius, d_center-1]
    d_hi_b = d_center - 1
    d_lo_b = max(lo, d_center - radius)
    pos = d_hi_b
    ci = 0
    while pos >= d_lo_b:
        start = max(d_lo_b, pos - chunk + 1)
        tasks.append(
            {
                "mode": "bwd",
                "d0": pos,
                "steps": pos - start,
                "px": px,
                "py": py,
                "anchor": anchor,
                "chunk": f"b{ci}",
            }
        )
        pos = start - 1
        ci += 1

    # center point
    hit_c, n_c = scroll_forward(d_center, 0, px, py)
    if hit_c:
        return hit_c, n_c

    total = n_c
    if not tasks:
        return None, total

    def consume(futs: list) -> tuple[int | None, int]:
        nonlocal total
        for fut in as_completed(futs):
            r = fut.result()
            total += r["checked"]
            if r["hit"]:
                for f in futs:
                    f.cancel()
                return r["hit"], total
        return None, total

    if pool is None:
        for t in tasks:
            r = scroll_chunk(t)
            total += r["checked"]
            if r["hit"]:
                return r["hit"], total
        return None, total

    futs = [pool.submit(scroll_chunk, t) for t in tasks]
    hit, total = consume(futs)
    return hit, total


@dataclass
class Anchor:
    name: str
    d: int
    priority: int


def p27_anchors(px: int, py: int) -> list[Anchor]:
    keys = parse_53125()
    pk27 = keys[27]
    gz_xd = f2s(pk27.px) - f2s(pk27.d)
    gz_yd = f2s(pk27.py) - f2s(pk27.d)
    fd_x = frac(f2s(px) - gz_xd)
    fd_y = frac(f2s(py) - gz_yd)
    out = [
        Anchor("p27_x_gz", d_from_band_frac(frac(2 * fd_x)), 0),
        Anchor("p27_y_gz", d_from_band_frac(frac(2 * fd_y)), 5),
    ]
    prefix = [k for n, k in keys.items() if n < 135 and k.d > 0]
    if prefix:
        gz_p = sum(f2s(k.px) - f2s(k.d) for k in prefix) / len(prefix)
        bf_p = frac(2 * frac(f2s(px) - gz_p))
        out.append(Anchor("p27_prefix_gz", d_from_band_frac(bf_p), 2))
    return out


def hinge_anchors() -> list[Anchor]:
    getcontext().prec = 80
    h = float(Decimal(PN).ln() / Decimal(2).ln())
    py = 46351506704828816385393879789131775975171267756561783641521771795450741674800
    lsy = float((Decimal(py).ln() / Decimal(2).ln()) / 2)
    dy = h - lsy
    bf_hinge = frac(lsy) - frac(dy)
    return [
        Anchor("hinge_frac", d_from_band_frac(bf_hinge), 3),
        Anchor("upper_half", d_from_band_frac(0.584963), 4),
    ]


def sqrt_shell_anchors(lo: int, hi: int) -> list[Anchor]:
    out: list[Anchor] = []
    for name, k in (
        ("sqrtN_x1e5", SQRT_N_INT * 100_000),
        ("sqrtN_int", SQRT_N_INT),
    ):
        d = clamp_band(k, lo, hi)
        if d is not None:
            out.append(Anchor(name, d, 6))
        d2 = clamp_band(lo + (k % lo), lo, hi)
        if d2 is not None:
            out.append(Anchor(f"{name}_lift", d2, 7))
    return out


def checkedkeys_anchors(lo: int, hi: int) -> list[Anchor]:
    if not CHECKED_KEYS.is_file():
        return []
    out: list[Anchor] = []
    pat = re.compile(r"\b(\d{35,})\b")
    seen: set[int] = set()
    for line in CHECKED_KEYS.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = pat.search(line)
        if not m:
            continue
        k = int(m.group(1))
        for d in (k, lo + (k % lo)):
            if lo <= d < hi and d not in seen:
                seen.add(d)
                out.append(Anchor(f"checked_{str(d)[-8:]}", d, 12))
    return out


def row0_hunt_anchors(lo: int, hi: int, limit: int = 20) -> list[Anchor]:
    if not ROW0_HUNT.is_file():
        return []
    out: list[Anchor] = []
    with ROW0_HUNT.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                d = int(row["d"])
            except (KeyError, ValueError):
                continue
            if lo <= d < hi:
                out.append(Anchor(f"row0", d, 14))
            if len(out) >= limit:
                break
    return out


def dedupe_anchors(anchors: list[Anchor]) -> list[Anchor]:
    best: dict[int, Anchor] = {}
    for a in anchors:
        cur = best.get(a.d)
        if cur is None or a.priority < cur.priority:
            best[a.d] = a
    return sorted(best.values(), key=lambda x: (x.priority, x.d))


def three_rail_anchors(px: int, py: int, n: int = 135) -> list[Anchor]:
    """P27 x-rail, frac(sqrt N) rail, {Delta_y} rail — displacement scroll only."""
    getcontext().prec = 120
    spn = Decimal(PN).sqrt()
    sn = Decimal(N).sqrt()
    frac_sn = sn - sn.to_integral_value(rounding="ROUND_FLOOR")

    h = float(Decimal(PN).ln() / Decimal(2).ln())
    ly = float((Decimal(py).sqrt().ln() / Decimal(2).ln()))
    fdy = (h - ly) - math.floor(h - ly)

    keys = parse_53125()
    pk27 = keys[27]
    gz_xd = f2s(pk27.px) - f2s(pk27.d)
    d_p27 = d_from_band_frac(frac(2 * frac(f2s(px) - gz_xd)))

    k_frac = n - 63  # P135 -> 72
    k_dy = n - 57  # P135 -> 78
    d_frac = int((frac_sn * spn * (Decimal(2) ** k_frac)).to_integral_value(rounding="ROUND_FLOOR"))
    d_dy = int((Decimal(str(fdy)) * spn * (Decimal(2) ** k_dy)).to_integral_value(rounding="ROUND_FLOOR"))

    return [
        Anchor(f"p27_x rail", d_p27, 0),
        Anchor(f"frac_sqrtN k={k_frac}", d_frac, 1),
        Anchor(f"Delta_y k={k_dy}", d_dy, 2),
    ]


def build_anchors(px: int, py: int, lo: int, hi: int) -> list[Anchor]:
    all_a: list[Anchor] = []
    all_a.extend(p27_anchors(px, py))
    all_a.extend(hinge_anchors())
    all_a.extend(sqrt_shell_anchors(lo, hi))
    all_a.extend(checkedkeys_anchors(lo, hi))
    all_a.extend(row0_hunt_anchors(lo, hi))
    return dedupe_anchors(all_a)


def load_target() -> tuple[int, int]:
    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn
    return px, py


def bench(steps: int = 100_000) -> None:
    px, py = load_target()
    lo, _, _ = puzzle_band(135)
    d0 = lo + 777_777
    t0 = time.perf_counter()
    scroll_forward(d0, steps, px, py)
    elapsed = time.perf_counter() - t0
    print(f"bench: {steps:,} scroll steps in {elapsed:.2f}s  ({steps/elapsed:,.0f}/s)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Fast Harvester endless scroll — Puzzle 135")
    ap.add_argument("--radius", type=int, default=1_000_000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--chunk", type=int, default=50_000, help="steps per worker chunk")
    ap.add_argument("--max-anchors", type=int, default=0)
    ap.add_argument("--priority-only", type=int, default=6)
    ap.add_argument("--three-rails", action="store_true", help="P27 + frac(sqrtN) + Delta_y only")
    ap.add_argument("--bench", action="store_true")
    args = ap.parse_args()

    if args.bench:
        bench()
        return 0

    px, py = load_target()
    lo, hi, _ = puzzle_band(135)
    if args.three_rails:
        anchors = three_rail_anchors(px, py, 135)
    else:
        anchors = build_anchors(px, py, lo, hi)
        if args.priority_only:
            anchors = [a for a in anchors if a.priority <= args.priority_only]
    if args.max_anchors:
        anchors = anchors[: args.max_anchors]

    lines = [
        "HARVESTER ENDLESS SCROLL (fast) — Puzzle 135",
        f"band [{lo}, {hi})  radius=+/-{args.radius:,}",
        f"workers={args.workers}  chunk={args.chunk:,}  anchors={len(anchors)}",
        "model: 1x scalar mult per chunk, then P+=G only",
        "",
    ]
    print("\n".join(lines[:5]), flush=True)

    total_checked = 0
    t0 = time.perf_counter()
    hit_d: int | None = None
    hit_name = ""

    workers = max(1, args.workers)
    if workers <= _MAX_POOL:
        print(f"spawning {workers} workers...", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for i, anc in enumerate(anchors, 1):
                t_a = time.perf_counter()
                d_hit, n = parallel_scroll(
                    anc.name, anc.d, args.radius, lo, hi, px, py, args.chunk, pool
                )
                dt = time.perf_counter() - t_a
                total_checked += n
                rate = n / dt if dt else 0
                status = f"HIT d={d_hit}" if d_hit else "none"
                line = (
                    f"[{i:3d}/{len(anchors)}] {anc.name:22s} d...{str(anc.d)[-10:]}  "
                    f"{n:,} pts in {dt:.1f}s ({rate:,.0f}/s)  {status}"
                )
                lines.append(line)
                print(line, flush=True)
                if d_hit:
                    hit_d = d_hit
                    hit_name = anc.name
                    break
    else:
        n_pools = (workers + _MAX_POOL - 1) // _MAX_POOL
        print(
            f"spawning {workers} workers across {n_pools} pool(s) (max {_MAX_POOL}/pool)...",
            flush=True,
        )
        with MultiExecutor(workers) as pool:
            for i, anc in enumerate(anchors, 1):
                t_a = time.perf_counter()
                d_hit, n = parallel_scroll(
                    anc.name, anc.d, args.radius, lo, hi, px, py, args.chunk, pool
                )
                dt = time.perf_counter() - t_a
                total_checked += n
                rate = n / dt if dt else 0
                status = f"HIT d={d_hit}" if d_hit else "none"
                line = (
                    f"[{i:3d}/{len(anchors)}] {anc.name:22s} d...{str(anc.d)[-10:]}  "
                    f"{n:,} pts in {dt:.1f}s ({rate:,.0f}/s)  {status}"
                )
                lines.append(line)
                print(line, flush=True)
                if d_hit:
                    hit_d = d_hit
                    hit_name = anc.name
                    break

    elapsed = time.perf_counter() - t0
    summary = (
        f"\ntotal={total_checked:,}  wall={elapsed:.1f}s  "
        f"avg={total_checked/elapsed:,.0f}/s  result={'SOLVED' if hit_d else 'not found'}"
    )
    lines.append(summary)
    print(summary, flush=True)

    if hit_d:
        save_hit(hit_d, source=f"harvester_endless_scroll:{hit_name}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if hit_d else 1


if __name__ == "__main__":
    raise SystemExit(main())
