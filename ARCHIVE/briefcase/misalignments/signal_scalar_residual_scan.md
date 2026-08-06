# signal_scalar_residual_scan

Wrong model (rejected): `frac(signal) · width → d`

This scan:

```text
scalar_position = (d - L) / width
residual = scalar_position - signal
spearman / kendall(signal, scalar_position)
P135 nearest neighbors in public fingerprint space
```

## Rank correlations

| signal | spearman | kendall | verdict |
|--------|----------|---------|---------|
| `x_ratio` | -0.2738 | -0.1769 | **WEAK** |
| `packet_frac` | -0.2738 | -0.1769 | **WEAK** |
| `y_ratio` | -0.1666 | -0.1172 | **WEAK** |
| `pmy_ratio` | +0.1666 | +0.1172 | **WEAK** |
| `p_to_n_floor_drift` | -0.1173 | -0.0798 | **REJECT** |
| `px2_ratio` | -0.0532 | -0.0340 | **REJECT** |
| `gx_ratio` | +0.0467 | +0.0340 | **REJECT** |
| `px1_ratio` | +0.0211 | +0.0033 | **REJECT** |
| `packet_defect_frac` | +0.0000 | +0.0000 | **REJECT** |
| `packet_N_frac` | +0.0000 | +0.0000 | **REJECT** |
| `packet_B4_frac` | +0.0000 | +0.0000 | **REJECT** |
| `defect_displacement_frac` | +0.0000 | +0.0000 | **REJECT** |

Best: `x_ratio` spearman=-0.2738

Any PROMISING/STRONG? **False**

## Residual stats (scalar_position − signal)

| signal | mean | stdev | min | max |
|--------|------|-------|-----|-----|
| `x_ratio` | +0.0640 | 0.4339 | -0.8692 | +0.9565 |
| `y_ratio` | -0.0014 | 0.4193 | -0.8912 | +0.7710 |
| `pmy_ratio` | +0.0044 | 0.3584 | -0.8333 | +0.7838 |
| `packet_frac` | +0.0640 | 0.4339 | -0.8692 | +0.9565 |
| `packet_defect_frac` | +0.5015 | 0.2696 | +0.0000 | +0.9780 |
| `packet_N_frac` | +0.5015 | 0.2696 | +0.0000 | +0.9780 |
| `packet_B4_frac` | +0.5015 | 0.2696 | +0.0000 | +0.9780 |
| `gx_ratio` | -0.0024 | 0.3949 | -0.8294 | +0.7716 |
| `px1_ratio` | +0.0218 | 0.3682 | -0.7917 | +0.8620 |
| `px2_ratio` | +0.0039 | 0.3911 | -0.8243 | +0.7294 |
| `p_to_n_floor_drift` | -338278380902415728801123997536850426511500446975551950815232.0000 | 2648545501843130335353807232960987774079000055838943075106816.0000 | -6223216700940001872061591709730357896085712825409855761154048.0000 | +6354289047538523844250642951392638582188853424097120544096256.0000 |
| `defect_displacement_frac` | +0.5015 | 0.2696 | +0.0000 | +0.9780 |

## P135 nearest solved neighbors (public fingerprint)

Neighbor mean scalar_position = `0.5440` → cluster hint: **middle_third**

| rank | puzzle | distance | scalar_position | offset_from_mid |
|------|--------|----------|-----------------|-----------------|
| 1 | 4 | 0.2737 | 0.0000 | -0.5000 |
| 2 | 30 | 0.2816 | 0.9244 | +0.4244 |
| 3 | 18 | 0.3774 | 0.5157 | +0.0157 |
| 4 | 20 | 0.4125 | 0.6466 | +0.1466 |
| 5 | 58 | 0.4604 | 0.3876 | -0.1124 |
| 6 | 47 | 0.4639 | 0.7006 | +0.2006 |
| 7 | 34 | 0.4646 | 0.6453 | +0.1453 |
| 8 | 22 | 0.4786 | 0.4341 | -0.0659 |
| 9 | 64 | 0.4963 | 0.9298 | +0.4298 |
| 10 | 66 | 0.5031 | 0.2562 | -0.2438 |

## Ruling

```text
The map is real.
The direct projection is false.
The fingerprint instrument is valid.
The scalar mask is not in raw range or raw packet fractions.
```

Ask: do packet/defect/β signals cluster solved puzzles by scalar behavior?

Judge Popcorn: **the stars are real, but the first star chart used a flat ruler on curved sky.**
