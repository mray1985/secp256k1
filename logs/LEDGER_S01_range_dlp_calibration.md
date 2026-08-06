# LEDGER S-01 — Range-DLP engine calibration

**Status:** **PASS** — reference interval-DLP implementation is correct and checkpoint-reproducible. **No P135 feasibility promotion.**

> **S-01: PASS** — reference interval-DLP implementation is correct and checkpoint-reproducible. No P135 feasibility promotion.

**Next:** S-02 native Kangaroo equivalence and throughput (`LEDGER_S02_native_kangaroo_equivalence.md`).

## Locked corrections (2026-07-10)

1. **No negation-symmetry acceleration claim.** Jump index uses \(x\) only; DP
   identity retains \(y\)-parity to avoid false \(P\leftrightarrow -P\) collisions.
   Correctness hygiene only — not quotient-by-negation speedup.
2. **DP model.** Density \(2^{-b}\); post-merge detection delay \(\sim 2^{b}\);
   memory falls with density. **Not** an extra \(2^{b/2}\) multiplicative workload.
3. **Tiny-interval oracle first** before treating ladder output as evidence.
4. **Collision equation.** Every hit: \(u=\mathrm{tame}-\mathrm{wild}\),
   \([u]G=Q\), \([2^{n-1}+u]G=P_n\).
5. **RFC6979** = final batch-scoped validator only; does not narrow the interval.
6. **Python harness** = correctness + op-count scaling, **not** a P135 runtime model.

## Promotion order

```text
random tiny-interval oracle → 35 → 40 → 45 → compiled native engine
```

## Workload scale

| n | \(\sqrt{2^{n-1}}\) |
|--:|-------------------:|
| 35 | \(2^{17}\) |
| 40 | \(2^{19.5}\) |
| 45 | \(2^{22}\) |
| 50 | \(2^{24.5}\) |
| 135 | \(2^{67}\approx 1.48\times 10^{20}\) |

At \(10^{12}\) ops/s ≈ 4.7 years; at \(10^{9}\)/s ≈ 4700 years.

## Oracle (PASS)

| width | trials | mean ops | ratio vs \(\sqrt{W}\) |
|------:|-------:|---------:|----------------------:|
| \(2^{16}\) | 8/8 | 842 | 3.29 |
| \(2^{20}\) | 8/8 | 4473 | 4.37 |
| \(2^{24}\) | 8/8 | 20444 | 4.99 |

Artifact: `logs/s01_calibration/S01_oracle_results.json`

## Ladder (PASS — Python reference)

| n | expected | ops | ratio | time_s | DPs | coll | Q | pub | eq | status |
|--:|---------:|----:|------:|-------:|----:|-----:|:-:|:-:|:-:|:------:|
| 35 | \(2^{17}\) | 269,215 | 2.05 | 18.4 | 787 | 1 | ✓ | ✓ | ✓ | PASS |
| 40 | \(2^{19.5}\) | 1,271,643 | 1.76 | 88.5 | 1961 | 1 | ✓ | ✓ | ✓ | PASS |
| 45 | \(2^{22}\) | 17,662,190 | 4.21 | 1172 | 6385 | 1 | ✓ | ✓ | ✓ | PASS |

Scaling: \(\log_2(\mathrm{ops})\) vs \(n\) slope ≈ 1.52 (expected ~0.5 per unit \(n\) in
\(\log_2\sqrt{2^{n-1}} = (n-1)/2\)) — confirms square-root curve within constant \(c\).

RFC6979: N/A on ladder spends (not hashkeys batch); pubkey gate decisive.

## Checkpoint resume (PASS)

n=35: partial run at 100k ops → resume from checkpoint → same \(u\), `eq=True`.

## Promotion gate

| Gate | Status |
|------|--------|
| Tiny oracle every trial | **PASS** |
| Ladder recoveries without hints | **PASS** |
| Collision equations | **PASS** |
| Checkpoints resume reproducibly | **PASS** (n=35) |
| Op-count ~ \(\sqrt{\mathrm{interval}}\) | **PASS** (c ≈ 1.8–4.2) |
| CPU/GPU identical keys | **blocked** — no native binary in tree |
| P135-ready | **NO** |

**Next:** compile/run JeanLucPons `Kangaroo/` on same ladder; keys must match.
Then measure whether native path can sustain \(2^{67}\) ops (feasibility, not pattern).

Script: `s01_range_dlp_calibration.py`
Artifacts: `logs/s01_calibration/S01_oracle_results.json`, `S01_calibration_results.json`
