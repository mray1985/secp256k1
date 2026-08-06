# TDAD scalar courtroom

Scalar-side packet: **TDAD/N** — same roof as **d/N**.

```text
field witness:  x/p + y/p²  = 0.x_y (base p)
scalar witness: T_n / N      = TDAD transcript value
```

## Verdict

```text
TDAD IS the scalar construction transcript — 82/82 exact, 82 EC pass
```

## Summary

| metric | count |
|--------|-------|
| puzzles in TDAD file | 160 |
| with numeric T | 82 |
| solved compare T vs d | 82 |
| **T == d** | **82** |
| T == N−d | 0 |
| [T]G == P | 82 |
| x([T]G) == r (T as k) | 0 / 82 |

## Scalar packet law (solved)

For every solved puzzle with a TDAD entry:

```text
T_n / N = d_n / N     (exact — 82/82)
delta_n / N = 0
[T_n]G = P            (82/82 EC verified)
```

## RSZ note

TDAD value is **d**, not nonce **k**. Testing x([T]G)==r correctly fails
(T is private key, not ephemeral k).

## TDAD reconstruction (thePattern.txt — empty double_and_add slots)

Blank lines in `double_and_add.txt` can still be rebuilt via TDAD/DA cycle `[3,2,1,2]`.

| puzzle | T bits | in range | DA cycle | eval==T | [T]G=address | T/N head |
|--------|--------|----------|----------|---------|--------------|----------|
| 71 | 71 | True | 10×3212 | True | no | 0.00000000000000000000000000… |
| 72 | 72 | True | 8×3212 | True | no | 0.00000000000000000000000000… |

**P71 DA pattern:** same operator head as P68–70:

```text
triple + double + add + double  (repeated 10 cycles)
```

## P135

```text
EMPTY — no TDAD operator sequence filed for puzzle 135. Scalar recipe missing; cannot form T_135/N packet.
```

## Ruling

TDAD/N is the scalar-side equivalent of 0.x_y(base p). For all 82 filed puzzles, T_n equals d_n and [T_n]G = P. The double/add file is literally the private-key construction transcript, not a decorative label. Puzzle 135 has no transcript yet — open work.
