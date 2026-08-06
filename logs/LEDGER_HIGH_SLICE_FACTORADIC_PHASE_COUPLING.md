# LEDGER — High-slice factoradic phase coupling

**Status:** **SUITE LOCKED (all four phase defs)** — pairing judged per-def  
**Date:** 2026-07-11  
**Artifacts:**
- `factoradic_all_phase_defs_null.py`
- `logs/FACTORADIC_ALL_PHASE_DEFS_NULL.txt`
- `logs/factoradic_all_phase_defs_null.json`
- `factoradic_multiply_then_subtract.py`

## Lead arithmetic (mandatory)

\[
\mathrm{term}=a\cdot k!,\qquad \mathrm{rem}=d-\mathrm{term}
\]

Rebuild: \(d=\sum_i a_i\cdot i!\). Exact on 70/70 solved keys.

## Phase suite (all chosen)

| def | formula |
|-----|---------|
| `digit_frac` | \(a/k\) |
| `cell_frac` | \(\mathrm{rem}/k! = (d-a\cdot k!)/k!\) |
| `plateau_frac` | \((d-k!)/(k\cdot k!)\) for \(d\in[k!,(k+1)!)\) |
| `mass_frac` | \((a\cdot k!)/d\) |

Native high slice: \(\lfloor Px / 2^{L-n}\rfloor\), \(L=\mathrm{bitlength}(Px)\).  
Low slice: \(Px \bmod 2^n\).

## Observed + primary stratified null (nearby \(\|\Delta n\|\le 10\))

| def | r_hi | r_lo | H_hi | H_lo | P(r) | P(H) | P(gap_r) | status |
|-----|-----:|-----:|-----:|-----:|-----:|-----:|---------:|--------|
| `digit_frac` | +0.610 | +0.113 | 43/70 | 26/70 | 0.0005 | 0.0005 | 0.0015 | **PAIRING-DEPENDENT** |
| `cell_frac` | +0.119 | +0.051 | 20/70 | 17/70 | 0.2439 | 0.0545 | 0.4388 | **NULL** |
| `plateau_frac` | +0.545 | +0.161 | 43/70 | 28/70 | 0.0005 | 0.0005 | 0.0055 | **PAIRING-DEPENDENT** |
| `mass_frac` | +0.259 | -0.080 | 45/70 | 36/70 | 0.0215 | 0.0120 | 0.0265 | **WEAK/MARGINAL** |

Trials = 2000. Exact-\(n\) strata have size 1; nearby/block/residual nulls used.

## Ruling

```text
Suite locked:                          YES (all four defs)
Lead multiply-then-subtract:           REQUIRED
Real descriptive hi/lo gap:            present for digit/plateau/mass; weak for cell
Recoverable private-key information:   NOT claimed
Pairing dependence:                    per-def status column above
```

**Ledger name:** High-slice factoradic phase coupling (full suite)

Related prior: `logs/FACTORADIC_EVIDENCE_DIGEST.md` (native-lead falsification under
unstratified / random-width nulls). This entry supersedes single-def promotion by
locking the whole suite and reporting stratified p-values for each.
