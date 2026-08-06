# hinge_power_signal_scan

For puzzle `n`:

```text
e_n = (n - 1 + HINGE) / 256
signal = (v / p) ** e_n
```

Example P130: `e_130 = (129 + HINGE) / 256 = 0.506191259768442`
Example P135: `e_135 = 0.525722509768442`

Applied to Px, Py, p−y, β-slots, differences from G, ratios, squares, curve polynomial.

## Rank correlations vs scalar_position

Prior plain `x_ratio` spearman ≈ **-0.2738**

| signal | spearman | kendall | verdict |
|--------|----------|---------|---------|
| `Px` | -0.2799 | -0.1943 | **WEAK** |
| `Px3` | -0.2799 | -0.1943 | **WEAK** |
| `packet_frac_pow` | -0.2799 | -0.1943 | **WEAK** |
| `x_ratio_pow` | -0.2799 | -0.1943 | **WEAK** |
| `Py` | -0.2260 | -0.1600 | **WEAK** |
| `Py_sq` | -0.1955 | -0.1401 | **WEAK** |
| `Px_cubed_plus_7` | -0.1955 | -0.1401 | **WEAK** |
| `Px_sq` | -0.1681 | -0.1172 | **WEAK** |
| `Px_pow_minus_Gx_pow` | +0.1232 | +0.0823 | **REJECT** |
| `Px2` | -0.1046 | -0.0774 | **REJECT** |
| `Px1` | -0.0958 | -0.0678 | **REJECT** |
| `pmy_minus_Gy` | -0.0893 | -0.0606 | **REJECT** |
| `p_minus_y` | +0.0447 | +0.0262 | **REJECT** |
| `Px_minus_Gx` | +0.0341 | +0.0220 | **REJECT** |
| `Py_minus_Gy` | +0.0296 | +0.0087 | **REJECT** |
| `Px_times_Gx_inv` | +0.0287 | +0.0244 | **REJECT** |
| `Py_times_Gy_inv` | -0.0229 | -0.0202 | **REJECT** |
| `Px_plus_Gx` | +0.0142 | +0.0087 | **REJECT** |
| `Py_pow_minus_Gy_pow` | +0.0137 | +0.0105 | **REJECT** |
| `defect_frac_pow` | +0.0000 | +0.0000 | **REJECT** |

Best: `Px` (-0.2799)

Beats plain x_ratio? **True**

## P135 hinge-power neighbors

e_135 = `0.525722509768442`
Neighbor mean scalar_position = `0.5490` → **middle_third** (weak hint)

| rank | puzzle | distance | scalar_position |
|------|--------|----------|-----------------|
| 1 | 64 | 0.894378 | 0.9298 |
| 2 | 58 | 0.900142 | 0.3876 |
| 3 | 53 | 0.919063 | 0.5018 |
| 4 | 115 | 0.937036 | 0.5149 |
| 5 | 110 | 0.951827 | 0.6798 |
| 6 | 67 | 0.999437 | 0.7978 |
| 7 | 90 | 1.039393 | 0.4023 |
| 8 | 85 | 1.052337 | 0.0903 |
| 9 | 68 | 1.072640 | 0.4901 |
| 10 | 62 | 1.148544 | 0.6950 |

## Ledger placement

```text
REJECTED (still):
  direct frac(signal)·width → d
  transferable binary error mask from range/packet rulers

VALID:
  fingerprint / exclusion filter
  hinge-power as per-puzzle warp of public coordinates

DOOR:
  candidate d/k → range → [d]G == P135 → RSZ
```

Judge Popcorn: **stars confirm where we think we are; they do not pave a road to d.**
