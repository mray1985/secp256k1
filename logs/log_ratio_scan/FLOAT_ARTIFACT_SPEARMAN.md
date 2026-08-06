# Float artifact: `1.0000000000000002` in Spearman fields

**Status:** Documented IEEE-754 artifact — **not** curve structure, **not** a hand fraction, **not** verified bits.

**Date:** 2026-07-10  
**Source JSON fields:** `spearman_F_vs_n`, `spearman_F_vs_log2d` (and Pearson-on-ranks Spearman in `analyze_log_ratio_pearson.py`)  
**Code path:** `scan_log_ratio_cross_puzzle.py` → `spearman()` (Pearson correlation of average ranks, float64)

---

## Observed value

Printed / serialized form:

```text
1.0000000000000002
```

Exact float64 identity:

\[
1 + 2^{-52}
= 1 + \frac{1}{4503599627370496}
\]

Expanded decimal (binary→decimal of that single float):

```text
1.0000000000000002220446049250313080847263336181640625
```

(Trailing zeros beyond that are padding, not extra precision.)

In Python:

```python
>>> 1.0 + 2**-52
1.0000000000000002
>>> (1.0 + 2**-52) == 1.0000000000000002
True
```

---

## Mathematical truth (exact)

Cohort: **82** solved puzzles with \(F \approx d\) (because \(\log a/\log b \approx 1\)).

Rank vectors of \(F\) and of puzzle height \(n\) are **identical**, so

\[
\sum_i d_i^2 = 0
\qquad\Rightarrow\qquad
\rho = 1 - \frac{6\sum d_i^2}{n(n^2-1)} = 1
\]

with \(n(n^2-1) = 82 \times 6723 = 551286\).

Exact / Decimal Spearman on the same ranks: **1**.

---

## Why float64 prints `1.0000000000000002`

Implementation computes Spearman as:

\[
\rho = \frac{\sum (r_i-\bar r)(s_i-\bar s)}
{\sqrt{\sum(r_i-\bar r)^2}\;\sqrt{\sum(s_i-\bar s)^2}}
\]

When ranks match, this is \(S / (\sqrt{S}\cdot\sqrt{S})\) with measured

\[
S = 45940.5
\]

| quantity | float64 result |
|----------|----------------|
| `num` (= \(S\)) | `45940.5` |
| `math.sqrt(S) * math.sqrt(S)` | `45940.49999999999` (\< \(S\)) |
| `num / (√S·√S)` | `1.0000000000000002` |

Cause: \(\sqrt{S}\sqrt{S}\) is not bit-exact \(S\) in IEEE-754 binary64; the product undershoots, so the ratio overshoots by **one ulp above 1.0**, which is \(2^{-52}\).

This is independent of secp256k1’s 256-bit field. The exponent **52** is the **binary64 mantissa width**, not \(256-204\) or any keyspace cut.

---

## What this is not

- Not a manual calculation of 78 decimal places  
- Not evidence that \(\sum d_i^2 < 0\)  
- Not modular / imaginary rank distance  
- Not a relation between machine epsilon and curve order \(N\) or prime \(p\)  
- Not a reason to prefer one log-ratio formula over another  

All formulas with \(F\approx d\) hit the **same** float slot for the same reason: perfect rank alignment + the same Pearson-on-ranks float path.

---

## How to cite in reports

| Context | Write |
|---------|--------|
| Scientific Spearman | `1` or `1.0` (exact under identical ranks) |
| Reproducing JSON / float dump | `1.0000000000000002` (= `1 + 2**-52`, float64 artifact) |
| Bits / ECDLP claims | **0** — artifact only |

---

## Minimal reproduction

```python
import math
S = 45940.5  # rank variance for n=82 identical ranks 1..82
print(S / (math.sqrt(S) * math.sqrt(S)))  # 1.0000000000000002
print(1.0 + 2**-52)                       # same bit pattern
```

Or any perfect Spearman via this codebase’s `spearman(F, n)` when ranks of `F` match ranks of `n`.
