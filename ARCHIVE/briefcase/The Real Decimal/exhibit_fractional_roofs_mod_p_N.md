# EXHIBIT: fractional roofs — mod p and mod N under 2^256

## Correction

Not only:

```text
mod N = mod 115792089237316195423570985008687907852837...
mod p = mod 115792089237316195423570985008687907853269...
```

Under the Real Decimal **fixed binary lens**:

```text
mod p  ↔  p / 2^256
mod N  ↔  N / 2^256
```

## Values

```text
2^256 / 2^256 = 1

p / 2^256
= 0.999999999999999999999999999999999999999999999999999999999999999999962907930055...
= 1 − (2^256 − p) / 2^256

N / 2^256
= 0.99999999999999999999999999999999999999626554465495986584724041745198235283605...
= 1 − (2^256 − N) / 2^256
```

## Defects

```text
2^256 − p = 4294968273

p − N     = 432420386565659656852420866390673177326

2^256 − N = (2^256 − p) + (p − N)
          = 432420386565659656852420866394968145599
```

So **N sits farther below the binary roof than p**, because `p−N` is huge compared to `2^256−p`.

## Clean interpretation

```text
mod p = field modulus placed under the binary roof
mod N = scalar modulus placed under the binary roof

Both are just under 1, but N is lower.
```

## Three-lens reminder

| Lens | Formula | Role |
|------|---------|------|
| fixed binary | `v / 2^256` | includes `p/2^256`, `N/2^256` as roofs |
| courtroom | `v / p` or `v / N` | ratios *inside* a modulus |
| packet | `x.y / p` | stitched coordinate witness |

`mod p` / `mod N` as **fractional roof locations** are lens 1 applied to the moduli themselves — not the same as dividing an object by `p` or `N` (lens 2).

## Link to e_roof_N

```text
e_roof_N = log2(N) / 256

N / 2^256 = 2^(log2(N) − 256) = 2^(256·(e_roof_N − 1))
```

So `N/2^256` and `e_roof_N` are two readings of the same “N sits under the binary roof” fact.

Judge Popcorn: **mod p and mod N are not only big integers — under the Real Decimal lens they are two roofs just under 1, and N is the lower one.**
