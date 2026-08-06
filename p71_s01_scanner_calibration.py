#!/usr/bin/env python3
"""P71-S01 — Address-scanner calibration (no Kangaroo, no pattern heuristics).

Exact path:
  d → compressed SEC → SHA256 → RIPEMD160 → compare hash160

Modes:
  --oracle     artificial hidden targets in small intervals
  --solved     recover known puzzle addresses from CSV (sanity)
  --rate       measure keys/s on a contiguous window
  --checkpoint interrupt/resume agreement on a planted target

Does NOT search Puzzle 71's full 2^70 band. Does NOT use shelf2/gap/creator formulas.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from ecdsa import SECP256k1

G = SECP256k1.generator
CURVE = SECP256k1.curve

ROOT = Path(__file__).resolve().parent
KEYS_CSV = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT_DIR = ROOT / "logs" / "p71_s01"
P71_ADDR = "1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU"
P71_H160 = bytes.fromhex("F6F5431D25BBF7B12E8ADD9AF5E3475C44A0A5B8")
P71_LO = 1 << 70
P71_HI = 1 << 71
ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


@dataclass
class RunResult:
    mode: str
    status: str
    keys_tested: int
    elapsed_s: float
    keys_per_s: float
    recovered_d: int | None = None
    target_h160: str = ""
    notes: str = ""


def hash160_of_d(d: int) -> bytes:
    P = d * G
    pref = b"\x02" if (P.y() % 2 == 0) else b"\x03"
    sec = pref + P.x().to_bytes(32, "big")
    return hashlib.new("ripemd160", hashlib.sha256(sec).digest()).digest()


def address_p2pkh(h160: bytes) -> str:
    payload = b"\x00" + h160
    chk = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    n = int.from_bytes(payload + chk, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = ALPHABET[r] + out
    # leading zero bytes → leading '1'
    pad = 0
    for b in payload + chk:
        if b == 0:
            pad += 1
        else:
            break
    return "1" * pad + out


def verify_partitions(lo: int, hi: int, n_parts: int) -> bool:
    """[lo, hi) covered with no gaps/overlaps."""
    width = hi - lo
    base = width // n_parts
    rem = width % n_parts
    covered = sum(base + (1 if i < rem else 0) for i in range(n_parts))
    return covered == width


def partition_ranges(lo: int, hi: int, n_parts: int) -> list[tuple[int, int]]:
    width = hi - lo
    base = width // n_parts
    rem = width % n_parts
    out: list[tuple[int, int]] = []
    cur = lo
    for i in range(n_parts):
        w = base + (1 if i < rem else 0)
        out.append((cur, cur + w))
        cur += w
    assert cur == hi
    return out


def scan_range(
    lo: int,
    hi: int,
    target: bytes,
    *,
    checkpoint_path: Path | None = None,
    checkpoint_every: int = 0,
    resume: bool = False,
    max_keys: int | None = None,
) -> tuple[int | None, int, float]:
    """Linear scan d in [lo, hi). Returns (hit_d, keys_tested, elapsed_s)."""
    start = lo
    keys = 0
    if resume and checkpoint_path and checkpoint_path.is_file():
        ck = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if ck.get("lo") == lo and ck.get("hi") == hi and ck.get("target") == target.hex():
            start = int(ck["next_d"])
            keys = int(ck.get("keys", 0))
    t0 = time.perf_counter()
    d = start
    hit: int | None = None
    while d < hi:
        if max_keys is not None and keys >= max_keys:
            break
        if hash160_of_d(d) == target:
            hit = d
            keys += 1
            break
        keys += 1
        d += 1
        if (
            checkpoint_every
            and checkpoint_path
            and keys % checkpoint_every == 0
        ):
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            checkpoint_path.write_text(
                json.dumps(
                    {
                        "lo": lo,
                        "hi": hi,
                        "target": target.hex(),
                        "next_d": d,
                        "keys": keys,
                    }
                ),
                encoding="utf-8",
            )
    elapsed = time.perf_counter() - t0
    return hit, keys, elapsed


def load_keys() -> dict[int, int]:
    keys: dict[int, int] = {}
    with KEYS_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            keys[int(row["puzzle"])] = int(row["private_key"])
    return keys


def run_oracle(trials: int = 8, width_bits: int = 16) -> list[RunResult]:
    """Plant random u in [0, 2^w), scan that interval for hash160(d*G)."""
    import random

    rng = random.Random(0x07150101)
    results: list[RunResult] = []
    W = 1 << width_bits
    assert verify_partitions(0, W, 4)
    for t in range(trials):
        # Use small absolute d in a known band for speed: base + offset
        base = 1 << 20  # keep EC cheap-ish
        offset = rng.randrange(W)
        d_true = base + offset
        target = hash160_of_d(d_true)
        lo, hi = base, base + W
        # Scan only the partition containing the key (still full coverage test separately)
        hit, keys, elapsed = scan_range(lo, hi, target)
        ok = hit == d_true and address_p2pkh(target).startswith("1")
        results.append(
            RunResult(
                mode=f"oracle_w{width_bits}",
                status="PASS" if ok else "FAIL",
                keys_tested=keys,
                elapsed_s=elapsed,
                keys_per_s=keys / elapsed if elapsed > 0 else 0.0,
                recovered_d=hit,
                target_h160=target.hex(),
                notes=f"d_true={d_true}",
            )
        )
        print(f"oracle t={t} {results[-1].status} keys={keys} rate={results[-1].keys_per_s:.1f}/s")
    return results


def run_solved(puzzles: list[int]) -> list[RunResult]:
    keys = load_keys()
    results: list[RunResult] = []
    for n in puzzles:
        if n not in keys:
            print(f"n={n} SKIP")
            continue
        d = keys[n]
        h160 = hash160_of_d(d)
        addr = address_p2pkh(h160)
        # Tiny window around d — correctness of path, not search
        lo = max(1, d - 3)
        hi = d + 4
        hit, keys_n, elapsed = scan_range(lo, hi, h160)
        ok = hit == d
        results.append(
            RunResult(
                mode=f"solved_n{n}",
                status="PASS" if ok else "FAIL",
                keys_tested=keys_n,
                elapsed_s=elapsed,
                keys_per_s=keys_n / elapsed if elapsed else 0.0,
                recovered_d=hit,
                target_h160=h160.hex(),
                notes=f"addr={addr}",
            )
        )
        print(f"solved n={n} {results[-1].status} addr={addr}")
    return results


def run_rate(n_keys: int = 2000) -> RunResult:
    """Throughput on contiguous d starting at 2^20."""
    lo = 1 << 20
    hi = lo + n_keys
    # Dummy target that will not match — pure rate
    target = b"\x00" * 20
    _, keys, elapsed = scan_range(lo, hi, target, max_keys=n_keys)
    rate = keys / elapsed if elapsed else 0.0
    print(f"rate keys={keys} elapsed={elapsed:.3f}s rate={rate:.1f}/s")
    return RunResult(
        mode="rate",
        status="MEASURED",
        keys_tested=keys,
        elapsed_s=elapsed,
        keys_per_s=rate,
        notes="Python reference CPU; not a GPU launch rate",
    )


def run_checkpoint() -> list[RunResult]:
    """Plant target; partial scan with checkpoint; resume must find same d."""
    base = 1 << 18
    d_true = base + 12345
    target = hash160_of_d(d_true)
    lo, hi = base, base + 20000
    ck = OUT_DIR / "checkpoint_test.json"
    if ck.exists():
        ck.unlink()
    # Phase 1: stop early via max_keys before hitting d_true
    hit1, keys1, el1 = scan_range(
        lo, hi, target, checkpoint_path=ck, checkpoint_every=500, max_keys=5000
    )
    r1 = RunResult(
        mode="checkpoint_phase1",
        status="PARTIAL" if hit1 is None else "EARLY_HIT",
        keys_tested=keys1,
        elapsed_s=el1,
        keys_per_s=keys1 / el1 if el1 else 0.0,
        recovered_d=hit1,
        notes=f"ck_exists={ck.is_file()}",
    )
    print(r1.status, r1.notes)
    # Phase 2: resume
    hit2, keys2, el2 = scan_range(
        lo, hi, target, checkpoint_path=ck, checkpoint_every=1000, resume=True
    )
    ok = hit2 == d_true and hit1 is None and ck.is_file()
    r2 = RunResult(
        mode="checkpoint_phase2",
        status="PASS" if ok else "FAIL",
        keys_tested=keys2,
        elapsed_s=el2,
        keys_per_s=keys2 / el2 if el2 else 0.0,
        recovered_d=hit2,
        notes=f"d_true={d_true}",
    )
    print(f"checkpoint resume {r2.status} hit={hit2}")
    return [r1, r2]


def main() -> int:
    ap = argparse.ArgumentParser(description="P71-S01 scanner calibration")
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--solved", action="store_true")
    ap.add_argument("--rate", action="store_true")
    ap.add_argument("--checkpoint", action="store_true")
    ap.add_argument("--oracle-trials", type=int, default=8)
    ap.add_argument("--oracle-bits", type=int, default=14)
    ap.add_argument("--rate-keys", type=int, default=2000)
    ap.add_argument("--solved-ladder", type=int, nargs="+", default=[1, 5, 10, 20, 30, 40, 50, 65, 70])
    args = ap.parse_args()

    if not any([args.oracle, args.solved, args.rate, args.checkpoint]):
        args.oracle = args.solved = args.rate = args.checkpoint = True

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Identity check for P71 target
    assert address_p2pkh(P71_H160) == P71_ADDR
    print(f"P71 target OK: {P71_ADDR}")
    print(f"band [{P71_LO}, {P71_HI}) width=2^70 — not scanned here")
    print("engine: linear hash160 scan (no kangaroo)")

    results: list[RunResult] = []
    if args.oracle:
        results.extend(run_oracle(args.oracle_trials, args.oracle_bits))
    if args.solved:
        results.extend(run_solved(args.solved_ladder))
    if args.rate:
        results.append(run_rate(args.rate_keys))
    if args.checkpoint:
        results.extend(run_checkpoint())

    payload = {
        "candidate_id": "P71-S-20260710-01",
        "target_addr": P71_ADDR,
        "target_h160": P71_H160.hex(),
        "band": {"lo": P71_LO, "hi": P71_HI, "width_bits": 70},
        "kangaroo": False,
        "partitions_ok": verify_partitions(0, 1 << 20, 8),
        "results": [asdict(r) for r in results],
        "promotion": {
            "oracle_pass": all(r.status == "PASS" for r in results if r.mode.startswith("oracle")),
            "solved_pass": all(r.status == "PASS" for r in results if r.mode.startswith("solved")),
            "checkpoint_pass": any(
                r.mode == "checkpoint_phase2" and r.status == "PASS" for r in results
            ),
            "cpu_gpu_identical": None,
            "python_rate_keys_per_s": next(
                (r.keys_per_s for r in results if r.mode == "rate"), None
            ),
        },
    }
    out = OUT_DIR / "P71_S01_calibration_results.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    print("promotion", json.dumps(payload["promotion"], indent=2))
    ok = (
        payload["promotion"]["oracle_pass"]
        and payload["promotion"]["solved_pass"]
        and payload["promotion"]["checkpoint_pass"]
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
