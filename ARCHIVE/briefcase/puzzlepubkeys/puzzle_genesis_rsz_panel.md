# Genesis RSZ scalar panel (revised scope)

Genesis: `08389f34c98c606322740c0be6a7125d9860bb8d5cb182c02f98461e5fa6cd15`  
Sweep 161-256: `5d45587cfd1d5b0fb826805541da7d94c61fe432259e68ee26f4a04544384164`

Puzzles with RSZ: **184** (every spent genesis output). **72 unspent** — no signature exists.

## What this test closes

> Does a **single normalized signature coordinate** (r/N, s/N, z/N, k⁻¹ left5) correlate with puzzle index n?

**Answer:** No strong honest signal on 161-256 (r/N perm p≈0.69). P135 sits inside the 161-256 cloud on r/N and z/N.

## What this test does NOT close

Coupled hypotheses in **f(r, s, z, k, d, p, N)**:

- s·k ≡ z + r·d (mod N) as a system, not marginals
- p−N field↔scalar bridge
- TDAD / d-paths
- Echo constructions on scalars
- Transaction batching structure (hashkeys partial spend, 96-input sweep)

Pearson on r/N alone cannot falsify those.

---

## Marginal correlations (all 184 spent)

| feature | r(n) |
|---------|------|
| r/N | +0.07 |
| s/N | −0.19 |
| z/N | −0.04 |
| k⁻¹ left5 (82 with d) | −0.11 |

## Band 65–160: the 0.61 question

Raw Pearson(n, r/N) = **0.61** — but **only n=24** puzzles have RSZ in this band (uneven indices: 65–69, then every 5th through 160). Do not over-read.

Control tests (`analyze_rsz_band_controls.py`):

| control | result |
|---------|--------|
| Pearson(n, r.bit_length) | +0.48 |
| Pearson(r.bits, r/N) | **+0.88** (r/N tracks magnitude/size) |
| partial(n, r/N \| r.bits) | **−0.47** (n signal not independent of bit length) |
| permute r/N within r.bit buckets | p=0.078 (borderline; n=24 small) |
| solved-with-d only (n=18) | r(n, r/N) drops to **0.32** |
| independent tx only (n=4) | too few to test |

**Interpretation:** The 0.61 is **plausibly scale/sampling mediated**, not closed as proof either way. Partial correlation collapses once r.bit_length is controlled; uneven puzzle spacing in the sample is an additional confound.

161-256 (n=96, uniform): r(n, r/N) = **0.04**.

---

## P135 projection (vs 161-256)

| quantity | P135 | z-score vs 161-256 |
|----------|------|---------------------|
| r/N | 0.783 | +0.99 |
| s/N | 0.134 | −0.64 |
| z/N | 0.572 | +0.43 |

Near the batch cloud, not an outlier trail.

---

## Next experiments (coupled, not marginal)

1. Residuals of s·k − z − r·d mod N against solved panel (should be 0; look at *structure of k* not r alone)
2. k⁻¹ mod N prefix vs 5⁻¹ mod N anchor — on solved spends only
3. (r/N − map_p_to_n(Px)) roof stitch across solved + P135
4. **AD operation paths** from `F:\New folder\secp256k1\DOUBLE_AND_ADD+BREAKDOWN.txt` + briefcase rules → `analyze_ad_operation_path.py`
5. Sweep vin order vs genesis vout (chain metadata)

Files: `puzzle_genesis_rsz_1_256.json`, `puzzle_genesis_rsz_band_controls.json`, **`puzzle_genesis_rsz_coupled.{md,json}`** (script: `analyze_rsz_coupled_invariants.py`)
