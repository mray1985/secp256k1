#!/usr/bin/env python3
"""Bounded integer walk around P71-P74 digit-predict anchors, hash160 verify."""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import puzzle_band, pubkey_from_scalar  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

REPORT = ROOT / "ARCHIVE" / "p72_74_digit_scroll.txt"

TARGETS = {
    71: bytes.fromhex("bf7413e8df4e7a34ce9dc13e2f2648783ec54adb"),
    72: bytes.fromhex("105b7f253f0ebd7843adaebbd805c944bfb863e4"),
    73: bytes.fromhex("9f1adb20baeacc38b3f49f3df6906a0e48f2df3d"),
    74: bytes.fromhex("86f9fea5cdecf033161dd2f8f8560768ae0a6d14"),
}

PRED = {
    71: {"len": 22, "missing": "ALL"},
    72: {"len": 22, "missing": "8"},
    73: {"len": 22, "missing": "ALL"},
    74: {"len": 23, "missing": "5"},
}

BAND_FRAC = {71: 0.00, 72: 0.05, 73: 0.10, 74: 0.15}


def frac(d: int, n: int) -> float:
    lo, hi, _ = puzzle_band(n)
    return (d - lo) / (hi - lo)


def anchors_for(n: int) -> list[tuple[str, int]]:
    lo, hi, _ = puzzle_band(n)
    w = hi - lo
    keys = parse_53125()
    out: list[tuple[str, int]] = []

    bf = BAND_FRAC[n]
    out.append((f"frac_{bf:.2f}", lo + int(bf * (w - 1))))

    for off, name in [(42, "floor+42"), (49, "floor+49"), (76, "floor+76"), (21, "floor+21")]:
        out.append((name, lo + off))

    d75 = keys[75].d
    f_lin = ((n - 71) / 4.0) * frac(d75, 75)
    out.append((f"lin_{f_lin:.3f}", lo + int(f_lin * (w - 1))))

    f70 = frac(keys[70].d, 70)
    out.append((f"mirror_P70_{f70:.3f}", lo + int(f70 * (w - 1))))

    seen: set[int] = set()
    uniq: list[tuple[str, int]] = []
    for name, d in out:
        if lo <= d < hi and d not in seen:
            seen.add(d)
            uniq.append((name, d))
    return uniq


def digit_profile(d: int) -> tuple[int, str]:
    s = str(d)
    miss = "".join(c for c in "0123456789" if c not in s)
    return len(s), miss or "ALL"


def digit_ok(d: int, pred: dict, *, strict: bool) -> bool:
    ln, miss = digit_profile(d)
    if strict:
        if ln != pred["len"]:
            return False
    elif abs(ln - pred["len"]) > 1:
        return False
    want = pred["missing"]
    if want == "ALL":
        return miss == "ALL"
    return want in miss


def hash160_scalar(d: int) -> bytes:
    x, y = pubkey_from_scalar(d)
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    return hashlib.new("ripemd160", hashlib.sha256(pref + x.to_bytes(32, "big")).digest()).digest()


def walk_chunk(task: dict) -> dict:
    n = task["n"]
    anchor = task["anchor"]
    d_start = task["d_start"]
    d_end = task["d_end"]
    pred = task["pred"]
    h160_tgt = bytes(task["h160_tgt"])
    strict = task["strict"]

    checked = digit_pass = 0
    for d in range(d_start, d_end):
        checked += 1
        if not digit_ok(d, pred, strict=strict):
            continue
        digit_pass += 1
        try:
            if hash160_scalar(d) == h160_tgt:
                return {
                    "hit": d,
                    "n": n,
                    "anchor": anchor,
                    "checked": checked,
                    "digit_pass": digit_pass,
                }
        except Exception:
            continue

    return {"hit": None, "n": n, "anchor": anchor, "checked": checked, "digit_pass": digit_pass}


def build_tasks(n: int, radius: int, chunk: int, strict: bool) -> list[dict]:
    lo, hi, _ = puzzle_band(n)
    pred = PRED[n]
    h160 = TARGETS[n]
    tasks: list[dict] = []
    seen_ranges: set[tuple[int, int]] = set()

    for anchor_name, center in anchors_for(n):
        a = max(lo, center - radius)
        b = min(hi, center + radius + 1)
        for start in range(a, b, chunk):
            end = min(start + chunk, b)
            key = (start, end)
            if key in seen_ranges:
                continue
            seen_ranges.add(key)
            tasks.append(
                {
                    "n": n,
                    "anchor": anchor_name,
                    "d_start": start,
                    "d_end": end,
                    "pred": pred,
                    "h160_tgt": h160,
                    "strict": strict,
                }
            )

    if n == 71:
        sweep_end = min(lo + max(radius, 2_000_000), hi)
        for start in range(lo, sweep_end, chunk):
            end = min(start + chunk, sweep_end)
            key = (start, end)
            if key not in seen_ranges:
                seen_ranges.add(key)
                tasks.append(
                    {
                        "n": n,
                        "anchor": "floor_sweep",
                        "d_start": start,
                        "d_end": end,
                        "pred": pred,
                        "h160_tgt": h160,
                        "strict": strict,
                    }
                )
    return tasks


def run_puzzle(n: int, radius: int, chunk: int, workers: int, strict: bool) -> dict:
    tasks = build_tasks(n, radius, chunk, strict)
    total_checked = total_digit = 0
    hit = None
    t0 = time.time()

    if workers <= 1:
        for t in tasks:
            r = walk_chunk(t)
            total_checked += r["checked"]
            total_digit += r["digit_pass"]
            if r.get("hit") is not None:
                hit = r
                break
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futs = [pool.submit(walk_chunk, t) for t in tasks]
            for fut in as_completed(futs):
                r = fut.result()
                total_checked += r["checked"]
                total_digit += r["digit_pass"]
                if r.get("hit") is not None:
                    hit = r
                    pool.shutdown(wait=False, cancel_futures=True)
                    break

    return {
        "n": n,
        "hit": hit,
        "checked": total_checked,
        "digit_pass": total_digit,
        "elapsed": time.time() - t0,
        "tasks": len(tasks),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="P71-P74 digit-constrained anchor walk")
    ap.add_argument("--radius", type=int, default=1 << 21)
    ap.add_argument("--chunk", type=int, default=50_000)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--relaxed", action="store_true")
    ap.add_argument("--puzzle", type=int, nargs="*", default=[71, 72, 73, 74])
    args = ap.parse_args()

    strict = not args.relaxed
    lines = [
        "P71-P74 DIGIT-CONSTRAINED ANCHOR WALK",
        f"radius={args.radius} chunk={args.chunk} workers={args.workers} strict={strict}",
        "",
    ]
    any_hit = False
    grand_checked = grand_digit = 0.0

    for n in args.puzzle:
        lines.append(f"=== P{n} pred len={PRED[n]['len']} miss={PRED[n]['missing']} ===")
        for name, d in anchors_for(n):
            ln, miss = digit_profile(d)
            lines.append(f"  anchor {name}: d={d} len={ln} miss={miss}")
        lines.append("")

        res = run_puzzle(n, args.radius, args.chunk, args.workers, strict)
        grand_checked += res["checked"]
        grand_digit += res["digit_pass"]
        lines.append(
            f"  tasks={res['tasks']} checked={res['checked']} digit_pass={res['digit_pass']} "
            f"elapsed={res['elapsed']:.1f}s"
        )
        if res["hit"]:
            h = res["hit"]
            ln, miss = digit_profile(h["hit"])
            lines.append(f"  *** HIT P{n} d={h['hit']} len={ln} miss={miss} anchor={h['anchor']}")
            any_hit = True
        else:
            lines.append("  no hit")
        lines.append("")

    lines.append(f"TOTAL checked={int(grand_checked)} digit_pass={int(grand_digit)}")
    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {REPORT}")
    return 0 if any_hit else 1


if __name__ == "__main__":
    raise SystemExit(main())
