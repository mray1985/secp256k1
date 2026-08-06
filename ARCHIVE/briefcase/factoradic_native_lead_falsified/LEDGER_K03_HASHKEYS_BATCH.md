# Ledger: K-03 Hashkeys batch RFC6979 attribution

## Clean ledger wording

> **RFC6979 attribution confirmed for all 14 solved inputs in the hashkeys batch.
> Puzzle 135 shares the transaction, making RFC6979-SHA256 the defensible
> batch-scoped nonce hypothesis. This strengthens validation and eliminates
> competing nonce narratives, but does not independently narrow the unknown
> private-key range.**

## Strongest justified statement

\[
\boxed{\text{The 14 solved inputs on transaction }17e4e323\ldots\text{ were signed with RFC6979-SHA256 or an exactly equivalent process.}}
\]

Because Puzzle 135 is another input on that transaction, the evidence
**supports—but does not mathematically prove**—that its signer used the same process:

\[
k_{135}=\operatorname{RFC6979}_{\mathrm{SHA256}}(d_{135},z_{135}).
\]

## Remaining uncertainty

**Input-level signer consistency.** One transaction can theoretically combine
signatures from different devices, wallets, or participants. “Same transaction”
is strong contextual evidence; “same signer implementation for every input”
remains the hypothesis.

## Consequence for the equation

The nonce is no longer an independent unknown. It is a deterministic function of \(d\):

\[
k=H_{\mathrm{RFC6979}}(d,z).
\]

Signature equation as a one-variable predicate:

\[
s\,H_{\mathrm{RFC6979}}(d,z)-rd-z\equiv0\pmod N.
\]

This does **not** reduce the keyspace algebraically: HMAC-SHA256 makes nearby
\(d\) values produce unrelated nonces (pseudorandom \(k(d)\), not smooth/invertible).

## What K-03 buys

1. **Nonce-model attribution** — random, timestamp-seeded, and pooled empirical nonce theories are inappropriate for this batch.
2. **Candidate rejection** — any proposed \(d\) must reproduce both the public key and its exact deterministic signature.
3. **Signer-batch isolation** — only evidence tied to the hashkeys transaction belongs in the Puzzle 135 nonce model.

## What K-03 does not buy

An extra equation independent of \(d\). Both checks are consequences of the same candidate:

\[
[d]G=P_{135},
\qquad
\operatorname{ECDSA}_{\mathrm{RFC6979}}(d,z)=(r,s).
\]

## Numbers (K-03)

| | |
|--|--|
| txid | `17e4e323cfbc68d7f0071cad09364e8193eedf8fefbcbd8a21b4b65717a4b3d3` |
| in-batch solved RFC6979 | **14/14** |
| out-of-batch | **30/68 (44.1%)** |
| P135 co-located | **True** |
| Verdict | **ATTRIBUTION_CONFIRMED** (batch-scoped) |

Artifacts: `K-20260710-03_hashkeys_batch_result.*`, `k03_hashkeys_batch_attribution.py`.
