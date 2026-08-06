# F-ordering sieve (leave-one-out)

**Status:** Tested — **0 usable verified bits**  
**Script:** `ordering_sieve_loo.py`  
**Artifact:** `ordering_sieve_loo.json`

## Route under test

\[
\texttt{1.0000000000000002}
\;\rightarrow\;
\rho(F,n)=1
\;\rightarrow\;
F_1<\cdots<F_{82}
\;\rightarrow\;
\frac{F_i}{q_m}<d_m<\frac{F_j}{q_m}
\]

with \(F=d\cdot q\), \(q=\log a/\log b\), intersected with the known band \([2^{n-1},2^n)\).

This path is logically valid as a **falsifiable sieve**. It is not algebraic inversion of the float.

## LOO results (82 solved)

| Formula | Coverage | Empty | Tighter than band | Max bits cut | Raw lo > \(2^{n-1}\) |
|---------|----------:|------:|------------------:|-------------:|---------------------:|
| \(d\log P_x/\log P_y\) | 1.000 | 0 | 1/82 | 0.0078 | 0 |
| \(d\log P_y/\log P_x\) | 1.000 | 0 | 1/82 | 0.0331 | 1 |
| Control \(q=1\) (pure \(d\)) | 1.000 | 0 | 0/82 | 0 | 0 |

Full-set \(F\) is strictly increasing with puzzle height for both formulas (inherited from \(d\) with \(q\approx 1\)).

The two “tighter” cases are sub-bit noise at the band edge (ceil/floor of a \(q\)-scaled neighbor), not a stable cut.

## Puzzle 135 (lower bound only)

Highest solved neighbor below: **130**. No solved point above 135.

For seed orientation \(q=\log P_y/\log P_x\):

| Quantity | Value |
|----------|--------|
| \(d_{\mathrm{lo}}=F_{\max}/q_{135}\) | \(\approx 1.097\times 10^{39}\) |
| Band floor \(2^{134}\) | \(\approx 2.178\times 10^{40}\) |
| \(d_{\mathrm{lo}} / 2^{134}\) | \(\approx 0.050\) |
| Beats floor? | **No** |
| Bits cut | **0** |

The ordering lower bound sits ~4–5 bits **below** the standard puzzle floor, so the intersect is just \([2^{134},2^{135})\).

## Interpretation

1. Perfect rank identity is real: solved \(F\) tracks puzzle order.
2. That ordering is almost entirely \(d\)’s band structure; \(q\approx 1\) does not push bounds inside the band.
3. Coverage stays 100% because the true \(d\) already lies between neighboring \(d\)’s at different bit lengths — the sieve rarely claims anything the band did not already know.
4. Float artifact remains documentation-only; it correctly *signposts* monotonicity, but monotonicity does not buy keyspace.

## Ruling

\[
\boxed{\text{F-ordering sieve: NULL for bit removal}}
\qquad
\boxed{0\text{ verified bits}}
\]
