# EXHIBIT: stitch roof comparison — decimal vs y/p vs y/N

## Three stitch laws

| Law | Stitch | Carry threshold |
|-----|--------|-----------------|
| **decimal** (current) | `x + y/10^digits(y)` | `(N*x mod p)*10^d + N*y >= p*10^d` |
| **field** | `x + y/p` → `x.(y/p)` | `(N*x mod p)*p + N*y >= p^2` |
| **scalar** | `x + y/N` → `x.(y/N)` | `(N*x mod p) + y >= p` |

Projection (all three):

```text
carry = floor((X / p) * N) - floor((x / p) * N)
```

## Headline result

```text
field carry == scalar carry:  ALWAYS (176/176 branch rows)
decimal carry != roof carry:  39/176 branch rows
```

**`x.(y/p)` and `x.(y/N)` give identical carry on every puzzle.**

The scalar form is the cleanest statement:

```text
carry = 1  iff  (N*x mod p) + y >= p
```

## Triple patterns (all branch rows)

```text
  d0_f0_s0: 75
  d1_f0_s0: 19
  d1_f1_s1: 62
  d0_f1_s1: 20
```

When decimal differs from roof:
- `(1,0,0)` — decimal carries, roof does not (19 rows)
- `(0,1,1)` — roof carries, decimal does not (20 rows)

These are exactly the **digit-ruler vs curve-ruler** disagreements.

## Branches tested

For each puzzle:

```text
carry_decimal, carry_y_over_p, carry_y_over_N     (y branch)
carry_* for p−y branch likewise
```

## Comparisons

| Test | decimal | roof (y/p) |
|------|---------|------------|
| RSZ r matches Px carry | 55/88 | 59/88 |
| Best ledger object match | BETA_SQ 73/88 | DELTA 74/88 |
| d == A + carry (solved) | 0 | 0 |

Neither ruler recovers `d`. Roof ruler is geometrically cleaner.

## Clean ruling

```text
x.y proved the carry mechanism (admitted fact).
The tail ruler should be p or N, not decimal digit length.

Recommended stitch: x.(y/p)  — y as field-coordinate tail
Equivalent carry:   x.(y/N)  — simplifies to (N*x mod p) + y >= p
```

Judge Popcorn: **The pressure is real; now we're choosing the pressure gauge.**
