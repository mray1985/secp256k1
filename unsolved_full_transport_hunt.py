#!/usr/bin/env python3
"""
Full transport hunt — unsolved batch (P135–P160) or all puzzles 1–160.

Phases per puzzle:
  1. Bridge alignment + shelf2 terms (offset-bit law row 0)
  2. Sampled shelf2 +/- offset with N-gap fingerprint (head3, then head2)
  3. Exact N-gap + offset-bit filter
  4. Heaven-lift y_comp head3 match on phase-2/3 survivors

Law: px^3 + 4 == py^2 - 3  (mod p)
N-gap: (py^2 - 3) - (px^3 + 4) mod N
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    DEFAULT_RY,
    N,
    band_representative,
    build_alignment_candidates,
    build_bridge_offset_terms,
    compressed_slot_y2,
    delta,
    n_slot_y_compress_constant,
    p,
    puzzle_band,
    pubkey_from_scalar,
    resolve_true_r_xy,
    slot_compress_carry,
)
from genesis_calibration import bridge_state  # noqa: E402
from gap_tier_common import gap_interval, observed_offset, sample_offsets_in_interval  # noqa: E402
from p135_160_shelf2_offset_hunt import (  # noqa: E402
    ROW_DELTA,
    build_cfg,
    ec_hit,
    offset_bits_ok,
    predicted_offset_bits,
)
from puzzle_keys_53125 import parse_53125  # noqa: E402
from unsolved_batch import UNSOLVED_PUZZLES, offset_law_row  # noqa: E402

SKIP_PUZZLES: frozenset[int] = frozenset({52})
ALL_PUZZLES: tuple[int, ...] = tuple(n for n in range(1, 161) if n not in SKIP_PUZZLES)

LOG = ROOT / "ARCHIVE" / "cloud_pages" / "unsolved_full_transport_hunt.log"
CSV = ROOT / "ARCHIVE" / "unsolved_full_transport_hunt.csv"
REPORT = ROOT / "ARCHIVE" / "unsolved_full_transport_hunt_report.txt"
ANCHORS_CSV = ROOT / "ARCHIVE" / "full_transport_anchors.csv"


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def head_dec(value: int, digits: int) -> str:
    s = str(value)
    return s[:digits] if len(s) >= digits else s


def n_gap(px: int, py: int) -> int:
    return ((pow(py, 2, N) - 3) - (pow(px, 3, N) + 4)) % N


def heaven_ycomp(x: int, y: int) -> int | None:
    carry, ok = slot_compress_carry(y, x)
    if not ok:
        return None
    qx = (x * delta) % N
    return compressed_slot_y2(qx, n_slot_y_compress_constant(carry))


@dataclass
class PuzzleCtx:
    n: int
    cfg: object
    lo: int
    hi: int
    shelf2: int
    gap_bits: int
    law_row: int
    pred_bits: list[int]
    target_px: int
    target_py: int
    rx: int
    r_source: str
    anchor_gap: int
    anchor_lhs: int
    anchor_rhs: int
    anchor_ycomp: int | None
    lam_p: int
    st: dict = field(repr=False)


def build_ctx(n: int, keys: dict) -> PuzzleCtx:
    cfg = build_cfg(n, keys)
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(n)
    pk = keys.get(n)
    rx, _, src = resolve_true_r_xy(cfg)
    ry_b = DEFAULT_RY
    gap_val = st["gap"]
    gap_lo = gap_val % lo
    law_row = offset_law_row(n, cfg.row)
    carry, ok = slot_compress_carry(ry_b, rx)
    ycomp = compressed_slot_y2((rx * delta) % N, n_slot_y_compress_constant(carry)) if ok else None
    return PuzzleCtx(
        n=n,
        cfg=cfg,
        lo=lo,
        hi=hi,
        shelf2=st["oitc"].shelf2,
        gap_bits=gap_lo.bit_length(),
        law_row=law_row,
        pred_bits=sorted(predicted_offset_bits(n, law_row)),
        target_px=pk.px if pk else cfg.Px[cfg.row],
        target_py=pk.py if pk else cfg.Py,
        rx=rx,
        r_source=src,
        anchor_gap=n_gap(rx, ry_b),
        anchor_lhs=(pow(rx, 3, N) + 4) % N,
        anchor_rhs=(pow(ry_b, 2, N) - 3) % N,
        anchor_ycomp=ycomp,
        lam_p=(cfg.Px[cfg.row] * pow(cfg.rx[cfg.row], -1, p)) % p,
        st=st,
    )


def gap_ok(g: int, ctx: PuzzleCtx, head: int) -> bool:
    if head < 0:
        return True
    if head == 0:
        return g == ctx.anchor_gap
    return head_dec(g, head) == head_dec(ctx.anchor_gap, head)


def offset_ok(d: int, ctx: PuzzleCtx) -> bool:
    off = observed_offset(d, ctx.shelf2, ctx.lo)
    return offset_bits_ok(off, ctx.n, ctx.law_row, ctx.gap_bits)


def heaven_ok(x: int, y: int, ctx: PuzzleCtx, head: int) -> bool:
    if ctx.anchor_ycomp is None or head <= 0:
        return True
    yc = heaven_ycomp(x, y)
    if yc is None:
        return False
    return head_dec(yc, head) == head_dec(ctx.anchor_ycomp, head)


def record_hit(
    rows: list[dict],
    seen: set[int],
    ctx: PuzzleCtx,
    d: int,
    source: str,
    *,
    gap_head: int,
    heaven_head: int,
) -> bool:
    if not (ctx.lo <= d < ctx.hi):
        d2 = band_representative(d, ctx.lo, ctx.hi)
        if ctx.lo <= d2 < ctx.hi:
            d = d2
        else:
            return False
    if d in seen:
        return False
    seen.add(d)
    x, y = pubkey_from_scalar(d)
    g = n_gap(x, y)
    yc = heaven_ycomp(x, y)
    hit = ec_hit(d, ctx.target_px, ctx.target_py)
    if not hit:
        hit = ec_hit((N - d) % N, ctx.target_px, ctx.target_py)
    row = {
        "n": ctx.n,
        "d": d,
        "d_hex": format(d, "064x"),
        "source": source,
        "ec_hit": hit,
        "gap_head2": head_dec(g, 2),
        "gap_head3": head_dec(g, 3),
        "gap_exact": g == ctx.anchor_gap,
        "ycomp_head3": head_dec(yc, 3) if yc is not None else "",
        "px_tail": str(x)[-3:],
        "py_tail": str(y)[-3:],
    }
    rows.append(row)
    if hit:
        log(f"  *** EC HIT P{ctx.n} d={d} [{source}] ***")
    return hit


def try_candidate(
    rows: list[dict],
    seen: set[int],
    ctx: PuzzleCtx,
    d: int,
    source: str,
    *,
    require_offset: bool,
    gap_head: int,
    heaven_head: int,
) -> bool:
    if require_offset and not offset_ok(d, ctx):
        return False
    if not (ctx.lo <= d < ctx.hi):
        d2 = band_representative(d, ctx.lo, ctx.hi)
        if not (ctx.lo <= d2 < ctx.hi):
            return False
        d = d2
    if d in seen:
        return False
    x, y = pubkey_from_scalar(d)
    g = n_gap(x, y)
    if not gap_ok(g, ctx, gap_head):
        return False
    if not heaven_ok(x, y, ctx, heaven_head):
        return False
    return record_hit(rows, seen, ctx, d, source, gap_head=gap_head, heaven_head=heaven_head)


def phase_bridge(rows: list[dict], seen: set[int], ctx: PuzzleCtx) -> int:
    log(f"  phase 1: bridge alignment + shelf2 terms")
    hits = 0
    st = ctx.st
    n = ctx.n

    def try_d(name: str, d: int) -> None:
        nonlocal hits
        if try_candidate(
            rows, seen, ctx, d, f"bridge:{name}",
            require_offset=True, gap_head=-1, heaven_head=0,
        ):
            hits += 1

    for name, d, _raw in build_alignment_candidates(
        af=st["af"],
        oitc=st["oitc"],
        sim=st["sim"],
        lambda_ns=st["lambda_ns"],
        gap=st["gap"],
        lambda_p=ctx.lam_p,
        lambda_n_target=ctx.lam_p,
    ):
        try_d(name, d)

    for tname, off in build_bridge_offset_terms(
        oitc=st["oitc"],
        sim=st["sim"],
        lambda_ns=st["lambda_ns"],
        lo=ctx.lo,
        hi=ctx.hi,
        gap=st["gap"],
        lambda_p=ctx.lam_p,
        lambda_n_target=ctx.lam_p,
        calibrated_offset=None,
    ):
        if not offset_bits_ok(off, n, ctx.law_row, ctx.gap_bits):
            continue
        try_d(f"shelf2+{tname}", ctx.shelf2 + off)
        try_d(f"shelf2-{tname}", ctx.shelf2 - off)

    log(f"    bridge phase ec_hits={hits}")
    return hits


def phase_sample(
    rows: list[dict],
    seen: set[int],
    ctx: PuzzleCtx,
    *,
    samples: int,
    gap_head: int,
    heaven_head: int,
    label: str,
    max_keep: int,
) -> int:
    log(f"  {label}: samples={samples} gap_head={gap_head} heaven_head={heaven_head}")
    _, o_lo, o_hi = gap_interval(ctx.n, 1)
    tested = 0
    kept = 0
    hits = 0
    for off in sample_offsets_in_interval(o_lo, o_hi, samples):
        for sign in (+1, -1):
            d = ctx.shelf2 + sign * off
            if not (ctx.lo <= d < ctx.hi):
                continue
            tested += 1
            if try_candidate(
                rows, seen, ctx, d, label,
                require_offset=True,
                gap_head=gap_head,
                heaven_head=heaven_head,
            ):
                kept += 1
                if rows[-1]["ec_hit"]:
                    hits += 1
            if kept >= max_keep:
                break
        if kept >= max_keep:
            break
    log(f"    tested={tested} kept={kept} ec_hits={hits}")
    return hits


def hunt_puzzle(ctx: PuzzleCtx, args: argparse.Namespace) -> list[dict]:
    rows: list[dict] = []
    seen: set[int] = set()
    log(f"=== P{ctx.n} FULL TRANSPORT HUNT ===")
    log(f"  rx ...{str(ctx.rx)[-3:]} ({ctx.r_source})")
    log(f"  anchor gap head2={head_dec(ctx.anchor_gap,2)} head3={head_dec(ctx.anchor_gap,3)}")
    log(f"  lhs tail ...{str(ctx.anchor_lhs)[-3:]} rhs tail ...{str(ctx.anchor_rhs)[-3:]}")
    if ctx.anchor_ycomp is not None:
        log(f"  heaven ycomp head3={head_dec(ctx.anchor_ycomp,3)}")
    log(f"  shelf2 {ctx.shelf2.bit_length()}b  offset_bits {ctx.pred_bits} (+gap±1)")
    log("")

    phase_bridge(rows, seen, ctx)
    phase_sample(
        rows, seen, ctx,
        samples=args.samples,
        gap_head=3,
        heaven_head=3 if args.heaven else 0,
        label="phase2_head3",
        max_keep=args.max_keep,
    )
    phase_sample(
        rows, seen, ctx,
        samples=args.samples,
        gap_head=2,
        heaven_head=3 if args.heaven else 0,
        label="phase3_head2",
        max_keep=args.max_keep,
    )
    phase_sample(
        rows, seen, ctx,
        samples=args.samples,
        gap_head=0,
        heaven_head=0,
        label="phase4_exact_gap",
        max_keep=args.max_keep // 2,
    )
    log("")
    return rows


def write_report(
    all_rows: list[dict],
    contexts: list[PuzzleCtx],
    *,
    report_path: Path,
    title: str,
) -> None:
    lines = [title, ""]
    for ctx in contexts:
        sub = [r for r in all_rows if r["n"] == ctx.n]
        lines.append(f"P{ctx.n}")
        lines.append(f"  anchor gap head2={head_dec(ctx.anchor_gap,2)} head3={head_dec(ctx.anchor_gap,3)}")
        lines.append(f"  lhs ...{str(ctx.anchor_lhs)[-3:]}  rhs ...{str(ctx.anchor_rhs)[-3:]}")
        lines.append(f"  candidates={len(sub)} ec_hits={sum(1 for r in sub if r['ec_hit'])}")
        lines.append("")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_anchors_csv(contexts: list[PuzzleCtx], keys: dict, path: Path) -> None:
    rows = []
    for ctx in contexts:
        pk = keys.get(ctx.n)
        rows.append({
            "n": ctx.n,
            "solved": pk is not None and pk.d > 0,
            "gap_head2": head_dec(ctx.anchor_gap, 2),
            "gap_head3": head_dec(ctx.anchor_gap, 3),
            "lhs_tail": str(ctx.anchor_lhs)[-3:],
            "rhs_tail": str(ctx.anchor_rhs)[-3:],
            "rx_tail": str(ctx.rx)[-3:],
            "r_source": ctx.r_source,
            "offset_bits": ",".join(str(b) for b in ctx.pred_bits),
        })
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def parse_puzzle_list(spec: str, keys: dict) -> list[int]:
    spec = spec.strip().lower()
    if spec == "unsolved":
        return list(UNSOLVED_PUZZLES)
    if spec == "all":
        return list(ALL_PUZZLES)
    if spec == "solved":
        return [n for n in ALL_PUZZLES if n in keys and keys[n].d > 0]
    out: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return [n for n in sorted(set(out)) if n not in SKIP_PUZZLES]


def build_contexts(puzzles: list[int], keys: dict) -> list[PuzzleCtx]:
    contexts: list[PuzzleCtx] = []
    for n in puzzles:
        try:
            contexts.append(build_ctx(n, keys))
        except Exception as exc:
            log(f"SKIP P{n}: {exc}")
    return contexts


def main() -> int:
    ap = argparse.ArgumentParser(description="Full transport hunt (batch or all puzzles)")
    ap.add_argument(
        "--puzzles",
        default="unsolved",
        help="unsolved | all | solved | comma list or ranges (e.g. 1-80,135)",
    )
    ap.add_argument("--samples", type=int, default=200_000)
    ap.add_argument("--max-keep", type=int, default=40, help="max kept candidates per sampled phase")
    ap.add_argument("--heaven", action="store_true", default=True, help="require heaven ycomp head3 on sampled phases")
    ap.add_argument("--no-heaven", action="store_false", dest="heaven")
    ap.add_argument("--bridge-only", action="store_true", help="skip sampled gap phases (fast all-puzzle pass)")
    args = ap.parse_args()

    puzzles = parse_puzzle_list(args.puzzles, parse_53125())
    all_mode = args.puzzles.strip().lower() == "all"
    tag = "all" if all_mode else "unsolved"
    log_path = ROOT / "ARCHIVE" / "cloud_pages" / f"{tag}_full_transport_hunt.log"
    csv_path = ROOT / "ARCHIVE" / f"{tag}_full_transport_hunt.csv"
    report_path = ROOT / "ARCHIVE" / f"{tag}_full_transport_hunt_report.txt"
    anchors_path = ROOT / "ARCHIVE" / f"{tag}_full_transport_anchors.csv"

    global LOG, CSV, REPORT, ANCHORS_CSV
    LOG, CSV, REPORT, ANCHORS_CSV = log_path, csv_path, report_path, anchors_path

    LOG.write_text("", encoding="utf-8")
    keys = parse_53125()
    contexts = build_contexts(puzzles, keys)
    all_rows: list[dict] = []

    title = "ALL FULL TRANSPORT HUNT REPORT" if all_mode else "UNSOLVED FULL TRANSPORT HUNT REPORT"
    log(f"=== {title} ===")
    log(f"puzzles: {len(contexts)} of {len(puzzles)} requested")
    log(f"samples/sign: {args.samples}  heaven_head3: {args.heaven}  bridge_only: {args.bridge_only}")
    log("")

    write_anchors_csv(contexts, keys, ANCHORS_CSV)

    for ctx in contexts:
        if args.bridge_only:
            rows: list[dict] = []
            seen: set[int] = set()
            log(f"=== P{ctx.n} BRIDGE TRANSPORT ===")
            log(f"  rx ...{str(ctx.rx)[-3:]} ({ctx.r_source})")
            log(f"  anchor gap head2={head_dec(ctx.anchor_gap,2)} head3={head_dec(ctx.anchor_gap,3)}")
            log("")
            phase_bridge(rows, seen, ctx)
            log("")
            all_rows.extend(rows)
        else:
            all_rows.extend(hunt_puzzle(ctx, args))

    if all_rows:
        with CSV.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            w.writeheader()
            w.writerows(all_rows)

    write_report(all_rows, contexts, report_path=REPORT, title=title)

    log("=== SUMMARY ===")
    any_hit = False
    hit_puzzles: list[int] = []
    for ctx in contexts:
        sub = [r for r in all_rows if r["n"] == ctx.n]
        eh = sum(1 for r in sub if r["ec_hit"])
        if eh:
            any_hit = True
            hit_puzzles.append(ctx.n)
        if all_mode and len(contexts) > 20:
            if eh or len(sub) > 0:
                log(f"  P{ctx.n}: kept={len(sub)} ec_hits={eh}")
        else:
            log(f"  P{ctx.n}: kept={len(sub)} ec_hits={eh}")
    if hit_puzzles:
        log(f"EC hits: {hit_puzzles}")
    log(f"anchors -> {ANCHORS_CSV}")
    log(f"csv -> {CSV}")
    log(f"report -> {REPORT}")
    log(f"log -> {LOG}")
    return 0 if any_hit else 1


if __name__ == "__main__":
    raise SystemExit(main())
