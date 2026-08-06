#!/usr/bin/env python3
"""
P160 two-level pubkey scroll from P — even-y (02 compressed) only.

Level 1: from each anchor scalar near P, walk until --even-quota even-y pubkeys
         per direction (+G, -G, optional endo / x2 stride lanes).
Level 2: from each L1 terminal even-y point, same quota in sub-directions.

Target P160 is 02 (even y); odd-y steps are skipped for hit checks and quota counting.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from p135_common import G, N, P, point_add, point_neg, scalar_mult  # noqa: E402
from scroll_g_table import fill_scroll_window, init_scroll_table  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "p160_billion_even_scroll.txt"
LIVE_LOG = ARCHIVE / "p160_billion_even_scroll_live.log"
CHECKPOINT_DIR = ARCHIVE / "p160_billion_even_checkpoints"
PROGRESS_FILE = CHECKPOINT_DIR / "progress.json"

BETA = 0x7AE96A2B657C07106E64479EAC3434F99CF0497512F58995C1396C28719501EE
PSI_G = (BETA * G[0] % P, G[1])
NEG_G = point_neg(G)
NEG_PSI_G = point_neg(PSI_G)

P160_PUB = (
    ROOT / "puzzle160_keyhunt_bsgs" / "P160_compressed.pub"
).read_text(encoding="ascii").strip().splitlines()[0].strip()


@dataclass(frozen=True)
class Target:
    px: int
    py: int
    prefix: str

    @classmethod
    def load(cls) -> Target:
        if not P160_PUB.startswith("02"):
            raise SystemExit(f"P160 must be 02 compressed, got {P160_PUB[:2]}")
        px = int(P160_PUB[2:], 16)
        yp, yn = y_roots(px)
        py = yp if yp % 2 == 0 else yn
        if py % 2 != 0:
            raise SystemExit("P160 y parity mismatch — not even")
        return cls(px=px, py=py, prefix="02")

    def hit(self, x: int, y: int) -> bool:
        return y % 2 == 0 and x == self.px and y == self.py


def compressed02(x: int, y: int) -> str:
    if y % 2 != 0:
        raise ValueError("not even y — cannot encode as 02")
    return "02" + format(x, "064x")


def h160_anchor() -> int:
    import hashlib

    tgt = Target.load()
    comp = bytes.fromhex(compressed02(tgt.px, tgt.py))
    h = int.from_bytes(
        hashlib.new("ripemd160", hashlib.sha256(comp).digest()).digest(),
        "big",
    )
    lo, _, _ = puzzle_band(160)
    return lo + (h - lo)  # h160 in band coordinates


def default_anchors() -> list[tuple[str, int]]:
    lo, hi, _ = puzzle_band(160)
    mid = (lo + hi) // 2
    prior = int(lo * 1.5)
    return [
        ("h160", h160_anchor()),
        ("mid", mid),
        ("prior_1p5x", prior),
        ("lo", lo),
    ]


def scroll_even_chunk(task: dict) -> dict:
    """Worker: table scroll; count/check only even-y (02) points."""
    init_scroll_table(max(task.get("table_size", task["steps"]), task["steps"]))
    tgt = Target.load()
    d0 = task["d0"]
    steps = task["steps"]
    forward = task["mode"] == "fwd"
    lane = task.get("lane", "g")
    spawn_stride = task.get("spawn_stride", 0)
    spawn_path = task.get("spawn_path")

    p0 = scalar_mult(d0, G)
    if p0 is None:
        return _result(task, hit=None, even=0, steps=0, end_d=d0, spawns=0)

    checked = 0
    even = 0
    spawns = 0
    hit = None
    x, y = p0
    if y % 2 == 0:
        even += 1
        checked += 1
        if spawn_path and spawn_stride <= 1:
            _append_spawn(spawn_path, d0)
            spawns += 1
        if tgt.hit(x, y):
            return _result(task, hit=d0, even=even, steps=checked, end_d=d0, spawns=spawns)

    if lane == "g":
        ds, xs, ys, sign = fill_scroll_window(d0, steps, forward=forward)
        step_vec = 1
    elif lane == "psi":
        ds, xs, ys, sign = _fill_psi_window(d0, steps, forward=forward)
        step_vec = 1
    elif lane == "x2":
        ds, xs, ys, sign = fill_scroll_window(d0, steps * 2, forward=forward)
        step_vec = 2
    else:
        raise ValueError(lane)

    for d_raw, x, y in zip(ds, xs, ys):
        if lane == "x2" and (d_raw - d0) % 2 != 0:
            continue
        checked += 1
        if y & 1:
            continue
        even += 1
        if spawn_path and spawn_stride <= 1:
            _append_spawn(spawn_path, d_raw)
            spawns += 1
        elif spawn_path and spawn_stride > 1 and even % spawn_stride == 0:
            _append_spawn(spawn_path, d_raw)
            spawns += 1
        if tgt.hit(x, y):
            hit = d_raw
            break

    end_d = d0 + sign * steps * step_vec if ds else d0
    if ds:
        end_d = ds[-1]
    return _result(task, hit=hit, even=even, steps=checked, end_d=end_d, spawns=spawns)


def _append_spawn(path: str, d: int) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="ascii") as f:
        f.write(f"{d}\n")


def _fill_psi_window(d_start: int, steps: int, *, forward: bool = True):
    """P0 = d_start*G, then add +/- i*psi(G). Scalar offset is approximate lane tag."""
    if steps <= 0:
        return [], [], [], 1 if forward else -1
    p0 = scalar_mult(d_start, G)
    if p0 is None:
        return [], [], [], 1 if forward else -1
    off = PSI_G if forward else NEG_PSI_G
    sign = 1 if forward else -1
    ds, xs, ys = [], [], []
    pt = p0
    for i in range(1, steps + 1):
        pt = point_add(pt, off)
        if pt is None:
            continue
        ds.append(d_start + sign * i)
        xs.append(pt[0])
        ys.append(pt[1])
    return ds, xs, ys, sign


def _result(task: dict, *, hit, even: int, steps: int, end_d: int, spawns: int = 0) -> dict:
    return {
        "hit": hit,
        "even": even,
        "steps": steps,
        "end_d": end_d,
        "spawns": spawns,
        "anchor": task["anchor"],
        "dir": task["dir"],
        "lane": task.get("lane", "g"),
        "level": task["level"],
        "chunk": task["chunk"],
    }


def build_tasks(
    level: int,
    anchor_name: str,
    d_center: int,
    direction: str,
    lane: str,
    even_quota: int,
    chunk: int,
    lo: int,
    hi: int,
    spawn_stride: int = 0,
    spawn_path: str | None = None,
) -> list[dict]:
    """Split one direction into chunks sized for ~even_quota total (max ~2x scalar steps)."""
    max_scalar = min(even_quota * 2 + 1, hi - lo)
    tasks: list[dict] = []
    if direction == "fwd":
        mode, d_start, d_end = "fwd", d_center, min(hi - 1, d_center + max_scalar)
        step = chunk
        pos = d_start
        ci = 0
        while pos < d_end:
            end = min(d_end, pos + step)
            tasks.append(
                {
                    "level": level,
                    "anchor": anchor_name,
                    "dir": direction,
                    "lane": lane,
                    "mode": mode,
                    "d0": pos,
                    "steps": end - pos,
                    "chunk": f"L{level}_{anchor_name}_{direction}_{lane}_{ci}",
                    "table_size": chunk,
                    "spawn_stride": spawn_stride,
                    "spawn_path": spawn_path,
                }
            )
            pos = end
            ci += 1
    elif direction == "bwd":
        d_end = max(lo, d_center - max_scalar)
        pos = d_center
        ci = 0
        while pos > d_end:
            start = max(d_end, pos - chunk)
            tasks.append(
                {
                    "level": level,
                    "anchor": anchor_name,
                    "dir": direction,
                    "lane": lane,
                    "mode": "bwd",
                    "d0": pos,
                    "steps": pos - start,
                    "chunk": f"L{level}_{anchor_name}_{direction}_{lane}_{ci}",
                    "table_size": chunk,
                    "spawn_stride": spawn_stride,
                    "spawn_path": spawn_path,
                }
            )
            pos = start
            ci += 1
    else:
        raise ValueError(direction)
    return tasks


def log_line(msg: str, *, live: bool = True) -> None:
    print(msg, flush=True)
    if live:
        ARCHIVE.mkdir(parents=True, exist_ok=True)
        try:
            with LIVE_LOG.open("a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except OSError:
            pass


def flush_report(lines: list[str]) -> None:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    return {"completed_l1": [], "l1": {}}


def save_progress(state: dict) -> None:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def spawn_resume_state(spawn_path: Path) -> tuple[int, int]:
    """Return (even_count, last_d) from an existing L1 spawn file."""
    if not spawn_path.exists() or spawn_path.stat().st_size == 0:
        return 0, 0
    even = 0
    last_d = 0
    with spawn_path.open(encoding="ascii") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            even += 1
            last_d = int(s)
    return even, last_d


def run_quota(
    tasks: list[dict],
    even_quota: int,
    workers: int,
    *,
    log_every: int = 5,
) -> tuple[int | None, int, int, dict[tuple[str, str, str], int]]:
    """Run chunks until even_quota reached across task group or tasks exhausted."""
    total_even = 0
    total_steps = 0
    hit = None
    terminals: dict[tuple[str, str, str], int] = {}
    done = 0

    with ProcessPoolExecutor(max_workers=max(1, workers)) as pool:
        futs = [pool.submit(scroll_even_chunk, t) for t in tasks]
        for fut in as_completed(futs):
            r = fut.result()
            total_even += r["even"]
            total_steps += r["steps"]
            done += 1
            key = (r["anchor"], r["dir"], r["lane"])
            terminals[key] = r["end_d"]
            if log_every and done % log_every == 0:
                log_line(
                    f"  ... chunk {done}/{len(tasks)} even={total_even:,}/{even_quota:,} "
                    f"terminal_d={terminals[key]}"
                )
            if r["hit"] is not None:
                hit = r["hit"]
                for f in futs:
                    f.cancel()
                break
            if total_even >= even_quota:
                break
    return hit, total_even, total_steps, terminals


def main() -> None:
    ap = argparse.ArgumentParser(description="P160 billion even-y (02) pubkey scroll")
    ap.add_argument("--even-quota", type=int, default=1_000_000_000)
    ap.add_argument("--level", type=int, default=2, choices=[1, 2])
    ap.add_argument("--chunk", type=int, default=500_000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument(
        "--lanes",
        default="g,psi,x2",
        help="g=+/-G, psi=+/-psi(G), x2=+/-2G (even scalar stride)",
    )
    ap.add_argument("--l2-spawn-every", type=int, default=1, help="L2 anchor every N even-y pubkeys from L1")
    ap.add_argument("--max-l2-spawns", type=int, default=0, help="cap L2 jobs (0 = all spawns)")
    ap.add_argument("--anchors", default="", help="comma names or 'all'")
    ap.add_argument(
        "--resume",
        action="store_true",
        help="continue L1 from checkpoint spawns/progress.json (do not wipe spawn files)",
    )
    ap.add_argument(
        "--log-every",
        type=int,
        default=5,
        help="progress line every N completed chunks within one L1/L2 job",
    )
    args = ap.parse_args()

    tgt = Target.load()
    lo, hi, _ = puzzle_band(160)
    lanes = [x.strip() for x in args.lanes.split(",") if x.strip()]
    anchors = default_anchors()
    if args.anchors:
        want = {x.strip() for x in args.anchors.split(",")}
        anchors = [(n, d) for n, d in anchors if n in want]

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    if not args.resume and LIVE_LOG.exists():
        LIVE_LOG.unlink()
    progress = load_progress() if args.resume else {"completed_l1": [], "l1": {}}

    lines = [
        "P160 billion even-y scroll (02 compressed only)",
        f"target={compressed02(tgt.px, tgt.py)}",
        f"even_quota={args.even_quota:,}  level={args.level}  chunk={args.chunk:,}  workers={args.workers}",
        f"lanes={lanes}  anchors={[a[0] for a in anchors]}",
        f"l2_spawn_every={args.l2_spawn_every}  max_l2_spawns={args.max_l2_spawns or 'all'}",
        f"resume={args.resume}",
        "",
    ]
    flush_report(lines)
    log_line("=== P160 billion even-y scroll start ===")
    log_line(lines[1])
    log_line(lines[2])

    t0 = time.time()
    global_hit = None
    l1_spawn_files: list[tuple[str, str, str, Path]] = []

    # --- Level 1 ---
    for aname, d_center in anchors:
        d_center = max(lo, min(hi - 1, d_center))
        for lane in lanes:
            for direction in ("fwd", "bwd"):
                l1_key = f"{aname}:{direction}:{lane}"
                if args.resume and l1_key in progress.get("completed_l1", []):
                    spawn_path = CHECKPOINT_DIR / f"L1_{aname}_{direction}_{lane}_spawns.txt"
                    l1_spawn_files.append((aname, direction, lane, spawn_path))
                    msg = f"SKIP L1 {l1_key} (completed)"
                    lines.append(msg)
                    log_line(msg)
                    continue

                spawn_path = CHECKPOINT_DIR / f"L1_{aname}_{direction}_{lane}_spawns.txt"
                if not args.resume and spawn_path.exists():
                    spawn_path.unlink()

                even_already = 0
                d_start = d_center
                if args.resume and spawn_path.exists():
                    even_already, last_d = spawn_resume_state(spawn_path)
                    if last_d:
                        d_start = last_d
                    if even_already:
                        log_line(
                            f"RESUME L1 {l1_key}: even_already={even_already:,} "
                            f"d_start={d_start}"
                        )

                remaining = max(0, args.even_quota - even_already)
                if remaining == 0:
                    progress.setdefault("completed_l1", []).append(l1_key)
                    save_progress(progress)
                    l1_spawn_files.append((aname, direction, lane, spawn_path))
                    msg = f"L1 {l1_key}: quota already met ({even_already:,} even-y)"
                    lines.append(msg)
                    log_line(msg)
                    flush_report(lines)
                    continue

                spawn_stride = args.l2_spawn_every if args.level >= 2 else 0
                tasks = build_tasks(
                    1,
                    aname,
                    d_start,
                    direction,
                    lane,
                    remaining,
                    args.chunk,
                    lo,
                    hi,
                    spawn_stride=spawn_stride,
                    spawn_path=str(spawn_path) if spawn_stride else None,
                )
                log_line(
                    f"RUN L1 {l1_key}: need {remaining:,} more even-y "
                    f"({len(tasks)} chunks from d={d_start})"
                )
                hit, even, steps, terms = run_quota(
                    tasks,
                    remaining,
                    args.workers,
                    log_every=args.log_every,
                )
                even_total = even_already + even
                l1_spawn_files.append((aname, direction, lane, spawn_path))
                progress.setdefault("l1", {})[l1_key] = {
                    "even": even_total,
                    "terminal_d": terms.get((aname, direction, lane), d_start),
                    "steps": steps,
                }
                if even_total >= args.even_quota:
                    progress.setdefault("completed_l1", []).append(l1_key)
                save_progress(progress)
                lines.append(
                    f"L1 {aname} {direction} {lane}: even={even_total:,} "
                    f"(+{even:,} this run) steps={steps:,} "
                    f"terminal_d={terms.get((aname, direction, lane), d_start)} "
                    f"spawns={spawn_path.stat().st_size if spawn_path.exists() else 0}B hit={hit}"
                )
                log_line(lines[-1])
                flush_report(lines)
                if hit is not None:
                    global_hit = hit
                    break
            if global_hit is not None:
                break
        if global_hit is not None:
            break

    # --- Level 2: from each even-y spawn on L1, another even-quota in +/-G ---
    if global_hit is None and args.level >= 2:
        lines.append("")
        lines.append("=== Level 2 from L1 even-y spawns (02 only) ===")
        for aname, direction, lane, spawn_path in l1_spawn_files:
            if not spawn_path.exists():
                continue
            spawns = [int(line.strip()) for line in spawn_path.read_text(encoding="ascii").splitlines() if line.strip()]
            if args.max_l2_spawns > 0:
                spawns = spawns[: args.max_l2_spawns]
            lines.append(f"L2 source {aname} {direction} {lane}: {len(spawns):,} spawn anchors")
            for si, d_spawn in enumerate(spawns):
                for sub in ("fwd", "bwd"):
                    tasks = build_tasks(
                        2,
                        f"{aname}#{si}",
                        d_spawn,
                        sub,
                        lane,
                        args.even_quota,
                        args.chunk,
                        lo,
                        hi,
                    )
                    hit, even, steps, _ = run_quota(
                        tasks,
                        args.even_quota,
                        args.workers,
                        log_every=args.log_every,
                    )
                    if si % max(1, len(spawns) // 20) == 0 or hit is not None:
                        lines.append(
                            f"L2 spawn#{si} {sub} {lane}: even={even:,} steps={steps:,} hit={hit}"
                        )
                        log_line(lines[-1])
                        flush_report(lines)
                    if hit is not None:
                        global_hit = hit
                        break
                if global_hit is not None:
                    break
            if global_hit is not None:
                break

    elapsed = time.time() - t0
    lines.extend(
        [
            "",
            f"elapsed={elapsed:.1f}s",
            f"RESULT: {'HIT d=' + str(global_hit) if global_hit else 'no hit'}",
        ]
    )
    if global_hit is not None:
        pt = scalar_mult(global_hit, G)
        assert pt is not None
        lines.append(f"verify 02={compressed02(pt[0], pt[1])}")

    flush_report(lines)
    log_line(f"report: {REPORT}")
    print(f"report: {REPORT}")


if __name__ == "__main__":
    main()
