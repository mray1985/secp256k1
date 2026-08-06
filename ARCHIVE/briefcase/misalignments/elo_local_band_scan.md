# elo_local_band_scan

Preferred shell: `e_lo = (n−1)/256` — filter coordinate, not scalar predictor.

## Local-band: does e_lo distance track scalar gap?

For each solved target, neighbors in `n±10` / `n±20` (solved only).
Spearman(fingerprint_distance, |scalar_position − target|).

Positive ⇒ closer fingerprints sit closer in range (local clustering).

### radius ±10

- n targets: `81`
- mean spearman: `+0.0602`
- stdev: `0.3514`
- fraction ρ > 0: `0.54`
- fraction ρ > 0.15: `0.33`

### radius ±20

- n targets: `82`
- mean spearman: `+0.0263`
- stdev: `0.2378`
- fraction ρ > 0: `0.52`
- fraction ρ > 0.15: `0.23`

## High-bit telescope (P135)

Control set: `[110, 115, 120, 125, 130, 135, 140, 145, 150, 155, 160]`
Solved present in set: `[110, 115, 120, 125, 130]`

| puzzle | status | e_lo | dist to P135 | scalar_position |
|--------|--------|------|--------------|-----------------|
| 110 | solved | 0.425781 | 0.573671 | 0.6798 |
| 115 | solved | 0.445312 | 0.650498 | 0.5149 |
| 120 | solved | 0.464844 | 1.075253 | 0.3833 |
| 125 | solved | 0.484375 | 1.039784 | 0.7703 |
| 130 | solved | 0.503906 | 0.750325 | 0.6220 |
| 135 | public_only | 0.523438 | 0.000000 | — |
| 140 | public_only | 0.542969 | 0.839081 | — |
| 145 | public_only | 0.562500 | 0.961128 | — |
| 150 | public_only | 0.582031 | 0.785030 | — |
| 155 | public_only | 0.601562 | 0.852426 | — |
| 160 | public_only | 0.621094 | 1.095077 | — |

Solved-neighbor cluster hint: **middle_third** (mean scalar `0.6055765183352873`)

## Verdict

```text
REJECTED: three-slice power as scalar predictor
VALID:    e_lo as preferred normalization shell
LOCAL:    see spearman stats above
DOOR:     candidate gate stack / [d]G / RSZ
```

`e_lo` wins the shell; it does not open the door.

Judge Popcorn: **we found the best lens, not the star's address.**
