#!/usr/bin/env python3
"""S-01 — Exact interval-DLP calibration (Pollard kangaroo).

Same code path as P135:
  L = 2**(n-1)
  Q = P - [L]G
  recover u in [0, L) with Q = [u]G
  d = L + u
  verify [d]G == P

RFC6979 is a final batch-scoped validator only — not part of the search.
Once [d]G = P, d is unique mod N; RFC6979 confirms signer model only.

Boundaries (locked 2026-07-10):
  * Do NOT claim negation-symmetry acceleration. Jump index uses x only;
    DP identity retains y-parity to avoid false P↔-P collisions. That is
    correctness hygiene, not quotient-by-negation speedup.
  * DP density 2^{-b}: expected post-merge detection delay ~2^b steps;
    memory falls by the same factor. Not an extra 2^{b/2} workload factor.
  * Python harness measures correctness + op-count scaling, not P135 runtime.
  * Promotion order: tiny-interval oracle → 35 → 40 → 45 → compiled native.

No creator-pattern heuristics. No claimed reduction beyond the known interval.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ecdsa import SECP256k1, rfc6979
from ecdsa.ellipticcurve import INFINITY, Point

CURVE = SECP256k1.curve
G = SECP256k1.generator
N = int(SECP256k1.order)

KEYS_CSV = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
NONCE_PANEL = Path(__file__).resolve().parent / "logs" / "SOLVED_NONCE_PANEL.json"
OUT_DIR = Path(__file__).resolve().parent / "logs" / "s01_calibration"
DEFAULT_SEED = 0x5301_CA11_B202_60710

# Hashkeys batch txid prefix (K-03 attribution). Outside this cohort, RFC6979
# is recorded as N/A — never a search constraint.
HASHKEYS_TX_PREFIX = "17e4e323"


@dataclass
class CollisionRecord:
    tame_dist: int
    wild_dist: int
    u_candidate: int
    equation_ok: bool  # tame_dist - wild_dist ≡ u (mod N) and [u]G == Q
    verify_Q: bool
    notes: str = ""


@dataclass
class RunMetrics:
    puzzle: int
    interval_bits: int
    expected_ops_log2: float
    ops: int
    elapsed_s: float
    distinguished_points: int
    collisions: int
    restarts: int
    recovered_u: int | None
    recovered_d: int | None
    verify_Q: bool
    verify_pubkey: bool
    verify_collision_eq: bool
    verify_rfc6979: bool | None  # None = N/A (not hashkeys batch / no panel)
    dp_bits: int
    n_tame: int
    n_wild: int
    seed: int
    checkpoint_resumed: bool
    status: str
    collision_records: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""
    # Explicit: no negation-accel / no DP-sqrt claim in this reference path
    negation_accel_claimed: bool = False
    dp_model: str = "density_2^{-b}; post-merge delay ~2^b; not extra 2^{b/2} workload"


class _SplitMix64:
    def __init__(self, seed: int) -> None:
        self.state = seed & ((1 << 64) - 1)

    def next(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & ((1 << 64) - 1)
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & ((1 << 64) - 1)
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & ((1 << 64) - 1)
        return (z ^ (z >> 31)) & ((1 << 64) - 1)


def load_keys() -> dict[int, int]:
    keys: dict[int, int] = {}
    with KEYS_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            keys[int(row["puzzle"])] = int(row["private_key"])
    return keys


def load_nonce_panel() -> dict[int, dict[str, Any]]:
    if not NONCE_PANEL.is_file():
        return {}
    rows = json.loads(NONCE_PANEL.read_text(encoding="utf-8"))
    return {int(r["puzzle"]): r for r in rows}


def point_from_priv(d: int) -> Point:
    return d * G


def band_floor_Q(P: Point, L: int) -> Point:
    """Exact P135 / calibration translation: Q = P - [L]G."""
    return P + ((-L) % N) * G


def jump_index(x: int, n_jumps: int) -> int:
    """Deterministic jump from x.

    Uses x only so P and -P select the same jump index. This is NOT claimed
    as quotient-by-negation acceleration — DP identity still keeps y-parity.
    """
    h = hashlib.sha256(x.to_bytes(32, "big")).digest()
    return int.from_bytes(h[:4], "big") % n_jumps


def is_distinguished(x: int, dp_mask: int) -> bool:
    """DP predicate: lowest b bits of x are zero (density 2^{-b})."""
    return (x & dp_mask) == 0


def build_jumps(seed: int, mean_bits: int, n_jumps: int = 32) -> tuple[list[int], list[Point]]:
    distances: list[int] = []
    points: list[Point] = []
    rng = _SplitMix64(seed ^ 0x4A55_4D50)
    lo = max(1, mean_bits - 2)
    hi = mean_bits + 2
    for _ in range(n_jumps):
        bits = lo + (rng.next() % (hi - lo + 1))
        j = (1 << bits) + (rng.next() & ((1 << max(bits - 1, 0)) - 1))
        j = max(1, j)
        distances.append(j)
        points.append(j * G)
    return distances, points


def partition_starts(L: int, n_workers: int, herd: str, seed: int) -> list[int]:
    """Deterministic starts. Index-space partitions of [0,L) have no gaps/overlaps.

    Tame herd: starts near mid-interval within each partition (classic kangaroo).
    Wild herd: small offsets from Q (partition of a narrow band near 0).
    """
    assert n_workers >= 1
    rng = _SplitMix64(seed ^ (0x5441 if herd == "tame" else 0x5749))
    base = L // n_workers
    rem = L % n_workers
    starts: list[int] = []
    cursor = 0
    for i in range(n_workers):
        width = base + (1 if i < rem else 0)
        if herd == "tame":
            if width == 0:
                starts.append(0)
            else:
                mid = cursor + width // 2
                jitter = rng.next() % max(width, 1)
                starts.append((mid + jitter) % L if L else 0)
        else:
            # Wild: small deterministic offsets so walks begin near Q
            span = max(n_workers * 8, 1)
            starts.append((i + (rng.next() % span)) % L if L else 0)
        cursor += width
    assert cursor == L or L == 0
    return starts


def verify_partitions(L: int, n_workers: int) -> bool:
    base = L // n_workers
    rem = L % n_workers
    return sum(base + (1 if i < rem else 0) for i in range(n_workers)) == L


def rfc6979_lock(d: int, z: int, r: int, s: int) -> bool:
    """Batch-scoped secondary validator — never part of kangaroo search."""
    z_bytes = z.to_bytes(32, "big")
    k = rfc6979.generate_k(N, d, hashlib.sha256, z_bytes)
    for kk in (k, (N - k) % N):
        if (s * kk - z - r * d) % N == 0:
            return True
    return False


def check_collision_equation(
    tame_dist: int, wild_dist: int, Q: Point, L: int
) -> CollisionRecord:
    """Every reported cross-herd collision must satisfy:
        u = (tame_dist - wild_dist) mod N
        [u]G = Q
    and (for puzzle path) [L+u]G = P is checked by the caller.
    """
    u = (tame_dist - wild_dist) % N
    eq_ok = (tame_dist - wild_dist - u) % N == 0
    verify_Q = 0 <= u < L and (u * G) == Q
    return CollisionRecord(
        tame_dist=tame_dist,
        wild_dist=wild_dist,
        u_candidate=u,
        equation_ok=eq_ok and verify_Q,
        verify_Q=verify_Q,
        notes="" if verify_Q else "u out of range or [u]G != Q",
    )


def kangaroo_solve(
    Q: Point,
    L: int,
    *,
    seed: int = DEFAULT_SEED,
    n_tame: int = 4,
    n_wild: int = 4,
    dp_bits: int | None = None,
    max_ops: int | None = None,
    checkpoint_path: Path | None = None,
    checkpoint_every: int = 0,
    resume: bool = False,
) -> tuple[int | None, RunMetrics]:
    """Recover u in [0, L) with Q = [u]G.

    Distinguished points: density 2^{-b}. Expected delay after walks merge is
    ~2^b steps; memory scales with density. This is NOT modeled as an extra
    2^{b/2} multiplicative workload on top of ~sqrt(L).
    """
    interval_bits = (L - 1).bit_length() if L > 0 else 0
    expected = 2.0 ** (interval_bits / 2.0)

    # Choose b so expected stored DPs before ~sqrt(L) ops is manageable.
    # Workload remains ~c*sqrt(L); b only trades memory vs post-merge delay.
    if dp_bits is None:
        dp_bits = max(2, min(interval_bits // 4, int(interval_bits / 2) - 2))
        dp_bits = max(2, dp_bits)
    dp_mask = (1 << dp_bits) - 1

    mean_jump_bits = max(1, interval_bits // 2)
    jump_dist, jump_pts = build_jumps(seed, mean_jump_bits, n_jumps=32)

    if not verify_partitions(L, n_tame) or not verify_partitions(L, n_wild):
        raise RuntimeError("partition coverage failed")

    tame_starts = partition_starts(L, n_tame, "tame", seed)
    wild_starts = partition_starts(L, n_wild, "wild", seed)

    tame_pts = [s0 * G for s0 in tame_starts]
    tame_dist = list(tame_starts)
    wild_pts = [Q + s0 * G for s0 in wild_starts]
    wild_dist = list(wild_starts)

    # DP table: key -> (herd, dist). herd 0=tame, 1=wild
    dp_table: dict[str, tuple[int, int]] = {}
    ops = 0
    restarts = 0
    collisions = 0
    dp_count = 0
    resumed = False
    collision_records: list[CollisionRecord] = []
    recovered_u: int | None = None
    t0 = time.perf_counter()

    if resume and checkpoint_path and checkpoint_path.is_file():
        ck = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if ck.get("seed") == seed and ck.get("L") == L and ck.get("dp_bits") == dp_bits:
            ops = int(ck["ops"])
            restarts = int(ck["restarts"])
            tame_dist = [int(x) for x in ck["tame_dist"]]
            wild_dist = [int(x) for x in ck["wild_dist"]]
            tame_pts = [Point(CURVE, int(x), int(y)) for x, y in ck["tame_xy"]]
            wild_pts = [Point(CURVE, int(x), int(y)) for x, y in ck["wild_xy"]]
            dp_table = {k: (int(v[0]), int(v[1])) for k, v in ck["dp_table"].items()}
            dp_count = len(dp_table)
            resumed = True

    if max_ops is None:
        max_ops = int(40 * expected) + 50_000

    def dp_key(pt: Point) -> str:
        # Retain y-parity: avoids false P↔-P DP collisions.
        # NOT a quotient-by-negation acceleration claim.
        return f"{pt.x():064x}:{'e' if (pt.y() % 2 == 0) else 'o'}"

    def record_dp(pt: Point, herd: int, dist: int) -> int | None:
        nonlocal collisions, dp_count
        if pt == INFINITY:
            return None
        if not is_distinguished(pt.x(), dp_mask):
            return None
        key = dp_key(pt)
        if key not in dp_table:
            dp_table[key] = (herd, dist)
            dp_count += 1
            return None
        other_herd, other_dist = dp_table[key]
        if other_herd == herd:
            return None
        collisions += 1
        if herd == 0:
            td, wd = dist, other_dist
        else:
            td, wd = other_dist, dist
        rec = check_collision_equation(td, wd, Q, L)
        collision_records.append(rec)
        if rec.equation_ok:
            return rec.u_candidate
        return None

    def step(pts: list[Point], dists: list[int], herd: int) -> int | None:
        nonlocal ops
        for i in range(len(pts)):
            pt = pts[i]
            if pt == INFINITY:
                continue
            j = jump_index(pt.x(), len(jump_pts))
            pts[i] = pt + jump_pts[j]
            dists[i] = (dists[i] + jump_dist[j]) % N
            ops += 1
            hit = record_dp(pts[i], herd, dists[i])
            if hit is not None:
                return hit
        return None

    next_restart_at = int(12 * expected) + 2000
    next_progress = int(max(expected, 100_000))
    while ops < max_ops and recovered_u is None:
        hit = step(tame_pts, tame_dist, 0)
        if hit is not None:
            recovered_u = hit
            break
        hit = step(wild_pts, wild_dist, 1)
        if hit is not None:
            recovered_u = hit
            break

        if ops >= next_progress:
            print(
                f"    ... ops={ops} DPs={dp_count} coll={collisions} "
                f"restarts={restarts} (~{ops/expected:.2f}x sqrt(L))",
                flush=True,
            )
            next_progress = ops + int(max(expected, 100_000))

        if ops >= next_restart_at and collisions == 0:
            restarts += 1
            next_restart_at = ops + int(12 * expected) + 2000
            tame_starts = partition_starts(L, n_tame, "tame", seed ^ (restarts << 16))
            wild_starts = partition_starts(L, n_wild, "wild", seed ^ (restarts << 16) ^ 1)
            tame_pts = [s * G for s in tame_starts]
            tame_dist = list(tame_starts)
            wild_pts = [Q + s * G for s in wild_starts]
            wild_dist = list(wild_starts)
            # Keep DP table across soft restarts (still valid points)

        if (
            checkpoint_every
            and checkpoint_path
            and ops > 0
            and ops % checkpoint_every == 0
        ):
            _save_checkpoint(
                checkpoint_path,
                seed,
                L,
                dp_bits,
                ops,
                restarts,
                tame_dist,
                wild_dist,
                tame_pts,
                wild_pts,
                dp_table,
            )

    elapsed = time.perf_counter() - t0
    verify_Q = recovered_u is not None and (recovered_u * G) == Q
    verify_coll = bool(collision_records) and all(r.equation_ok for r in collision_records if r.verify_Q)
    # Accept: the successful collision must have equation_ok
    if recovered_u is not None:
        verify_coll = any(r.equation_ok and r.u_candidate == recovered_u for r in collision_records)

    metrics = RunMetrics(
        puzzle=0,
        interval_bits=interval_bits,
        expected_ops_log2=math.log2(expected) if expected > 0 else 0.0,
        ops=ops,
        elapsed_s=elapsed,
        distinguished_points=dp_count,
        collisions=collisions,
        restarts=restarts,
        recovered_u=recovered_u,
        recovered_d=None,
        verify_Q=verify_Q,
        verify_pubkey=False,
        verify_collision_eq=verify_coll,
        verify_rfc6979=None,
        dp_bits=dp_bits,
        n_tame=n_tame,
        n_wild=n_wild,
        seed=seed,
        checkpoint_resumed=resumed,
        status="recovered" if recovered_u is not None else "budget_exhausted",
        collision_records=[asdict(r) for r in collision_records],
    )
    return recovered_u, metrics


def _save_checkpoint(
    path: Path,
    seed: int,
    L: int,
    dp_bits: int,
    ops: int,
    restarts: int,
    tame_dist: list[int],
    wild_dist: list[int],
    tame_pts: list[Point],
    wild_pts: list[Point],
    dp_table: dict[str, tuple[int, int]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "seed": seed,
                "L": L,
                "dp_bits": dp_bits,
                "ops": ops,
                "restarts": restarts,
                "tame_dist": tame_dist,
                "wild_dist": wild_dist,
                "tame_xy": [(int(p.x()), int(p.y())) for p in tame_pts],
                "wild_xy": [(int(p.x()), int(p.y())) for p in wild_pts],
                "dp_table": {k: list(v) for k, v in dp_table.items()},
            }
        ),
        encoding="utf-8",
    )


def run_tiny_oracle(
    widths: list[int],
    trials_per_width: int,
    *,
    seed: int = DEFAULT_SEED,
    n_tame: int = 2,
    n_wild: int = 2,
) -> dict[str, Any]:
    """Exhaustive correctness oracle on artificial intervals.

    For each width W in {2^16, 2^20, 2^24, ...}: choose random u in [0,W),
    form Q=[u]G, require recovery of every trial. Catches walk / distance /
    restart / checkpoint bugs before the solved-puzzle ladder.
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "mode": "tiny_interval_oracle",
        "negation_accel_claimed": False,
        "dp_model": "density_2^{-b}; post-merge delay ~2^b; not extra 2^{b/2}",
        "widths": [],
        "all_pass": True,
    }
    rng = _SplitMix64(seed ^ 0x0AACE001)

    for wbits in widths:
        W = 1 << wbits
        expected = 2.0 ** (wbits / 2.0)
        max_ops = int(60 * expected) + 100_000
        trials = []
        fails = 0
        print(f"oracle width=2^{wbits} trials={trials_per_width} max_ops={max_ops}")
        for t in range(trials_per_width):
            u_true = rng.next() % W
            Q = u_true * G
            trial_seed = seed ^ (wbits << 24) ^ (t << 8) ^ u_true
            u_hat, m = kangaroo_solve(
                Q,
                W,
                seed=trial_seed & ((1 << 64) - 1),
                n_tame=n_tame,
                n_wild=n_wild,
                max_ops=max_ops,
            )
            ok = (
                u_hat == u_true
                and m.verify_Q
                and m.verify_collision_eq
                and (u_hat is not None and (u_hat * G) == Q)
            )
            if not ok:
                fails += 1
                report["all_pass"] = False
            trials.append(
                {
                    "trial": t,
                    "u_true": u_true,
                    "u_hat": u_hat,
                    "ok": ok,
                    "ops": m.ops,
                    "elapsed_s": m.elapsed_s,
                    "DPs": m.distinguished_points,
                    "collisions": m.collisions,
                    "restarts": m.restarts,
                    "verify_Q": m.verify_Q,
                    "verify_collision_eq": m.verify_collision_eq,
                    "expected_ops": expected,
                    "ratio": m.ops / expected if expected else None,
                }
            )
            status = "PASS" if ok else "FAIL"
            print(
                f"  t={t} {status} u={u_true} ops={m.ops} "
                f"ratio={m.ops/expected:.2f} coll={m.collisions} "
                f"eq={m.verify_collision_eq}"
            )
        block = {
            "width_bits": wbits,
            "width": W,
            "trials": trials_per_width,
            "fails": fails,
            "pass": fails == 0,
            "expected_ops": expected,
            "mean_ops": sum(x["ops"] for x in trials) / len(trials),
            "mean_ratio": sum(x["ratio"] for x in trials if x["ratio"]) / len(trials),
            "trials_detail": trials,
        }
        report["widths"].append(block)
        print(
            f"  width 2^{wbits}: {'PASS' if fails == 0 else 'FAIL'} "
            f"({trials_per_width - fails}/{trials_per_width}) "
            f"mean_ops={block['mean_ops']:.0f} mean_ratio={block['mean_ratio']:.2f}"
        )

    out_path = OUT_DIR / "S01_oracle_results.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {out_path}")
    return report


def calibrate_puzzle(
    n: int,
    d_true: int,
    nonce_row: dict[str, Any] | None,
    *,
    seed: int = DEFAULT_SEED,
    n_tame: int = 4,
    n_wild: int = 4,
    max_ops: int | None = None,
    checkpoint: bool = False,
) -> RunMetrics:
    """Exact P135 code path on solved puzzle n (no secret hints in search)."""
    L = 1 << (n - 1)
    assert L <= d_true < (1 << n), f"d not in puzzle-{n} band"

    # Public point only — in production P comes from the puzzle pubkey.
    P = point_from_priv(d_true)
    Q = band_floor_Q(P, L)
    u_true = d_true - L
    assert (u_true * G) == Q

    ck_path = OUT_DIR / f"p{n}_checkpoint.json" if checkpoint else None
    u_hat, metrics = kangaroo_solve(
        Q,
        L,
        seed=seed,
        n_tame=n_tame,
        n_wild=n_wild,
        max_ops=max_ops,
        checkpoint_path=ck_path,
        checkpoint_every=1_000_000 if checkpoint else 0,
    )
    metrics.puzzle = n

    if u_hat is None:
        metrics.status = "FAIL_not_recovered"
        metrics.notes = f"u_true_bits={u_true.bit_length()}"
        return metrics

    d_hat = L + u_hat
    metrics.recovered_u = u_hat
    metrics.recovered_d = d_hat
    metrics.verify_Q = (u_hat * G) == Q
    metrics.verify_pubkey = point_from_priv(d_hat) == P and d_hat == d_true

    # RFC6979: final batch-scoped lock only. Does not narrow the interval.
    # Outside hashkeys cohort → None (N/A), never a FAIL of the pubkey gate.
    if nonce_row is not None and str(nonce_row.get("txid", "")).startswith(HASHKEYS_TX_PREFIX):
        metrics.verify_rfc6979 = rfc6979_lock(
            d_hat, int(nonce_row["z"]), int(nonce_row["r"]), int(nonce_row["s"])
        )
    else:
        metrics.verify_rfc6979 = None
        metrics.notes = (metrics.notes + "; " if metrics.notes else "") + (
            "rfc6979 N/A (not hashkeys batch); pubkey gate is decisive"
        )

    if metrics.verify_pubkey and metrics.verify_Q and metrics.verify_collision_eq:
        metrics.status = "PASS"
    else:
        metrics.status = "FAIL_verify"
    return metrics


def scaling_check(rows: list[RunMetrics]) -> dict[str, Any]:
    points = []
    for r in rows:
        if r.ops <= 0 or r.status != "PASS":
            continue
        exp = 2.0 ** ((r.puzzle - 1) / 2.0)
        points.append(
            {
                "n": r.puzzle,
                "ops": r.ops,
                "expected_sqrt": exp,
                "ratio_ops_over_expected": r.ops / exp,
                "log2_ops": math.log2(r.ops),
                "log2_expected": (r.puzzle - 1) / 2.0,
            }
        )
    return {
        "model": "ops ~ c * 2**((n-1)/2)  [c = O(1)–O(10) typical; not P135 wall-clock]",
        "p135_ops_order": "2**67 ≈ 1.48e20 group ops before constant-factor improvements",
        "points": points,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="S-01 range-DLP kangaroo calibration")
    ap.add_argument(
        "--mode",
        choices=["oracle", "ladder", "both"],
        default="oracle",
        help="oracle first (default); ladder only after oracle passes",
    )
    ap.add_argument(
        "--oracle-widths",
        type=int,
        nargs="+",
        default=[16, 20, 24],
        help="log2 interval widths for tiny oracle",
    )
    ap.add_argument("--oracle-trials", type=int, default=8)
    ap.add_argument(
        "--ladder",
        type=int,
        nargs="+",
        default=[35, 40, 45],
    )
    ap.add_argument("--seed", type=lambda x: int(x, 0), default=DEFAULT_SEED)
    ap.add_argument("--tame", type=int, default=4)
    ap.add_argument("--wild", type=int, default=4)
    ap.add_argument("--checkpoint", action="store_true")
    ap.add_argument("--max-ops-factor", type=float, default=40.0)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("S-01 Range-DLP calibration")
    print("negation_accel_claimed=False")
    print("dp_model: density 2^{-b}; post-merge delay ~2^b; NOT extra 2^{b/2} workload")
    print("python_role: correctness + op-count scaling (not P135 runtime model)")
    print(f"seed=0x{args.seed:x}")
    print("-" * 72)

    oracle_ok = True
    if args.mode in ("oracle", "both"):
        # Fewer workers for tiny intervals
        report = run_tiny_oracle(
            args.oracle_widths,
            args.oracle_trials,
            seed=args.seed,
            n_tame=min(2, args.tame),
            n_wild=min(2, args.wild),
        )
        oracle_ok = bool(report["all_pass"])
        if not oracle_ok:
            print("ORACLE FAILED — do not treat ladder output as evidence")
            return 2
        print("ORACLE PASS — ladder may proceed")
        print("-" * 72)

    if args.mode == "oracle":
        return 0 if oracle_ok else 2

    if not oracle_ok:
        return 2

    keys = load_keys()
    panel = load_nonce_panel()
    results: list[RunMetrics] = []

    for n in args.ladder:
        if n not in keys:
            print(f"n={n}: SKIP (no key)")
            continue
        expected = 2.0 ** ((n - 1) / 2.0)
        max_ops = int(args.max_ops_factor * expected) + 50_000
        print(f"n={n}: L=2^{n-1} expected~2^{((n-1)/2):.1f} max_ops={max_ops}")
        m = calibrate_puzzle(
            n,
            keys[n],
            panel.get(n),
            seed=args.seed,
            n_tame=args.tame,
            n_wild=args.wild,
            max_ops=max_ops,
            checkpoint=args.checkpoint,
        )
        results.append(m)
        print(
            f"  status={m.status} ops={m.ops} time={m.elapsed_s:.2f}s "
            f"DPs={m.distinguished_points} coll={m.collisions} restarts={m.restarts} "
            f"Q={m.verify_Q} pub={m.verify_pubkey} eq={m.verify_collision_eq} "
            f"rfc6979={m.verify_rfc6979}"
        )

    scaling = scaling_check(results)
    out = {
        "candidate_id": "S-20260710-01",
        "engine": "pollard_kangaroo_python_reference",
        "negation_accel_claimed": False,
        "glv": "not_enabled",
        "dp_model": "density_2^{-b}; post-merge delay ~2^b; not extra 2^{b/2} workload",
        "python_role": "correctness_and_opcount_scaling_not_p135_runtime",
        "p135_formulation": "Q=P-[2**(n-1)]G; u in [0,2**(n-1))",
        "p135_expected_ops_order": "2**67 ≈ 1.48e20",
        "rfc6979": "batch-scoped final validator only; does not narrow interval",
        "seed": args.seed,
        "results": [asdict(r) for r in results],
        "scaling": scaling,
        "promotion_gate": {
            "oracle_required_first": True,
            "all_recovered": all(r.status == "PASS" for r in results) and len(results) > 0,
            "collision_equations_ok": all(r.verify_collision_eq for r in results if r.status == "PASS"),
            "partitions_no_gap_overlap": True,
            "cpu_gpu_identical": None,
            "next": "compiled native JeanLucPons Kangaroo after 35/40/45 PASS",
        },
    }
    out_path = OUT_DIR / "S01_calibration_results.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("-" * 72)
    print(f"wrote {out_path}")
    print(json.dumps(scaling, indent=2))
    return 0 if out["promotion_gate"]["all_recovered"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
