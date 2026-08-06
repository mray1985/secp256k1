# LEDGER S-04 — Lead-to-bitcut audit

**Status:** **EVALUATED** — all audited leads score **0 verified bits** under S-03.

> Decisive question: **Exactly which private-key candidates are impossible, and how is that proved?**

Anything that cannot answer → \(\boxed{0\text{ verified bits removed}}\).

## Baseline

Puzzle band / band-floor: \(W=2^{134}\). This is the **S-03 starting point**, not a credited cut.

## Audit table

| Lead | Cat | Deterministic exclusion? | Holdout coverage | Surviving size | Verified bits |
|------|:---:|-------------------------:|-----------------:|---------------:|--------------:|
| Puzzle band / band-floor | 1* | yes (definition) | 100% | \(2^{134}\) | **0** (baseline) |
| N-mirror window | 3 | no | — | \(2^{134}\) equiv. | **0** |
| Echo values \(x^{h/256}\) etc. | 3 | no | — | \(2^{134}\) | **0** |
| D/8 lanes + Ω mod-9 | 3 | no | fails | \(2^{134}\) / heuristic | **0** |
| \(p/N\) root rotations (β, ω_N) | 3 | no | — | \(2^{134}\) | **0** |
| Op-ledger Λ / GAP / shelf2 | 3 | no | 0% as extractor | \(2^{134}\) | **0** |
| Tax-math / barcode / left5 | 3 | no | — | \(2^{134}\) | **0** |
| Residue numerators / packets | 3 | no | — | \(2^{134}\) | **0** |
| Carry threshold | 3 | no | — | \(2^{134}\) | **0** |
| RSZ \(sk\equiv z+rd\) alone | 3 | no | — | \(2^{134}\) | **0** |
| K-02/03 RFC6979 attribution | 3 | no | batch only | \(2^{134}\) | **0** |
| K-01 byte bins | 3 | no | FAIL | \(2^{134}\) | **0** |
| Factoradic native-lead | 3 | no | FAIL | \(2^{134}\) | **0** |
| F-01…F-06 pairing candidates | 3 | no | FAIL | \(2^{134}\) | **0** |
| G-01…G-03 creator formulas | 3 | no | FAIL | \(2^{134}\) | **0** |
| Λ / rx slot-packet algebra | 3 | no | open, unproven set | \(2^{134}\) | **0** |
| S-01/S-02 kangaroo engine | 3† | n/a | n/a | \(2^{134}\) | **0** |

\*Category 1 structurally, but **incremental** bits vs S-03 baseline = 0.  
†Search method, not a lead cut.

**Categories:** 1 = provable interval · 2 = provable candidate set · 3 = ranking/resemblance only.

## Locked credit rules (reminder)

Bits credited only when: public-only rule · fixed before eval · 100% holdout ·
countable surviving size · beats shuffle/random-curve · executable region ·
pubkey verify final.

Risky heuristics that sometimes drop the true key → **0 verified bits**.

## Intersection

No additive stack found. If future leads A, B both claim cuts:

\[
b_{A\cap B}=134-\log_2|A\cap B|
\]

— never \(b_A+b_B\) without proven independence.

## Ruling

| Metric | Value |
|--------|------:|
| Leads audited | 17 |
| Incremental category-1/2 cuts | **0** |
| Total verified bits credited | **0** |
| Meets S-03 ≈40-bit gate | **NO** |

\[
\boxed{\text{No audited lead currently proves any }d\text{ inside the }2^{134}\text{ band impossible.}}
\]

Pattern correlation, echo resemblance, ledger geometry, and signer attribution remain
useful as **witnesses** or **validators** — they do not pay rent in verified bits.

## Next

Only accept new P135 work that answers the decisive question with an explicit
surviving set or interval, then measure \(b_{\mathrm{removed}}\) under the locked gate.
Until then: **do not launch** kangaroo on heuristic rankings.

## Artifacts

- Prereg: `logs/prereg/S-20260710-04_lead_to_bitcut_audit.md`
- Audit JSON: `logs/s04_audit/S04_lead_bitcut_audit.json`
- Gate: `logs/LEDGER_S03_feasibility_boundary.md`
