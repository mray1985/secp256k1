# Puzzle-height mod convention (k_x / k_y → d probes)

Saved from user specification. **N = puzzle number** = range height.

## Band

```
d ∈ [2^(N−1), 2^N)     LO = 2^(N−1),   TOP = 2^N − 1
```

Both transforms must land in **[LO, TOP]** (inclusive).

## Transforms

Given scalar `k` and puzzle **N**:

| Name | Formula | Range |
|------|---------|--------|
| **r1 (floor lift)** | `(k mod 2^(N−1)) + 2^(N−1)` | always `[LO, TOP]` |
| **r2 (height residue)** | `k mod (2^N − 1)`, then lift: `0 → TOP`; if `< LO` then `+ LO` | `[LO, TOP]` |

### Example: Puzzle 135 (N = 135)

```
LO   = 2^134
TOP  = 2^135 − 1
r1   = (k mod 2^134) + 2^134
r2   = k mod (2^135 − 1)  → band lift if needed
```

**Wrong (do not use):** `(k mod 2^N) + 2^N` — that jumps above TOP into `[2^N, 2^(N+1))`.

### Example: Puzzle 115 (N = 115)

```
LO   = 2^114
TOP  = 2^115 − 1
r1   = (k mod 2^114) + 2^114
r2   = k mod (2^115 − 1)  → band lift if needed
```

## k sources

| Label | Definition |
|-------|------------|
| **k_x** | `floor(N · Λ / p)` where `Λ = Px/rx mod p` |
| **k_y** | `floor(N · k_y,p / p)` where `k_y,p = (Py/ry)/Λ mod p` |

## Distance probe

```
dist_r1 = |d − r1|
dist_r2 = |d − r2|
```

Win condition: **stable distance pattern** across solved puzzles (not a single `dist=0`).

## Scripts

- `k_xy_mod134_distance.py` — `puzzle_k_transforms(N, k)`
- `k_xy_distance_table.py` — batch 5…135 step 5
- `ARCHIVE/k_xy_distance_table_5_135.csv`
