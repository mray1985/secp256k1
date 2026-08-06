# Gap-Based Effective N — Puzzle 135 (validated 2026-06-09)

## Summary

The four corner deltas hold exactly. The two gap spaces are clean powers-of-two lanes.
Interior motion satisfies `defect(d) = delta + d = p - (N - d)`. Gap-sized modulus gives a
**measurable relative offset** from the interior defect at each boundary.

## Dual bands (user-corrected mirror)

| Side | Low | High |
|------|-----|------|
| **+d** | `2^134` | `2^135 - 1` |
| **mirror** | `N - (2^135 + 1)` | `N - 2^134` |

Mirror ceiling is **2 below** naive `N - (2^135 - 1)` — pairs `2^135 - 1` with `N - (2^135 + 1)`.

## Two gaps (= effective new N sizes at boundaries)

```
G_low  = (N - 2^134) - 2^134       = N - 2^135
G_high = (N - (2^135+1)) - (2^135-1) = N - 2^136

G_low - G_high = 2^135  (exact)
```

## Four corner deltas (all verified OK)

```
delta_A = p - (N + 2^134)       = delta - 2^134
delta_B = p - (N - 2^135)       = delta + 2^135
delta_C = p - (N - 2^134)       = delta + 2^134
delta_D = p - (N - (2^135+1))   = delta + 2^135 + 1
```

## Interior (if d known)

```
new_N(d) = N - d
defect(d) = delta + d = p - new_N(d)
rho(d)    = defect(d) - delta = d
```

## Relative offset (gap delta vs defect delta)

Using `delta_gap(G) = p - G`:

| Position | defect(d) | delta_gap | **relative offset** |
|----------|-----------|-----------|---------------------|
| `d = 2^134` (floor) | `delta + 2^134` | `delta + 2^135` | **`2^134`** |
| `d = 2^135 - 1` (ceil) | `delta + 2^135 - 1` | `delta + 2^136` (via G_high) | **`2^135 + 1`** |
| mirror defect(TOP) vs delta_D | — | — | **exactly 2** |

So gap-sized N at the floor is **one full lane shelf (`2^134`) above** the interior defect.
At the ceiling the gap reference is **`2^135 + 1` above** interior defect — the same +2 as mirror correction.

## Lane boundary `2^134.999...`

```
TOP / LO = 2 - epsilon   (TOP = 2^135 - 1)
```

Work in `d' = d - 2^134` with denominator `TOP - LO = 2^135 - 1`.
This keeps arithmetic on the `2^n` shelf without leaving the puzzle band.

## Fingerprint (measurability)

```
F_n = (p - 2^n)/p - (N - 2^n)/N = 2^n * delta / (p*N)
F_135 / F_134 = 2  (exact)
```

## Lambda reconfiguration (open)

P-side: `Lambda = Px3/rx3 mod p` (fixed).

N-side shrinkage at position d:
```
Lambda_N(d) = Lambda * (N - d) // N   (integer)
Px3/rx3 mod N = Lambda + GAP
```

Single-floor inversion `d = N - (Px3*rx3^-1 * N // Lambda)` lands **outside** `[2^134, 2^135)` and does not satisfy the floor identity — so **d is not pinned by Lambda alone**; needs joint gap-relative offset + barcoding.

## Scripts

| File | Role |
|------|------|
| `gap_new_n_relative_offset.py` | Full validation + corner checks + `gap_new_n_report.json` |
| `gap_offset_135_solver.py` | Lambda interval + anchor search (avoid multi-million ECDSA scroll) |

## Next steps

1. Close `d` from **relative offset** + barcode mask (digit-level), not Lambda floor alone.
2. Re-run barcoding with `delta_A..D` corners instead of single global `Lambda`.
3. Tile KeyHunt/Kangaroo on `LO + (GAP % 2^134)` and lane-C gap offset anchors.
