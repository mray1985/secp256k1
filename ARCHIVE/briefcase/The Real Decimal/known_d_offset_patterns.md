# Known-d offset pattern hunt

Solved puzzles with known `d`: **82**

Offsets = `actual_d − expected` from range/packet rulers; plus structure of `(d − L)` and `N−d`.

## Overlooked? Summary

- CONFIRMED identity: scalar_position + N_mirror_position = 1 - 1/width (floor/height switch).
- No strong overlooked leak beyond the N-mirror identity: bitmasks high-entropy, mods near chance, low-bits near chance, packet landings uncorrelated with d.

## Findings

### scalar_position + N_mirror_position = 1 - 1/width

```json
{
  "mean_abs_err": 0.0,
  "max_abs_err": 0.0,
  "holds": true,
  "note": "Floor/height switch identity (exact with inclusive bounds)"
}
```

### shared relative bitmasks of (d - L)

```json
{
  "unique_patterns": 80,
  "top": [
    {
      "pattern": [],
      "count": 2
    },
    {
      "pattern": [
        -2,
        -1
      ],
      "count": 2
    },
    {
      "pattern": [
        -1
      ],
      "count": 1
    },
    {
      "pattern": [
        -4,
        -2
      ],
      "count": 1
    },
    {
      "pattern": [
        -5,
        -1
      ],
      "count": 1
    }
  ],
  "entropy": 6.308771516813206,
  "note": "High unique count / entropy \u21d2 no shared shifted mask"
}
```

### band-local delta bitmasks

```json
{
  "bands": [
    {
      "band": "1-32",
      "n": 32,
      "unique": 30,
      "entropy": 4.875,
      "top": [
        {
          "pattern": [],
          "count": 2
        },
        {
          "pattern": [
            -2,
            -1
          ],
          "count": 2
        },
        {
          "pattern": [
            -1
          ],
          "count": 1
        }
      ]
    },
    {
      "band": "33-64",
      "n": 32,
      "unique": 32,
      "entropy": 5.0,
      "top": [
        {
          "pattern": [
            -29,
            -28,
            -26,
            -25,
            -21,
            -19,
            -17,
            -14,
            -13,
            -11,
            -10,
            -8,
            -5,
            -3,
            -1
          ],
          "count": 1
        },
        {
          "pattern": [
            -33,
            -31,
            -30,
            -29,
            -25,
            -21,
            -18,
            -17,
            -15,
            -12,
            -11,
            -8,
            -6,
            -3,
            -1
          ],
          "count": 1
        },
        {
          "pattern": [
            -30,
            -29,
            -28,
            -26,
            -22,
            -17,
            -14,
            -12,
            -11,
            -9,
            -8,
            -7,
            -5,
            -3
          ],
          "count": 1
        }
      ]
    },
    {
      "band": "65-96",
      "n": 11,
      "unique": 11,
      "entropy": 3.4594316186372973,
      "top": [
        {
          "pattern": [
            -64,
            -63,
            -62,
            -59,
            -58,
            -53,
            -51,
            -50,
            -47,
            -44,
            -43,
            -41,
            -40,
            -38,
            -32,
            -30,
            -28,
            -27,
            -24,
            -20,
            -19,
            -
```

### delta mod m distribution

```json
{
  "mods": [
    {
      "mod": 3,
      "entropy": 1.584097025265715,
      "max_entropy_for_sample": 1.584962500721156,
      "top": [
        [
          0,
          28
        ],
        [
          2,
          28
        ],
        [
          1,
          26
        ]
      ],
      "skew": false
    },
    {
      "mod": 5,
      "entropy": 2.3033959616972286,
      "max_entropy_for_sample": 2.321928094887362,
      "top": [
        [
          1,
          19
        ],
        [
          2,
          19
        ],
        [
          0,
          16
        ],
        [
          3,
          16
        ],
        [
          4,
          12
        ]
      ],
      "skew": false
    },
    {
      "mod": 7,
      "entropy": 2.7630430780964534,
      "max_entropy_for_sample": 2.807354922057604,
      "top": [
        [
          3,
          16
        ],
        [
          0,
          14
        ],
        [
          5,
          14
        ],
        [
          1,
          11
        ],
        [
          2,
          10
        ]
      ],
      "skew": false
    },
    {
      "mod": 16,
      "entropy": 3.8024792202599,
      "max_entropy_for_sample": 4.0,
      "top": [
        [
          4,
          10
        ],
        [
          0,
          8
        ],
        [
          3,
          8
        ],
        [
          15,
          8
        ],
        [
          12,
          7
        ]
      ],
      "skew": false
    },
    {
      "mod": 256,
      "entropy": 6.089259321691254,
      "max_entropy_for_sample": 6.357552004618084,
      "top": [
        [
          0,
          2
        ],
        [
          5,
          2
        ],
        [
          12,
          2
        ],
        [
          96,
          2
        ],
        [
          243,
          2
        ]
      ],
      "skew": false
    }
  ]
}
```

### low-bit agreement d/delta vs public ints

```json
{
  "rates": {
    "d_vs_px_low8": 0.0,
    "d_vs_pmy_low8": 0.0,
    "delta_vs_px_low8": 0.0,
    "delta_vs_floor_pktN_low8": 0.0,
    "d_vs_px_low16": 0.0,
    "d_vs_pmy_low16": 0.0,
    "delta_vs_px_low16": 0.0,
    "delta_vs_floor_pktN_low16": 0.0,
    "d_vs_px_low32": 0.0,
    "d_vs_pmy_low32": 0.0,
    "delta_vs_px_low32": 0.0,
    "delta_vs_floor_pktN_low32": 0.0
  },
  "note": "Rate near 1/2^k is chance; much higher would be a leak"
}
```

### delta popcount vs n

```json
{
  "mean_popcount": 21.804878048780488,
  "spearman_popcount_vs_n": 0.9793321821702802,
  "note": "Random delta in 2^(n-1) width has expected popcount ~(n-1)/2"
}
```

### offset sign bias: d - packet_p_landing

```json
{
  "signs": {
    "0": 2,
    "1": 46,
    "-1": 34
  },
  "frac_positive": 0.5609756097560976,
  "frac_negative": 0.4146341463414634,
  "frac_zero": 0.024390243902439025
}
```

### offset sign bias: d - packet_256_landing

```json
{
  "signs": {
    "0": 2,
    "1": 46,
    "-1": 34
  },
  "frac_positive": 0.5609756097560976,
  "frac_negative": 0.4146341463414634,
  "frac_zero": 0.024390243902439025
}
```

### offset sign bias: d - hinge

```json
{
  "signs": {
    "0": 2,
    "1": 35,
    "-1": 45
  },
  "frac_positive": 0.4268292682926829,
  "frac_negative": 0.5487804878048781,
  "frac_zero": 0.024390243902439025
}
```

### offset sign bias: d - mid

```json
{
  "signs": {
    "0": 1,
    "1": 41,
    "-1": 40
  },
  "frac_positive": 0.5,
  "frac_negative": 0.4878048780487805,
  "frac_zero": 0.012195121951219513
}
```

### |d-packet_p_landing|/width

```json
{
  "mean": 0.3638864952050749,
  "stdev": 0.2352919125226297,
  "min": 0.0,
  "max": 0.9565300345420837
}
```

### |d-hinge|/width

```json
{
  "mean": 0.22985953776211,
  "stdev": 0.147261922462165,
  "min": 0.0,
  "max": 0.580078125
}
```

### |d-mid|/width

```json
{
  "mean": 0.23048064860325918,
  "stdev": 0.1423506441521591,
  "min": 0.0,
  "max": 0.5
}
```

### delta in upper half of window

```json
{
  "count": 41,
  "of": 81,
  "frac": 0.5061728395061729,
  "note": "Random would be ~0.5"
}
```

### longest set-bit run in (d-L)

```json
{
  "mean": 3.975609756097561,
  "max": 10,
  "distribution": [
    [
      3,
      18
    ],
    [
      4,
      15
    ],
    [
      5,
      15
    ],
    [
      2,
      11
    ],
    [
      6,
      11
    ],
    [
      7,
      5
    ],
    [
      1,
      4
    ],
    [
      0,
      2
    ]
  ]
}
```

### popcount(d XOR L) vs popcount(d-L)

```json
{
  "mean_xor": 21.804878048780488,
  "mean_delta": 21.804878048780488,
  "always_equal": true,
  "note": "When L=2^(n-1), d^L equals d-L bit pattern (bit n-1 off). Identity, not a leak."
}
```

### spearman(scalar_position, packet_p_offset/width)

```json
{
  "rho": 0.7868730239179634,
  "note": "Near \u00b11 would mean packet landing tracks d; near 0 means independent"
}
```

## Sample (d − L) bit structure

| P | scalar_pos | popcount(d−L) | lowest | highest | mod 256 |
|---|------------|---------------|--------|---------|---------|
| 1 | 0.0000 | 0 | None | None | 0 |
| 2 | 0.5000 | 1 | 0 | 0 | 1 |
| 3 | 0.7500 | 2 | 0 | 1 | 3 |
| 4 | 0.0000 | 0 | None | None | 0 |
| 5 | 0.3125 | 2 | 0 | 2 | 5 |
| 6 | 0.5312 | 2 | 0 | 4 | 17 |
| 7 | 0.1875 | 2 | 2 | 3 | 12 |
| 8 | 0.7500 | 2 | 5 | 6 | 96 |
| 9 | 0.8242 | 5 | 0 | 7 | 211 |
| 10 | 0.0039 | 1 | 1 | 1 | 2 |
| 11 | 0.1279 | 3 | 0 | 7 | 131 |
| 12 | 0.3101 | 7 | 0 | 9 | 123 |
| 13 | 0.2734 | 3 | 5 | 10 | 96 |
| 14 | 0.2871 | 4 | 4 | 11 | 48 |
| 15 | 0.6398 | 8 | 0 | 13 | 243 |
| 16 | 0.5720 | 7 | 1 | 14 | 54 |
| 17 | 0.4621 | 10 | 0 | 14 | 79 |
| 18 | 0.5157 | 5 | 0 | 16 | 13 |
| 19 | 0.3639 | 11 | 0 | 16 | 159 |
| 20 | 0.6466 | 9 | 0 | 18 | 85 |

## Ruling

Patterns from known private keys were re-checked for subtle structure.
Clean structural hit: N-mirror identity
`scalar_position + mirror_position = 1 - 1/width`.
No transferable offset mask or public low-bit leak stood out.

Rebuild: `python build_known_d_offset_patterns.py`
