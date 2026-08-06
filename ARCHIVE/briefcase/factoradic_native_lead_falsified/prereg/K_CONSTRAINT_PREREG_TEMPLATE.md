# K-constraint candidate pre-registration

**Register before examining results.** Do not tune after peeking.

Save dated copies under `logs/prereg/` and
`ARCHIVE/briefcase/factoradic_native_lead_falsified/prereg/`.

---

## Identity

| Field | Value |
|-------|-------|
| Candidate ID | K-YYYYMMDD-## |
| Short name | |
| Date registered | |
| Date first evaluated | *(pending)* |

## Exact constraint \(R\)

State the full predicate / sieve. Inputs may include observables
\((r,s,z,P)\) and hypothesized structure on \(k\). Must **not** require
unknown Puzzle-135 \(d\) at test time for the sieve itself (calibration
uses known \(d\) only to recover ground-truth \(k\)).

```text
R(...) = ...
```

How candidates are enumerated / counted under \(R\):

```text
surviving set size = ...
```

## Domains

| Object | Domain |
|--------|--------|
| \(k\) | \(\mathbb{Z}/N\mathbb{Z}\) |
| \(r,s,z\) | from spend tx |
| \(P\) | compressed / affine |

## Score / promotion metrics (locked)

```text
retention = fraction of held-out solved signatures whose true k satisfies R
reduction = mean( |{k' : R(k'; observables)}| / N )   over held-out rows
```

**Promote only if:**

```text
retention = 100% on held-out solved signatures
reduction << 1   (state pre-committed threshold, e.g. < 2^{-32} or < 2^{-64})
```

Also require train/holdout consistency of reduction order-of-magnitude.

## Allowed parameters

| Parameter | Pre-committed value(s) |
|-----------|------------------------|
| | |

No post-hoc expansion of the parameter grid after seeing retention/reduction.

## Holdout split

| Split | Definition |
|-------|------------|
| Train | puzzles \(n \le 50\) (or pre-committed set) |
| Test | puzzles \(n > 50\) |

## Null / controls

| Check | Requirement |
|-------|-------------|
| True \(k\) retained | 100% on test |
| Random \(k\) pass rate | near `reduction` (rule not vacuous) |
| Shuffled \((r,s,z)\) among puzzles | retention collapses unless rule is trivial |
| Not DL recompute | does not verify \(P=[d]G\) using known \(d\) as the sieve |
| Not curve membership alone | |

## Laboratory question

> Does this preregistered constraint on the actual nonce \(k\), derived from
> observable transaction data, generalize across solved puzzles and meaningfully
> narrow the search relative to \(N\)?

## Result (fill only after evaluation)

| Metric | Train | Test |
|--------|------:|-----:|
| retention | | |
| reduction | | |
| Verdict | PROMOTE / FAIL / BORDERLINE | |

Notes:
