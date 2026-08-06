# TDAD index playlist scan

```text
TDAD determinant = fixed rhythm [3,2,1,2] + unique index path
Operators: low-entropy.  Indices: high-entropy.
```

## Global constraints (solved playlists)

| metric | value |
|--------|-------|
| playlists parsed | 21 |
| pure `[3,2,1,2]^k` | 4 |
| unique prior indices used | 66 |
| unique `(coeff,index)` pairs | 140 |
| cycle count distribution | {1: 3, 3: 1, 8: 2, 10: 2} |
| distance n−index (mean) | 26.40 |
| 10-cycle puzzles | [70, 71] |
| 8-cycle puzzles | [69, 72] |

### Top index frequency (corpus)

- P5: 15 term slots
- P7: 14 term slots
- P1: 12 term slots
- P14: 11 term slots
- P3: 11 term slots
- P2: 10 term slots
- P4: 9 term slots
- P13: 8 term slots
- P8: 8 term slots
- P10: 7 term slots
- P58: 6 term slots
- P19: 6 term slots

### Anchor index hits (65, 70, 75, …)

```json
{
  "65": 2,
  "70": 1
}
```

### Cycle-position preferences

**Slot 0 (triple, coeff 3)** — top indices: P13×4, P6×4, P1×4, P10×4, P4×3, P2×3
**Slot 1 (double, coeff 2)** — top indices: P5×6, P14×3, P7×3, P1×3, P3×3, P4×3
**Slot 2 (add, coeff 1)** — top indices: P7×5, P5×5, P9×4, P3×3, P58×2, P42×2
**Slot 3 (double, coeff 2)** — top indices: P1×4, P7×4, P63×3, P14×3, P4×3, P2×3

## Per-puzzle playlists

| n | terms | cycles | pure 3212 | unique idx | max reuse | anchors | eval |
|---|-------|--------|-----------|------------|-----------|---------|------|
| 2 | 1 | None | False | 1 | 1 | 0 | False |
| 3 | 2 | None | False | 2 | 1 | 0 | False |
| 4 | 3 | None | False | 2 | 2 | 0 | False |
| 5 | 1 | None | False | 1 | 1 | 0 | False |
| 6 | 2 | None | False | 2 | 1 | 0 | False |
| 7 | 4 | 1 | False | 4 | 1 | 0 | False |
| 8 | 5 | None | False | 3 | 3 | 0 | False |
| 9 | 6 | None | False | 3 | 3 | 0 | False |
| 10 | 4 | 1 | False | 3 | 2 | 0 | False |
| 11 | 5 | None | False | 4 | 2 | 0 | False |
| 12 | 5 | None | False | 4 | 2 | 0 | False |
| 13 | 10 | None | False | 8 | 2 | 0 | False |
| 14 | 4 | 1 | False | 3 | 2 | 0 | False |
| 15 | 10 | None | False | 7 | 3 | 0 | False |
| 16 | 10 | None | False | 8 | 2 | 0 | False |
| 17 | 12 | 3 | False | 8 | 4 | 0 | False |
| 68 | 33 | None | False | 27 | 3 | 1 | False |
| 69 | 32 | 8 | True | 24 | 3 | 0 | True |
| 70 | 40 | 10 | True | 33 | 2 | 1 | False |
| 71 | 40 | 10 | True | 33 | 2 | 0 | True |
| 72 | 32 | 8 | True | 29 | 2 | 1 | True |

## P135 projection

```json
{
  "puzzle": 135,
  "expected_rhythm": [
    3,
    2,
    1,
    2
  ],
  "expected_cycles_guess": 10,
  "expected_terms_guess": 40,
  "formula": "T_135 = \u03a3 coeff_i * d_{index_i}  with coeff from [3,2,1,2]*10",
  "index_slots_unknown": 40,
  "available_prior_indices": 84,
  "available_anchor_indices": [
    65,
    70,
    75,
    80,
    85,
    90,
    95,
    100,
    105,
    110,
    115,
    120,
    125,
    130
  ],
  "gates": [
    "T_135 in [2^134, 2^135)",
    "[T_135]G == P135 compressed address"
  ],
  "warnings_from_p71_p72": "Correct [3,2,1,2] rhythm + wrong playlist \u2192 range-valid scalar, fails address gate",
  "constraints_from_solved": {
    "pure_3212_rate": "4/21 playlists",
    "common_cycle_counts": {
      "1": 3,
      "3": 1,
      "8": 2,
      "10": 2
    },
    "top_anchor_indices": [
      65,
      70
    ],
    "distance_mean_prior": 26.39846743295019,
    "max_reuse_seen": 4
  },
  "search_target": "index path [a1..a40], NOT operator combinations",
  "status": "index playlist missing \u2014 rhythm known"
}
```

## Ruling

The drummer is obvious: [3,2,1,2] repeated. The sheet music is the index playlist. P71/P72 prove rhythm without correct indices fails [T]G=P. P135 search target: 40 index slots (10 cycles), not operator combos.
