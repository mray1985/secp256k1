# P160 band — full RIPEMD160 decimal correlation sweep

Sample: `d = 2^159 + offset`, offset `0..9999`
P160 anchor (49 digits): `1326093679998364004747100419105194353286137352850`

## Top correlations with band offset

| feature | Pearson | Spearman |
|---------|---------|----------|
| digit_pos17 | -0.01905 | +0.02120 |
| digit_pos5 | -0.01951 | -0.01727 |
| mid[13:16] | -0.01873 | -0.01872 |
| digit_pos12 | -0.01426 | -0.01751 |
| digit_pos39 | +0.01680 | +0.00374 |
| digit_pos26 | +0.01499 | -0.00274 |
| mid[26:29] | +0.01491 | +0.01469 |
| mid[26:31] | +0.01491 | +0.01470 |
| digit_pos41 | +0.01447 | +0.00359 |
| suffix_dist_k5 | -0.01421 | n/a |
| mid[44:49] | -0.01421 | -0.00498 |
| mid[44:47] | -0.01419 | -0.00498 |
| digit_pos30 | -0.01406 | +0.00625 |
| digit_pos28 | +0.01356 | -0.00871 |
| suffix_dist_k9 | +0.01311 | n/a |
| mid[40:49] | +0.01311 | +0.01213 |
| mid[40:45] | +0.01311 | +0.01213 |
| mid[40:43] | +0.01310 | +0.01212 |
| mid[6:9] | -0.01305 | -0.01031 |
| mid[6:13] | -0.01304 | -0.01031 |
| digit_pos14 | +0.01301 | +0.00787 |
| digit_pos23 | +0.01222 | -0.00612 |
| suffix match length | -0.00860 | -0.01212 |
| last decimal digit | +0.01125 | +0.01136 |
| suffix_dist_k1 | +0.01125 | n/a |

Features with |r|>0.05: **0**

## Ruling

No material correlation between band offset and any decimal segment of hash160.
P160 anchor alignment does not tighten as d walks the band floor.