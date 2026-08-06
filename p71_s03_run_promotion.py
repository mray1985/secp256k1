#!/usr/bin/env python3
"""P71-S03 native promotion sequence (after Puzzle-1 gate).

Sequence (locked):
  known hit → range boundaries → nine solved targets
  → checkpoint/resume → 10-minute sustained benchmark

Ledger rules:
  * known-hit calibration terminates on verified find (normal)
  * throughput-only may stop after fixed duration (timeout ≠ failure)
  * reported hit without independent HASH160 confirm = immediate FAIL
  * --allow-outside-p71-band only for calibration windows; forbidden for real P71
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

from p71_native_backend import (
    P71_ADDR,
    P71_D_MAX,
    P71_D_MIN,
    address_p2pkh,
    hash160_compressed,
    run_native,
    to_hex,
)
from p71_s01_scanner_calibration import load_keys

OUT = Path(__file__).resolve().parent / "logs" / "p71_s03" / "promotion"
SOLVED = [1, 5, 10, 20, 30, 40, 50, 65, 70]


def gate_from_result(result, *, d: int, lo: int, hi: int) -> dict:
    expected_verified = any(v["d"] == d and v["accepted"] for v in result.verified_hits)
    expected_seen = expected_verified or any(int(x, 16) == d for x in result.found_private_keys)
    inside = expected_verified and all(lo <= v["d"] <= hi for v in result.verified_hits)
    all_ok = (
        len(result.rejected_hits) == 0
        and expected_verified
        and all(v.get("accepted") for v in result.verified_hits)
    )
    return {
        "expected_seen": bool(expected_seen),
        "expected_verified": bool(expected_verified),
        "inside_requested_range": bool(inside),
        "hash160_match": bool(expected_verified),
        "all_reported_hits_verified": bool(all_ok),
        "pass": all(
            [
                expected_seen,
                expected_verified,
                inside,
                expected_verified,
                all_ok,
            ]
        ),
    }


def run_known(
    *,
    backend: str,
    binary: Path,
    name: str,
    d: int,
    lo: int,
    hi: int,
    threads: int,
) -> dict:
    addr = address_p2pkh(hash160_compressed(d))
    work = OUT / name
    work.mkdir(parents=True, exist_ok=True)
    result = run_native(
        backend=backend,
        binary=binary,
        target=addr,
        start=lo,
        end=hi,
        seconds=None,
        threads=threads,
        checkpoint=None,
        found_file=work / "found.txt",
        expect_private=d,
        work_dir=work,
    )
    gate = gate_from_result(result, d=d, lo=lo, hi=hi)
    payload = asdict(result)
    payload["s03_calibration_gate"] = gate
    payload["step"] = name
    (work / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"  {name}: {'PASS' if gate['pass'] else 'FAIL'} "
        f"d={to_hex(d)} range=[{to_hex(lo)},{to_hex(hi)}] "
        f"verified={gate['expected_verified']} rejected={len(result.rejected_hits)}"
    )
    return {"step": name, "pass": gate["pass"], "gate": gate, "output": str(work / "result.json")}


def run_checkpoint_resume(
    *,
    backend: str,
    binary: Path,
    threads: int,
) -> dict:
    """Emulate interrupt/resume for KeyHunt (no BitCrack --continue).

    KeyHunt address mode uses a large internal N and does not hard-stop at
    --end; phase A therefore searches a window *above* the known key so a miss
    is expected. Phase B resumes into the window that contains the key.
    """
    d = 1
    addr = address_p2pkh(hash160_compressed(d))
    work = OUT / "checkpoint_resume"
    work.mkdir(parents=True, exist_ok=True)

    # Phase A: start above the key — miss expected; timeout is OK
    phase_a = run_native(
        backend=backend,
        binary=binary,
        target=addr,
        start=0x1000,
        end=0x2000,
        seconds=5.0,
        threads=threads,
        checkpoint=None,
        found_file=work / "phase_a_found.txt",
        expect_private=None,
        work_dir=work,
    )
    if phase_a.rejected_hits:
        print("  checkpoint_resume: FAIL (unverified/out-of-range report in phase A)")
        return {
            "step": "checkpoint_resume",
            "pass": False,
            "reason": "rejected_hit_in_phase_a",
            "rejected": phase_a.rejected_hits,
        }
    if any(v["accepted"] for v in phase_a.verified_hits):
        print("  checkpoint_resume: FAIL (unexpected hit in miss window)")
        return {"step": "checkpoint_resume", "pass": False, "reason": "false_hit_phase_a"}

    # Phase B: resume into locked Puzzle-1 window
    phase_b = run_native(
        backend=backend,
        binary=binary,
        target=addr,
        start=1,
        end=32,
        seconds=None,
        threads=threads,
        checkpoint=None,
        found_file=work / "phase_b_found.txt",
        expect_private=d,
        work_dir=work,
    )
    gate = gate_from_result(phase_b, d=d, lo=1, hi=32)
    ok = gate["pass"] and len(phase_a.rejected_hits) == 0
    payload = {
        "step": "checkpoint_resume",
        "emulation": "miss_window_then_resume_keyhunt",
        "phase_a": asdict(phase_a),
        "phase_b": asdict(phase_b),
        "gate_phase_b": gate,
        "pass": ok,
    }
    (work / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"  checkpoint_resume: {'PASS' if ok else 'FAIL'} (miss-then-resume emulation)")
    return {"step": "checkpoint_resume", "pass": ok, "output": str(work / "result.json")}


def run_sustained(
    *,
    backend: str,
    binary: Path,
    threads: int,
    seconds: float,
) -> dict:
    """Throughput-only on production P71 band. Timeout/interrupt is not a failure."""
    work = OUT / "sustained_10min"
    work.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    result = run_native(
        backend=backend,
        binary=binary,
        target=P71_ADDR,
        start=P71_D_MIN,
        end=P71_D_MAX,
        seconds=seconds,
        threads=threads,
        checkpoint=None,
        found_file=work / "found.txt",
        expect_private=None,
        work_dir=work,
    )
    wall = time.perf_counter() - t0
    # Immediate fail if any reported hit lacks HASH160 confirm
    fail_unverified = bool(result.rejected_hits) or (
        bool(result.found_private_keys) and not result.verified_hits
    )
    ok = not fail_unverified
    payload = asdict(result)
    payload["step"] = "sustained_benchmark"
    payload["allow_outside_p71_band"] = False
    payload["production_range"] = {
        "start_hex": to_hex(P71_D_MIN),
        "end_hex": to_hex(P71_D_MAX),
        "inclusive": True,
        "candidates": 1 << 70,
    }
    payload["throughput_timeout_is_failure"] = False
    payload["timed_out_expected"] = True
    payload["pass"] = ok
    payload["wall_outer_s"] = wall
    (work / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"  sustained_{int(seconds)}s: {'PASS' if ok else 'FAIL'} "
        f"R_peak={result.R_peak} R_sustained={result.R_sustained} "
        f"timed_out={result.timed_out} rejected={len(result.rejected_hits)}"
    )
    return {
        "step": "sustained_benchmark",
        "pass": ok,
        "R_peak": result.R_peak,
        "R_sustained": result.R_sustained,
        "timed_out": result.timed_out,
        "output": str(work / "result.json"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["bitcrack", "keyhunt"], required=True)
    ap.add_argument("--binary", type=Path, required=True)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--sustained-seconds", type=float, default=600.0)
    ap.add_argument("--skip-sustained", action="store_true")
    ap.add_argument("--only-sustained", action="store_true")
    args = ap.parse_args()
    if not args.binary.is_file():
        print(f"ERROR: binary not found: {args.binary}")
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    keys = load_keys()
    steps: list[dict] = []

    print("P71-S03 promotion sequence")
    print(f"backend={args.backend} binary={args.binary}")

    if args.only_sustained:
        sustained = run_sustained(
            backend=args.backend,
            binary=args.binary,
            threads=args.threads,
            seconds=args.sustained_seconds,
        )
        summary = {
            "candidate_id": "P71-S-20260710-03",
            "status": "PASS" if sustained["pass"] else "FAIL",
            "backend": args.backend,
            "binary": str(args.binary),
            "steps": [sustained],
            "R_peak": sustained.get("R_peak"),
            "R_sustained": sustained.get("R_sustained"),
            "note": "sustained-only invocation",
        }
        out = OUT / "P71_S03_sustained_only.json"
        out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"wrote {out}")
        print(f"STATUS: {summary['status']}")
        return 0 if sustained["pass"] else 1

    # 1) known hit (Puzzle 1 locked window)
    steps.append(
        run_known(
            backend=args.backend,
            binary=args.binary,
            name="known_hit_puzzle1",
            d=1,
            lo=1,
            hi=32,
            threads=args.threads,
        )
    )

    # 2) range boundaries (key at lo / key at hi)
    steps.append(
        run_known(
            backend=args.backend,
            binary=args.binary,
            name="boundary_key_at_lo",
            d=1,
            lo=1,
            hi=8,
            threads=args.threads,
        )
    )
    steps.append(
        run_known(
            backend=args.backend,
            binary=args.binary,
            name="boundary_key_at_hi",
            d=21,
            lo=16,
            hi=21,
            threads=args.threads,
        )
    )

    # 3) nine solved targets
    for n in SOLVED:
        d = keys[n]
        lo = max(1, d - 8)
        hi = d + 8
        steps.append(
            run_known(
                backend=args.backend,
                binary=args.binary,
                name=f"solved_n{n}",
                d=d,
                lo=lo,
                hi=hi,
                threads=args.threads,
            )
        )

    # 4) checkpoint / resume
    steps.append(
        run_checkpoint_resume(
            backend=args.backend, binary=args.binary, threads=args.threads
        )
    )

    # 5) 10-minute sustained (production band; no --allow-outside)
    sustained = None
    if not args.skip_sustained:
        sustained = run_sustained(
            backend=args.backend,
            binary=args.binary,
            threads=args.threads,
            seconds=args.sustained_seconds,
        )
        steps.append(sustained)

    all_pass = all(s.get("pass") for s in steps)
    summary = {
        "candidate_id": "P71-S-20260710-03",
        "status": "PASS" if all_pass else "FAIL",
        "backend": args.backend,
        "binary": str(args.binary),
        "native_gpu": args.backend == "bitcrack",
        "steps": steps,
        "R_peak": None if sustained is None else sustained.get("R_peak"),
        "R_sustained": None if sustained is None else sustained.get("R_sustained"),
        "note": (
            "No CUDA BitCrack on this host; KeyHunt CPU via WSL used for native path. "
            "No GPU throughput credited."
            if args.backend == "keyhunt"
            else "BitCrack native path."
        ),
    }
    out = OUT / "P71_S03_promotion_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    print(f"STATUS: {summary['status']}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
