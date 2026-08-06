# F-20260709-02 — Mersenne carry ladder (PRE-REGISTERED)

**Status:** LOCKED before evaluation. Do not change formula/parameters after peeking.

| Field | Value |
|-------|-------|
| Candidate ID | F-20260709-02 |
| Short name | mersenne_carry_ladder |
| Date registered | 2026-07-09 |
| Date first evaluated | 2026-07-09 |

---

## Exact formula

```text
A_j = 2^j - 1,   j = 0,1,...,256

u_{i,j} = (d_i - A_j) mod N
Q_{i,j} = P_i - [A_j] G = (Q_x, Q_y)

g(Q) = (Q_x + Q_y) mod p
phi = factoradic lead fraction

S_j = Pearson_corr_i( phi(u_{i,j}), phi(g(Q_{i,j})) )

Δ_j = S_j^{real} - mean_b(S_j^{(b)})
      where S_j^{(b)} uses the same u but Q from shuffled puzzle index π_b
      (one π_b shared across all rungs j)

FORBIDDEN: any direct check Q=[u]G or P=[d]G.
FORBIDDEN: lead-width sweep; feature g and phi are frozen from F-20260709-01.
```

Reductions:

- [x] mod p — inside g only
- [x] mod N — scalar u only
- [ ] native top-n / lead-width
- [x] factoradic lead frac (locked)
- [x] Mersenne offset A_j = 2^j−1

## Two experiments (report separately — do not blend)

| Region | j range (per puzzle n_i) | Meaning |
|--------|--------------------------|---------|
| **Payload / carry** | `0 ≤ j ≤ n_i−1` | ordinary nonnegative difference; no wrap |
| **Modular complement** | `n_i ≤ j ≤ 256` | wraps mod N |

Global ladder still runs j=0..256 over all puzzles; region tables restrict which (i,j) enter each summary.

**Primary hinge (pre-committed focus):** for each puzzle, the transition

```text
j = n-1  →  j = n
```

where subtraction changes from non-wrapping payload to modular wrap.
Also note: `(2^{256}-1) mod N` is only ~129 bits — top rungs are not “largest scalars.”

## Score / null (multiple-testing safe)

```text
M_real = max_{0≤j≤256} |Δ_j|

For each shuffle trial b:
  recompute full 257-rung ladder with π_b
  M_b = max_j |S_j^{(b)} - mean_{b'}(S_j^{(b')})|
  (equivalently, if shuffle means ≈ 0: M_b = max_j |S_j^{(b)}|)

p_global = (#{b : M_b ≥ M_real} + 1) / (B + 1)
```

**Do not** report the ordinary per-rung p of the winning j as if it were a single test.

## Holdout discipline

1. On **train** (n∈1..50) only: j* = argmax_j |Δ_j^{train}|
2. Freeze j*
3. Evaluate that exact rung on **test** (n∈51..70): S, Δ, shuffle p
4. No second selection after seeing holdout

## Domains

| Object | Domain |
|--------|--------|
| d | puzzle band |
| A_j, u | scalars mod N |
| Q | 𝔽_p curve points |
| g | 𝔽_p |

## Allowed parameters

| Parameter | Pre-committed |
|-----------|---------------|
| Feature | identical to F-20260709-01: phi(u) vs phi((Qx+Qy) mod p) |
| j grid | {0,1,...,256} only — no other offsets |
| B shuffle trials | 500 |
| Holdout | train 1..50 / test 51..70 |
| Ranges | 1..35 / 36..70 |

Isolates: **was the offset wrong, rather than the feature?**

## Null families

| Null | Role |
|------|------|
| Shuffle π (shared across j) | wrong attachment; builds p_global |
| Native-n sawtooth control | false-positive benchmark |
| Hinge-only shuffle | j∈{n−1,n} local transition |

## Trivial-class exclusion

1. Not DL recompute — never scores Q=[u]G.
2. Not curve membership alone — phi(u)↔phi(g(Q)) not implied by y²=x³+7; wrong Q must destroy any real signal.

## Laboratory question

> With the locked coordinate-sum factoradic feature, does any Mersenne offset A_j=2^j−1 create a pairing fingerprint that survives a 257-rung search null — especially at the j=n−1→n wrap hinge?

## Promotion gate

Same as lab standard, applied to **holdout-frozen j*** and requiring **p_global < 0.01** for the ladder search (not a cherry-picked rung p).

```text
advantage(j*) > 0.12
p_shuffle(j*) < 0.01
p_global < 0.01
holds out-of-sample at frozen j*
direction consistent
```

## Result (evaluated 2026-07-09)

| Metric | Value |
|--------|------:|
| M_real | 0.3119 (j_peak=65) |
| p_global | 0.5250 |
| j* (train) | 3 |
| holdout S / Δ / p | +0.3257 / +0.3367 / 0.1677 |
| hinge j=n-1 Δ / p | -0.0127 / 0.9321 |
| hinge j=n Δ / p | +0.0000 / 1.0000 |
| Verdict | FAIL |

Notes: Feature locked from F-01. Global null pays for 257-rung search. j* frozen from train.
