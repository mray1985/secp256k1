# packet_range_error_bitmask

Point-derived rulers: `expected = L + floor(frac(signal) · width)`

Range-only baseline entropy ≈ **6.3**

Thresholds: STRONG >50% reconstruct · PROMISING count≥5 & entropy≪6.3 · WEAK 2–3 · REJECT

## Rankings

| ruler | entropy | best_pattern_count | transfer_reconstruct | puzzles_matched | beats_6.3 | verdict |
|-------|---------|--------------------|--------------------|-----------------|-----------|---------|
| `gx_ratio_width` | 6.284 | 2 | 2 | 2/82 | False | **WEAK** |
| `packet_B4_width` | 6.300 | 3 | 4 | 4/82 | False | **WEAK** |
| `px1_ratio_width` | 6.300 | 3 | 3 | 3/82 | False | **WEAK** |
| `packet_width` | 6.309 | 2 | 2 | 2/82 | False | **WEAK** |
| `x_ratio_width` | 6.309 | 2 | 2 | 2/82 | False | **WEAK** |
| `hinge_control` | 6.309 | 2 | 2 | 2/82 | False | **WEAK** |
| `packet_defect_width` | 6.333 | 2 | 2 | 2/82 | False | **WEAK** |
| `y_ratio_width` | 6.333 | 2 | 2 | 2/82 | False | **WEAK** |
| `pmy_ratio_width` | 6.333 | 2 | 3 | 3/82 | False | **WEAK** |
| `beta_slot_width` | 6.333 | 2 | 2 | 2/82 | False | **WEAK** |
| `px2_ratio_width` | 6.333 | 2 | 3 | 3/82 | False | **WEAK** |
| `packet_N_shadow` | 6.358 | 1 | 1 | 1/82 | False | **REJECT** |

## Top patterns

### `gx_ratio_width` — WEAK

- count **2**: `[]`
- count **2**: `[-2, -1]`
- count **2**: `[-3, -1]`

### `packet_B4_width` — WEAK

- count **3**: `[-1]`
- count **1**: `[]`
- count **1**: `[-2, -1]`

### `px1_ratio_width` — WEAK

- count **3**: `[]`
- count **1**: `[-2, -1]`
- count **1**: `[-2]`

### `packet_width` — WEAK

- count **2**: `[]`
- count **2**: `[-3]`
- count **1**: `[-1]`

### `x_ratio_width` — WEAK

- count **2**: `[]`
- count **2**: `[-3]`
- count **1**: `[-1]`

### `hinge_control` — WEAK

- count **2**: `[]`
- count **2**: `[-2]`
- count **1**: `[-1]`

### `packet_defect_width` — WEAK

- count **2**: `[]`
- count **1**: `[-1]`
- count **1**: `[-3, -2]`

### `y_ratio_width` — WEAK

- count **2**: `[]`
- count **1**: `[-2]`
- count **1**: `[-3, -1]`

### `pmy_ratio_width` — WEAK

- count **2**: `[-1]`
- count **1**: `[]`
- count **1**: `[-2]`

### `beta_slot_width` — WEAK

- count **2**: `[]`
- count **1**: `[-2]`
- count **1**: `[-3, -1]`

### `px2_ratio_width` — WEAK

- count **2**: `[-1]`
- count **1**: `[]`
- count **1**: `[-2]`

### `packet_N_shadow` — REJECT

- count **1**: `[]`
- count **1**: `[-1]`
- count **1**: `[-2, -1]`

## P135 candidates

_None — no STRONG transferable mask._

## Ruling

Best entropy: `6.284` on `gx_ratio_width` (baseline 6.3).

Beats baseline? **False**

Judge Popcorn: **the range fence alone is not the sky. Telescope on Px, Py, packet, defect, β — only [d]G is sunrise.**
