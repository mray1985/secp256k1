# S-20260710-01 — Exact interval-DLP calibration (PRE-REGISTERED)

**Status:** LOCKED before evaluation. Search-engine calibration — not a creator-pattern hunt.

| Field | Value |
|-------|-------|
| Candidate ID | S-20260710-01 |
| Short name | range_dlp_engine_calibration |
| Date registered | 2026-07-10 |
| Date first evaluated | 2026-07-10 |

---

## Boundary

G-03 closed invent-another-formula. Nonce lab left at RFC6979 batch attribution
(validator only). This branch is **search-engine calibration**.

## Exact P135 formulation (locked code path)

```text
L = 2^{134}
P_135 = [d]G
Q = P_135 - [L]G
u = d - L,   0 ≤ u < 2^{134}
Q = [u]G
```

Standard interval discrete log. Expected workload ~ √(2^{134}) = 2^{67} group ops
before constant-factor improvements (GLV, parallelism). Constants help; they do not
turn 2^{67} into a small search.

## Calibration path (identical code, solved puzzles)

```text
Q_n = P_n - [2^{n-1}]G
0 ≤ u_n < 2^{n-1}
```

Recover `u_n`, then `d_n = 2^{n-1} + u_n`. Verify `[d_n]G = P_n`.

## Engine requirements (locked)

* Pollard kangaroo
* deterministic interval partitioning
* distinguished points (density \(2^{-b}\); post-merge detection delay \(\sim 2^{b}\); **not** an extra \(2^{b/2}\) workload factor)
* jump index may use \(x\) only; DP identity retains \(y\)-parity — **do not claim negation-symmetry acceleration** until a true quotient-by-negation path is implemented and measured
* GLV where correctly implemented (optional; must not change correctness)
* full public-key verification for every recovered candidate
* every reported collision must satisfy \(u=\mathrm{tame}-\mathrm{wild}\) and \([u]G=Q\), then \([2^{n-1}+u]G=P_n\)
* checkpointing and reproducible worker seeds

## Promotion order (locked)

```text
random tiny-interval oracle (2^16, 2^20, 2^24)
  → puzzle 35 → 40 → 45
  → compiled native engine
```

Do not treat ladder output as evidence until the oracle passes.
Python harness = correctness + op-count scaling, **not** a P135 wall-clock model.

## RFC6979 boundary

Final batch-scoped validator only. Once \([d]G=P\), \(d\) is unique mod \(N\);
RFC6979 confirms signer model and does **not** narrow the kangaroo interval.

## Calibration ladder

Exact recoveries at increasing difficulty. Initial CPU reference ladder:

```text
n ∈ {35, 40, 45, 50}   # then 55, 60, 65 as practical with GPU/native Kangaroo
```

Record per run:

```text
group operations, elapsed time, distinguished points, collisions, restarts
```

Expected scaling ≈ √(2^{n-1}) = 2^{(n-1)/2}.

## Promotion gate (P135-ready)

1. Recovers every selected solved puzzle without secret hints
2. CPU/GPU implementations return identical keys (when both exist)
3. Partitions have no gaps or overlaps
4. Checkpoints resume reproducibly
5. Observed scaling matches expected square-root curve
6. Every hit passes `[d]G = P` and secondary batch-scoped RFC6979 validator when RSZ exists:

```text
s * RFC6979(d,z) - z - r*d ≡ 0 (mod N)
```

RFC6979 is **not** part of the search — final extra lock only.

## Ledger line

> **S-01: Range-DLP engine calibration.** Determine measured feasibility using
> solved puzzles and the exact P135 code path; no heuristics, no creator-pattern
> assumptions, and no claimed reduction beyond the known 2^{134} interval.

## Result (2026-07-10)

**Oracle:** PASS 24/24 (widths \(2^{16}, 2^{20}, 2^{24}\); 8 trials each).

**Ladder (Python reference):** PASS 35/40/45 — all collision equations verified.

| n | ops | time_s | DPs | coll | ratio vs \(\sqrt{2^{n-1}}\) | status |
|--:|----:|-------:|----:|-----:|-----------------------------:|:------:|
| 35 | 269215 | 18.4 | 787 | 1 | 2.05 | PASS |
| 40 | 1271643 | 88.5 | 1961 | 1 | 1.76 | PASS |
| 45 | 17662190 | 1172 | 6385 | 1 | 4.21 | PASS |

Checkpoint resume: PASS (n=35). CPU/GPU match: pending native build.

**Not P135-ready.** Python path confirms correctness + scaling only.
Next: compiled native engine on same ladder.
