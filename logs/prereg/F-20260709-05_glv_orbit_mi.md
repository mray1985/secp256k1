# F-20260709-05 — GLV order-3 orbit mutual information (PRE-REGISTERED)

**Status:** LOCKED before evaluation. Do not change formula/parameters after peeking.

| Field | Value |
|-------|-------|
| Candidate ID | F-20260709-05 |
| Short name | glv_orbit_mutual_information |
| Date registered | 2026-07-09 |
| Date first evaluated | 2026-07-09 |

---

## Closed prior branch

Translated-point / doubling-feature family (F-01…F-04) is **CLOSED**. No \(T^{-1}\), \(Y_2\), \(x(4Q)\), \(x(8Q)\), or further offset knobs.

## Exact formula (one score only)

secp256k1 GLV constants (locked):

```text
λ = 0x5363ad4cc05c30e0a5261c028812645a122e22ea20816678df02967c1b23bd72
β = 0x7ae96a2b657c07106e64479eac3434e99cf0497512f58995c1396c28719501ee

[λ](x,y) = (β x mod p, y)
λ³ ≡ 1 (mod N),  β³ ≡ 1 (mod p)
```

Labels (locked ranking rule — **argmin**, ties → smallest j):

```text
a_i = argmin_{j∈{0,1,2}} ( λ^j * d_i  mod N )
b_i = argmin_{j∈{0,1,2}} ( β^j * P_{x,i}  mod p )
```

Score (locked — **mutual information only**, not match-rate / correlation):

```text
S = I(a; b)   with log base 2 (bits)
  = Σ_{a,b} p(a,b) log2( p(a,b) / (p(a) p(b)) )
```

over the empirical 3×3 joint table on puzzles 1..70 (n≥1).

**FORBIDDEN after peeking:** alternate ranking (argmax, mid, etc.); switching to match-rate or Pearson; offset/doubling features.

## Domains

| Object | Domain |
|--------|--------|
| d | scalars mod N |
| Px | 𝔽_p |
| a, b | {0,1,2} |

## Expected direction

Higher \(I(a;b)\) is better.

## Allowed parameters

| Parameter | Pre-committed |
|-----------|---------------|
| λ, β | values above only |
| label rule | argmin, ties → min j |
| score | MI (bits) only |
| Grid | none |

## Holdout / nulls

| Train / test | n∈1..50 / 51..70 |
| Ranges | 1..35 / 36..70 |
| Shuffle | keep \(a_i\), replace \(b_i\) by \(b_{\pi(i)}\) (shuffle points / Px) |
| Random n-bit | random band \(d'\) + random field \(x'\) → labels |
| Random EC | random band \(d'\) with \(P'=[d']G\) → labels |
| Nearby height | attach \(P_x\) from similar-n puzzle |
| Control | native-n sawtooth advantage (false-positive benchmark) |

Advantage:

```text
Δ = I(a_i; b_i) - mean_π I(a_i; b_π(i))
```

## Trivial-class exclusion

1. Not DL recompute — never checks \(P=[d]G\).
2. Not curve membership alone — orbit labels of \(d\) and \(P_x\) are not fixed by \(y^2=x^3+7\); wrong attachment should destroy categorical alignment if any exists.

## Laboratory question

> Does the exact \(d\leftrightarrow P_x\) attachment preserve any categorical alignment under secp256k1’s shared order-3 endomorphism?

## Promotion gate

```text
advantage > 0.12   (bits; same numeric floor as lab standard)
p_shuffle < 0.01
beats random n-bit / random EC
holds out-of-sample
direction consistent across ranges
```

## Result (evaluated 2026-07-09)

| Metric | Value |
|--------|------:|
| I_real | +0.0000 |
| I_shuffled mean | +0.0000 |
| Δ | +0.0000 |
| p_shuffle | 1.0000 |
| train / test I | +0.0000 / +0.0000 |
| train / test Δ | +0.0000 / +0.0000 |
| Verdict | FAIL |

Notes: prereg locked: F-20260709-05 (glv_orbit_mutual_information); Advantage near zero / shuffle does not destroy score.
