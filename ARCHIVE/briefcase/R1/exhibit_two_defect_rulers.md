# EXHIBIT: R1 two (actually four) defect rulers

**Same gaps, different ruler.** Change the ruler, change the exponent.

## Gaps

```text
2^256 − p : how far the field prime sits below the 256-bit ceiling
p − n     : how far the scalar order sits below the field prime
2^256 − n : total ceiling gap down to the scalar order
```

Identity:

```text
2^256 − n = (2^256 − p) + (p − n)
```

## Exponents

| Label | Formula | Value |
|-------|---------|-------|
| **field-base** | `log_(2^256 − p)(p − n)` | `0.5628044295342295…` |
| **order-ceiling-base** | `log_(2^256 − n)(p − n)` | `0.5628044295342295…` |
| **reciprocal order-ceiling** | `log_(p − n)(2^256 − n)` | `1.7768161505544447…` |
| **reciprocal field** | `log_(p − n)(2^256 − p)` | `1.7768161505544447…` |

Field-base and order-ceiling-base are nearly equal because for R1:

```text
2^256 − n ≈ 2^256 − p
```

(the inner `p−n` is tiny next to the field defect).

## Label correction

The reading `1.7768161505…` is **not**:

```text
log_(2^256 − n)(p − n)     ← that is still ≈ 0.5628
```

It is the reciprocal:

```text
log_(p − n)(2^256 − n)
  = 1 / log_(2^256 − n)(p − n)
  ≈ 1.7768161505
```

So:

```text
0.5628…  = how the inner gap scales against the ceiling gap
1.7768…  = how the ceiling gap scales against the inner gap
```

Same courtroom pair, inverted question.

## Verdict

Keep both orientations side by side in the R1 catalog. Do not mix with k1’s

```text
log_(2^32+977)(p−N) ≈ 4.0108
```

Judge Popcorn: **same defect, different ruler. Change the ruler, change the exponent.**
