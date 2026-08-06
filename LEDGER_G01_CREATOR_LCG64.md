# Ledger: G-01 Creator-side 64-bit LCG

## Question

$$
\boxed{\text{Do the normalized puzzle payloads follow a fixed creator-side recurrence?}}
$$

## Result

**Verdict: FAIL**

(w_80 - w_75) = 11727712612230228442 is even => not invertible mod 2^64. Locked LCG hypothesis fails immediately (no alternate modulus).

| | |
|--|--|
| chain | n=75,80,...,130 |
| infer | w75,w80,w85 → (a,c) |
| holdout | 0/9 exact |
| a | n/a |
| c | n/a |

Promotion required every holdout prediction exact. One miss closes this branch.
No width/modulus/encoding reopen.

Artifacts: `G-20260710-01_creator_lcg64_result.*`, `g01_creator_lcg64.py`.
