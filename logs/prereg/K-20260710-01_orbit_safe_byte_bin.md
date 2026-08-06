# K-20260710-01 — Orbit-safe byte-bin recurrence (PRE-REGISTERED)

**Status:** LOCKED before evaluation. Do not change formula/parameters after peeking.

| Field | Value |
|-------|-------|
| Candidate ID | K-20260710-01 |
| Short name | orbit_safe_byte_bin_recurrence |
| Date registered | 2026-07-10 |
| Date first evaluated | 2026-07-10 |

---

## Prerequisite

K-00 panel admissibility tags. Use only \(k^\star=\min(k,N-k)\).

## Exact rule (locked — 8 bits only)

```text
k* = min(k, N-k)

c(k) = 2 * k* / N ∈ [0,1]

b(k) = min(255, floor(256 * c(k)))     # 8-bit bin, LOCKED

B_train = { b(k_i) : i in train }

R(k) = 1  iff  b(k) ∈ B_train
```

**FORBIDDEN after peeking:** 4/12/16-bit bins; using raw \(k\) instead of \(k^\star\); feature tuning on \(r,s,z\).

## Metrics

```text
retention = #{test : b(k_test) ∈ B_train} / #test
survivor_fraction = |B_train| / 256
```

## Holdout / nulls (locked)

| Split | Definition |
|-------|------------|
| Train | puzzles \(n \le 50\) |
| Test | puzzles \(n > 50\) |
| Leave-one-source-out | for each source \(S\): train on all other sources, test on \(S\) |
| Random uniform \(k^\star\) | draw \(k\sim U\{1..N-1\}\), take \(k^\star\), measure pass rate into \(B_{\rm train}\) |
| Random EC signatures | random \(d',k'\) → fake \((r,s,z)\) not required; use random \(k'^\star\) bins |
| \(k\leftrightarrow N-k\) control | rule must be identical on \(k\) and \(N-k\) (true by construction of \(k^\star\)) |

## Promote only if

```text
holdout retention = 100%
|B_train|/256 << 1
survives random uniform nonces (pass rate ≈ |B|/256, not retention 100% on random)
survives leave-one-source-out (or document failure)
k↔N-k control OK
```

## Laboratory question

> Do independently observed nonces repeatedly occupy a restricted set of sign-invariant 8-bit magnitude bands?

## Result (evaluated 2026-07-10)

| Metric | Value |
|--------|------:|
| \|B_train\| / 256 | 47/256 = 0.1836 |
| holdout retention | 0.2188 |
| random pass rate | 0.1876 |
| LOSO ok | False |
| k↔N-k control | True |
| Verdict | FAIL |

LOSO detail: {"blockstream spend tx": {"n_test": 68, "n_train": 14, "B_size": 14, "survivor_fraction": 0.0546875, "retention": 0.07352941176470588, "skipped": false}, "hashkeys.space partial spend": {"n_test": 14, "n_train": 68, "B_size": 62, "survivor_fraction": 0.2421875, "retention": 0.35714285714285715, "skipped": false}}
