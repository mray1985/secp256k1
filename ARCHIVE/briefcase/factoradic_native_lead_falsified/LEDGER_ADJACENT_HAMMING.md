# Ledger: Adjacent Hamming coupling — FALSIFIED

> **Adjacent private/public Hamming coupling — FALSIFIED.** Scalar-multiplication
> avalanche destroys local binary similarity; \(S=0.041\), \(\Delta=0.047\),
> \(p=0.73\), with train/holdout direction reversal.

\[
\boxed{\text{Stop asking coordinates to resemble }d;\text{ start testing constraints on }k\text{ inside ECDSA.}}
\]

## Closed similarity branches (do not reopen with knobs)

| Branch | Status |
|--------|--------|
| Native-lead factoradic / sawtooth pairing | FALSIFIED (null model) |
| Band-floor + \(Q_x+Q_y\) / Mersenne offsets | FALSIFIED |
| Doubling features \(T(Q)\), \(X_2(Q)\) | FALSIFIED — entire translated/doubling branch CLOSED |
| GLV argmin \(I(a;b)\) | FAIL (degenerate on puzzle keys) |
| Adjacent Hamming \(h_d\leftrightarrow h_P\) | FALSIFIED |

Stop inventing new distance metrics (edit distance, byte Hamming, \(x\)-only Hamming,
cosine, multi-step neighbors) — same avalanche question.

## Strategic pivot

Move from coordinate-pattern hunting to the ECDSA linear constraint:

\[
s k \equiv z + r d \pmod N
\qquad\Longrightarrow\qquad
k \equiv (z + r d)\, s^{-1} \pmod N
\]

Laboratory objects for solved spends:

\[
(d_i,\, k_i,\, r_i,\, s_i,\, z_i,\, P_i)
\]

**Target question:** Is there a preregistered constraint on the actual nonce \(k\),
derived from observable transaction data, that generalizes across solved puzzles
and narrows the unknown Puzzle 135 equation?

Promotion for a nonce rule \(R\):

```text
retention of true k on held-out solved signatures = 100%
surviving candidates / N  << 1
```

See: `logs/prereg/K_CONSTRAINT_PREREG_TEMPLATE.md`, `logs/K_CONSTRAINT_LAB.md`.
