# EXHIBIT: carry threshold ledger

Builds on **y-tail carry** (admissible fact).

## Exact formula

```text
rem   = (N * x) % p
d     = decimal digits of y

carry = 1  iff  rem * 10^d + N * y  >=  p * 10^d
carry = 0  otherwise

margin = p * 10^d - (rem * 10^d + N * y)
         > 0  no carry
         <= 0 carry event
```

`N * y` is the **carry pressure term**. `rem` is the field residue before the tail pushes.

## Verification

```text
int vs Decimal mismatch:     0
threshold vs int mismatch:   0
all_ok:                      True
```

## Branch differential (39 puzzles)

When `carry_y != carry_pmy`, one tail crosses the threshold and one does not:

```text
y=1, pmy=0: 19 puzzles
y=0, pmy=1: 20 puzzles
```

These are the puzzles where **y vs p−y pick different sides of the floorboard**.

## Beta-slot ladder

```text
all three slots same carry (p−y):  45 / 88
slots differ:                    43 / 88
```

β-rotation changes `rem`; same y-tail can flip carry at different slots.

## Ledger wrap (16 objects × 88 puzzles)

Each ledger integer head stitched with each puzzle's `p−y` tail.

Best carry agreement with puzzle `carry_pmy`:

```text
BETA_SQ: 73 / 88 matches
```

No universal ledger carry mask — agreement is object-specific and weak.

## RSZ r carry (88 puzzles)

```text
r stitched carry_pmy == Px carry_pmy:  55 / 88
```

## Clean ruling

```text
Carry is an exact integer threshold law.
y is not ornament — it is the N*y term in rem*10^d + N*y >= p*10^d.
Still not d. Still admissible structure.
```

Judge Popcorn: **The pressure has a formula now: rem*10^d + N*y vs p*10^d. Cross the line, N hears +1.**
