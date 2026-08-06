#!/usr/bin/env python3
"""
Scan precomputed baby_h160.bin for Puzzle 71 target (j=0 lane).

Each record: 20-byte hash160 + 5-byte big-endian r  (hash160 of (LO+r)*G).
Uses a cheap hash160 prefix gate, full 20-byte confirm, Base58 only on hit.

Exit codes:
  0 = target found
  1 = scan complete, no hit
  2 = error (missing file, bad size, etc.)
"""

from __future__ import annotations

import argparse
import mmap
import sys
import time
from pathlib import Path

from paths import BABY_DIR
from p71_common import (
    H160_RECORD,
    LO,
    TARGET_ADDR,
    TARGET_H160,
    TOP,
    save_p71_hit,
)


def load_meta(baby_dir: Path) -> dict[str, int]:
    meta: dict[str, int] = {}
    meta_path = baby_dir / "baby_meta.txt"
    if meta_path.exists():
        for line in meta_path.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                if k in ("M", "M_full", "start_r", "end_r", "h160_bytes"):
                    meta[k] = int(v)
    target_path = baby_dir / "TARGET.txt"
    if target_path.exists():
        for line in target_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("M=") and "M" not in meta:
                meta["M"] = int(line.split("=", 1)[1])
    return meta


def resolve_baby_path(baby_dir: Path) -> Path:
    path = baby_dir / "baby_h160.bin"
    if not path.exists():
        raise FileNotFoundError(f"missing baby table: {path}")
    return path


def scan_baby_table(
    baby_path: Path,
    *,
    m: int,
    start_r: int = 0,
    end_r: int = 0,
    prefix_len: int = 1,
    progress_every: int = 50_000_000,
    emit=print,
) -> tuple[int, int] | None:
    """
    Linear mmap scan of baby_h160.bin.
    Returns (r, d) on hit where d = LO + r.
    """
    if prefix_len < 1 or prefix_len > 20:
        raise ValueError("prefix_len must be in [1, 20]")
    pref = TARGET_H160[:prefix_len]
    size = baby_path.stat().st_size
    if size % H160_RECORD:
        raise ValueError(f"bad file size {size}: not multiple of {H160_RECORD}")
    total = size // H160_RECORD
    if total > m:
        emit(f"warning: file has {total:,} records > M={m:,}; scanning first {m:,}")
        total = m
    d_lo = LO + start_r
    d_hi = LO + (end_r - 1 if end_r else start_r + total - 1)

    emit(f"scan {baby_path}")
    emit(f"  records={total:,}  record_bytes={H160_RECORD}  prefix_len={prefix_len}")
    emit(f"  target_h160={TARGET_H160.hex()}")
    emit(f"  target_addr={TARGET_ADDR}")
    emit(f"  r in [{start_r:,}, {start_r + total:,})  d in [{d_lo}, {d_hi}]")
    emit("")

    t0 = time.perf_counter()
    checked = 0
    prefix_pass = 0

    with baby_path.open("rb") as fh:
        with mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            limit = total * H160_RECORD
            off = 0
            while off < limit:
                h = mm[off : off + 20]
                checked += 1
                if h[:prefix_len] == pref:
                    prefix_pass += 1
                    if h == TARGET_H160:
                        r_rel = int.from_bytes(mm[off + 20 : off + H160_RECORD], "big")
                        r = start_r + r_rel
                        d = LO + r
                        elapsed = time.perf_counter() - t0
                        rate = checked / elapsed if elapsed else 0.0
                        emit(
                            f"*** HIT *** r={r:,} d={d} "
                            f"checked={checked:,} prefix_pass={prefix_pass:,} "
                            f"elapsed={elapsed:.2f}s rate={rate:,.0f}/s"
                        )
                        return r, d
                off += H160_RECORD
                if progress_every and checked % progress_every == 0:
                    elapsed = time.perf_counter() - t0
                    rate = checked / elapsed if elapsed else 0.0
                    pct = 100.0 * checked / total
                    emit(
                        f"  progress {checked:,}/{total:,} ({pct:.1f}%)  "
                        f"{rate:,.0f}/s  prefix_pass={prefix_pass:,}"
                    )

    elapsed = time.perf_counter() - t0
    rate = checked / elapsed if elapsed else 0.0
    emit(
        f"NO HIT in baby table  checked={checked:,}  "
        f"prefix_pass={prefix_pass:,}  elapsed={elapsed:.2f}s  rate={rate:,.0f}/s"
    )
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan baby_h160.bin for Puzzle 71 target")
    ap.add_argument("--baby-dir", type=Path, default=BABY_DIR)
    ap.add_argument("--m", type=int, default=0, help="baby M (default: baby_meta / TARGET.txt)")
    ap.add_argument("--prefix-len", type=int, default=1, help="hash160 prefix bytes before full compare")
    ap.add_argument("--progress-every", type=int, default=50_000_000)
    ap.add_argument("--hit-path", type=Path, default=None, help="optional extra HIT.txt path")
    args = ap.parse_args()

    try:
        baby_path = resolve_baby_path(args.baby_dir)
        meta = load_meta(args.baby_dir)
        m = args.m or meta.get("M") or meta.get("end_r") or (baby_path.stat().st_size // H160_RECORD)
        start_r = meta.get("start_r", 0)
        end_r = meta.get("end_r", 0)
        result = scan_baby_table(
            baby_path,
            m=m,
            start_r=start_r,
            end_r=end_r,
            prefix_len=args.prefix_len,
            progress_every=args.progress_every,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        print("Build with build_baby_2p30.bat or build_baby_h160.py", file=sys.stderr, flush=True)
        return 2
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        return 2

    if result is None:
        return 1

    r, d = result
    if not (LO <= d <= TOP):
        print(f"ERROR: hit out of band d={d}", file=sys.stderr, flush=True)
        return 2

    hit_path = args.hit_path or (args.baby_dir.parent / "giant" / "HIT.txt")
    save_p71_hit(d, source="baby_h160_scan", j=0, r=r, m=m, hit_path=hit_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
