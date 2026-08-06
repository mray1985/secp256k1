# Candidate F pre-registration

**Register before examining results.** Do not tune after peeking.

Fill this form, save a dated copy under
`ARCHIVE/briefcase/factoradic_native_lead_falsified/prereg/`
(or `logs/prereg/`), then run `pairing_advantage_filter.py` / evaluate.

---

## Identity

| Field | Value |
|-------|-------|
| Candidate ID | F-YYYYMMDD-## |
| Short name | |
| Author / session | |
| Date registered | |
| Date first evaluated | *(fill only after registration locked)* |

## Exact formula

Write the full definition, including all reductions / mods / truncations:

```text
F(d, Px, Py, n) = ...
```

Reductions (check all that apply):

- [ ] mod p (field)
- [ ] mod N (scalar order)
- [ ] native bit-length / top-n
- [ ] factoradic phase / lead frac
- [ ] other: _______________

## Domains

| Object | Domain |
|--------|--------|
| d | ℤ / band `[2^{n-1}, 2^n)` / other: ___ |
| Px, Py | 𝔽_p coordinates |
| Intermediate g(Px,Py) | p-domain / N-domain / both |

## Score definition

How is a single number produced from the sample of puzzles?

```text
score = ...   (e.g. Pearson corr, mean |Δ|, fraction close, …)
```

**Expected direction** (lock before run): higher is better / lower is better / |score| large.

## Allowed parameters

List every free parameter and the **pre-committed** value or grid.
No post-hoc expansion of the grid after seeing scores.

| Parameter | Pre-committed value(s) |
|-----------|------------------------|
| | |

If the grid has >1 cell: state multiple-testing plan (Bonferroni / pre-chosen primary cell).

## Holdout split

| Split | Definition |
|-------|------------|
| Train | puzzles n ∈ … (default 1..50) |
| Test | puzzles n ∈ … (default 51..70) |
| Range A / B | (default 1..35 / 36..70) |

## Null families (required)

| Null | What it breaks |
|------|----------------|
| Shuffle π | pairing: keep d_i, assign P_π(i) |
| Random n-bit | scalar band structure without true EC map |
| Random EC pairs | generic [d']G, not puzzle d series |
| Nearby height | wrong point from similar n |

## Trivial-class exclusion (must pass)

Confirm this F is **not**:

1. **DL recomputation:** \(F=\mathbf{1}\{P=[d]G\}\) or any check that only verifies the already-known solved scalar against its point.
2. **Curve membership alone:** any formula implied by \(y^2\equiv x^3+7\pmod p\) for every valid point, independent of which d it is paired with.

Justification (1–3 sentences): why F uses (d, Px, Py) jointly, is not guaranteed by curve membership, and should collapse under permutation.

## Laboratory rule (locked)

```text
"Looks similar"  ≠  "depends on the correct pairing."

Ask:  P_i = [d_i]G   versus   P_π(i) ≠ [d_i]G

Need simultaneously:
  score_real      strong
  score_shuffled  ordinary
  Δ = real − shuffled   unusually large  (low null p)

False-positive benchmark (sawtooth): Δ ≈ 0.125 with p ≈ 0.15 — not a magical cutoff.
```

## Promotion gate (all required)

```text
advantage > 0.12
p_shuffle < 0.01
beats random n-bit
beats random EC pairs
holds out-of-sample
direction consistent across ranges
```

## Result (fill only after evaluation)

| Metric | Value |
|--------|------:|
| score_real | |
| score_shuffled | |
| Δ (advantage) | |
| p_shuffle | |
| Verdict | PROMOTE / FAIL / BORDERLINE |

Notes:
