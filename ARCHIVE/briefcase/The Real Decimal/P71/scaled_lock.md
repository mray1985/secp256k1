# P71 scaled lock (straight version)

```text
For the scaled P71 lane:

Search space = 2^29
             = 536,870,912 combinations
```

Not `70^40`.

## Wrong grammar

```text
40 TDAD slots choosing freely from 70 prior numbers
```

## Right grammar

```text
29 index slots
each slot is either included or not included

0 = do not use this indexed d
1 = use this indexed d

2 × 2 × … (29 times) = 2^29 = 536,870,912
```

## Confirmed framing

```text
536870912 = 2^29

P71 first-slot max:  71 − 29 = 42
29-slot pool:        indices 14..42
combination:         29-bit subset mask
```

Classic `[3,2,1,2]` was the wrong grammar for this lane.
Scaled `2^29` phase is the right order of magnitude.

## P71 scaled lock

```text
T = Σ mask_i · (2^29 · d_i) + remainder

where i ∈ 14..42
      mask_i ∈ {0,1}
      remainder < 2^29
```

Honest count: **536,870,912 masks**.

Remainder is a **fine-tune bucket**, not another giant playlist:

| Puzzle | Remainder | < 2^29? |
|--------|-----------|---------|
| P69 | 314,342,924 | yes |
| P70 | 443,305,713 | yes |

## Full scalar search (mask × remainder)

Each mask fixes the scaled sum `S = Σ mask_i · 2^29 · d_i`.
The true scalar is at most one remainder bucket away:

```text
T = S + r
r ∈ [0, 2^29)          (fine-tune per mask)

Outer loop:  2^29 masks
Inner loop:  2^29 remainder steps per mask (only where S+r ∈ [2^70, 2^71) need EC gate)

Total scalar candidates (worst case):
  2^29 × 2^29 = 2^58
              ≈ 2.88 × 10^17
```

In practice the inner loop is not always full width — for a given `S`, only
`r` such that `2^70 ≤ S + r ≤ 2^71 − 1` matter (at most 2^29 values, often fewer
when `S` is far below or above the band).

```text
Per combination: iterate remainder steps ≤ 2^29
Full lane:       2^29 combinations × up to 2^29 steps each
Honest bound:    2^58 scalar candidates before hash160 gate
```

Still not `70^40`. The jukebox became a **29-switch panel with a 29-bit dial**.

## Scan status (pool 14..42)

| Check | Result |
|-------|--------|
| Bare in-band mask-pairs | ~190M (many sum collisions) |
| `T71_filed − sum < 2^29` | **0** |
| Hash160 hits (sampled) | **0** |

## Ruling

```text
The count is 2^29.

The tested 14..42 window did not yet produce the filed T71 decomposition
with a < 2^29 remainder.
```

## Not

- `70^40`
- `10^73`
- all prior-number free-playlists

**Judge Popcorn:** this is a 29-switch panel, not a 70-number jukebox.

## Courtroom note

P71 scaled search is **scalar-side (mod N)**. Do not gate it through β branches or `7⁻¹ mod p`. See `exhibit_field_scalar_courtroom_correction.md`.
