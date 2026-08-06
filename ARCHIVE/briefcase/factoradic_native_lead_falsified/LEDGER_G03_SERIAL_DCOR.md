# Ledger: G-03 Serial dependence gate (dCor) — FAIL

## Question

Is there detectable serial dependence in normalized within-band payload locations?

## Result

| Chain | S_real | p_perm | p99_null | Gate |
|-------|-------:|-------:|---------:|------|
| A 1..70 | 0.148568 | 0.843116 | 0.337352 | FAIL |
| B 75..130 step5 | 0.438213 | 0.654035 | 0.758612 | FAIL |

**Overall: FAIL** (require p_perm < 0.01 on **both**)

Solved payload locations behave like independently ordered draws at the detectable scale. Close invent-another-recurrence/hash cycle; prefer direct search-space engineering for Puzzle 135.

$$
\boxed{\text{Solved payload locations behave like independently ordered draws at the detectable scale.}}
$$

Close invent-another-recurrence/hash cycle. Prefer direct search-space engineering for Puzzle 135.

No lag sweep, Pearson/Spearman, or chain-combining reopen.

Artifacts: `G-20260710-03_serial_dcor_result.*`, `g03_serial_dcor.py`.
