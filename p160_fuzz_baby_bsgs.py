#!/usr/bin/env python3
"""
P160 pubkey-rooted fuzz baby table (BSGS-style file) + target Px lookup.

Structure from RSZ pubkey (Px, Py scalar axes):
  axis + k                    — mandatory pubkey ±k
  (axis ± 2^n) + k            — n = 1 .. 158

Build sorted pub_x table once; lookup = binary search + y-verify. One hit = solution.
"""

from __future__ import annotations

import argparse
import heapq
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from p160_pubkey_ladder import (  # noqa: E402
    fuzz_for_target,
    grid_width,
    load_pubkey_target,
    per_axis_count,
)

# secp256k1
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G = (Gx, Gy)

RECORD = 52  # 32-byte pub_x + 20-byte full d (160-bit band)
CHUNK_RECORDS = 4_000_000  # ~208 MB sort chunks
MEMORY_LIMIT = 25_000_000  # in-RAM build if total points below this


def inv_mod(a: int, m: int) -> int:
    return pow(a % m, -1, m)


def point_add(p1: tuple[int, int] | None, p2: tuple[int, int] | None) -> tuple[int, int] | None:
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if p1 == p2:
        lam = (3 * x1 * x1) * inv_mod(2 * y1, P) % P
    else:
        lam = (y2 - y1) * inv_mod(x2 - x1, P) % P
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return (x3, y3)


def scalar_mult(k: int, point: tuple[int, int] = G) -> tuple[int, int] | None:
    k %= N
    result = None
    addend: tuple[int, int] | None = point
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result


def neg(p: tuple[int, int]) -> tuple[int, int]:
    x, y = p
    return (x, (-y) % P)


NEG_G = neg(G)


def in_band(d: int, lo: int, hi: int) -> bool:
    return lo <= d < hi


def lift(d: int, lo: int, hi: int) -> int:
    from ecdlp_full_pipeline import band_representative  # noqa: WPS433

    return band_representative(d, lo, hi)


def pack_record(x: int, d: int) -> bytes:
    return x.to_bytes(32, "big") + d.to_bytes(20, "big")


def unpack_record(rec: bytes) -> tuple[int, int]:
    return int.from_bytes(rec[:32], "big"), int.from_bytes(rec[32:], "big")


def axis_path(out_dir: Path, aname: str, fuzz: int, max_pow: int) -> Path:
    return out_dir / f"baby_pubkey_{aname}_f{fuzz}_p{max_pow}.bin"


def walk_fuzz_from_point(
    base_d: int,
    base_pt: tuple[int, int],
    lo: int,
    hi: int,
    fuzz: int,
    n: int,
    sign: int,
    axis: int,
    dedup: bool,
):
    seen: set[int] | None = set() if dedup else None

    def emit(d: int, pt: tuple[int, int]):
        if seen is not None:
            if d in seen:
                return
            seen.add(d)
        yield pt[0], pt[1], d, n, sign, axis

    d0 = base_d if in_band(base_d, lo, hi) else lift(base_d, lo, hi)
    yield from emit(d0, base_pt)

    pt_fwd = base_pt
    for k in range(1, fuzz + 1):
        nxt = point_add(pt_fwd, G)
        if nxt:
            pt_fwd = nxt
            d = base_d + k
            d = d if in_band(d, lo, hi) else lift(d, lo, hi)
            yield from emit(d, pt_fwd)

    pt_back = base_pt
    for k in range(1, fuzz + 1):
        nxt = point_add(pt_back, NEG_G)
        if nxt:
            pt_back = nxt
            d = base_d - k
            d = d if in_band(d, lo, hi) else lift(d, lo, hi)
            yield from emit(d, pt_back)


def walk_pubkey_ladder(
    anchor: int,
    axis: int,
    lo: int,
    hi: int,
    fuzz: int,
    max_pow: int,
    dedup: bool = False,
):
    base_pt = scalar_mult(anchor % N)
    if base_pt is None:
        return
    yield from walk_fuzz_from_point(anchor, base_pt, lo, hi, fuzz, 0, 0, axis, dedup)

    for n in range(1, max_pow + 1):
        step = 1 << n
        for sign, base_d in ((+1, anchor + step), (-1, anchor - step)):
            pt = scalar_mult(base_d % N)
            if pt:
                yield from walk_fuzz_from_point(base_d, pt, lo, hi, fuzz, n, sign, axis, dedup)


def print_plan(fuzz: int, max_pow: int, axes: list[tuple[str, int]], target_points: int | None) -> None:
    per = per_axis_count(fuzz, max_pow)
    total = per * len(axes)
    gb = total * RECORD / 1e9
    print("P160 PUBKEY LADDER BABY TABLE")
    print(f"  axes: {[n for n, _ in axes]}")
    print(f"  ladder: pubkey ±k, pubkey ± 2^n ±k  (n=1..{max_pow})")
    print(f"  fuzz=±{fuzz:,}  bases/axis={grid_width(max_pow)}")
    print(f"  est_points={total:,}  (~{gb:.1f} GB .bin)")
    if target_points is not None:
        print(f"  target_budget={target_points:,}")


def external_sort(in_path: Path, out_path: Path) -> None:
    chunks: list[Path] = []
    with in_path.open("rb") as src:
        idx = 0
        while True:
            buf = src.read(CHUNK_RECORDS * RECORD)
            if not buf:
                break
            rows = [buf[i : i + RECORD] for i in range(0, len(buf), RECORD)]
            rows.sort(key=lambda r: int.from_bytes(r[:32], "big"))
            chunk = in_path.with_suffix(f".chunk{idx:05d}.bin")
            with chunk.open("wb") as cf:
                cf.write(b"".join(rows))
            chunks.append(chunk)
            idx += 1
            print(f"  sorted chunk {idx:,} ({len(rows):,} records)", flush=True)
    in_path.unlink(missing_ok=True)

    with out_path.open("wb") as out:
        handles = [c.open("rb") for c in chunks]
        heap: list[tuple[int, int, bytes]] = []
        for i, hf in enumerate(handles):
            rec = hf.read(RECORD)
            if rec:
                heapq.heappush(heap, (int.from_bytes(rec[:32], "big"), i, rec))
        while heap:
            _x, i, rec = heapq.heappop(heap)
            out.write(rec)
            nxt = handles[i].read(RECORD)
            if nxt:
                heapq.heappush(heap, (int.from_bytes(nxt[:32], "big"), i, nxt))
        for hf in handles:
            hf.close()
    for c in chunks:
        c.unlink(missing_ok=True)


def build_axis_streaming(
    aname: str,
    anchor: int,
    ai: int,
    out_path: Path,
    lo: int,
    hi: int,
    fuzz: int,
    max_pow: int,
) -> int:
    unsorted = out_path.with_suffix(".unsorted.bin")
    count = 0
    with unsorted.open("wb") as f:
        for x, _y, d, _n, _sign, _axis in walk_pubkey_ladder(
            anchor, ai, lo, hi, fuzz, max_pow, dedup=False
        ):
            f.write(pack_record(x, d))
            count += 1
            if count % 5_000_000 == 0:
                print(f"  {aname}: {count:,} written", flush=True)
    print(f"  {aname}: external sort {count:,} records", flush=True)
    external_sort(unsorted, out_path)
    return count


def build_axis_memory(
    aname: str,
    anchor: int,
    ai: int,
    out_path: Path,
    lo: int,
    hi: int,
    fuzz: int,
    max_pow: int,
) -> int:
    records: list[tuple[int, int]] = []
    for x, _y, d, _n, _sign, _axis in walk_pubkey_ladder(
        anchor, ai, lo, hi, fuzz, max_pow, dedup=True
    ):
        records.append((x, d))
    records.sort(key=lambda t: t[0])
    with out_path.open("wb") as f:
        for x, d in records:
            f.write(pack_record(x, d))
    return len(records)


def build_baby(out_dir: Path, fuzz: int, max_pow: int) -> int:
    lo, hi, row, target_x, target_y, axes = load_pubkey_target()
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    est = per_axis_count(fuzz, max_pow) * len(axes)
    streaming = est > MEMORY_LIMIT

    print_plan(fuzz, max_pow, axes, None)
    print(f"target Px row{row}: {target_x}", flush=True)
    print(f"mode={'stream' if streaming else 'memory'}", flush=True)

    total = 0
    meta_lines = [
        f"# P160 pubkey ladder baby fuzz={fuzz} max_pow={max_pow}",
        f"# structure: pubkey_axis + k, (axis ± 2^n) + k, n=1..{max_pow}",
        f"# target_x={target_x}",
        f"# record_bytes={RECORD}",
    ]
    for ai, (aname, anchor) in enumerate(axes):
        print(f"build pubkey axis {aname} ...", flush=True)
        path = axis_path(out_dir, aname, fuzz, max_pow)
        if streaming:
            n = build_axis_streaming(aname, anchor, ai, path, lo, hi, fuzz, max_pow)
        else:
            n = build_axis_memory(aname, anchor, ai, path, lo, hi, fuzz, max_pow)
        total += n
        gb = path.stat().st_size / 1e9
        print(f"  {aname}: {n:,} points -> {path.name} ({gb:.2f} GB)", flush=True)
        meta_lines.append(f"# {aname}={path.name} records={n}")

    meta = out_dir / f"baby_pubkey_f{fuzz}_p{max_pow}.meta"
    meta.write_text("\n".join(meta_lines) + f"\n# total_records={total}\n", encoding="utf-8")
    elapsed = time.time() - t0
    print(f"done {total:,} records in {elapsed:.1f}s")
    print(f"wrote {meta}")
    return total


def lookup_axis(f, target_x: int, target_y: int, n: int) -> int | None:
    lo_i, hi_i = 0, n - 1
    while lo_i <= hi_i:
        mid = (lo_i + hi_i) // 2
        f.seek(mid * RECORD)
        rec = f.read(RECORD)
        x, d = unpack_record(rec)
        if x < target_x:
            lo_i = mid + 1
        elif x > target_x:
            hi_i = mid - 1
        else:
            from ecdlp_full_pipeline import pubkey_from_scalar  # noqa: WPS433

            pub_x, pub_y = pubkey_from_scalar(d)
            if pub_x == target_x and pub_y == target_y:
                return d
            for j in range(mid - 1, -1, -1):
                f.seek(j * RECORD)
                x2, d2 = unpack_record(f.read(RECORD))
                if x2 != target_x:
                    break
                pub_x, pub_y = pubkey_from_scalar(d2)
                if pub_x == target_x and pub_y == target_y:
                    return d2
            for j in range(mid + 1, n):
                f.seek(j * RECORD)
                x2, d2 = unpack_record(f.read(RECORD))
                if x2 != target_x:
                    break
                pub_x, pub_y = pubkey_from_scalar(d2)
                if pub_x == target_x and pub_y == target_y:
                    return d2
            return None
    return None


def lookup(out_dir: Path, fuzz: int, max_pow: int) -> int:
    _lo, _hi, row, target_x, target_y, axes = load_pubkey_target()

    print(f"lookup pubkey ladder for Px row{row} = {target_x}")
    for aname, _ in axes:
        path = axis_path(out_dir, aname, fuzz, max_pow)
        if not path.exists():
            print(f"  missing {path.name}")
            continue
        n = path.stat().st_size // RECORD
        print(f"  search {path.name} ({n:,} records)", flush=True)
        with path.open("rb") as f:
            d = lookup_axis(f, target_x, target_y, n)
        if d is not None:
            print("*** SOLUTION ***")
            print(f"axis={aname}")
            print(f"d={d}")
            print(f"hex={hex(d)}")
            return 0

    print("NO Px match in pubkey ladder baby table")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="P160 pubkey ladder baby table (BSGS-style)")
    ap.add_argument("--fuzz", type=int, default=None, help="half-width k fuzz (default from --target-points)")
    ap.add_argument("--target-points", type=int, default=9_500_000_000, help="total point budget (default 9.5B)")
    ap.add_argument("--max-pow", type=int, default=158)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "puzzle160_keyhunt_bsgs" / "fuzz_baby")
    ap.add_argument("--estimate", action="store_true", help="print grid plan only")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--lookup", action="store_true")
    args = ap.parse_args()

    _lo, _hi, _row, _tx, _ty, axes = load_pubkey_target()
    fuzz = args.fuzz
    if fuzz is None:
        fuzz = fuzz_for_target(int(args.target_points), len(axes), args.max_pow)

    if args.estimate:
        print_plan(fuzz, args.max_pow, axes, args.target_points)
        return 0

    out_dir = args.out_dir

    if args.build or not any(
        axis_path(out_dir, n, fuzz, args.max_pow).exists() for n, _ in axes
    ):
        build_baby(out_dir, fuzz, args.max_pow)
    if args.lookup or not args.build:
        return lookup(out_dir, fuzz, args.max_pow)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
