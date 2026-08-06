# P71-S-20260710-02 — Scanner feasibility boundary (PRE-REGISTERED)

**Status:** LOCKED. Policy from measured \(R\) (after P71-S01) + illustrative rates.

| Field | Value |
|-------|-------|
| Candidate ID | P71-S-20260710-02 |
| Short name | p71_scanner_feasibility_boundary |
| Date registered | 2026-07-10 |
| Prerequisite | P71-S01 for **launch** \(R\); illustrative table uses stated rates |

---

## Model

Surviving set \(S\subseteq[2^{70},2^{71}]\cap\mathbb{Z}\) (inclusive band), scanner rate \(R\):

\[
T_{\mathrm{mean}}=\frac{|S|}{2R},\qquad
T_{\mathrm{worst}}=\frac{|S|}{R},\qquad
P(\text{hit by }t)=\min\!\left(1,\frac{Rt}{|S|}\right).
\]

\[
b_{\mathrm{cut}}=70-\log_2|S|=70-\log_2(2RT)
\quad\text{when }|S|_{\max}=2RT.
\]

Clarification: \(70-\log_2(2RT)\), **not** \(70-2\log_2(2RT)\).

Full band, no cut: \(|S|=2^{70}\), expected \(\sim 2^{69}\) tests.

## Illustrative tables (not measured \(R\))

### At \(R=10^{12}\) keys/s

| Budget | Required verified cut |
|--------|----------------------:|
| 1 day | ≈ **12.7** bits |
| 30 days | ≈ **7.8** bits |
| 1 year | ≈ **4.2** bits |
| No cut | ≈ **18.7** years average |

### At \(R=10^{9}\) keys/s

| Budget | Required verified cut |
|--------|----------------------:|
| 1 day | ≈ **22.7** bits |
| 30 days | ≈ **17.8** bits |
| 1 year | ≈ **14.2** bits |
| No cut | ≈ **18 705** years average |

**Launch boundary must use measured scanner throughput from P71-S01**, not these illustrations.

## Admission (transfers from S-05)

\[
\boxed{(F,\; S,\; |S|,\; \text{justification})}
\quad\text{with}\quad
S\subseteq[2^{70},2^{71}).
\]

## What does **not** transfer from P135

* public \((x,y)\) · \(Q\)-shifted DLP · RSZ · RFC6979 · public-point echoes / root rotations

Creator-sequence toward \(d_{71}\): G-03 found no serial dependence through \(d_1,\ldots,d_{70}\).
Reopening arbitrary recurrence hunting violates the freeze. “Probably here” = category 3 = **0 bits**.

## Freeze

\[
\boxed{\text{No P71 experiment unless it defines an explicit }S\subseteq[2^{70},2^{71})\text{ or calibrates the scanner.}}
\]
