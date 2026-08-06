# F-20260709-06 — Adjacent Hamming coupling (PRE-REGISTERED)

**Status:** LOCKED before evaluation. Do not change formula/parameters after peeking.

| Field | Value |
|-------|-------|
| Candidate ID | F-20260709-06 |
| Short name | adjacent_hamming_coupling |
| Date registered | 2026-07-09 |
| Date first evaluated | 2026-07-09 |

---

## Closed prior branches

- Translated-point / doubling (F-01…F-04) — CLOSED
- GLV argmin MI (F-05) — FAIL (degenerate \(H(a)=0\))

No factoradics, offsets, coordinate sums, slopes, or GLV relabeling.

## Exact formula (one score only)

For each neighboring solved edge \((i,i+1)\) with puzzles ordered by \(n\):

```text
pad_{n_{i+1}}(d_i) = d_i as an n_{i+1}-bit integer (zero-extend on the left)

h_d(i) = HW( pad_{n_{i+1}}(d_i) XOR d_{i+1} ) / n_{i+1}

SEC(P) = compressed SEC1 encoding:
         0x02 || x   if y even
         0x03 || x   if y odd
         (33 bytes = 264 bits)

h_P(i) = HW( SEC(P_i) XOR SEC(P_{i+1}) ) / 264

S = SpearmanCorr( {h_d(i)}, {h_P(i)} )   over edges
```

**FORBIDDEN after peeking:** uncompressed SEC; Hamming on raw \(P_x\) only; Pearson instead of Spearman; factoradic / GLV / doubling features.

## Domains

| Object | Domain |
|--------|--------|
| edges | consecutive puzzles by \(n\) (1–2, 2–3, …) |
| \(h_d\) | \([0,1]\) |
| \(h_P\) | \([0,1]\) |

## Expected direction

Higher Spearman correlation is better (positive coupling of binary change rates).

## Allowed parameters

| Parameter | Pre-committed |
|-----------|---------------|
| Public encoding | compressed SEC only |
| Score | Spearman only |
| Grid | none |

## Holdout (edge-based)

| Split | Edges |
|-------|-------|
| Train | \((1,2),\ldots,(50,51)\) |
| Test | edges with both endpoints \(n\ge 51\) (i.e. \((51,52),\ldots,(69,70)\)) |
| Ranges | early edges among \(n\le 35\) vs late among \(n\ge 36\) |

## Null families

| Null | Construction |
|------|----------------|
| Shuffle public order | keep \(d\) sequence / \(h_d\); permute \(P\) sequence then recompute \(h_P\) |
| Circular shift of \(P\) | \(P_i \leftarrow P_{i+k}\) |
| Random exact-\(n\)-bit | random band scalars + their true EC points → edges |
| Unrelated random EC | independent random points (ignore \(d\)) with random \(n\)-bit \(d'\) for \(h_d\) |
| Control | native-\(n\) sawtooth advantage on single pairs (benchmark only) |

Advantage:

```text
Δ = S_real - mean(S_shuffled_public_order)
```

## Trivial-class exclusion

1. Not DL recompute — never checks \(P=[d]G\).
2. Not curve membership alone — Hamming rates on neighboring encodings are not fixed by \(y^2=x^3+7\).

## Laboratory question

> Does any local similarity in the private-key sequence survive into local public-key similarity?

\[
\boxed{\text{Does any local similarity in the private-key sequence survive into local public-key similarity?}}
\]

## Promotion gate

```text
advantage > 0.12
p_shuffle < 0.01
beats random n-bit / random EC
holds out-of-sample (edge holdout)
direction consistent across ranges
```

## Result (evaluated 2026-07-09)

| Metric | Value |
|--------|------:|
| S_real | +0.0411 |
| S_shuffled mean | -0.0062 |
| Δ | +0.0473 |
| p_shuffle | 0.7293 |
| train / test S | -0.0552 / +0.3131 |
| train / test Δ | -0.0498 / +0.3190 |
| Verdict | FAIL |

Notes: prereg locked; compressed SEC; Spearman only; edge holdout.
