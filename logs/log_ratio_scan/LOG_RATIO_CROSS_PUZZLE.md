# Cross-puzzle log-ratio scan

**Status:** **NULL / FALSIFIED** — 0 verified bits.

This file closes the loop: a reproduced seed value that looked strong, then a proper cross-puzzle falsification.

## Seed (Puzzle 60) — reproduced exactly

\[
d\frac{\log(P_y)}{\log(P_x)}=1.141812980483051\times 10^{18}
\]

Screenshot value was genuine; implementation matched.

## Why it looked stronger than it was

For

\[
F=d\frac{\log(P_y)}{\log(P_x)},
\]

\[
\frac{\log(P_y)}{\log(P_x)}\approx 1
\quad\Rightarrow\quad
F\approx d.
\]

Private keys increase with puzzle height, so \(\rho(F,n)=1\) is inherited from known \(d\), not extracted from \((P_x,P_y,r,s,z)\).

## Correct diagnostic

\[
\frac{F}{d}=\frac{\log(P_y)}{\log(P_x)}.
\]

| Formula | \(\rho(F/d,n)\) | \(p_{\mathrm{emp}}\) |
|---------|----------------:|---------------------:|
| \(d\log(P_y)/\log(P_x)\) | \(+0.0358\) | \(0.76\) |
| \(d\log(P_x)/\log(P_y)\) | \(-0.0358\) | \(0.76\) |
| \(d\log(P_x)/\log(r)\) | | \(0.415\) |
| \(d\log(r)/\log(s)\) | | \(0.795\) |
| \(d\log(P_x)/\log(s)\) | | \(0.94\) |
| \(d\log(P_x)/\log(z)\) | | \(0.97\) |

\(k\)-weighted formulas match shuffled controls (\(p\sim 0.66\)–\(0.91\)).

### Fake \(\rho=-1\)

\((\text{log ratio})/d \approx 1/d\) decreases monotonically with puzzle height; shuffled data gives the same \(-1\).

## Ruling

\[
\boxed{\text{Cross-puzzle log-ratio hypothesis: NULL}}
\]

\[
\boxed{\text{Verified bits removed: }0}
\]

Log ratios are real numerical features (tight band around 1, often within ~1%), but they do not predict private-key position once the known \(d\) multiplier is removed.

**Strongest result:** proper falsification — distinguishes “reproduces a known value” from “predicts an unknown key.”

JSON: `logs/log_ratio_scan/log_ratio_cross_puzzle.json`  
Ledger: `logs/LEDGER_LOG_RATIO_FALSIFICATION.md`
