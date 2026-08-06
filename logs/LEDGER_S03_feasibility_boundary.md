# LEDGER S-03 — P135 feasibility boundary (bit-cut gate)

**Status:** **PASS / LOCKED** — policy boundary from S-02 calibration. No engine run.

> **S-02 PASS:** native CPU implementation is correct, reproducible, and empirically calibrated.  
> **P135 NOT READY:** direct search remains computationally infeasible.  
> **No launch gate:** require a reproducible, holdout-validated interval reduction of at least about **40 bits** for a one-year CPU-class campaign, or about **47 bits** for a 30-day campaign.

## Model

\[
T\approx\frac{C\sqrt{W}}{R},\qquad
b_{\max}=2\log_2\!\left(\frac{RT}{C}\right),\qquad
\Delta b=134-b_{\max}.
\]

\(R=1.70\times 10^{7}\) ops/s (S-02, n≥45).

## \(C\) wording cleanup

| label | value | use |
|-------|------:|-----|
| median-of-medians (35–50) | **1.66** | S-02 \(T_{135}\) headline (not pooled n≥45) |
| median of \{45,50\} size-medians | **2.22** | if restricting to throughput regime by size-medians |
| **pooled \(n\ge 45\) median** (20 runs) | **≈ 2.08** | **S-03 primary** (matches \(R\) regime) |
| **empirical p90** (\(n\ge 45\), 20 runs) | **≈ 4.53** | **S-03 primary** (coarse but honest) |
| median-of-p90s (35–50) | **≈ 3.84** | S-02 published companion to 1.66 |

Arithmetic check (S-02): \(\frac{1.66\cdot 2^{67}}{1.70\times 10^{7}}\approx 4.57\times 10^{5}\) years.

## Bit-cut table (\(R=1.70\times 10^{7}\))

### Primary — pooled \(n\ge 45\)

| CPU budget | Median \(C\approx 2.08\) | Empirical p90 \(C\approx 4.53\) |
| ---------- | -----------------------: | -----------------------------: |
| 1 day | width \(\approx 2^{78.7}\); need **≈55.3-bit cut** | \(\approx 2^{76.5}\); need **≈57.5-bit cut** |
| 30 days | \(2^{88.5}\); need **≈45.5-bit cut** | \(2^{86.3}\); need **≈47.7-bit cut** |
| 1 year | \(2^{95.8}\); need **≈38.3-bit cut** | \(2^{93.5}\); need **≈40.5-bit cut** |
| 10 years | \(2^{102.4}\); need **≈31.6-bit cut** | \(2^{100.1}\); need **≈33.9-bit cut** |

### Reference — S-02 constants \(C=1.66\) / \(3.84\)

| CPU budget | \(C=1.66\) | \(C=3.84\) |
| ---------- | ---------: | ---------: |
| 1 day | **54.63-bit cut** | **57.05-bit cut** |
| 30 days | **44.81-bit cut** | **47.23-bit cut** |
| 1 year | **37.60-bit cut** | **40.02-bit cut** |
| 10 years | **30.96-bit cut** | **33.38-bit cut** |

## Promotion rule

\[
\boxed{\text{A proposed P135 lead is operationally relevant only if it independently removes roughly 40–57 verified bits.}}
\]

- **1-year CPU-class:** ≳ 38–41 verified bits  
- **30-day CPU-class:** ≳ 45–48 verified bits  
- **1-day CPU-class:** ≳ 55–58 verified bits  

Few-bit correlations, visual alignments, checksum coincidences, and ranking heuristics do **not** pay rent. A genuine 20-bit cut still leaves \(\sim 2^{57}\) kangaroo work on this CPU.

## Verified-bits criteria

1. Independent of secret \(d\) (or holdout-validated).  
2. Explicit sub-interval / union with total width \(\le 2^{134-\Delta b}\).  
3. Survives existing null / pairing / prereg gates.  
4. No creator-pattern or unverified heuristic claims.

## Artifacts

- Prereg: `logs/prereg/S-20260710-03_feasibility_boundary.md`
- Source calibration: `logs/LEDGER_S02_native_kangaroo_equivalence.md`, `logs/s02_native/S02_results.json`
