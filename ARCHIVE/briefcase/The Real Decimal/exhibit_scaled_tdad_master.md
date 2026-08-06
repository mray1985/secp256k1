# Scaled TDAD master reference (filed from user notes)

Verified against `puzzle_catalog` — **0 d-value mismatches** on puzzles 1–130 in the filed table.

## Core grammar (puzzles 68+)

```text
T_n = Σ k_i · (M · d_{index_i}) + remainder

Standard phase:  M = 536870912 = 2^29
Remainder:       r < 2^29  (always verified on P68–P100 filed paths)

First-slot ceiling:  index₀ ≤ n − 29
Solo in-band anchor: 536870912(n−29) when that term alone fits [2^{n−1}, 2^n)
```

## Index → ladder weight (reference table)

For puzzle **n**, index **i** carries weight **2^(n−i) · d_i** in the general ladder.
At the **2^29 phase** (P68–P100 standard), **M is fixed at 2^29** regardless of n.

User reference ladder (puzzle 61 context, `2^(67−i)`):

| index | 2^(67−i) |
|------:|---------:|
| 61 | 64 = 2^6 |
| 38 | 536870912 = 2^29 |
| 35 | 4294967296 = 2^32 |
| 17 | 1125899906842624 = 2^50 |

Convergence path on **P68** (exact):

| mult | path | remainder | = d_68? |
|------|------|-----------|---------|
| 8 = 2^3 | 26 terms | +1 | ✓ |
| 16 = 2^4 | 35 terms | +1 | ✓ |
| 32 = 2^5 | 34 terms | +17 | ✓ |
| 536870912 = 2^29 | 13 terms | +284955793 | ✓ |

## Filed scaled paths (2^29 phase) — all exact

| Puzzle | terms | remainder | rem < 2^29 |
|--------|------:|----------:|:----------:|
| P68 | 13 | 284955793 | ✓ |
| P69 | 17 | 314342924 | ✓ |
| P70 | 21 | 443305713 | ✓ |
| P75 | 22 | 20147719 | ✓ |
| P100 | 35 | 517097510 | ✓ |

Partial sum example (P68):  
`536870912(39)+536870912(36)+536870912(36)+536870912(30)+536870912(26)+536870912(22)`  
= **219,897,610,403,737,239,552**

## P71 band endpoints (not d_71)

```text
[2^70, 2^71) = [1180591620717411303424, 2361183241434822606847]

536870912(42) = 1554442376562402656256   ← only solo term in P71 band
536870912(41) = 782893191303280984064    ← below 2^70 floor
```

User filed **2^70** and **2^71** band decompositions (subset sums at 2^29) — verified as band endpoints, **not** hash160 hits.

## Alternative multiplier phases (same index pool, different M)

| M | name | P70 example |
|---|------|-------------|
| 1125899906842624 = 2^50 | high-bit lane | `2·M(19)+M(17)+…+200399322369777` = **d_70 ✓** |
| 36893488147419103232 = 2^65 | band floor | `M(5)+M(4)+M(2)` = **2^70 exactly ✓** |

Higher **M** → smaller index ceiling (`n − log2(M)`) → terms shrink toward low indices.

## Classic [3,2,1,2] vs scaled (P68 drafts)

| path | terms | target | result |
|------|------:|--------|--------|
| sparse P68 draft | 32+1 | d_68 | in-range, wrong sum |
| dense P68 draft | 96+1 | d_68 | off by 64 |
| scaled 2^29 | 13+rem | d_68 | **exact ✓** |

Classic grammar is pre-convergence / wrong lane for P68+; scaled 2^29 is the verified lane.

## P135 filed index playlist (22 indices)

```text
69 66 61 56 54 50 45 41 39 38 35 29 22 17 14 13 11 10 7 5 4 1
```

User combination estimate: **~3.46 × 10^49** (≈ **1.59 × 2^134**).

Interpretation: P135 scaled search at full prior pool is **~2^134** mask order (134 slots at 2^29), not the P71 **2^42** pool. The filed 22-index path is one playlist candidate, not the full search space.

**Gate:** `[T]G == P135` (pubkey known — direct EC, not hash160-only).

## Search counts summary

| Puzzle | pool | mask count | remainder dial |
|--------|------|------------|----------------|
| P71 | 1..42 | **2^42** | < **2^29** per unique S |
| P135 | 1..134 | **~2^134** | < **2^29** per unique S |

Pipeline: **dedupe masks → unique S → remainder dial → EC gate**.

## d-table anchor (puzzles 1–70 + anchors)

Stored in `scaled_d_table.json` (generated from this filing).

## Courtroom

Scalar-side only for TDAD lock. Field β / 7⁻¹ mod p is separate room. See `exhibit_field_scalar_courtroom_correction.md`.
