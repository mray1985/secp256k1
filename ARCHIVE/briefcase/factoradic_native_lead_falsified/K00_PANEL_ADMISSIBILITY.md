# K-00 Panel admissibility

**Date:** 2026-07-10

## Warning

82/82 r-verification proves algebraic correctness, NOT a shared nonce-generation process. Do not train a universal P135 rule from a mixture unless it survives leave-one-source-out.

Also: Bitcoin low-S normalization can flip recovered nonce `k -> N-k`.
All nonce-pattern tests use `k* = min(k, N-k)`.

## Stratification

| Tag | Counts |
|-----|--------|
| source | {'blockstream spend tx': 68, 'hashkeys.space partial spend': 14} |
| era_proxy | {'early_n_le_50': 50, 'mid_51_100': 26, 'late_gt_100': 6} |
| low_S | 76/82 (92.7%) |
| unique pubkeys | 82 |
| unique txids | 58 |
| unique 8-bit bins (all panel) | 71 / 256 |

Sighash / SegWit: **unknown** (not in RSZ cache).

## Implication for K-01+

Train universal rules only if they survive **leave-one-source-out**.
The heterogeneous 82-row set remains useful as a **null panel**.
