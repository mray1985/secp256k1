# S-20260710-03 — P135 feasibility boundary / bit-cut gate (PRE-REGISTERED)

**Status:** LOCKED. Not an engine run — converts S-02 calibration into a minimum
interval-reduction requirement.

| Field | Value |
|-------|-------|
| Candidate ID | S-20260710-03 |
| Short name | p135_feasibility_boundary_bitcut |
| Date registered | 2026-07-10 |
| Prerequisite | **S-02 PASS** (native CPU equivalence + throughput) |

---

## Boundary

S-02 established native correctness and CPU throughput. S-03 does **not** search.
It states when a proposed lead becomes operationally relevant.

## Inputs (from S-02)

| symbol | meaning | value |
|--------|---------|------:|
| \(R\) | measured effective ops/s (n≥45 median) | \(1.70\times 10^{7}\) |
| \(W_{135}\) | band-floor interval width | \(2^{134}\) |
| \(C\) | kangaroo ops / \(\sqrt{W}\) | see labeling below |

### \(C\) labeling (cleanup)

| label | definition | value |
|-------|------------|------:|
| median-of-medians (35–50) | median of per-size medians | **1.66** |
| median of \{45,50\} medians | median(2.78, 1.66) | **2.22** |
| **pooled \(n\ge 45\) median** | median of 20 individual \(C_i\) | **≈ 2.08** |
| **empirical p90** (\(n\ge 45\), 20 runs) | 90th percentile of those \(C_i\) | **≈ 4.53** |
| median-of-p90s (35–50) | median of per-size p90s | **≈ 3.84** |

S-02’s \(T_{135}\) used **median-of-medians = 1.66** and **median-of-p90s = 3.84**.
For S-03, the primary operational columns use **pooled \(n\ge 45\)** \(C\) (same regime as \(R\)).
Ten seeds per size → empirical p90 is useful but coarse.

## Model

For interval width \(W=2^{b}\):

\[
T\approx\frac{C\sqrt{W}}{R}
\qquad\Rightarrow\qquad
b_{\max}=2\log_2\!\left(\frac{RT}{C}\right).
\]

Bits that must be removed from the \(2^{134}\) unknown:

\[
\Delta b = 134 - b_{\max}.
\]

## Feasibility table (\(R=1.70\times 10^{7}\))

### Primary — pooled \(n\ge 45\)

| CPU budget | Pooled median \(C\approx 2.08\) | Empirical p90 \(C\approx 4.53\) |
| ---------- | -----------------------------: | -----------------------------: |
| 1 day | \(b_{\max}\approx 2^{78.72}\); need **≈55.3-bit cut** | \(b_{\max}\approx 2^{76.48}\); need **≈57.5-bit cut** |
| 30 days | \(2^{88.54}\); need **≈45.5-bit cut** | \(2^{86.29}\); need **≈47.7-bit cut** |
| 1 year | \(2^{95.75}\); need **≈38.3-bit cut** | \(2^{93.50}\); need **≈40.5-bit cut** |
| 10 years | \(2^{102.39}\); need **≈31.6-bit cut** | \(2^{100.14}\); need **≈33.9-bit cut** |

### Reference — S-02 published constants (median-of-medians / median-of-p90s)

| CPU budget | Median-of-medians \(C=1.66\) | Median-of-p90s \(C=3.84\) |
| ---------- | --------------------------: | -----------------------: |
| 1 day | \(2^{79.37}\); need **54.63-bit cut** | \(2^{76.95}\); need **57.05-bit cut** |
| 30 days | \(2^{89.19}\); need **44.81-bit cut** | \(2^{86.77}\); need **47.23-bit cut** |
| 1 year | \(2^{96.40}\); need **37.60-bit cut** | \(2^{93.98}\); need **40.02-bit cut** |
| 10 years | \(2^{103.04}\); need **30.96-bit cut** | \(2^{100.62}\); need **33.38-bit cut** |

(Matches the arithmetic check \(\frac{1.66\cdot 2^{67}}{1.70\times 10^{7}}\approx 4.57\times 10^{5}\) years.)

## Promotion rule (locked)

\[
\boxed{\text{A proposed P135 lead is operationally relevant only if it independently removes roughly 40–57 verified bits.}}
\]

| Campaign class | Required verified cut (order of magnitude) |
|----------------|--------------------------------------------|
| 1-year CPU-class | ≳ **38–41 bits** (median → empirical p90) |
| 30-day CPU-class | ≳ **45–48 bits** |
| 1-day CPU-class | ≳ **55–58 bits** |

A few-bit correlation, visual alignment, checksum coincidence, or candidate ranking
does **not** change feasibility. A genuine **20-bit** reduction still leaves
\(\sim 2^{57}\) kangaroo-scale work — enormous on this CPU.

## What counts as “verified bits removed”

1. Independent of the secret \(d\) (or holdout-validated if trained).
2. Produces an explicit sub-interval or union of intervals of total width \(\le 2^{134-\Delta b}\).
3. Survives nulls / pairing-advantage / prereg gates already in force.
4. Does not claim reduction from unverified heuristics or creator-pattern assumptions.

## Ledger lines

> **S-02 PASS:** native CPU implementation is correct, reproducible, and empirically calibrated.  
> **P135 NOT READY:** direct search remains computationally infeasible.  
> **No launch gate:** require a reproducible, holdout-validated interval reduction of at least about **40 bits** for a one-year CPU-class campaign, or about **47 bits** for a 30-day campaign.

## Result

S-03 is a **policy / boundary** result — accepted when the table and promotion rule
are locked into the ledger. No further engine run required.
