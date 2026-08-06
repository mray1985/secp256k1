# K-20260710-03 — Hashkeys batch RFC6979 attribution strength (PRE-REGISTERED)

**Status:** LOCKED before evaluation. Do not change formula/parameters after peeking.

| Field | Value |
|-------|-------|
| Candidate ID | K-20260710-03 |
| Short name | hashkeys_batch_rfc6979_attribution |
| Date registered | 2026-07-10 |
| Date first evaluated | 2026-07-10 |

---

## Prior result (K-02)

Hashkeys partial-spend source: **14/14** exact RFC6979 matches (orbit `{k,N-k}`).
Blockstream: 30/68 mixed. Not a universal sieve.

## Locked strategic claims

\[
\boxed{\text{P135 probably has a deterministic nonce, but that nonce is cryptographically bound to the unknown }d.}
\]

Defensible P135 hypothesis (batch co-location, not universal transfer):

\[
\boxed{k_{135}=\operatorname{RFC6979}_{\mathrm{SHA256}}(d_{135},z_{135})}
\]

Candidate validator only:

```text
F(d) = s * RFC6979(d,z) - z - r*d  ≡ 0 (mod N)
```

HMAC keyed by `d` ⇒ not an algebraic solve; search still required.

## Exact test (this candidate)

**In-batch:** all solved panel rows whose `txid` equals the hashkeys partial-spend tx:

```text
txid = 17e4e323cfbc68d7f0071cad09364e8193eedf8fefbcbd8a21b4b65717a4b3d3
```

Require:

```text
match_rate_in_batch = 100%
  (RFC6979(d,z) ∈ {k, N-k} for every solved row on that txid)
```

**Out-of-batch contrast:** solved rows with any other txid:

```text
match_rate_out_of_batch   # report; need NOT be 100%
```

Primary claim promotes as **batch attribution** iff:

```text
in_batch retention = 100%
AND in_batch rate >> out_of_batch rate
```

**FORBIDDEN:** pooling blockstream into the batch; transferring the rule as a universal k-sieve; post-hoc encoding variants; claiming key recovery.

## Score

| Metric | Definition |
|--------|------------|
| in_batch_n / matches | solved panel rows on hashkeys txid |
| out_batch_n / matches | all other solved panel rows |
| P135 co-located | whether P135 RSZ row shares that txid (metadata only) |

## Result (evaluated 2026-07-10)

| Metric | Value |
|--------|------:|
| in-batch matches | 14/14 (100.0%) |
| out-of-batch matches | 30/68 (44.1%) |
| P135 co-located | True |
| Verdict | ATTRIBUTION_CONFIRMED |

In-batch 100% RFC6979 with substantially lower out-of-batch rate: hashkeys tx is one deterministic signing process. P135 co-located => defensible hypothesis k_135=RFC6979(d_135,z_135). This is a candidate VALIDATOR (F(d)=0), not an algebraic solve — HMAC keyed by d. Not transferable from blockstream spends.
