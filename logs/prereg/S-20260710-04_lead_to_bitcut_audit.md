# S-20260710-04 — Lead-to-bitcut audit (PRE-REGISTERED)

**Status:** LOCKED before classification. Audit, not a new hypothesis.

| Field | Value |
|-------|-------|
| Candidate ID | S-20260710-04 |
| Short name | lead_to_bitcut_audit |
| Date registered | 2026-07-10 |
| Prerequisite | **S-03 LOCKED** (≈40–57 verified bits required for operational relevance) |

---

## Decisive question

\[
\boxed{\text{Exactly which private-key candidates are impossible, and how is that proved?}}
\]

Anything that cannot answer receives **0 verified bits** under S-03.

## Categories (forced)

1. **Provable interval reduction** — guaranteed interval or union containing \(d_{135}\).
2. **Provable candidate-set reduction** — explicit finite set guaranteed to contain \(d_{135}\).
3. **Ranking or resemblance only** — changes search order; does not exclude candidates.

\[
\boxed{0\text{ verified bits removed}}
\quad\text{(category 3)}
\]

## Bit formulas

Candidate set size \(M\) inside the \(2^{134}\) interval:

\[
b_{\mathrm{removed}}=134-\log_2 M.
\]

Surviving total interval width \(W\):

\[
b_{\mathrm{removed}}=134-\log_2 W.
\]

Baseline for all credits: the puzzle band / band-floor interval of width \(2^{134}\).
The band itself is the **starting point**, not a credited cut.

## Locked promotion requirements (credit bits only if all hold)

* Rule computed from **public** information, not the known private key
* Fixed **before** target evaluation
* Contains **every** locked holdout private key (100% coverage)
* Surviving size countable or rigorously bounded
* Beats shuffled pairing and random-curve controls
* Maps to an **executable** search region
* Full public-key verification remains the final gate

A filter that retains 1 in \(2^{20}\) but occasionally excludes the true key has **not**
removed 20 verified bits — it is a risky heuristic.

## Intersection rule

Do **not** add claimed reductions \(b_A+b_B\) unless independence is established.
Measure intersection directly:

\[
b_{A\cap B}=134-\log_2|A\cap B|.
\]

## Audit targets (from ledger)

Echo values; \(p/N\) rotations; operation-ledger / Λ / shelf2 slots; tax-math /
barcode constraints; RSZ-derived filters; factoradic / F-series; nonce K-series;
creator G-series; N-mirror; residue witnesses; lane/compass heuristics.

## Result (2026-07-10)

**17 leads audited → 0 incremental verified bits.** No lead meets S-03’s ≈40-bit gate.

Ruling: no audited object proves any private-key candidate inside \(2^{134}\) impossible.
Ranking / echo / ledger / RSZ-attribution → category 3 → 0 bits.

Artifact: `logs/s04_audit/S04_lead_bitcut_audit.json` · Ledger: `logs/LEDGER_S04_lead_to_bitcut_audit.md`
