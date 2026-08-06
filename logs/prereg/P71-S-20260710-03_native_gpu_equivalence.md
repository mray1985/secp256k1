# P71-S-20260710-03 — Native/GPU scanner equivalence (PRE-REGISTERED)

**Status:** LOCKED before evaluation. **Only active P71 experiment.**

| Field | Value |
|-------|-------|
| Candidate ID | P71-S-20260710-03 |
| Short name | p71_native_gpu_scanner_equivalence |
| Date registered | 2026-07-10 |
| Prerequisite | P71-S01 PASS (Python reference) |
| Target | Puzzle 71 still **unsolved**; pubkey **not** exposed → linear HASH160 only |

---

## Exact candidate path (locked)

\[
d \rightarrow [d]G \rightarrow \text{compressed SEC}
\rightarrow \mathrm{SHA256} \rightarrow \mathrm{RIPEMD160}
\]

Compare the **20-byte HASH160** directly. Do **not** Base58-encode every candidate;
reconstruct the full address only after a HASH160 hit.

## Inclusive band

\[
2^{70} \le d \le 2^{71}-1
\]

(explicit inclusive endpoints; equivalent to half-open \([2^{70},2^{71})\)).

## Correctness gate

Native scanner must reproduce:

* all P71-S01 artificial oracle targets;
* all nine solved calibration targets;
* exact private keys returned by the Python reference;
* range-start and range-end boundary cases;
* interrupted and resumed scans;
* multiworker partition coverage with no gaps or overlaps.

Each hit must finally satisfy:

\[
\mathrm{HASH160}(\mathrm{SEC}_{\mathrm{compressed}}([d]G))
= \mathrm{HASH160}(\text{P71 address}).
\]

Promotion identity:

\[
\boxed{\text{native hits}=\text{Python hits}=\text{known keys}}
\]

## Throughput (record separately)

\[
R_{\mathrm{peak}}\quad\text{and}\quad R_{\mathrm{sustained}}
\]

Use **sustained** for feasibility — long enough to include initialization,
temperature stabilization, checkpoint writes, and worker coordination.

Record: GPU model/count · driver/runtime · compressed-only mode · keys tested ·
wall-clock · rejected/invalid · range assignments · checkpoint overhead ·
duplicate-work count · sustained keys/s.

External pool figures (~45.9 B keys/s current, ~1.16 T historical high on btcpuzzle.info)
are **not** substitutes for a reproducible local benchmark.

## After measured \(R\): replace P71-S02 illustrations

\[
T_{\mathrm{mean}}=\frac{|S|}{2R},\qquad
T_{\mathrm{worst}}=\frac{|S|}{R},\qquad
P(\text{hit by }t)=\min\!\left(1,\frac{Rt}{|S|}\right).
\]

Uncut: \(|S|=2^{70}\). Required cut for mean-time budget \(T\):

\[
|S|_{\max}=2RT,\qquad
b_{\mathrm{cut}}=70-\log_2(2RT).
\]

(Clarification: \(70-\log_2(2RT)\), **not** \(70-2\log_2(2RT)\).)

## Status after PASS

> **Scanner ready; Puzzle 71 launch depends on measured throughput or an independently proved candidate-set reduction.**

Shelf2 / GAP / barcode / creator-pattern lanes remain **0-bit** unless they supply
\((F,S,|S|,\text{justification})\).

## Result (2026-07-10)

Python self-checks: **PASS**. Native KeyHunt CPU: **PASS** (Puzzle-1 gate + promotion + 600 s sustained).

\[
R_{\mathrm{sustained}}=1.33\times 10^{7}\ \text{keys/s}
\]

GPU / `cuBitCrack`: **NOT EVALUATED** (no hardware/binary).

> **Scanner ready; Puzzle 71 launch depends on measured GPU throughput or an independently proved candidate-set reduction (~20.4 verified bits for one-year CPU mean).**

Monitor: Puzzle 71 still unsolved; no pubkey on page → stay on linear HASH160.
