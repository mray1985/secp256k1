# Full Spearman matrix (cohort 82)

**Script:** `spearman_full_matrix.py`  
**Artifact:** `spearman_full_matrix.json`

`Rx` ≡ ECDSA `r` (x-coordinate of \(R=[k]G\)). `Ry` is separate when \(k\) known.

## Core (raw values)

|  | n | d | Px | Py | Pmy | r(=Rx) | s | z | Ry |
|--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **n** | 1 | 1 | −0.12 | −0.01 | +0.01 | −0.02 | −0.10 | −0.08 | −0.01 |
| **Px** | | | 1 | +0.07 | −0.07 | **+0.24** | +0.04 | +0.07 | +0.14 |
| **Py** | | | | 1 | **−1** | −0.03 | −0.05 | −0.02 | −0.04 |
| **r** | | | | | | 1 | −0.15 | −0.16 | −0.17 |
| **s** | | | | | | | 1 | +0.19 | +0.02 |
| **z** | | | | | | | | 1 | +0.00 |

- \(n\), \(d\), \(\log_2 d\): mutual Spearman **1** (band structure).
- \(P_y\) vs \(P_{my}=p-P_y\): Spearman **−1** (algebraic, not a discovery).
- Strongest non-trivial limb pair: \(P_x\) vs \(r\) ≈ **+0.24** (weak).
- No raw limb tracks puzzle height (\(|\rho|\lesssim 0.12\)).

## Scale-free \(q=\log a/\log b\) vs \(n\)

All \(|\rho|\lesssim 0.10\) (same noise band as before).

## \(F=d\cdot q\) vs \(n\) / \(d\)

All Spearman **+1** — \(F\approx d\) inheritance (float print may show `1.0000000000000002`).

## Ruling

Correlating “all of it” does not surface a public-limb predictor of \(d\) or \(n\). Only \(d\)-multiplied features lock to perfect rank order.
