#!/usr/bin/env python3
"""
Hierarchical cloud page scroll for Puzzle 135.

Page grid at keys-per-page K:
  page_index = (d - LO) // K
  slot       = page / K  with page ≈ d/60
  CF: q1_real / (8.831469 * K/1000) ≈ slot

Cloud mode emits JSONL work units (one page slice per line) for parallel workers.
Local mode ranks seeds, scrolls priority mega-pages, EC-gates d and N-d mirrors.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

try:
    from ecdsa import SECP256k1

    G = SECP256k1.generator
    _HAS_ECDSA = True
except ImportError:
    G = None
    _HAS_ECDSA = False

N_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LO = 1 << 134
TOP = (1 << 135) - 1
BAND_WIDTH = TOP - LO + 1

PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800

# Hurwitz closed form (N mod 360 = 97)
LN_SEC = math.log(8.205509048125085)
C_RD = LN_SEC / (LN_SEC * LN_SEC + math.pi * math.pi)
CF_PER_1K = 8.831469143725139


@dataclass
class PageLevel:
    name: str
    keys_per_page: int

    @property
    def num_pages(self) -> int:
        return (BAND_WIDTH + self.keys_per_page - 1) // self.keys_per_page

    @property
    def cf_multiplier(self) -> float:
        return CF_PER_1K * (self.keys_per_page / 1000.0)

    def page_index(self, d: int) -> int:
        if d < LO or d > TOP:
            return -1
        return (d - LO) // self.keys_per_page

    def d_range_for_page(self, page_index: int) -> tuple[int, int]:
        d_lo = LO + page_index * self.keys_per_page
        d_hi = min(TOP, d_lo + self.keys_per_page - 1)
        return d_lo, d_hi


MEGA = PageLevel("mega", 10**39)
MID = PageLevel("mid", 10**18)
FINE = PageLevel("fine", 10**3)


def q1_real_from_d(d: int) -> int:
    return int(round(d * C_RD))


def cf_score(d: int, k: int = 1000) -> float:
    """Lower is better: |predicted slot - page/k| relative to page."""
    if not (LO <= d <= TOP):
        return float("inf")
    page_est = d / 60.0
    slot_est = page_est / k
    q1 = q1_real_from_d(d)
    mult = CF_PER_1K * (k / 1000.0)
    slot_cf = q1 / mult
    if slot_est == 0:
        return float("inf")
    return abs(slot_cf - slot_est) / slot_est


def ec_hit(d: int) -> bool:
    if not _HAS_ECDSA:
        return False
    pt = d * G
    return pt.x() == PX and pt.y() == PY


def load_hex_candidates(path: Path) -> list[int]:
    out: list[int] = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("02"):
            continue
        try:
            d = int(line, 16)
        except ValueError:
            continue
        if LO <= d <= TOP:
            out.append(d)
    return out


def load_shelf2_anchor() -> int:
    try:
        from p135_carry_remainder_report import build_p135_bridge

        return build_p135_bridge(puzzle_row=2)["shelf2"] % LO
    except Exception:
        return 12_399_803_124_245_147_579_303_535_673_221_407_674_145


@dataclass
class WorkUnit:
    level: str
    keys_per_page: int
    page_index: int
    d_lo: int
    d_hi: int
    delta_start: int
    delta_end: int
    stride: int
    seed_label: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))


def emit_cloud_shards(
    out_dir: Path,
    level: PageLevel,
    stride: int,
    batch_deltas: int,
    anchor: int,
    priority_pages: list[int] | None,
) -> int:
    """Write JSONL shards for cloud workers."""
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / f"shards_{level.name}_K{level.keys_per_page}.jsonl"
    pages = priority_pages if priority_pages else list(range(level.num_pages))
    count = 0
    with manifest.open("w", encoding="utf-8") as f:
        for pg in pages:
            d_lo, d_hi = level.d_range_for_page(pg)
            # scroll around anchor projected into this page band
            t_anchor = anchor % LO
            d_anchor = LO + t_anchor
            if d_anchor < d_lo or d_anchor > d_hi:
                center_delta = 0
            else:
                center_delta = d_anchor - d_lo
            half = batch_deltas // 2
            for base in range(-half, half + 1, batch_deltas):
                ds = max(0, center_delta + base - half)
                de = min(d_hi - d_lo, center_delta + base + half)
                if ds > de:
                    continue
                wu = WorkUnit(
                    level=level.name,
                    keys_per_page=level.keys_per_page,
                    page_index=pg,
                    d_lo=d_lo,
                    d_hi=d_hi,
                    delta_start=ds,
                    delta_end=de,
                    stride=stride,
                    seed_label=f"anchor+{base}",
                )
                f.write(wu.to_json() + "\n")
                count += 1
    meta = {
        "puzzle": 135,
        "level": level.name,
        "keys_per_page": level.keys_per_page,
        "num_pages": level.num_pages,
        "cf_multiplier": level.cf_multiplier,
        "shard_count": count,
        "band": {"lo": LO, "top": TOP},
        "target": {"Px": PX, "Py": PY},
    }
    (out_dir / f"manifest_{level.name}.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    return count


def run_shard(wu: WorkUnit) -> dict:
    tested = 0
    t0 = time.perf_counter()
    d_lo = wu.d_lo
    for delta in range(wu.delta_start, wu.delta_end + 1, wu.stride):
        d = d_lo + delta
        if d > wu.d_hi:
            break
        for cand in (d, N_ORDER - d):
            if not (LO <= cand <= TOP):
                continue
            tested += 1
            if ec_hit(cand):
                return {
                    "hit": True,
                    "d": cand,
                    "page_index": wu.page_index,
                    "tested": tested,
                    "elapsed_s": time.perf_counter() - t0,
                }
    return {
        "hit": False,
        "tested": tested,
        "elapsed_s": time.perf_counter() - t0,
        "page_index": wu.page_index,
    }


def page_histogram(candidates: list[int], level: PageLevel) -> dict[int, int]:
    hist: dict[int, int] = {}
    for d in candidates:
        p = level.page_index(d)
        if p >= 0:
            hist[p] = hist.get(p, 0) + 1
    return hist


def main() -> None:
    ap = argparse.ArgumentParser(description="P135 hierarchical cloud page scroll")
    ap.add_argument(
        "--mode",
        choices=("report", "cloud", "run-local", "run-shard-file"),
        default="run-local",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "ARCHIVE" / "cloud_pages",
    )
    ap.add_argument("--level", choices=("mega", "mid", "fine"), default="mega")
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--batch-deltas", type=int, default=10_000)
    ap.add_argument("--max-shards-run", type=int, default=5)
    ap.add_argument("--all-pages", action="store_true", help="emit every page index at this level")
    ap.add_argument("--shard-file", type=Path, default=None)
    ap.add_argument(
        "--kanga",
        type=Path,
        default=ROOT / "135kanga_2p65_candidates.txt",
    )
    args = ap.parse_args()

    level = {"mega": MEGA, "mid": MID, "fine": FINE}[args.level]
    anchor = load_shelf2_anchor()

    lines: list[str] = [
        "P135 CLOUD PAGE SCROLL",
        f"  band width 2^134 keys ~ {BAND_WIDTH:.6e}",
        f"  ECDSA available: {_HAS_ECDSA}",
        "",
        "=== Page levels ===",
    ]
    for lv in (MEGA, MID, FINE):
        lines.append(
            f"  {lv.name:5s} K={lv.keys_per_page:.6e}  pages={lv.num_pages}  "
            f"cf_mult={lv.cf_multiplier:.6e}"
        )
    lines.append("")
    lines.append(f"  shelf2 anchor (mod LO) = {anchor}")

    kanga = load_hex_candidates(args.kanga)
    hist = page_histogram(kanga, MEGA)
    priority = sorted(hist.keys(), key=lambda p: hist[p], reverse=True)
    page_list: list[int] | None
    if args.all_pages or args.mode == "report":
        page_list = list(range(MEGA.num_pages))
    elif priority:
        page_list = priority
    else:
        page_list = None
    lines.append(f"  kanga in-band: {len(kanga)}  mega-page buckets: {len(hist)}")
    if priority:
        lines.append("  top mega-pages by kanga density:")
        for p in priority[:8]:
            d0, d1 = MEGA.d_range_for_page(p)
            lines.append(f"    page {p:3d}: count={hist[p]}  d=[{d0}, {d1}]")

    # CF rank top kanga
    ranked = sorted(((cf_score(d), d) for d in kanga), key=lambda x: x[0])
    lines.append("")
    lines.append("=== Top 10 kanga by CF score (K=1000 ref) ===")
    for score, d in ranked[:10]:
        pg = MEGA.page_index(d)
        lines.append(
            f"  cf={score:.6e}  d={d}  mega_page={pg}  q1~{q1_real_from_d(d)}  ec={ec_hit(d)}"
        )

    report_path = args.out_dir / "page_scroll_report.txt"
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "report":
        text = "\n".join(lines) + "\n"
        report_path.write_text(text, encoding="utf-8")
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
        print(f"\nwrote {report_path}", flush=True)
        return

    if args.mode == "cloud":
        n = emit_cloud_shards(
            args.out_dir,
            level,
            args.stride,
            args.batch_deltas,
            anchor,
            page_list,
        )
        lines.append(f"  emitted {n} shards for level={level.name} -> {args.out_dir}")
        text = "\n".join(lines) + "\n"
        report_path.write_text(text, encoding="utf-8")
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
        print(f"\ncloud shards: {args.out_dir / f'shards_{level.name}_K{level.keys_per_page}.jsonl'}", flush=True)
        return

    shard_path = args.shard_file
    if args.mode == "run-local":
        emit_cloud_shards(
            args.out_dir,
            level,
            args.stride,
            args.batch_deltas,
            anchor,
            page_list[:22] if page_list else None,
        )
        shard_path = args.out_dir / f"shards_{level.name}_K{level.keys_per_page}.jsonl"

    if not shard_path or not shard_path.exists():
        print("no shard file", file=sys.stderr)
        sys.exit(1)

    lines.append("")
    lines.append(f"=== Running up to {args.max_shards_run} shards from {shard_path.name} ===")
    hits: list[dict] = []
    total_tested = 0
    t0 = time.perf_counter()
    with shard_path.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= args.max_shards_run:
                break
            wu = WorkUnit(**json.loads(line))
            res = run_shard(wu)
            total_tested += res["tested"]
            rate = total_tested / max(time.perf_counter() - t0, 1e-9)
            lines.append(
                f"  shard {i+1} page={res['page_index']} tested={res['tested']} "
                f"hit={res.get('hit', False)} elapsed={res['elapsed_s']:.2f}s"
            )
            if res.get("hit"):
                hits.append(res)
                lines.append(f"  *** EC HIT d={res['d']} ***")
                break

    elapsed = time.perf_counter() - t0
    lines.append("")
    lines.append(f"  total tested={total_tested}  elapsed={elapsed:.2f}s  rate={total_tested/elapsed:.0f} d/s")
    lines.append(f"  EC hits={len(hits)}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    text = "\n".join(lines) + "\n"
    sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
    print(f"\nwrote {report_path}", flush=True)


if __name__ == "__main__":
    main()
