# EXHIBIT: pair-minus-wrap scan

## Residue lane

```text
P_pair  = (x*p + y) / p^2
wrap    = m / p^2        m = (x^3 + 7 - y^2) // p
residue = P_pair - wrap  = (x*p + y - m) / p^2
```

Coordinate limbs and curve wrap share the **same p² roof**.

## Aggregates (88 pubkey puzzles)

```text
exact equality hits to refs:  0
beta residue == slot_3:       88 / 264
```

### Nearest reference (p−y branch, float distance)

```text
  s_over_N: 38
  z_over_N: 24
  r_over_N: 14
  DELTA_over_p2: 12
```

No exact hits to `d/N`, `r/N`, `N/p`, or `DELTA/p²` — residue is its own object.

## P135

```text
P_pair   = 0.07954633649946047...
m/p²     = 0.0005033389619581097...
residue  = 0.07904299753750235...
ratio    = 158.03731185443317...
```

β-slot residues (p−y):

| Slot | residue (head) | Δ from slot 3 |
|------|----------------|---------------|
| 1 | 0.35805458459735173… | 0.2790115870598494… |
| 2 | 0.36702103079952625… | 0.2879780332620239… |
| 3 | 0.07904299753750235… | 0 |

## Clean ruling

```text
This is factual structure: yes
This is d:                 no
Better missing-term target: yes
```

Judge Popcorn: **We finally put the point limbs and the curve wrap under the same roof. Now the residue can testify.**
