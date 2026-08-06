# Pearson / scale-free follow-up

Cohort: 82 solved puzzles. Artifact: `pearson_and_scale_free.json`.

## 1. Pearson vs Spearman

| Metric | Typical value | Meaning |
|--------|---------------|---------|
| Spearman\((F,n)\) | \(+1.0000\) | Ranks of \(F\) = ranks of \(d\) |
| Pearson\((F,n)\) | \(\approx +0.315\) | Same as Pearson\((d,n)\); linear, not rank |
| Spearman\((F/d,n)\) | \(\sim -0.1\ldots +0.04\) | Weak / unstable |
| Pearson\((F/d,n)\) | \(\sim -0.10\ldots +0.12\) | Weak / unstable |

Pearson does **not** break the fake-perfect story by finding structure in \(F\); it only shows that \(F\) vs \(n\) is not linear (same as \(d\) vs \(n\)).

## 2. Why \(b=r\) looks negative

For \(\log(P_x)/\log(r)\):

- Spearman vs \(n\): \(-0.099\) (most negative among \(P_x/\cdot\))
- Pearson vs \(n\): \(-0.039\)
- Band means: \(1.0017\) (\(n\le20\)) → \(0.9989\) (\(n\) 41–60) → \(1.0024\) (\(n\ge81\))

Limb logs vs \(n\) are all near zero correlation (\(|\rho|\lesssim 0.2\)). The \(b=r\) dip is a small cohort fluctuation, not a stable ECDLP signal. Pairing shuffle: \(p_{\mathrm{emp}}=0.705\).

## 3. Scale-free baseline (strip \(d\) / \(10^{39}\))

Use only \(\log a/\log b\):

- mean \(\approx 1.000\)
- stdev \(\approx 0.007\)–\(0.010\)
- range roughly \(0.96\)–\(1.04\)

Pairing shuffle on Pearson\((F/d,n)\): all \(p_{\mathrm{emp}}\ge 0.41\).

## Ruling

Unchanged: cross-puzzle log-ratio hypothesis **NULL**, **0 verified bits**.
