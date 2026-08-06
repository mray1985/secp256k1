# F-20260709-03 — Band-floor + tangent slope T(Q) (PRE-REGISTERED)

**Status:** LOCKED before evaluation. Do not change formula/parameters after peeking.

| Field | Value |
|-------|-------|
| Candidate ID | F-20260709-03 |
| Short name | band_floor_tangent_slope |
| Date registered | 2026-07-09 |
| Date first evaluated | 2026-07-09 |

---

## Why this candidate

F-01 and F-02 falsified the locked feature \(\phi((Q_x+Q_y)\bmod p)\) under band-floor and all Mersenne offsets. This candidate **replaces the feature**, not the translation:

```text
keep:   u = d - 2^{n-1},   Q = P - [2^{n-1}]G
replace g = (Qx+Qy) mod p
with:   T(Q) = 3 Qx^2 * (2 Qy)^{-1}  (mod p)   # EC doubling tangent slope
```

**Not chosen (sibling fork, not evaluated here):** \(X_2(Q)=T(Q)^2-2Q_x\pmod p\). Only one feature locked.

## Exact formula

```text
u = d - 2^{n-1}
Q = P - [2^{n-1}]G = (Qx, Qy)

T(Q) = 3 * Qx^2 * inv(2 * Qy)  mod p     (skip row if Qy ≡ 0)

phi = factoradic lead fraction

score = Pearson_corr( phi(u), phi(T(Q)) )

FORBIDDEN: any Q=[u]G / P=[d]G verifier.
FORBIDDEN: offset ladder / lead-width sweep / switching to X_2 after peeking.
```

## Domains

| Object | Domain |
|--------|--------|
| u | `[0, 2^{n-1})` |
| Q, T(Q) | 𝔽_p |

## Score / expected direction

```text
score = Pearson(phi(u), phi(T(Q))) over eligible puzzles
```

**Expected direction:** higher is better.

## Allowed parameters

| Parameter | Pre-committed |
|-----------|---------------|
| Translation | band floor only: \(A=2^{n-1}\) |
| Feature | \(T(Q)\) only |
| Grid | none |

## Holdout / nulls

| Split | 1..50 train / 51..70 test; ranges 1..35 / 36..70 |
| Shuffle | keep u, shuffle Q (hence T) |
| Random (n−1)-bit | random u' + random field (Qx,Qy) → T |
| Random EC | random u' with Q'=[u']G → T(Q') |
| Nearby height | wrong Q from similar n |
| Control | native-n sawtooth on original (d,Px) |

## Trivial-class exclusion

1. Not DL recompute.
2. Not curve membership alone — \(T(Q)\) is the doubling slope at Q; \(\phi(u)\leftrightarrow\phi(T)\) is not implied by \(y^2=x^3+7\) for arbitrary attachment; wrong Q should destroy any real signal.

## Laboratory question

> After band-floor translation, does the EC doubling tangent \(T(Q)\) leave a factoradic fingerprint of the private payload that disappears under wrong attachment?

## Promotion gate

```text
advantage > 0.12
p_shuffle < 0.01
beats random (n-1)-bit
beats random EC
holds out-of-sample
direction consistent across ranges
```

## Result (evaluated 2026-07-09)

| Metric | Value |
|--------|------:|
| score_real | -0.1497 |
| score_shuffled | -0.0046 |
| Δ | -0.1450 |
| p_shuffle | 0.2298 |
| train / test score | -0.1968 / +0.1477 |
| train / test advantage | -0.1876 / +0.1426 |
| Verdict | FAIL |

Notes: prereg locked: F-20260709-03 (band_floor_tangent_slope); Advantage near zero / shuffle does not destroy score.
