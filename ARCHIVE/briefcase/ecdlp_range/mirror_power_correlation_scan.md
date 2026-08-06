# mirror_power_correlation_scan

## Roofs

```text
e_roof_binary  = 256/256 = 1
e_roof_N       = log2(N)/256 = 0.99999999999999999999999999999999999999997895437419253638948718276206465148566582
1 - e_roof_N   = 0.00000000000000000000000000000000000000002104562580746361051281723793534851433418
e_mirror_proxy = 255/256 = 0.99609375
```

Because `N < 2^256`, `e_roof_N < 1`. Deficit is ~1e-41 — **Decimal only**
(float64 rounds `e_roof_N` to `1.0`).

## Hierarchy

- 256/256 = 1 — ideal binary ceiling (identity warp)
- log2(N)/256 — true scalar-order ceiling
- 255/256 — coarse one-bit-below proxy
- log2(N-d)/256 — true solved mirror height
- log2(N-2^n)/256 .. log2(N-2^(n-1))/256 — unsolved mirror window band

## Solved: e_q = log2(N−d)/256

- mean e_q: `0.99999999999999999999999999999999999999997827628145553014741505503227696648897685`
- mean |e_q − e_roof_N|: `0.00000000000000000000000000000000000000000067809273700624207212772978768499668897085365853658536585365853658536585365853659`
- fraction closer to e_roof_N than 255/256: **1.00**
- fraction e_q in mirror exp band: **1.00**

## Direct shell closest to e_roof_N

`{'e_lo': 0, 'e_hinge': 0, 'e_hi': 160}`

## Correlations (with band control)

| pair | spearman all | spearman 65–130 | verdict all | verdict band |
|------|--------------|-----------------|-------------|--------------|
| `Px_pow(e_q) vs priv(e_q)` | -0.1235 | +0.2982 | **REJECT** | **WEAK** |
| `Px_pow(e_roof_N) vs priv(e_roof_N)` | -0.1235 | +0.2982 | **REJECT** | **WEAK** |
| `Px_pow(e_lo) vs priv(e_q)` | -0.7018 | -0.0175 | **STRONG** | **REJECT** |

## P135 (unsolved) mirror exponent band

- e_hi / e_lo / e_hinge: `{'e_hi': '0.52734375', 'e_lo': '0.5234375', 'e_hinge': '0.52572250976844201640625'}`
- e_q_window_low: `0.99999999999999999999999999999999999999785910453603715442368745768559718271711320`
- e_q_window_high: `0.99999999999999999999999999999999999999891902945511484540658732022383091710148914`
- e_roof_N: `0.99999999999999999999999999999999999999997895437419253638948718276206465148566582`

q = N−d unknown; band sits right under e_roof_N.

## Ruling

```text
256/256 = 1:     abstract binary ceiling (identity warp)
log2(N)/256:     true scalar-order roof (use this; Decimal)
log2(N-d)/256:   solved mirror height (sits under e_roof_N)
mirror window:   log2(N-2^n)/256 .. log2(N-2^(n-1))/256
255/256:         coarse proxy (farther from e_q than e_roof_N)
```

Judge Popcorn: **the better roof is the order roof, not the abstract 256.**

Rebuild: `python build_mirror_power_correlation_scan.py`
