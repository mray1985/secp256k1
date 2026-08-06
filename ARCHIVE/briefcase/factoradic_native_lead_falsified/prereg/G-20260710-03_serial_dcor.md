# G-20260710-03 — Normalized payload serial-dependence gate (PRE-REGISTERED)

**Status:** LOCKED before evaluation. Do not change formula/parameters after peeking.

| Field | Value |
|-------|-------|
| Candidate ID | G-20260710-03 |
| Short name | payload_serial_dcor_gate |
| Date registered | 2026-07-10 |
| Date first evaluated | 2026-07-10 |

---

## Purpose

Stop/go test for **creator-side serial dependence** — not another guessed generator.
G-01/G-02 closed fitted LCG and SHA-256 chain. This asks whether consecutive
normalized payloads are dependent at all.

## Exact definitions (locked)

```text
q_n = (d_n - 2^{n-1}) / 2^{n-1}  ∈ [0,1)
```

Two sequences (tested **separately**; do not combine):

```text
A: q_1, q_2, …, q_70          (consecutive puzzles)
B: q_75, q_80, …, q_130       (five-step chain)
```

Score (locked — distance correlation only):

```text
S = dCor(q_t, q_{t+1})
```

on consecutive pairs within each sequence (A: 69 pairs; B: 11 pairs).

Distance correlation: Székely–Rizzo–Bakirov empirical dCor on the paired sample
\((q_t, q_{t+1})\). Parameter-free; detects nonlinear dependence.

## Null (locked)

Within each sequence, randomly permute the order of the \(q\)-values, rebuild
consecutive pairs, recompute \(S\). Real order used once.

```text
p_perm = (#{b : S_b >= S_real} + 1) / (B + 1)
```

\(B = 10000\) permutations per sequence.

## Promotion gate

\[
\boxed{p_{\mathrm{perm}}<0.01\text{ in BOTH chains A and B}}
\]

with real \(S\) above the null’s 99th percentile in each.

**FORBIDDEN after peeking:** lag sweep; bin width; Pearson/Spearman; combining
chains if one fails; other dependence scores.

## Interpretation

| Outcome | Meaning |
|---------|---------|
| PASS both | consecutive payload positions depend; predictive generator search justified |
| FAIL either | at detectable scale, payloads behave like independently ordered draws; close invent-another-formula cycle |

## Laboratory question

> Is there detectable serial dependence in normalized within-band payload locations?

If fail:

\[
\boxed{\text{Solved payload locations behave like independently ordered draws at the detectable scale.}}
\]

## Result (evaluated 2026-07-10)

| Chain | S_real | p_perm | p99_null | Verdict |
|-------|-------:|-------:|---------:|---------|
| A 1..70 | 0.148568 | 0.843116 | 0.337352 | FAIL |
| B 75..130 step 5 | 0.438213 | 0.654035 | 0.758612 | FAIL |
| Overall | | | | **FAIL** |

Solved payload locations behave like independently ordered draws at the detectable scale. Close invent-another-recurrence/hash cycle; prefer direct search-space engineering for Puzzle 135.
