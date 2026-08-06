# EXHIBIT: y-tail carry / wrap scan

## Question

```text
Does y act as the carry/wrap amount?
```

**Not:** does `x.y` become `d`?

## Mechanism

```text
A       = floor((x / p) * N)     = map_p_to_n(Px)
B       = floor((x.y / p) * N)
carry   = B - A                  (0 or 1)

Under p: floor((x.y / p) * p) = x   — tail invisible
Under N: tail may push A → A+1      — wrap event
```

## Verdict counts (88 pubkey puzzles)

| Carry | y branch | p−y branch |
|-------|----------|------------|
| 0 | 48 | 47 |
| 1 | 40 | 41 |

```text
carry_y == carry_pmy:  49 puzzles
carry_y != carry_pmy:  39 puzzles
all carry in {0,1}:  True
```

## Solved puzzle checks (82 puzzles)

| Test | Hits |
|------|------|
| `d == A + carry_pmy` | 0 |
| `d == B_pmy` | 0 |
| `carry_pmy == (d > A)` | 43 |

No direct key recovery — confirms carry is mechanical, not scalar identity.

## RSZ r/N landing (88 puzzles with r)

```text
carry_pmy == (map_p_to_n(r) > A):  50 / 88
```

## Confound control

```text
Spearman(n, carry_y):   -0.0368
Spearman(n, carry_pmy): -0.0022
```

Carry is **point-specific** (which y-tail crosses the boundary), not a puzzle-index compass.

## Roof-stitch carry (same principle)

| Stitch | carry p→N | over_p |
|--------|-----------|--------|
| `p.N` | 0 | overflow |
| `N.p` | 0 | under_roof |
| `p.(p−N)` | 0 | overflow |
| `N.(p−N)` | 1 | under_roof |

Head sets the main room; tail sets under-roof vs overflow vs +1 carry.

## Admissible fact (filed)

```text
x.y is not merely a display packet.

When projected from p to N:
  x sets the floor
  y decides whether the projected floor stays A
  or carries to A + 1

y = carry pressure in p→N projection
```

```text
d == B_pmy:     0 / 82 solved
d == A + carry: 0 / 82 solved
```

**Not the private key.** Structural rule only.

P135: `B_y = A+1`, `B_pmy = A+1` — both tails push across the boundary.

## Clean ruling

```text
Admissible fact, not conviction.
x is the floor; y is the pressure; N hears the carry.
```

Judge Popcorn: **Admissible fact, not conviction. x is the floor; y is the pressure; N hears the carry.**
