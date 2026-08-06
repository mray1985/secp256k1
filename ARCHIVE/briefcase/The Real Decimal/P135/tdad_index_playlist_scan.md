# P135 TDAD index playlist

Rhythm known: `[3,2,1,2]` × 10 cycles (40 terms guess).

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
