# P71-S-20260710-01 — Address-scanner correctness (PRE-REGISTERED)

**Status:** LOCKED before evaluation. Not Kangaroo. Not pattern search.

| Field | Value |
|-------|-------|
| Candidate ID | P71-S-20260710-01 |
| Short name | p71_address_scanner_calibration |
| Date registered | 2026-07-10 |
| Target | Puzzle 71 · `1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU` |
| Band | \(d\in[2^{70},2^{71})\), \(W=2^{70}\) |
| Pubkey | **not exposed** — hash160 / address only |

---

## Crucial difference from P135

No public key ⇒ no \(Q=P-[2^{70}]G\) ⇒ **no interval-DLP kangaroo**.

Exact path:

\[
d \rightarrow \text{compressed SEC} \rightarrow \mathrm{SHA256} \rightarrow \mathrm{RIPEMD160}
\]

until hash160 matches. Expected \(\sim 2^{69}\) candidate tests on the full band.

## Calibration requirements

* Exact key recovery on artificial hidden targets and solved puzzle addresses
* No missing or overlapping range partitions
* Checkpoint / resume agreement
* CPU and GPU agreement (when both exist)
* Final address / hash160 verification
* Measured keys per second

**Forbidden:** Kangaroo; shelf2/gap heuristics; creator-sequence ranking without explicit \(S\).

## Promotion gate

1. Recovers every calibration target without secret hints in the search loop
2. Partitions cover \([L,R)\) with no gaps/overlaps
3. Checkpoint resume recovers the same key
4. Reported rate reproducible across runs
5. Every hit: \(\mathrm{HASH160}([d]G)=\mathrm{target}\)

## Result (2026-07-10)

**PASS** (Python reference): oracle 8/8, solved 9/9, checkpoint PASS.  
Rate ≈ 9.3×10³ keys/s (CPU reference only). GPU agreement pending.

Artifact: `logs/p71_s01/P71_S01_calibration_results.json`
