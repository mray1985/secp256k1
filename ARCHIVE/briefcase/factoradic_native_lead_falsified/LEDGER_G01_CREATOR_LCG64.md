# Ledger: G-01 Creator-side 64-bit LCG — FALSIFIED

## Question

\[
\boxed{\text{Do the normalized puzzle payloads follow a fixed creator-side recurrence?}}
\]

## Precise falsification

For an LCG \(w_{n+5}\equiv a w_n+c\pmod{2^{64}}\), subtracting consecutive steps eliminates \(c\):

\[
a(w_{80}-w_{75})\equiv w_{85}-w_{80}\pmod{2^{64}}.
\]

Here:

\[
\Delta_1=w_{80}-w_{75}=11727712612230228442,
\qquad
\gcd(\Delta_1,2^{64})=2,
\]

\[
\Delta_2=(w_{85}-w_{80})\bmod 2^{64}=4822242642774648023
\quad\text{(odd)}.
\]

A solution exists only when \(\gcd(\Delta_1,2^{64})\mid\Delta_2\). But \(2\nmid\Delta_2\).

Therefore **no multiplier \(a\) exists at all**, and consequently no pair \((a,c)\) can fit the first three points.

> **G-01 — FALSIFIED.** The required congruence
> \(a(w_{80}-w_{75})\equiv w_{85}-w_{80}\pmod{2^{64}}\)
> has no solution because \(\gcd(w_{80}-w_{75},2^{64})=2\) does not divide the odd right-hand side.

**Note:** “even denominator / no inverse” alone would not always kill an LCG (even \(\Delta_1\) can yield solutions when \(\Delta_2\) shares the gcd). The odd \(\Delta_2\) makes the contradiction absolute.

No \(w_{135}\) prediction, no \(2^{70}\) remainder, no reopen of this locked 64-bit LCG.

Artifacts: `G-20260710-01_creator_lcg64_result.*`, `g01_creator_lcg64.py`.
