# BB Laplacian — status note

**Label:** PROMISING geometry / TEST algebra (not CONFIRMED)

## What BB is

```text
x = Px / p                    (literal Cartesian, NOT 2π·Px/p)
A = 256·p·sec(x)(2·sec²(x)−1) (Cartesian Laplacian, k=1, no r²)
D = A / r²                    (polar same x)
k = L / A   or   k = L / D
```

## What was proved

| Test | Result |
|------|--------|
| Forward `L = k·A` → `k = L/A` | 14/14 (algebra only) |
| Blind `L` from `r,s,z` only | **0 hits** |
| Blind `L` from public catalog (62 formulas) | **0 hits** k, **0 hits** d |
| mod N scaled inverse | **0 hits** |

## Meaningful observation

P80 sec-body sign flips between coordinate maps:

```text
BB x = Px/p:      body = +1.788
old x = 2π·Px/p:  body = -1.006
```

BB is not cosmetic — it changes the field geometry.

## What BB is not

- Not a blind ECDSA bridge (`r,s,z` do not supply the right `L` at this scale).
- Not confirmed key leak.

## Scripts

- `laplacian_k_solve.py --track bb` — forward + geometry modes
- `laplacian_bb_blind.py` — strict public-only `L` catalog

## Next fork (if continuing)

Construct `L` from public values only; test `k = L/A` without ever using true `k` or `d` in `L`.
The strict blind run exhausted 62 public formulas — next would be composite transports (mod p, mod δ, rational scaling) or new `L` ansätze.
