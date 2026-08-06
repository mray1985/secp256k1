#!/usr/bin/env python3
"""S-02 — Native Kangaroo equivalence and throughput.

Separate from S-01 (correctness reference). Uses the same band-floor target:

  L = 2**(n-1)
  Q = P_n - [L]G
  recover u in [0, L) with Q = [u]G

Locked before evaluation — see logs/prereg/S-20260710-02_native_kangaroo_equivalence.md

Modes:
  --prepare          Write native infiles + Python reference scalars (no native run)
  --python-baseline  Run Python reference once per (n, seed) for comparison table
  --native           Run JeanLucPons Kangaroo (requires built binary)
  --aggregate        Summarize C_i median / range / p90 from results JSON

Operation metrics:
  * python_ops  — S-01 harness step counter
  * native_count — JeanLuc stdout "Count 2^..." at termination (separate definition)
  Treat as identical only after demonstrated equivalence on shared trials.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import re
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ecdsa import SECP256k1
from ecdsa.ellipticcurve import Point

from s01_range_dlp_calibration import (
    DEFAULT_SEED,
    band_floor_Q,
    calibrate_puzzle,
    check_collision_equation,
    kangaroo_solve,
    load_keys,
    load_nonce_panel,
    point_from_priv,
)

CURVE = SECP256k1.curve
G = SECP256k1.generator
N = int(SECP256k1.order)

ROOT = Path(__file__).resolve().parent
KANGAROO_DIR = ROOT / "Kangaroo"
KANGAROO_EXE_CANDIDATES = [
    KANGAROO_DIR / "Kangaroo.exe",
    KANGAROO_DIR / "x64" / "Release" / "Kangaroo.exe",
    KANGAROO_DIR / "VC_CUDA102" / "x64" / "Release" / "Kangaroo.exe",
    KANGAROO_DIR / "VC_CUDA10" / "x64" / "Release" / "Kangaroo.exe",
    KANGAROO_DIR / "VC_CUDA8" / "x64" / "Release" / "Kangaroo.exe",
    KANGAROO_DIR / "kangaroo",
]

OUT_DIR = ROOT / "logs" / "s02_native"
INFILE_DIR = OUT_DIR / "infiles"
RESULTS_PATH = OUT_DIR / "S02_results.json"

LADDER_DEFAULT = [35, 40, 45, 50]
LADDER_CONDITIONAL = 55
SEEDS_PER_N = 10


@dataclass
class TransformedTarget:
    puzzle: int
    L: int
    u_true: int
    d_true: int
    P: Point
    Q: Point
    pub_compressed: str
    q_compressed: str


@dataclass
class RunRecord:
    puzzle: int
    seed: int
    engine: str  # "python" | "native"
    u_recovered: int | None
    u_true: int
    python_ops: int | None = None
    native_count: int | None = None
    native_count_log2: float | None = None
    C_i: float | None = None
    elapsed_s: float | None = None
    device: str = ""
    dp_bits: int | None = None
    threads: int | None = None
    kangaroo_count_log2: float | None = None
    verify_Q: bool = False
    verify_pubkey: bool = False
    match_python: bool | None = None
    match_known: bool = False
    checkpoint_test: str | None = None
    notes: str = ""
    status: str = "pending"


def find_kangaroo_exe(explicit: Path | None = None) -> Path | None:
    if explicit and explicit.is_file():
        return explicit
    # Prefer WSL-built patched binary (emits Final Count) over stock Windows exe
    preferred = [
        KANGAROO_DIR / "kangaroo",
        KANGAROO_DIR / "Kangaroo.exe",
    ] + KANGAROO_EXE_CANDIDATES
    seen: set[Path] = set()
    for p in preferred:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        if p.is_file():
            return p
    return None


def to_wsl_path(path: Path | str) -> str:
    resolved = str(Path(path).resolve())
    if len(resolved) >= 2 and resolved[1] == ":":
        return "/mnt/" + resolved[0].lower() + resolved[2:].replace("\\", "/")
    return resolved.replace("\\", "/")


def run_cmd_for_exe(exe: Path, args: list[str]) -> list[str]:
    """Windows Kangaroo.exe runs natively; Linux 'kangaroo' via WSL."""
    if exe.suffix.lower() == ".exe":
        return [str(exe), *args]
    return ["wsl", "-d", "Ubuntu", "--", to_wsl_path(exe), *args]


def compress(pt: Point) -> str:
    prefix = "02" if (pt.y() % 2 == 0) else "03"
    return prefix + format(pt.x(), "064x")


def point_from_panel(row: dict[str, Any]) -> Point:
    return Point(CURVE, int(row["px"]), int(row["py"]))


def build_target(n: int, d_true: int, panel_row: dict[str, Any]) -> TransformedTarget:
    L = 1 << (n - 1)
    assert L <= d_true < (1 << n)
    P = point_from_panel(panel_row)
    Q = band_floor_Q(P, L)
    u_true = d_true - L
    assert (u_true * G) == Q
    return TransformedTarget(
        puzzle=n,
        L=L,
        u_true=u_true,
        d_true=d_true,
        P=P,
        Q=Q,
        pub_compressed=str(panel_row["pub_compressed"]),
        q_compressed=compress(Q),
    )


def write_native_infile(target: TransformedTarget, path: Path) -> None:
    """JeanLuc format: start, end (inclusive), compressed pubkey = Q."""
    path.parent.mkdir(parents=True, exist_ok=True)
    end = target.L - 1
    path.write_text(
        f"0\n{end:x}\n{target.q_compressed}\n",
        encoding="ascii",
    )


def verify_recovered(target: TransformedTarget, u: int) -> tuple[bool, bool]:
    verify_Q = (u * G) == target.Q and 0 <= u < target.L
    verify_pub = point_from_priv(target.L + u) == target.P
    return verify_Q, verify_pub


def seed_ladder(n: int, run_index: int, base: int = DEFAULT_SEED) -> int:
    return (base ^ (n << 20) ^ (run_index << 8) ^ 0x5202) & ((1 << 64) - 1)


def expected_sqrt(n: int) -> float:
    return 2.0 ** ((n - 1) / 2.0)


def C_i(ops: int, n: int) -> float:
    return ops / expected_sqrt(n)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    xs = sorted(values)
    k = (len(xs) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return xs[int(k)]
    return xs[f] * (c - k) + xs[c] * (k - f)


def summarize_C(values: list[float]) -> dict[str, float]:
    if not values:
        return {"median": float("nan"), "min": float("nan"), "max": float("nan"), "p90": float("nan")}
    return {
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "p90": percentile(values, 0.90),
        "mean": statistics.mean(values),
    }


def run_python_reference(
    target: TransformedTarget,
    seed: int,
    *,
    n_tame: int = 4,
    n_wild: int = 4,
    max_ops_factor: float = 40.0,
) -> RunRecord:
    expected = expected_sqrt(target.puzzle)
    max_ops = int(max_ops_factor * expected) + 50_000
    t0 = time.perf_counter()
    u_hat, metrics = kangaroo_solve(
        target.Q,
        target.L,
        seed=seed,
        n_tame=n_tame,
        n_wild=n_wild,
        max_ops=max_ops,
    )
    elapsed = time.perf_counter() - t0
    rec = RunRecord(
        puzzle=target.puzzle,
        seed=seed,
        engine="python",
        u_recovered=u_hat,
        u_true=target.u_true,
        python_ops=metrics.ops,
        elapsed_s=elapsed,
        device=platform.processor() or "cpu",
        dp_bits=metrics.dp_bits,
        verify_Q=metrics.verify_Q,
        verify_pubkey=False,
        match_known=u_hat == target.u_true if u_hat is not None else False,
        status="PASS" if u_hat == target.u_true and metrics.verify_Q else "FAIL",
        notes="S-01 reference path; ops=step counter",
    )
    if u_hat is not None:
        vq, vp = verify_recovered(target, u_hat)
        rec.verify_Q = vq
        rec.verify_pubkey = vp
        rec.C_i = C_i(metrics.ops, target.puzzle)
        if not (vq and vp):
            rec.status = "FAIL_verify"
    return rec


# JeanLuc output: Priv + Count / Final Count lines
_PRIV_RE = re.compile(r"Priv:\s*0x([0-9a-fA-F]+)")
_COUNT_LOG2_RE = re.compile(r"(?:Final Count|Count|Cnt) 2\^([0-9.]+)")
_KANG_LOG2_RE = re.compile(r"(?:Number of kangaroos|Kang):\s*2\^([0-9.]+)|Kang 2\^([0-9.]+)")
_DP_RE = re.compile(r"DP size:\s*(\d+)")
_THREADS_RE = re.compile(r"Number of CPU thread:\s*(\d+)")


def parse_native_output(text: str) -> dict[str, Any]:
    u: int | None = None
    m = _PRIV_RE.search(text)
    if m:
        u = int(m.group(1), 16)
    counts = [float(x) for x in _COUNT_LOG2_RE.findall(text)]
    count_log2 = counts[-1] if counts else None
    count = int(round(2 ** count_log2)) if count_log2 is not None else None
    kang_vals = []
    for a, b in _KANG_LOG2_RE.findall(text):
        kang_vals.append(float(a or b))
    dp_m = _DP_RE.search(text)
    th_m = _THREADS_RE.search(text)
    return {
        "u": u,
        "native_count": count,
        "native_count_log2": count_log2,
        "kangaroo_count_log2": kang_vals[-1] if kang_vals else None,
        "dp_bits": int(dp_m.group(1)) if dp_m else None,
        "threads_reported": int(th_m.group(1)) if th_m else None,
    }


def run_native_kangaroo(
    target: TransformedTarget,
    infile: Path,
    *,
    exe: Path,
    seed: int,
    threads: int = 4,
    dp_bits: int | None = None,
    gpu: bool = False,
    workfile: Path | None = None,
    resume_work: Path | None = None,
    work_interval: int = 60,
    timeout_s: float | None = None,
) -> RunRecord:
    out_file = OUT_DIR / f"p{target.puzzle}_s{seed}_native_out.txt"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    use_wsl = exe.suffix.lower() != ".exe"

    def path_arg(p: Path) -> str:
        return to_wsl_path(p) if use_wsl else str(p.resolve())

    arglist: list[str] = ["-t", str(threads)]
    if dp_bits is not None:
        arglist.extend(["-d", str(dp_bits)])
    if gpu:
        arglist.append("-gpu")
    if workfile:
        arglist.extend(["-w", path_arg(workfile), "-wi", str(work_interval), "-ws"])
    if resume_work:
        arglist.extend(["-i", path_arg(resume_work)])
    arglist.extend(["-o", path_arg(out_file), path_arg(infile)])
    cmd = run_cmd_for_exe(exe, arglist)

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(exe.parent),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            encoding="utf-8",
            errors="replace",
        )
        combined = proc.stdout + "\n" + proc.stderr + "\n"
        if out_file.is_file():
            combined += out_file.read_text(encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired as exc:
        elapsed = time.perf_counter() - t0
        partial = (exc.stdout or "") + "\n" + (exc.stderr or "")
        return RunRecord(
            puzzle=target.puzzle,
            seed=seed,
            engine="native",
            u_recovered=None,
            u_true=target.u_true,
            elapsed_s=elapsed,
            device="native",
            status="FAIL_timeout",
            notes=f"cmd={' '.join(cmd)}",
        )
    elapsed = time.perf_counter() - t0

    parsed = parse_native_output(combined)
    u_hat = parsed["u"]
    native_count = parsed["native_count"]
    count_log2 = parsed["native_count_log2"]

    rec = RunRecord(
        puzzle=target.puzzle,
        seed=seed,
        engine="native",
        u_recovered=u_hat,
        u_true=target.u_true,
        native_count=native_count,
        native_count_log2=count_log2,
        elapsed_s=elapsed,
        device="gpu" if gpu else "cpu",
        threads=threads,
        dp_bits=parsed["dp_bits"] if parsed["dp_bits"] is not None else dp_bits,
        kangaroo_count_log2=parsed["kangaroo_count_log2"],
        match_known=u_hat == target.u_true if u_hat is not None else False,
        status="pending",
        notes=(
            f"exit={proc.returncode}; native_count separate from python_ops"
            + ("; count_missing_fast_solve" if native_count is None else "")
        ),
    )
    if u_hat is not None:
        vq, vp = verify_recovered(target, u_hat)
        rec.verify_Q = vq
        rec.verify_pubkey = vp
        if native_count is not None:
            rec.C_i = C_i(native_count, target.puzzle)
        rec.status = "PASS" if vq and vp and rec.match_known else "FAIL"
    else:
        rec.status = "FAIL_not_recovered"
    return rec


def prepare_ladder(puzzles: list[int]) -> dict[str, Any]:
    keys = load_keys()
    panel = load_nonce_panel()
    manifest: dict[str, Any] = {"targets": [], "infiles": []}
    for n in puzzles:
        if n not in keys or n not in panel:
            print(f"n={n}: SKIP missing key/panel")
            continue
        tgt = build_target(n, keys[n], panel[n])
        infile = INFILE_DIR / f"p{n}_bandfloor_Q.txt"
        write_native_infile(tgt, infile)
        meta = {
            "puzzle": n,
            "L": tgt.L,
            "L_bits": n - 1,
            "u_true": tgt.u_true,
            "u_true_hex": f"{tgt.u_true:x}",
            "d_true": tgt.d_true,
            "q_compressed": tgt.q_compressed,
            "pub_compressed": tgt.pub_compressed,
            "infile": str(infile),
            "expected_sqrt": expected_sqrt(n),
        }
        manifest["targets"].append(meta)
        manifest["infiles"].append(str(infile))
        print(f"prepared n={n} u_true={tgt.u_true} Q={tgt.q_compressed[:20]}...")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "S02_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {path}")
    return manifest


def run_python_baseline(
    puzzles: list[int],
    seeds_per_n: int,
    *,
    base_seed: int = DEFAULT_SEED,
) -> list[RunRecord]:
    keys = load_keys()
    panel = load_nonce_panel()
    records: list[RunRecord] = []
    for n in puzzles:
        if n not in keys or n not in panel:
            continue
        tgt = build_target(n, keys[n], panel[n])
        print(f"python baseline n={n} ({seeds_per_n} seeds)")
        for i in range(seeds_per_n):
            seed = seed_ladder(n, i, base_seed)
            rec = run_python_reference(tgt, seed)
            records.append(rec)
            print(
                f"  seed={seed} status={rec.status} ops={rec.python_ops} "
                f"C={rec.C_i:.2f}" if rec.C_i else f"  seed={seed} status={rec.status}"
            )
    return records


def project_p135(C_values: dict[str, float], ops_per_s: float) -> dict[str, Any]:
    """T_135 ~ C * 2^67 / ops_per_s — range from distribution, not best run."""
    ops_67 = 2.0 ** 67
    out: dict[str, Any] = {"ops_67": ops_67, "ops_per_s": ops_per_s, "estimates_s": {}}
    for label, C in C_values.items():
        if math.isnan(C) or ops_per_s <= 0:
            continue
        T = C * ops_67 / ops_per_s
        out["estimates_s"][label] = T
        out.setdefault("estimates_human", {})[label] = {
            "seconds": T,
            "days": T / 86400,
            "years": T / (86400 * 365.25),
        }
    return out


def save_results(payload: dict[str, Any], *, merge: bool = True) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if merge and RESULTS_PATH.is_file():
        prev = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
        prev_recs = prev.get("records", [])
        new_recs = payload.get("records", [])
        # Key by (engine, puzzle, seed, checkpoint_test)
        def key(r: dict[str, Any]) -> tuple:
            return (
                r.get("engine"),
                r.get("puzzle"),
                r.get("seed"),
                r.get("checkpoint_test"),
            )
        merged = {key(r): r for r in prev_recs}
        for r in new_recs:
            merged[key(r)] = r
        payload["records"] = list(merged.values())
        # Recompute C_summary from all PASS records with C_i
        by_n: dict[int, list[float]] = {}
        for r in payload["records"]:
            if r.get("status") == "PASS" and r.get("C_i") is not None:
                by_n.setdefault(int(r["puzzle"]), []).append(float(r["C_i"]))
        payload["C_summary"] = {str(n): summarize_C(v) for n, v in sorted(by_n.items())}
    RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return RESULTS_PATH


def main() -> int:
    ap = argparse.ArgumentParser(description="S-02 native Kangaroo equivalence")
    ap.add_argument("--prepare", action="store_true", help="Write infiles + manifest")
    ap.add_argument("--python-baseline", action="store_true")
    ap.add_argument("--native", action="store_true")
    ap.add_argument("--checkpoint-test", type=int, metavar="N", help="n for checkpoint test")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--ladder", type=int, nargs="+", default=LADDER_DEFAULT)
    ap.add_argument("--seeds", type=int, default=SEEDS_PER_N)
    ap.add_argument("--seed-base", type=lambda x: int(x, 0), default=DEFAULT_SEED)
    ap.add_argument("--kangaroo-exe", type=Path, default=None)
    ap.add_argument("-t", "--threads", type=int, default=4)
    ap.add_argument("-d", "--dp-bits", type=int, default=None)
    ap.add_argument("--gpu", action="store_true")
    ap.add_argument("--ops-per-s", type=float, default=None, help="for T_135 projection")
    args = ap.parse_args()

    if not any(
        [args.prepare, args.python_baseline, args.native, args.checkpoint_test, args.aggregate]
    ):
        ap.print_help()
        return 0

    if args.prepare:
        prepare_ladder(args.ladder + ([LADDER_CONDITIONAL] if LADDER_CONDITIONAL else []))

    records: list[RunRecord] = []
    if args.python_baseline:
        records.extend(run_python_baseline(args.ladder, args.seeds, base_seed=args.seed_base))

    if args.native:
        exe = find_kangaroo_exe(args.kangaroo_exe)
        if exe is None:
            print("ERROR: Kangaroo binary not found. Build JeanLucPons Kangaroo first.")
            print("Candidates:", [str(p) for p in KANGAROO_EXE_CANDIDATES])
            return 1
        print(f"native exe: {exe}")
        keys = load_keys()
        panel = load_nonce_panel()
        for n in args.ladder:
            if n not in keys or n not in panel:
                continue
            tgt = build_target(n, keys[n], panel[n])
            infile = INFILE_DIR / f"p{n}_bandfloor_Q.txt"
            if not infile.is_file():
                write_native_infile(tgt, infile)
            print(f"native n={n} ({args.seeds} runs)")
            for i in range(args.seeds):
                seed = seed_ladder(n, i, args.seed_base)
                rec = run_native_kangaroo(
                    tgt,
                    infile,
                    exe=exe,
                    seed=seed,
                    threads=args.threads,
                    dp_bits=args.dp_bits,
                    gpu=args.gpu,
                )
                records.append(rec)
                print(f"  run={i} status={rec.status} u={rec.u_recovered} native_count={rec.native_count}")

    if args.checkpoint_test is not None:
        exe = find_kangaroo_exe(args.kangaroo_exe)
        if exe is None:
            print("ERROR: Kangaroo binary required for checkpoint test")
            return 1
        n = args.checkpoint_test
        keys = load_keys()
        panel = load_nonce_panel()
        tgt = build_target(n, keys[n], panel[n])
        infile = INFILE_DIR / f"p{n}_bandfloor_Q.txt"
        write_native_infile(tgt, infile)
        work = OUT_DIR / f"p{n}_checkpoint.work"
        print(f"checkpoint test n={n}: phase1 partial (timeout) then resume")
        # Phase 1: short timeout to force partial work save
        r1 = run_native_kangaroo(
            tgt,
            infile,
            exe=exe,
            seed=seed_ladder(n, 0),
            threads=args.threads,
            dp_bits=args.dp_bits,
            workfile=work,
            work_interval=5,
            timeout_s=30.0,
        )
        r1.checkpoint_test = "phase1_partial"
        records.append(r1)
        r2 = run_native_kangaroo(
            tgt,
            infile,
            exe=exe,
            seed=seed_ladder(n, 0),
            threads=args.threads,
            dp_bits=args.dp_bits,
            resume_work=work,
            workfile=work,
            work_interval=30,
            timeout_s=None,
        )
        r2.checkpoint_test = "phase2_resume"
        records.append(r2)
        if r1.u_recovered and r2.u_recovered:
            match = r1.u_recovered == r2.u_recovered == tgt.u_true
            print(f"checkpoint scalar match: {match}")

    if records:
        # Attach python match for native runs when baseline exists in same session
        py_by_seed: dict[tuple[int, int], int] = {}
        for r in records:
            if r.engine == "python" and r.u_recovered is not None:
                py_by_seed[(r.puzzle, r.seed)] = r.u_recovered
        for r in records:
            if r.engine == "native" and r.u_recovered is not None:
                py_u = py_by_seed.get((r.puzzle, r.seed))
                r.match_python = (r.u_recovered == py_u) if py_u is not None else None

        by_n: dict[int, list[float]] = {}
        for r in records:
            if r.C_i is not None and r.status == "PASS":
                by_n.setdefault(r.puzzle, []).append(r.C_i)

        summary = {str(n): summarize_C(v) for n, v in by_n.items()}
        payload: dict[str, Any] = {
            "candidate_id": "S-20260710-02",
            "status": "evaluated_partial" if args.native else "python_baseline_only",
            "negation_glv_claimed": False,
            "op_metrics": {
                "python": "S-01 step counter",
                "native": "JeanLuc Count from stdout — separate until proven identical",
            },
            "records": [asdict(r) for r in records],
            "C_summary": summary,
        }
        if args.ops_per_s and summary:
            # Use median C per n, then median across ns for rough band
            meds = [s["median"] for s in summary.values() if not math.isnan(s["median"])]
            p90s = [s["p90"] for s in summary.values() if not math.isnan(s["p90"])]
            if meds:
                payload["T135_projection"] = {
                    "median_C": project_p135({"median": statistics.median(meds)}, args.ops_per_s),
                    "p90_C": project_p135({"p90": statistics.median(p90s)}, args.ops_per_s)
                    if p90s
                    else None,
                    "note": "Range from distribution; not best-run C; not a feasibility claim",
                }
        path = save_results(payload)
        print(f"wrote {path}")
        if summary:
            print("C_i summary:", json.dumps(summary, indent=2))

    if args.aggregate and RESULTS_PATH.is_file():
        data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
        print(json.dumps(data.get("C_summary", {}), indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
