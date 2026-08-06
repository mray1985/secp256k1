# three_slice_hinge_power

For puzzle `n`:

```text
e_hi    = n / 256
e_lo    = (n - 1) / 256
e_hinge = (n - 1 + HINGE) / 256

signal = (v / p) ** e
priv   = (d / 2^256) ** e   (and d/2^n, d/2^(n-1), d/N, scalar_position)
distance = |signal - priv|
```

P130: `e_hi=0.5078125` `e_lo=0.50390625` `e_hinge=0.506191259768442`
P135: `e_hi=0.52734375` `e_lo=0.5234375` `e_hinge=0.525722509768442`

## Which slice lands closest to priv?

| slice | wins (of 82) | mean closest distance |
|-------|----------------------|------------------------|
| `e_lo` | 79 | 0.006213 |
| `e_hinge` | 2 | 0.006359 |
| `e_hi` | 1 | 0.006451 |

**Winning slice:** `e_lo`

## Smallest mean distances (signal vs priv)

| slice | pair | mean_distance | stdev |
|-------|------|---------------|-------|
| `e_lo` | `Px__vs__d_over_2_n` | 0.129706 | 0.136872 |
| `e_hinge` | `Px__vs__d_over_2_n` | 0.131200 | 0.137496 |
| `e_hi` | `Px__vs__d_over_2_n` | 0.132256 | 0.137942 |
| `e_lo` | `Px__vs__scalar_position_pow` | 0.157694 | 0.182413 |
| `e_hinge` | `Px__vs__scalar_position_pow` | 0.159241 | 0.182264 |
| `e_hi` | `Px__vs__scalar_position_pow` | 0.160333 | 0.182167 |
| `e_lo` | `Px__vs__d_over_2_n_minus_1` | 0.238449 | 0.206229 |
| `e_hinge` | `Px__vs__d_over_2_n_minus_1` | 0.241354 | 0.206863 |
| `e_hi` | `Px__vs__d_over_2_n_minus_1` | 0.243412 | 0.207317 |
| `e_hi` | `Px__vs__scalar_position` | 0.395188 | 0.267848 |
| `e_hi` | `packet_frac__vs__scalar_position` | 0.395188 | 0.267848 |
| `e_hinge` | `Px__vs__scalar_position` | 0.395890 | 0.268009 |

## Rank correlation (powered signal vs priv norm)

| slice | signal | priv_norm | spearman | verdict |
|-------|--------|-----------|----------|---------|
| `e_lo` | `Px` | `d_over_2_256` | +0.7018 | **STRONG** |
| `e_lo` | `Px` | `d_over_N` | +0.7018 | **STRONG** |
| `e_lo` | `packet_frac` | `d_over_2_256` | +0.7018 | **STRONG** |
| `e_lo` | `packet_frac` | `d_over_N` | +0.7018 | **STRONG** |
| `e_hinge` | `Px` | `d_over_2_256` | +0.6944 | **STRONG** |
| `e_hinge` | `Px` | `d_over_N` | +0.6944 | **STRONG** |
| `e_hinge` | `packet_frac` | `d_over_2_256` | +0.6944 | **STRONG** |
| `e_hinge` | `packet_frac` | `d_over_N` | +0.6944 | **STRONG** |
| `e_hi` | `Px` | `d_over_2_256` | +0.6899 | **STRONG** |
| `e_hi` | `Px` | `d_over_N` | +0.6899 | **STRONG** |
| `e_hi` | `packet_frac` | `d_over_2_256` | +0.6899 | **STRONG** |
| `e_hi` | `packet_frac` | `d_over_N` | +0.6899 | **STRONG** |
| `e_lo` | `Px` | `d_over_2_n_minus_1` | -0.6427 | **STRONG** |
| `e_lo` | `packet_frac` | `d_over_2_n_minus_1` | -0.6427 | **STRONG** |
| `e_hinge` | `Px` | `d_over_2_n_minus_1` | -0.6360 | **STRONG** |

Any PROMISING/STRONG on full set? **True**

## Confound control (bit-length n)

Both `(Px/p)^e` and `(d/2^256)^e` depend on `e(n)`. Across all bit lengths this
inflates Spearman:

- Px_pow vs d_pow: `+0.7018`
- Px_pow vs n: `-0.7018`
- d_pow vs n: `-1.0000` (monotonic in n)

Within bit-length bands:

- band `1_40`: n=40 spearman=`0.5589118198874297`
- band `41_80`: n=32 spearman=`0.6220674486803518`
- band `65_130`: n=18 spearman=`0.017543859649122806`

**Ruling:** full-set STRONG is mostly **n-confound**. Band 65–130 collapses to ~0.
Three-slice warp remains a fingerprint tool, not a priv-distance compass.

## Sample (first 12 solved)

| P | best_slice | closest_pair | distance |
|---|------------|--------------|----------|
| 1 | `e_lo` | `Px__vs__d_over_2_256` | 0.000000 |
| 2 | `e_lo` | `Px_minus_Gx__vs__scalar_position_pow` | 0.000017 |
| 3 | `e_lo` | `Px_minus_Gx__vs__d_over_2_n` | 0.000104 |
| 4 | `e_lo` | `Px_sq__vs__d_over_2_n` | 0.000151 |
| 5 | `e_lo` | `Px_cubed_plus_7__vs__d_over_2_n` | 0.000976 |
| 6 | `e_lo` | `Px1__vs__scalar_position_pow` | 0.000106 |
| 7 | `e_lo` | `Px__vs__d_over_2_n` | 0.000258 |
| 8 | `e_lo` | `Px1__vs__scalar_position_pow` | 0.000736 |
| 9 | `e_lo` | `Px_times_Gx_inv__vs__d_over_2_n` | 0.000053 |
| 10 | `e_lo` | `Px1__vs__d_over_2_n` | 0.004096 |
| 11 | `e_lo` | `Px__vs__d_over_2_n` | 0.001442 |
| 12 | `e_lo` | `Py__vs__d_over_2_n` | 0.002485 |

## Ruling

Three range-height warps (floor, hinge, ceiling of the bit window).
Distance to priv norms tests whether any slice aligns public power with scalar power.
Still a filter/fingerprint lane unless correlation is PROMISING+.

Door: candidate gate stack / [d]G / RSZ.
