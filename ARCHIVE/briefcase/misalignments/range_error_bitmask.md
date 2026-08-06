# range_error_bitmask — misalignment fingerprints

For each solved puzzle and each ruler:

```text
error_n = actual_d - expected_landing
error_n = Σ 2^i  (set bits)
relative_bits = bit - (n-1)
```

**Case:** `B_weak_structure`

Some repeated patterns; not yet a clean global mask.

## Ruler rankings (lower entropy = more structure)

| Rank | Ruler | Entropy | Unique patterns | Best pattern count | Mean popcount |
|------|-------|---------|-----------------|--------------------|---------------|
| 1 | `upper_anchor` | 6.300 | 80 | 3 | 22.50 |
| 2 | `lower_anchor` | 6.309 | 80 | 2 | 21.80 |
| 3 | `hinge_58496_range` | 6.309 | 80 | 2 | 21.94 |
| 4 | `hinge_58496_power` | 6.309 | 80 | 2 | 21.22 |
| 5 | `log_midpoint` | 6.309 | 80 | 2 | 20.87 |
| 6 | `midpoint` | 6.333 | 81 | 2 | 21.39 |
| 7 | `quarter` | 6.333 | 81 | 2 | 21.40 |
| 8 | `three_quarter` | 6.358 | 82 | 1 | 21.71 |

## Top patterns per ruler

### `upper_anchor`

- count **3**: `[]` → 0
- count **1**: `[-3, -2, -1]` → 2^(n-1-1) + 2^(n-1-2) + 2^(n-1-3)
- count **1**: `[-3, -1]` → 2^(n-1-1) + 2^(n-1-3)

### `lower_anchor`

- count **2**: `[]` → 0
- count **2**: `[-2, -1]` → 2^(n-1-1) + 2^(n-1-2)
- count **1**: `[-1]` → 2^(n-1-1)

### `hinge_58496_range`

- count **2**: `[]` → 0
- count **2**: `[-2]` → 2^(n-1-2)
- count **1**: `[-1]` → 2^(n-1-1)

### `hinge_58496_power`

- count **2**: `[]` → 0
- count **2**: `[-2]` → 2^(n-1-2)
- count **1**: `[-1]` → 2^(n-1-1)

### `log_midpoint`

- count **2**: `[-1]` → 2^(n-1-1)
- count **2**: `[-8, -5, -3, -2]` → 2^(n-1-2) + 2^(n-1-3) + 2^(n-1-5) + 2^(n-1-8)
- count **1**: `[]` → 0

### `midpoint`

- count **2**: `[-1]` → 2^(n-1-1)
- count **1**: `[]` → 0
- count **1**: `[-3, -2]` → 2^(n-1-2) + 2^(n-1-3)

### `quarter`

- count **2**: `[-3]` → 2^(n-1-3)
- count **1**: `[]` → 0
- count **1**: `[-1]` → 2^(n-1-1)

### `three_quarter`

- count **1**: `[]` → 0
- count **1**: `[-1]` → 2^(n-1-1)
- count **1**: `[-2]` → 2^(n-1-2)

## Transfer test (reconstruct mask from relative bits)

- ruler: `upper_anchor`
- pattern: `[]`
- exact matches: **3** / 82 (3.7%)

## Sample rows (best ruler, first 15 solved)

Ruler: `upper_anchor`

| P | expected | error bits | relative_msb | popcount | norm_err |
|---|----------|------------|--------------|----------|----------|
| 1 | `1…` | `[]` | `[]` | 0 | `0` |
| 2 | `3…` | `[]` | `[]` | 0 | `0` |
| 3 | `7…` | `[]` | `[]` | 0 | `0` |
| 4 | `15…` | `[0, 1, 2]` | `[-3, -2, -1]` | 3 | `-0.875` |
| 5 | `31…` | `[1, 3]` | `[-3, -1]` | 2 | `-0.625` |
| 6 | `63…` | `[1, 2, 3]` | `[-4, -3, -2]` | 3 | `-0.4375` |
| 7 | `127…` | `[0, 1, 4, 5]` | `[-6, -5, -2, -1]` | 4 | `-0.796875` |
| 8 | `255…` | `[0, 1, 2, 3, 4]` | `[-7, -6, -5, -4, -3]` | 5 | `-0.2421875` |
| 9 | `511…` | `[2, 3, 5]` | `[-6, -5, -3]` | 3 | `-0.171875` |
| 10 | `1023…` | `[0, 2, 3, 4, 5, 6, 7, 8]` | `[-9, -7, -6, -5, -4, -3, -2, -1]` | 8 | `-0.994140625` |
| 11 | `2047…` | `[2, 3, 4, 5, 6, 8, 9]` | `[-8, -7, -6, -5, -4, -2, -1]` | 7 | `-0.87109375` |
| 12 | `4095…` | `[2, 7, 8, 10]` | `[-9, -4, -3, -1]` | 4 | `-0.689453125` |
| 13 | `8191…` | `[0, 1, 2, 3, 4, 7, 8, 9, 11]` | `[-12, -11, -10, -9, -8, -5, -4, -3, -1]` | 9 | `-0.726318359` |
| 14 | `16383…` | `[0, 1, 2, 3, 6, 7, 9, 10, 12]` | `[-13, -12, -11, -10, -7, -6, -4, -3, -1]` | 9 | `-0.712768554` |
| 15 | `32767…` | `[2, 3, 8, 9, 10, 12]` | `[-12, -11, -6, -5, -4, -2]` | 6 | `-0.360107421` |

## P135 ruler landings (no d — candidates only if mask transfers)

- **lower_anchor:** `21778071482940061661655974875633165533184`
- **upper_anchor:** `43556142965880123323311949751266331066367`
- **midpoint:** `32667107224410092492483962313449748299775`
- **hinge_58496_range:** `34517426638484778351476028754534349894733`
- **hinge_58496_power:** `32667107224410092492483962313449748299780`
- **log_midpoint:** `30798844053504577477764322877136007286670`
- **quarter:** `27222589353675077077069968594541456916479`
- **three_quarter:** `38111625095145107907897956032358039683071`

_No auto candidates — mask does not transfer cleanly enough._

## Ruling

```text
Case A: random-looking offsets → ruler not predictive
Case B: structured offsets → error_n = shifted_mask(n)
         candidate_d = expected_landing + shifted_mask(135)
         truth: [candidate_d]G == P135
```

This scan: **B_weak_structure**.

Judge Popcorn: **binary fingerprints are constellations. Only [d]G is sunrise.**
