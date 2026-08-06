# Ledger: K-02 RFC6979 identification

## Strategic boundary

> A nonce pattern from solved-puzzle spending transactions describes the
> **people/software that spent those coins**, not necessarily the creator of
> the puzzle set.

$$
\boxed{\text{No universal empirical }k\text{-rule may be transferred from heterogeneous puzzle spends to P135.}}
$$

## K-01 reminder

Byte-bin clustering FALSIFIED (holdout ≈ random).

## K-02 result (2026-07-10)

Exact RFC6979_SHA256(d,z) with match in {k, N-k}.

| | |
|--|--|
| overall | **44/82** |
| blockstream | {'n': 68, 'matches': 30, 'rate': 0.4411764705882353} |
| hashkeys | {'n': 14, 'matches': 14, 'rate': 1.0} |
| **Verdict** | **ATTRIBUTION** |

Many exact matches concentrated in source(s): hashkeys.space partial spend. Those spends likely used RFC6979. Signer attribution only — not transferable to P135 unless P135 shares that signer.

Even success would be **signer attribution**, not key recovery for P135, unless
the P135 signature shares that signing process.

**Co-location fact (not a solve):** Puzzle 135's RSZ entry is on the same
`hashkeys.space partial spend` transaction (`17e4e323…`) as the 14/14 RFC6979
matches. That supports analyzing P135 under a *preregistered* RFC6979 hypothesis
for that batch only — it does not transfer empirical rules from blockstream spends,
and it does not by itself yield `d`.

Artifacts: `K-20260710-02_rfc6979_result.*`, `k02_rfc6979_id.py`.
