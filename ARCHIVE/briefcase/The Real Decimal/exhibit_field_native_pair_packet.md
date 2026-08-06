# EXHIBIT: field-native coordinate-pair packet

## Keeper

```text
0.x_y in base p  =  x/p + y/p^2  =  (x*p + y) / p^2
```

Not human decimal stitch. **Field-native two-limb witness.**

| Limb | Formula | Role |
|------|---------|------|
| U | `x/p` | first-order field placement |
| V | `y/p` | y under field roof |
| W | `y/p^2` | second-order tail pressure |
| P_pair | `U + W` | flattened coordinate-pair packet |

## Curve wrap (exact, all 88 pubkey puzzles)

```text
y^2 = x^3 + 7 - m*p
m   = (x^3 + 7 - y^2) // p

y^2/p^3 = x^3/p^3 + 7/p^3 - m/p^2     verified: True failures
```

`m/p^2` is the **wrap limb** at the same `p^2` denominator as P_pair.

```text
P_pair - m/p^2 = (x*p + y - m) / p^2
```

P_pair and m/p^2 are **not equal** — different numerators, shared denominator.

## P135 (p−y primary branch)

```text
P_pair   = 0.07954633649946047...
m/p^2    = 0.0005033389619581097...
P - m/p^2 = 0.07904299753750235...
ratio    = 158.03731185443317...
```

## Reference roof terms (P135 context)

```text
V^2/p = y^2/p^3 = 1.3838564487348034e-78...
U^3   = x^3/p^3  = 0.0005033389619581097...
7/p^3           = 4.5088041387179933e-231...
DELTA/p^2       = 3.225138582123998e-116...
sqrt(p)/p       = 2.938735877055719e-39...
sqrt(N)/p       = 2.938735877055719e-39...
```

## Sqrt caution

```text
REJECT (as written):  x/p = -y*sqrt(p)   — unit mismatch

REFRAME: x/p + y/p^2 are linear field placements.
         Curve relation lives in y^2 = x^3 + 7 - m*p.
         sqrt belongs to 128-bit midpoint roof after normalization.
```

## Ratio P_pair / (m/p^2) across puzzles

```text
min  = 1.0106568619775784
max  = 2167.2652572296647
P135 = 158.03731185443317
```

Point-specific — not a universal constant.

## Clean ruling

```text
x/p + y/p^2 is the right field-native coordinate-pair packet.
It is a flattened ECC point witness (0.x_y in base p).
m/p^2 is the curve wrap limb at the same denominator.
Sqrt relations need normalized units before they are factual.
```

Judge Popcorn: **We stopped spelling coordinates in human decimal and started spelling them in the field's own alphabet. That's where the floorboards finally line up.**
