# F-20260709-04 — Band-floor + doubled x-coordinate X₂(Q) (PRE-REGISTERED)

**Status:** LOCKED before evaluation. Do not change formula/parameters after peeking.

| Field | Value |
|-------|-------|
| Candidate ID | F-20260709-04 |
| Short name | band_floor_doubled_x |
| Date registered | 2026-07-09 |
| Date first evaluated | 2026-07-09 |

---

## Context

- F-01/F-02: coordinate-sum feature falsified (including Mersenne offset rescue).
- F-03: \(T(Q)\) tangent slope — **FAIL**.
- This candidate is the **sibling fork** named in the ledger: replace feature with doubled-point \(x\)-coordinate only.

## Exact formula

```text
u = d - 2^{n-1}
Q = P - [2^{n-1}]G = (Qx, Qy)

T(Q) = 3 * Qx^2 * inv(2 * Qy)  mod p     (skip if 2Qy ≡ 0)
X2(Q) = T(Q)^2 - 2 * Qx                 mod p

phi = factoradic lead fraction
score = Pearson_corr( phi(u), phi(X2(Q)) )

FORBIDDEN: Q=[u]G verifier; offset ladder; switching back to T or Qx+Qy after peeking.
```

## Domains / score / direction

| | |
|--|--|
| Domains | u in `[0,2^{n-1})`; Q, X2 in 𝔽_p |
| Score | Pearson(phi(u), phi(X2)) |
| Expected direction | higher is better |
| Parameters | band floor only; feature X2 only; no grid |

## Holdout / nulls

Same as F-03: train 1..50 / test 51..70; shuffle Q; random (n−1)-bit; random EC; nearby height; sawtooth control.

## Trivial-class exclusion

Not DL recompute. Not curve membership alone — \(X_2\) is the \(x\)-coordinate of \([2]Q\); \(\phi(u)\leftrightarrow\phi(X_2)\) is not implied by \(y^2=x^3+7\) under wrong attachment.

## Laboratory question

> After band-floor translation, does \(X_2(Q)=x([2]Q)\) leave a factoradic fingerprint of the private payload that disappears under wrong attachment?

## Promotion gate

```text
advantage > 0.12
p_shuffle < 0.01
beats random (n-1)-bit / random EC
holds out-of-sample
direction consistent across ranges
```

## Result (evaluated 2026-07-09)

| Metric | Value |
|--------|------:|
| score_real | -0.0330 |
| score_shuffled | -0.0084 |
| Δ | -0.0246 |
| p_shuffle | 0.8002 |
| train / test score | +0.0360 / -0.2558 |
| train / test advantage | +0.0265 / -0.2325 |
| Verdict | FAIL |

Notes: prereg locked: F-20260709-04 (band_floor_doubled_x); Advantage near zero / shuffle does not destroy score.
