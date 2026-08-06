# LEDGER P71-S02 — Scanner feasibility boundary

**Status:** **UPDATED** — measured CPU \(R\) from P71-S03 is the feasibility baseline. OpenCL iGPU also measured (slower). CUDA **N/A**.

## Model (locked)

\[
T_{\mathrm{mean}}=\frac{|S|}{2R},\qquad
T_{\mathrm{worst}}=\frac{|S|}{R},\qquad
P(\text{hit by }t)=\min\!\left(1,\frac{Rt}{|S|}\right).
\]

Uncut: \(|S|=W=2^{70}\). For mean-time budget \(T\):

\[
|S|_{\max}=2RT,\qquad
b_{\mathrm{cut}}=70-\log_2(2RT).
\]

Clarification: \(70-\log_2(2RT)\), **not** \(70-2\log_2(2RT)\).  
Worst-case cut within the same wall budget: add **one bit** (\(b_{\mathrm{cut}}+1\)).

Use **sustained** local \(R\) — not pool dashboards.

## Measured rates (P71-S03)

| Source | \(R_{\mathrm{sustained}}\) | Role |
|--------|---------------------------:|------|
| KeyHunt CPU (4 threads, 600 s) | \(1.33\times10^{7}\) keys/s | **feasibility baseline** |
| clBitCrack OpenCL / HD 530 (180 s) | \(4.59\times10^{6}\) keys/s | evaluated; slower than CPU |
| CUDA | — | N/A on this host |

### Full-band times (\(|S|=2^{70}\), CPU \(R=1.33\times10^{7}\))

| Quantity | Value |
|----------|------:|
| \(T_{\mathrm{mean}}=2^{70}/(2R)\) | \(\approx 1.41\times 10^{6}\) years |
| \(T_{\mathrm{worst}}=2^{70}/R\) | \(\approx 2.81\times 10^{6}\) years |

Mean assumes the key is uniform relative to scan order; worst case is a complete traversal.

### Measured CPU bit-rent (mean-time)

| Budget | Required verified cut \(b_{\mathrm{cut}}\) |
|--------|------------------------------------------:|
| 1 day | 28.94 bits |
| 30 days | 24.03 bits |
| 1 year | 20.42 bits |
| 10 years | 17.10 bits |

### Worst-case cut (guaranteed completion; \(+1\) bit)

| Budget | Worst-case cut |
|--------|---------------:|
| 1 day | 29.94 bits |
| 30 days | 25.03 bits |
| 1 year | 21.42 bits |
| 10 years | 18.10 bits |

\[
\boxed{\text{Puzzle 71 needs roughly 20.4 verified bits removed for a one-year mean CPU campaign.}}
\]

Audited leads still contribute \(0\) verified bits. One-year CPU target ⇒ surviving set size about \(2^{70-20.4}=2^{49.6}\) (reduction factor \(\sim 2^{20.4}\)).

## Stack / launch

| ID | Status |
|----|--------|
| P71-S01 | **PASS** — reference scanner |
| P71-S02 | **UPDATED** — measured CPU feasibility |
| P71-S03 | **PASS** — KeyHunt CPU + OpenCL iGPU (HD 530) measured |
| OpenCL iGPU | **EVALUATED** — \(R_{\mathrm{sust}}\approx4.59\times10^{6}\)/s (slower than CPU) |
| CUDA lane | **N/A** (no NVIDIA) |
| Launch | **NO** |

\[
\boxed{\text{Scanner ready; search not economically ready.}}
\]

Feasibility tables above use **CPU** \(R=1.33\times10^{7}\). Remain frozen unless a **faster** discrete GPU/CUDA backend appears or a lead supplies explicit \(S\) worth \(\sim 2^{20.4}\) reduction for a one-year CPU mean.

## Admission / freeze

\[
\boxed{(F,\; S,\; |S|,\; \text{justification})}
\quad S\subseteq[2^{70},2^{71}).
\]

\[
\boxed{\text{No P71 experiment unless it defines an explicit }S\subseteq[2^{70},2^{71})\text{ or calibrates the scanner.}}
\]

Does **not** transfer from P135: pubkey geometry, kangaroo, RSZ, RFC6979, echoes, rotations.
Creator “probably here” without explicit \(S\) → **0 verified bits**.

## Comparison (order of magnitude)

| Target | Work unit | One-year mean cut (this host) |
|--------|-----------|------------------------------:|
| P71 address scan | HASH160 tests | ≈20.4 bits @ \(R=1.33\times10^{7}\)/s |
| P135 kangaroo | group ops | ≈40–57 bits (S-03) |

## Artifacts

- Prereg: `logs/prereg/P71-S-20260710-02_feasibility_boundary.md`
- Freeze: `logs/p71_s02/P71_S02_freeze.json`
- Measured \(R\): `logs/p71_s03/promotion/P71_S03_sustained_only.json`
