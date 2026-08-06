#!/usr/bin/env python3
"""P71-S03 — Native/GPU scanner equivalence harness.

Compares a native scanner backend against the P71-S01 Python reference on the
locked path:

  d → [d]G → compressed SEC → SHA256 → RIPEMD160  (20-byte compare)

Backends:
  --backend python   reference (always available)
  --backend cmd      external CLI (BitCrack/KeyHunt/etc.) via --scanner-cmd template

Does not Base58-encode per candidate. Does not open shelf2/pattern lanes.
Does not scan the full 2^70 band unless explicitly asked with a tiny test window.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from ecdsa import SECP256k1

from p71_s01_scanner_calibration import (
    P71_ADDR,
    P71_H160,
    P71_HI,
    P71_LO,
    address_p2pkh,
    hash160_of_d,
    load_keys,
    partition_ranges,
    verify_partitions,
)

G = SECP256k1.generator
ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "logs" / "p71_s03"
S01_RESULTS = ROOT / "logs" / "p71_s01" / "P71_S01_calibration_results.json"

# Inclusive endpoints (locked)
P71_D_MIN = 1 << 70          # 2^70
P71_D_MAX = (1 << 71) - 1    # 2^71 - 1


@dataclass
class ThroughputReport:
    R_peak: float
    R_sustained: float
    keys_tested: int
    wall_s: float
    device: str
    notes: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class EquivalenceResult:
    check: str
    status: str
    python_d: int | None
    native_d: int | None
    notes: str = ""


def hash160_path_locked(d: int) -> bytes:
    """Locked candidate path — HASH160 only, no Base58."""
    return hash160_of_d(d)


def python_scan(
    lo: int,
    hi_inclusive: int,
    target: bytes,
    *,
    on_progress: Callable[[int, float], None] | None = None,
) -> tuple[int | None, int, float]:
    """Scan inclusive [lo, hi_inclusive]. Returns (hit, keys, elapsed)."""
    assert lo <= hi_inclusive
    keys = 0
    t0 = time.perf_counter()
    hit: int | None = None
    d = lo
    last_report = t0
    while d <= hi_inclusive:
        keys += 1
        if hash160_path_locked(d) == target:
            hit = d
            break
        d += 1
        now = time.perf_counter()
        if on_progress and now - last_report >= 0.5:
            on_progress(keys, now - t0)
            last_report = now
    return hit, keys, time.perf_counter() - t0


def measure_throughput_python(
    n_keys: int,
    *,
    warm_keys: int = 200,
    sustained_keys: int | None = None,
) -> ThroughputReport:
    """Peak = best short window; sustained = long contiguous miss-scan."""
    sustained_keys = sustained_keys or n_keys
    lo = 1 << 20
    target = b"\xff" * 20  # no hit

    # Warm
    python_scan(lo, lo + warm_keys - 1, target)

    # Peak: several short bursts
    peaks: list[float] = []
    burst = max(100, n_keys // 10)
    for i in range(5):
        a = lo + warm_keys + i * burst
        _, k, el = python_scan(a, a + burst - 1, target)
        if el > 0:
            peaks.append(k / el)
    R_peak = max(peaks) if peaks else 0.0

    # Sustained
    a = lo + warm_keys + 5 * burst
    rates: list[float] = []

    def prog(k: int, el: float) -> None:
        if el > 0:
            rates.append(k / el)

    _, k, el = python_scan(a, a + sustained_keys - 1, target, on_progress=prog)
    R_sust = k / el if el > 0 else 0.0
    # Prefer late-window rate if available
    if len(rates) >= 2:
        R_sust = rates[-1]

    return ThroughputReport(
        R_peak=R_peak,
        R_sustained=R_sust,
        keys_tested=k,
        wall_s=el,
        device=f"python_cpu/{platform.processor() or platform.machine()}",
        notes="reference only — not a launch R",
        extras={"peak_bursts": peaks, "compressed_only": True, "base58_per_candidate": False},
    )


def feasibility_from_R(R: float) -> dict[str, Any]:
    """Replace illustrative P71-S02 rows using measured R."""
    rows = {}
    for name, T in [("1_day", 86400.0), ("30_days", 30 * 86400.0), ("1_year", 365.25 * 86400.0)]:
        S_max = 2 * R * T
        b_cut = 70 - math.log2(S_max) if S_max > 0 else float("inf")
        rows[name] = {
            "T_s": T,
            "S_max": S_max,
            "S_max_log2": math.log2(S_max) if S_max > 0 else None,
            "b_cut": b_cut,
            "T_mean_full_band_s": (2**70) / (2 * R) if R > 0 else None,
            "T_worst_full_band_s": (2**70) / R if R > 0 else None,
        }
    full_mean_y = ((2**70) / (2 * R)) / (86400 * 365.25) if R > 0 else None
    return {
        "formula": {
            "T_mean": "|S|/(2R)",
            "T_worst": "|S|/R",
            "P_hit": "min(1, R*t/|S|)",
            "b_cut": "70 - log2(2*R*T)",
            "S_max": "2*R*T",
        },
        "R_used": R,
        "uncut_S": 2**70,
        "full_band_mean_years": full_mean_y,
        "budgets": rows,
        "pool_external_not_used": {
            "note": "btcpuzzle.info ~45.9e9 current / ~1.16e12 high — not local R",
        },
    }


def boundary_cases() -> list[tuple[str, int]]:
    """Inclusive endpoints + neighbors (for path correctness, not P71 search)."""
    return [
        ("band_lo", P71_D_MIN),
        ("band_lo_plus_1", P71_D_MIN + 1),
        ("band_hi", P71_D_MAX),
        ("band_hi_minus_1", P71_D_MAX - 1),
    ]


def run_correctness_python() -> list[EquivalenceResult]:
    """Self-equivalence of reference path + S01 targets + boundaries."""
    out: list[EquivalenceResult] = []
    keys = load_keys()

    # Solved ladder from S01
    for n in [1, 5, 10, 20, 30, 40, 50, 65, 70]:
        d = keys[n]
        h = hash160_path_locked(d)
        # tiny inclusive window — clamp so d>=1 (secp private keys)
        lo = max(1, d - 2)
        hi = d + 2
        hit, _, _ = python_scan(lo, hi, h)
        out.append(
            EquivalenceResult(
                check=f"solved_n{n}",
                status="PASS" if hit == d else "FAIL",
                python_d=d,
                native_d=hit,  # python backend acting as native for protocol dry-run
                notes=address_p2pkh(h),
            )
        )

    # Boundaries: verify hash160 is well-defined (not that they match P71)
    for name, d in boundary_cases():
        h = hash160_path_locked(d)
        ok = len(h) == 20 and (P71_D_MIN <= d <= P71_D_MAX)
        out.append(
            EquivalenceResult(
                check=f"boundary_{name}",
                status="PASS" if ok else "FAIL",
                python_d=d,
                native_d=d,
                notes=h.hex()[:16] + "...",
            )
        )

    # Inclusive endpoint identity
    assert P71_D_MIN == P71_LO
    assert P71_D_MAX == P71_HI - 1
    out.append(
        EquivalenceResult(
            check="inclusive_endpoints",
            status="PASS",
            python_d=P71_D_MIN,
            native_d=P71_D_MAX,
            notes=f"[{P71_D_MIN}, {P71_D_MAX}]",
        )
    )

    # Partitions
    parts = partition_ranges(P71_D_MIN, P71_D_MAX + 1, 8)  # half-open helper
    ok_p = verify_partitions(P71_D_MIN, P71_D_MAX + 1, 8) and parts[0][0] == P71_D_MIN and parts[-1][1] - 1 == P71_D_MAX
    out.append(
        EquivalenceResult(
            check="partitions_8",
            status="PASS" if ok_p else "FAIL",
            python_d=None,
            native_d=None,
            notes=f"n_parts=8 covered={ok_p}",
        )
    )

    # P71 target identity (address ↔ h160), not a key find
    ok_id = address_p2pkh(P71_H160) == P71_ADDR
    out.append(
        EquivalenceResult(
            check="p71_target_identity",
            status="PASS" if ok_id else "FAIL",
            python_d=None,
            native_d=None,
            notes=P71_ADDR,
        )
    )
    return out


def run_checkpoint_python() -> EquivalenceResult:
    base = 1 << 18
    d_true = base + 7777
    target = hash160_path_locked(d_true)
    ck = OUT_DIR / "s03_checkpoint.json"
    # phase1: stop before hit
    hit1, keys1, _ = python_scan(base, base + 5000, target)
    # manual checkpoint state
    ck.write_text(
        json.dumps({"next_d": base + 5001, "target": target.hex(), "keys": keys1}),
        encoding="utf-8",
    )
    # phase2: resume from checkpoint
    state = json.loads(ck.read_text(encoding="utf-8"))
    hit2, _, _ = python_scan(int(state["next_d"]), base + 20000, target)
    ok = hit1 is None and hit2 == d_true
    return EquivalenceResult(
        check="checkpoint_resume",
        status="PASS" if ok else "FAIL",
        python_d=d_true,
        native_d=hit2,
        notes=f"phase1_hit={hit1}",
    )


def try_external_scanner(cmd_template: str, lo: int, hi: int, target_h160: str) -> dict[str, Any]:
    """Invoke external scanner. Template may include {lo} {hi} {h160} {out}."""
    out_file = OUT_DIR / "native_scan_out.txt"
    cmd = cmd_template.format(lo=lo, hi=hi, h160=target_h160, out=out_file)
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    elapsed = time.perf_counter() - t0
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "elapsed_s": elapsed,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
        "out_file": str(out_file) if out_file.is_file() else None,
    }


def try_native_backend_bridge(
    *,
    backend: str,
    binary: Path,
    puzzle_n: int,
) -> dict[str, Any]:
    """P71-S03 calibration via p71_native_backend --expect-private.

    Puzzle 1 locked window: d=1, S=[1,32] inclusive.
    """
    from dataclasses import asdict as _asdict

    from p71_native_backend import address_p2pkh, hash160_compressed, run_native

    keys = load_keys()
    if puzzle_n not in keys:
        return {"status": "FAIL", "error": f"no key for puzzle {puzzle_n}"}
    d = keys[puzzle_n]
    addr = address_p2pkh(hash160_compressed(d))
    # Locked Puzzle-1 calibration set; other puzzles use a tight window around d
    if puzzle_n == 1:
        assert d == 1
        lo, hi = 1, 32
    else:
        lo = max(1, d - 8)
        hi = d + 8
    work = OUT_DIR / "native_calib"
    work.mkdir(parents=True, exist_ok=True)
    result = run_native(
        backend=backend,
        binary=binary,
        target=addr,
        start=lo,
        end=hi,
        seconds=None,  # known-hit run: terminate normally on find
        threads=4,
        checkpoint=None,
        found_file=work / f"found_n{puzzle_n}.txt",
        expect_private=d,
        work_dir=work,
    )
    out_path = work / f"s03_calib_n{puzzle_n}.json"

    expected_seen = any(v["d"] == d for v in result.verified_hits) or any(
        int(x, 16) == d for x in result.found_private_keys
    )
    expected_verified = any(v["d"] == d and v["accepted"] for v in result.verified_hits)
    inside = all(lo <= v["d"] <= hi for v in result.verified_hits) if result.verified_hits else expected_verified
    hash160_ok = expected_verified
    all_verified = len(result.rejected_hits) == 0 and (
        (not result.found_private_keys) or len(result.verified_hits) > 0
    )
    # Stricter: every reported priv that parses must be accepted or explicitly rejected logged
    all_reported_hits_verified = (
        len(result.rejected_hits) == 0
        and expected_verified
        and all(v.get("accepted") for v in result.verified_hits)
    )

    gate = {
        "expected_seen": expected_seen or expected_verified,
        "expected_verified": expected_verified,
        "inside_requested_range": bool(inside) and expected_verified,
        "hash160_match": hash160_ok,
        "all_reported_hits_verified": all_reported_hits_verified,
        "calibration_range": {"start": lo, "end": hi, "inclusive": True},
        "allow_outside_p71_band": True,
        "throughput_timeout_is_failure": False,
        "known_hit_timeout_is_failure": True,
    }
    payload = _asdict(result)
    payload["s03_calibration_gate"] = gate
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    passed = all(
        [
            gate["expected_seen"],
            gate["expected_verified"],
            gate["inside_requested_range"],
            gate["hash160_match"],
            gate["all_reported_hits_verified"],
        ]
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "puzzle": puzzle_n,
        "expect_d": d,
        "expect_match": result.expect_match,
        "verified_hits": result.verified_hits,
        "rejected_hits": result.rejected_hits,
        "R_peak": result.R_peak,
        "R_sustained": result.R_sustained,
        "command": result.command,
        "output": str(out_path),
        "device_notes": result.device_notes,
        "s03_calibration_gate": gate,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="P71-S03 native/GPU equivalence")
    ap.add_argument("--backend", choices=["python", "cmd", "native"], default="python")
    ap.add_argument("--scanner-cmd", type=str, default="", help="CLI template with {lo},{hi},{h160},{out}")
    ap.add_argument("--native-backend", choices=["bitcrack", "keyhunt"], default=None)
    ap.add_argument("--native-binary", type=Path, default=None)
    ap.add_argument("--calib-puzzle", type=int, default=1)
    ap.add_argument("--throughput-keys", type=int, default=5000)
    ap.add_argument("--skip-throughput", action="store_true")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("P71-S03 native/GPU scanner equivalence")
    print("path: d->[d]G->SEC->SHA256->RIPEMD160 (no per-candidate Base58)")
    print(f"band inclusive: [{P71_D_MIN}, {P71_D_MAX}]")
    print(f"backend: {args.backend}")
    print("kangaroo: False")

    results = run_correctness_python()
    for r in results:
        print(f"  {r.check}: {r.status}")

    ck = run_checkpoint_python()
    results.append(ck)
    print(f"  {ck.check}: {ck.status}")

    throughput = None
    feas = None
    if not args.skip_throughput and args.backend == "python":
        throughput = measure_throughput_python(args.throughput_keys)
        print(
            f"  throughput peak={throughput.R_peak:.1f}/s "
            f"sustained={throughput.R_sustained:.1f}/s device={throughput.device}"
        )
        feas = feasibility_from_R(throughput.R_sustained)
        print(f"  full-band mean years @ this R: {feas['full_band_mean_years']:.3e}")

    external = None
    native_calib = None
    if args.backend == "cmd":
        if not args.scanner_cmd:
            print("ERROR: --scanner-cmd required for cmd backend")
            return 2
        external = try_external_scanner(args.scanner_cmd, 1, 100, P71_H160.hex())
        print(f"  external returncode={external['returncode']}")
    elif args.backend == "native":
        if not args.native_backend or not args.native_binary:
            print("ERROR: --native-backend and --native-binary required")
            return 2
        if not args.native_binary.is_file():
            print(f"ERROR: binary not found: {args.native_binary}")
            return 2
        native_calib = try_native_backend_bridge(
            backend=args.native_backend,
            binary=args.native_binary,
            puzzle_n=args.calib_puzzle,
        )
        print(f"  native_calib: {native_calib['status']} expect_match={native_calib.get('expect_match')}")
        if native_calib.get("R_sustained"):
            feas = feasibility_from_R(float(native_calib["R_sustained"]))

    all_pass = all(r.status == "PASS" for r in results)
    native_eq = None if native_calib is None else native_calib.get("status") == "PASS"
    payload = {
        "candidate_id": "P71-S-20260710-03",
        "status": (
            "native_pass" if native_eq else ("python_protocol_pass" if all_pass else "FAIL")
        ),
        "native_gpu_evaluated": native_calib is not None,
        "promotion_gate": {
            "native_eq_python_eq_known": native_eq,
            "python_self_checks": all_pass,
            "R_reproducible": None,
            "scanner_ready": bool(native_eq),
            "launch_depends_on": "measured GPU R or proved |S| cut",
        },
        "band_inclusive": {"min": P71_D_MIN, "max": P71_D_MAX},
        "path": "HASH160(compressed SEC([d]G)); Base58 only after hit",
        "correctness": [asdict(r) for r in results],
        "throughput": asdict(throughput) if throughput else None,
        "feasibility_from_sustained_R": feas,
        "external": external,
        "native_calibration": native_calib,
        "pool_figures_not_local": {"current_Bkeys_s": 45.9, "high_Tkeys_s": 1160},
        "frozen_zero_bit_lanes": ["shelf2", "GAP", "barcode", "creator-pattern"],
    }
    out = OUT_DIR / "P71_S03_results.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    if native_eq:
        print("STATUS: Native equivalence PASS for calibration target.")
    else:
        print(
            "STATUS: Scanner protocol ready on Python; "
            "Puzzle 71 launch depends on measured GPU throughput or proved candidate-set reduction."
        )
    if args.backend == "native":
        return 0 if native_eq and all_pass else 1
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
