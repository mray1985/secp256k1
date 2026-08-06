#!/usr/bin/env python3
"""Resumable P135 band search with all state on E: (or --out-dir)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from ecdsa import SECP256k1

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "ECDLP"))

LO = 1 << 134
TOP = (1 << 135) - 1
PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
G = SECP256k1.generator

DEFAULT_OUT = Path(r"E:\secp256k1_search\p135")


def ec_hit(d: int) -> bool:
    pt = d * G
    return pt.x() == PX and pt.y() == PY


def load_anchor() -> int:
    try:
        from p135_carry_remainder_report import build_p135_bridge

        return build_p135_bridge(puzzle_row=2)["shelf2"] % LO
    except Exception:
        return 12_399_803_124_245_147_579_303_535_673_221_407_674_145


def write_manifest(out: Path, anchor: int, args: argparse.Namespace) -> None:
    manifest = {
        "puzzle": 135,
        "band": {"lo": LO, "top": TOP},
        "target": {"Px": PX, "Py": PY},
        "anchor_t": anchor,
        "delta_start": args.delta_start,
        "delta_end": args.delta_end,
        "gate": "d*G == P",
        "framework": "Lambda unity landing rx3; shelf2 anchor; stride 1",
        "started_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))


def load_checkpoint(cp: Path) -> int:
    if not cp.exists():
        return 0
    data = json.loads(cp.read_text())
    return int(data.get("next_delta", 0))


def save_checkpoint(cp: Path, next_delta: int, tested: int, rate: float) -> None:
    cp.write_text(
        json.dumps(
            {
                "next_delta": next_delta,
                "tested_total": tested,
                "rate_per_s": rate,
                "updated_utc": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
    )


def log_line(log: Path, msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {msg}\n"
    print(msg, flush=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(line)


def run_search(out: Path, anchor: int, d0: int, d1: int, ckpt_every: int) -> int | None:
    out.mkdir(parents=True, exist_ok=True)
    cp = out / "checkpoint.json"
    log = out / "search.log"
    start_delta = max(d0, load_checkpoint(cp))
    tested = 0
    t0 = time.perf_counter()

    log_line(log, f"resume delta={start_delta} range=[{d0},{d1}] anchor_t={anchor}")

    for delta in range(start_delta, d1 + 1):
        t = (anchor + delta) % LO
        d = LO + t
        if d > TOP:
            continue
        tested += 1
        if ec_hit(d):
            hit = out / "HIT.json"
            payload = {"d": d, "d_hex": hex(d), "t": t, "delta": delta}
            hit.write_text(json.dumps(payload, indent=2))
            log_line(log, f"MATCH d={d} hex={hex(d)}")
            return d
        if tested % ckpt_every == 0:
            elapsed = time.perf_counter() - t0
            rate = tested / max(elapsed, 1e-9)
            save_checkpoint(cp, delta + 1, tested, rate)
            log_line(log, f"checkpoint delta={delta+1} tested={tested} rate={rate:.0f}/s")

    elapsed = time.perf_counter() - t0
    rate = tested / max(elapsed, 1e-9)
    save_checkpoint(cp, d1 + 1, tested, rate)
    log_line(log, f"done no hit tested={tested} rate={rate:.0f}/s")
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="P135 resumable search -> E: drive")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--anchor", type=int, default=None, help="t anchor mod LO (default shelf2)")
    ap.add_argument("--delta-start", type=int, default=0)
    ap.add_argument("--delta-end", type=int, default=50_000_000, help="scan anchor+delta")
    ap.add_argument("--checkpoint-every", type=int, default=100_000)
    ap.add_argument("--init-only", action="store_true", help="write manifest only")
    args = ap.parse_args()

    out = args.out_dir
    if not out.drive or not Path(str(out.drive) + "\\").exists():
        print(f"ERROR: drive not available: {out}", file=sys.stderr)
        return 2

    out.mkdir(parents=True, exist_ok=True)
    anchor = (args.anchor if args.anchor is not None else load_anchor()) % LO
    write_manifest(out, anchor, args)

    if args.init_only:
        print(f"manifest written: {out / 'manifest.json'}")
        return 0

    found = run_search(out, anchor, args.delta_start, args.delta_end, args.checkpoint_every)
    return 0 if found else 1


if __name__ == "__main__":
    raise SystemExit(main())
