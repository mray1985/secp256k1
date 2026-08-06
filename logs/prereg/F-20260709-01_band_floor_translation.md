# F-20260709-01 — Band-floor translation (PRE-REGISTERED)

**Status:** LOCKED before evaluation. Do not change formula/parameters after peeking.

| Field | Value |
|-------|-------|
| Candidate ID | F-20260709-01 |
| Short name | band_floor_translation |
| Date registered | 2026-07-09 |
| Date first evaluated | 2026-07-09 |

---

## Exact formula

```text
u_i = d_i - 2^{n_i - 1}

Q_i = P_i - [2^{n_i - 1}] G
    = (Q_{x,i}, Q_{y,i})

g(Q_x, Q_y) = (Q_x + Q_y) mod p

phi(x) = factoradic lead fraction of x
       = a_max / max_k   (0 if x = 0)

F is not evaluated pointwise as a verifier.
score = Pearson_corr( {phi(u_i)}, {phi(g(Q_{x,i}, Q_{y,i}))} )
```

Reductions:

- [x] mod p (field) — only inside `g = (Qx+Qy) mod p`
- [ ] mod N
- [ ] native bit-length / top-n  **(explicitly forbidden — no lead-width sweep)**
- [x] factoradic lead frac
- [x] other: EC translation by known band floor `[2^{n-1}]G`

**Forbidden:** any check of `Q == [u]G` or `P == [d]G`.

## Domains

| Object | Domain |
|--------|--------|
| d | puzzle band `[2^{n-1}, 2^n)` |
| u | payload in `[0, 2^{n-1})` |
| Px, Py / Qx, Qy | 𝔽_p curve points |
| g(Qx,Qy) | 𝔽_p |

## Score definition

```text
score = Pearson correlation of phi(u) vs phi(g(Qx,Qy)) across puzzles 1..70
```

**Expected direction (locked):** higher is better.

## Allowed parameters

| Parameter | Pre-committed value(s) |
|-----------|------------------------|
| *(none)* | single primary cell only — no grid, no lead-width sweep |

## Holdout split

| Split | Definition |
|-------|------------|
| Train | n ∈ 1..50 |
| Test | n ∈ 51..70 |
| Range A / B | 1..35 / 36..70 |

## Null families

| Null | Construction |
|------|----------------|
| Shuffle π | keep `u_i`, assign `Q_π(i)` (shuffle **translated** points, not raw P with wrong floor) |
| Random (n−1)-bit | random `u' ∈ [0, 2^{n-1})` with random field-like `(Qx',Qy')` |
| Random EC | random `u' ∈ [0, 2^{n-1})` with true `Q' = [u']G` |
| Nearby height | attach `Q` from a puzzle with `|n_i−n_j|≤3` |
| Control | native-`n` sawtooth on original `(d, Px)` — false-positive benchmark |

## Trivial-class exclusion

1. **Not DL recompute:** score never tests `Q=[u]G` / `P=[d]G`.
2. **Not curve membership alone:** `phi(u)` vs `phi((Qx+Qy) mod p)` is not implied by `y²=x³+7`; wrong `Q` should destroy the correlation if any pairing signal exists.

Justification: uses private payload `u` and both coordinates of the translated point jointly; curve equation alone does not fix `phi(u)↔phi(g(Q))`; permutation of `Q` among `u` breaks correct attachment.

## Laboratory question

> After removing the known `2^{n-1}` band floor, does the correct private payload leave any compact fingerprint on its translated public point that disappears under wrong attachment?

## Promotion gate

```text
advantage > 0.12
p_shuffle < 0.01
beats random (n-1)-bit
beats random EC pairs
holds out-of-sample
direction consistent across ranges
```

## Result (evaluated 2026-07-09)

| Metric | Value |
|--------|------:|
| score_real | -0.0709 |
| score_shuffled | -0.0018 |
| Δ (advantage) | -0.0691 |
| p_shuffle | 0.5734 |
| train / test score | -0.0012 / -0.1432 |
| train / test advantage | -0.0100 / -0.1650 |
| Verdict | FAIL |

Notes: prereg locked: F-20260709-01 (band_floor_translation); Advantage near zero / shuffle does not destroy score.
