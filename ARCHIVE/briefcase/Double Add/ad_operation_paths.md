# AD operation paths

Canonical: `F:\New folder\secp256k1\DOUBLE_AND_ADD+BREAKDOWN.txt`
Rules: `Double Add Rules.txt`

## Work ceiling

- **Last solved transcript:** P70
- **Highest active target:** P73 (unsolved — path to reconstruct)
- **Gap (no d):** P71–P74 — cannot reference `d(71)`…`d(74)` in paths
- **P73 anchor:** `d(70)` (n−3); band `[2^72, 2^73−1]`

## Early sequence correction (P1–P4)

Raw `double_and_add.txt` prose for **P4** says `7+1`. Correct path is **D(1)A(1)D(1)A(1)D(1)** per breakdown + rules.
P3 value 7 is **D(2)A(1)** under AD grammar (not “double previous” shorthand).
From P4 forward the global AD alternation is stable.

**Validation:** 37 puzzles parsed | AD violations: **3**

First violations:
- P21: starts A but P20 ended A
- P31: AD sum 2102388548 != d 2102388551
- P32: AD sum 2692763920 != d 3093472814

## RSZ cross (k vs path — solved with spend)

| metric | value |
|--------|-------|
| n | 37 |
| r_n_k_minus_path_final | -0.2704 |
| perm_k_minus_path | +0.1035 |
| r_n_anchor_repeats | +0.2774 |

## Sample paths

| n | ops | steps | anchor(n-3) reps | eval ok |
|---|-----|-------|------------------|---------|
| 1 | A(1) | 1 | 0 | True |
| 2 | D(1)A(1) | 2 | 0 | True |
| 3 | D(2)A(1) | 2 | 0 | True |
| 4 | D(1)A(1)D(1)A(1)D(1) | 5 | 5 | True |
| 5 | A(2)D(2)A(2)D(2)A(1)D(1) | 6 | 4 | True |
| 6 | A(3)D(3)A(3)D(3)A(3) | 5 | 5 | True |
| 7 | D(4)A(4)D(4)A(4)D(4)A(2)D(2)A(1)D(1) | 9 | 5 | True |
| 8 | A(5)D(5)A(5)D(5)A(5)D(5)A(5)D(3) | 8 | 7 | True |
| 9 | A(6)D(6)A(6)D(6)A(6)D(5)A(5)D(5)A(4)D(2) | 12 | 5 | True |
| 10 | A(7)D(7)A(7)D(7)A(6)D(2)A(2) | 7 | 4 | True |
| … | | | | |
| 35 | A(32)D(32)A(32)D(32)A(29)D(29)A(27)D(27) | 29 | 4 | True |
| 36 | D(33)A(33)D(33)A(31)D(31)A(27)D(27)A(26) | 21 | 3 | True |
| 37 | A(34)D(34)A(34)D(34)A(34)D(29)A(29)D(25) | 35 | 5 | True |
