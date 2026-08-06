# P71 TDAD combination space

## Lock model

```text
Each slot:  coeff × d_{index}     (coeff from fixed rhythm)
40 slots:   sum = d_71             (combination opens)
EC gate:    [T]G == P71             (proves true key)
```

## Structure (observed P70/P71)

```text
10 cycles × 4 terms = 40 TDAD slots
Operator rhythm: [3, 2, 1, 2] × 10   (fixed)
Variation: which prior puzzle index fills each slot
```

## Scaled phase: fixed mult 2^29 = 536870912

From P68→P70 filed paths:

```text
T_n = Σ 536870912(index_j) + remainder
    = Σ 2^29 · d_{index_j} + remainder

First-slot ceiling:  index₀ ≤ n − 29
Remainder bucket:    remainder < 2^29   (P69/P70 verified)
```

### 2^29 combinations (search space collapse)

```text
29 index slots  →  2^29 = 536,870,912 subsets
Pool for P71:   indices 14..42  (because 42 = 71 − 29, count = 29)
Each subset:    include/exclude each slot once at weight 2^29 · d_i
Fine tune:      + remainder < 2^29 (one 29-bit bucket, not another full search)
```

| Layer | Count |
|-------|-------|
| Subset mask over 29 slots | **2^29** |
| Remainder (if free) | **< 2^29** |
| User claim (total) | **~2^29** → subset mask is the combination; remainder is internal |

This replaces the naive `69^40` / `70^40` classic-TDAD counts for the **scaled P71 lane**.

### MITM scan (pool 14..42)

| Check | Result |
|-------|--------|
| Subset pairs with bare sum ∈ `[2^70, 2^71)` | **~1.9×10^8** mask pairs (many collisions) |
| Subset sums where `T71_filed − sum < 2^29` | **0** |
| Hash160 hits (first 200 in-band samples) | **0** |

Filed `T71 = 1411488254391826260559` is **not** expressible as `Σ 2^29·d_i` over pool 14..42 plus a remainder `< 2^29`. Either the pool/window differs, filed T71 is wrong, or the classic `[3,2,1,2]` path (not pure scaled) is the correct grammar.

Full EC gate over all **2^29** masks is feasible (≈537M integer sums); hash160 only on sums landing in-band. Python brute force is slow; MITM half-split (2^14 × 2^15) builds in ~3s.

| Puzzle | max first index | n − 29 | 536870912(max first) bits | in [2^{n−1}, 2^n)? |
|--------|-----------------|--------|---------------------------|---------------------|
| P68 | 39 | 39 | 68 | yes |
| P69 | 40 | 40 | 69 | yes |
| P70 | 41 | 41 | 70 | yes |
| P71 | **42** | **42** | **71** | **yes** |
| P71 | 41 | 41 | 70 | **no** (below 2^70) |

**536870912(42)** is the largest single opening term that still lands in the P71 bit band.
**536870912(41)** is only 70 bits — too small to anchor a P71 sum at the floor.

### Multiplier ladder (P68 convergence)

Same playlist grammar at increasing uniform scale — all exact for d_68 with atomic tail:

| mult | first index | n − first | + tail | = d_68? |
|------|-------------|-----------|--------|---------|
| 8 = 2^3 | 64 | 4 | +1 | **exact** |
| 16 = 2^4 | 63 | 5 | +1 | **exact** |
| 32 = 2^5 | 62 | 6 | +17 | **exact** |
| 536870912 = 2^29 | 39 | 29 | +284955793 | partial |

P69/P70 scaled sums + filed remainders also verified:
- P69 remainder **314342924**
- P70 remainder **443305713**

### Lookup table rule

User table maps puzzle index `i` → `2^(67 − i)` up to 2^29 at index 38:
`536870912(i) = 2^(n − i) · d_i` only when the decomposition uses the **fixed** 2^29 phase (i.e. i = n − 29 for the lead term).

## Index ceiling = initial term (first slot)

```text
Every verified playlist (20/21):  max(index) ≤ first_slot_index
The opening triple 3(index₀) sets the ceiling for all 40 slots.
Nothing later in the path may reference a higher prior puzzle.
```

| Puzzle | first slot index | max index used | n − first |
|--------|------------------|----------------|-----------|
| P68 | 66 | 66 | 2 |
| P69 | 66 | 66 | 3 |
| P70 | 68 | 68 | 2 |
| P71 | 69 | 69 | 2 |
| P72 | 70 | 70 | 2 |
| P100 | 70 (× 2^29) | 70 | 30 |

For P71: prior pool is **not** 1–70. It is **1–69** (first slot = 69 = n−2).
Index 70 is **out of bounds** until P71 closes and P72 opens with first slot 70.

## Global multiplier phase (n ≥ 71)

From P100 filed pattern:

```text
T_100 = 2^29 × d_70 + 2^29 × d_69 + … + remainder
        ^^^^^
        initial multiplier = 2^(n − 71) = 2^29 for P100
```

You only go as high as the **initial multiplier phase** allows:

| Rule | Meaning |
|------|---------|
| `mult = 2^(n − 71)` | Scaled TDAD starts at P71 (mult = 1) |
| Index ceiling | All indices ≤ first-slot index (~ n−2) |
| Chain ceiling | All indices ≤ last **verified** prior (currently **70**) |
| 2^32 ladder | `2^32 × d_n` lands near **P_{n+32}** — can't skip rungs |

```text
You cannot reference priors above the opening term's index.
You cannot reference priors above the verified chain head (70 until P71 closes).
You cannot jump past P71 in sequence — the 2^(n−71) phase starts there.
```

## Theoretical search space (prior puzzles 1–70)

| Model | Formula | Count |
|-------|---------|-------|
| **Naive (wrong): any of 70 priors** | `70^40` | ≈ 6.37 × 10^73 |
| **Correct: capped at first slot (69)** | `69^40` | **≈ 3.02 × 10^73** |
| **4 distinct per cycle, pool 69** | `C(69,4)^10` | ≈ 3.4 × 10^59 |
| **40 distinct, ordered, pool 69** | `69P40` | ≈ 1.2 × 10^67 |
| **40 distinct, unordered, pool 69** | `C(69,40)` | ≈ 1.2 × 10^19 |

Most permissive **correct** bound: **`69^40`** (indices 1–69 only; index 70 forbidden at P71).

## Sequential chain rule (no skipping)

```text
Verified TDAD/DA chain in double_and_add.txt:  puzzles 1–70
First gap:                                      puzzle 71 (empty)
Also empty:                                     puzzles 72, 73, 74
Next filed T only:                              puzzle 75 (value, no verified path)

Rule: each puzzle n uses d_{index} with index < n only.
But the SEQUENCE matters: later puzzles inherit the index grammar
from verified prior playlists. You cannot jump to P135 (or even P72+)
with a valid TDAD/DA reading until P71 is closed on-chain.
```

Why P71 blocks everything after it:

| Fact | Implication |
|------|-------------|
| P70 last verified in `double_and_add.txt` | Prior pool for P71 is exactly **1–70** |
| P71 empty in DA file; filed paths fail `[T]G == P71` | **No trusted d_71** exists in the chain |
| P72/P73/P74 also empty | Sequence breaks at the 10-cycle transition |
| P100 pattern uses `536870912(70)` etc., never index 71 | Later puzzles pull from **verified** priors only |
| Anchor ladder 65, 70, **75**, 80… | P71 sits between anchors; skipping it breaks the ladder |

```text
P71 is not "one more combinatorics exercise."
It is the first missing rung. Every TDAD/DA step after 70 is off-sequence
until P71's playlist passes [T]G == P71.
```

## P135 is downstream (blocked at P71)

P135 TDAD projection is **not** a parallel search with `84^40` or `134^40` priors.
Those counts are theoretical upper bounds **after** the chain through P134 is verified.
Current status: **blocked at P71** — do not advance TDAD/DA past 70 until the gap closes.

| Constraint | P71 filed path |
|------------|----------------|
| Terms | 40 |
| Pure `[3,2,1,2]` | yes |
| Unique prior indices used | 33 of 70 |
| Max reuse of one index | 2 |
| In-range partial paths documented | 4+ (before final 40-term path) |
| Playlists tested vs address | 5 in-range → **0** pass `[T]G = P71` |

Observed paths use **reuse ≤ 2** and **33 unique indices** — tighter than raw `70^40`, but still astronomically large.

Observed paths use **reuse ≤ 2** and **33 unique indices** — tighter than raw `70^40`, but still astronomically large.

## Observed constraints (actual P71 playlist in thePattern)

```text
Operators:  one metronome [3,2,1,2]
Combinations: 10^59 – 10^73 for P71 (model-dependent)
Sequence:   locked at P70; P71 must close before any later TDAD/DA
Observed:     1 canonical 40-term path tested; 4+ in-range alternates exist
True key:     exactly one playlist sums to d_71 with [T]G = P71

The drummer plays one beat.
There are roughly 10^74 ways to hand him the sheet music.
But you cannot hand sheet music for P135 until P71's song is verified.
The address gate picks the one correct song.
```
