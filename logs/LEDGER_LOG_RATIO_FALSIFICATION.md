# LEDGER — Cross-puzzle log-ratio falsification

**Status:** **NULL / FALSIFIED** — 0 verified bits.

**Date:** 2026-07-10  
**Artifacts:** `scan_log_ratio_cross_puzzle.py`, `logs/log_ratio_scan/log_ratio_cross_puzzle.json`, `logs/log_ratio_scan/LOG_RATIO_CROSS_PUZZLE.md`

## Seed (reproduced exactly)

Puzzle 60:

\[
d\frac{\log(P_y)}{\log(P_x)}=1.141812980483051\times 10^{18}
\]

Screenshot value was genuine; implementation matched.

## Why it looked stronger than it was

For

\[
F=d\frac{\log(P_y)}{\log(P_x)},
\]

the ratio stays near unity:

\[
\frac{\log(P_y)}{\log(P_x)}\approx 1
\quad\Rightarrow\quad
F\approx d.
\]

Solved private keys increase with puzzle height, so

\[
\rho(F,n)=1
\]

is **inherited from known \(d\)**, not extracted from \((P_x,P_y,r,s,z)\).

## Correct diagnostic

\[
\frac{F}{d}=\frac{\log(P_y)}{\log(P_x)}.
\]

Then:

| Formula | \(\rho(F/d,n)\) | \(p_{\mathrm{emp}}\) (shuffle) |
|---------|----------------:|-------------------------------:|
| \(d\log(P_y)/\log(P_x)\) | \(+0.0358\) | \(0.76\) |
| \(d\log(P_x)/\log(P_y)\) | \(-0.0358\) | \(0.76\) |
| \(d\log(P_x)/\log(r)\) | \(-0.099\) | \(0.415\) |
| \(d\log(r)/\log(s)\) | \(+0.026\) | \(0.795\) |
| \(d\log(P_x)/\log(s)\) | — | \(0.94\) |
| \(d\log(P_x)/\log(z)\) | — | \(0.97\) |

\(k\)-weighted formulas match their shuffled controls (\(p\sim 0.66\)–\(0.91\)).

## Second fake-perfect correlation

\[
\frac{\text{log ratio}}{d}\approx\frac{1}{d}
\]

has Spearman \(-1\) vs puzzle height because the numerator ≈ 1 while \(d\) grows. Shuffled data produces the same \(-1\) — arithmetic scaling, not structure.

## Ruling

\[
\boxed{\text{Cross-puzzle log-ratio hypothesis: NULL}}
\]

\[
\boxed{\text{Verified bits removed: }0}
\]

Log ratios are real numerical features (tight band around 1, often within ~1%), but they do **not** predict private-key position once the known \(d\) multiplier is removed.

**Value of this file:** proper falsification — distinguishes “reproduces a known value” from “predicts an unknown key.”

## Follow-up (Pearson / b=r / scale-free)

Script: `analyze_log_ratio_pearson.py` → `logs/log_ratio_scan/pearson_and_scale_free.json`

1. **Pearson does not rescue \(F\).** Spearman\((F,n)=1\) because ranks track \(d\). Pearson\((F,n)\approx 0.315\) for every formula — identical to Pearson\((d,n)\). Linear correlation still sees the \(d\)-dominated mass, not limb structure.
2. **\(b=r\) “sign flip” is noise.** Spearman\((F/d,n)\) for \(\log P_x/\log r\) is \(-0.099\); Pearson is only \(-0.039\). Band means of the ratio drift by ~0.003 across \(n\)-bins. Pairing shuffle \(p_{\mathrm{emp}}=0.705\).
3. **Scale-free baseline:** report only \(F/d=\log a/\log b\). Means \(\approx 1.000\pm 0.007\)–\(0.010\); no \(10^{39}\) mass. Pairing gates on Pearson\((F/d,n)\) all \(p_{\mathrm{emp}}\in[0.41,0.85]\).

Ruling unchanged: **NULL / 0 bits.**

## Float artifact documentation

JSON `spearman_F_vs_n` / `spearman_F_vs_log2d` = `1.0000000000000002` is **IEEE-754 binary64** \(1+2^{-52}\), from Pearson-on-ranks when \(\sqrt{S}\sqrt{S}<S\). Exact Spearman is **1**. Full write-up: `logs/log_ratio_scan/FLOAT_ARTIFACT_SPEARMAN.md`.

## F-ordering sieve (sideways path)

Hypothesis: \(\rho(F,n)=1\) ⇒ ordering inequalities ⇒ interval for unknown \(d\) via public \(q_m\).

LOO on 82 solved: coverage 100%, band tightening in ≤1/82 cases at ≪1 bit. P135 lower bound from solved ≤130 is ~0.05×\(2^{134}\) — **does not beat the floor**.

Ruling: **NULL / 0 bits**. Details: `logs/log_ratio_scan/ORDERING_SIEVE_LOO.md`, `ordering_sieve_loo.py`.
