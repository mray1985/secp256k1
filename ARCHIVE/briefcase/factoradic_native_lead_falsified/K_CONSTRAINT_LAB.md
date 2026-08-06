# K-constraint laboratory

**Strategic pivot** (after F-06):

> Stop asking coordinates to resemble d; start testing constraints on k inside ECDSA.

## Identity

```text
s*k ≡ z + r*d  (mod N)
k ≡ (z + r*d) * s^{-1}  (mod N)
```

## Panel

| | |
|--|--|
| Source RSZ | `ARCHIVE/puzzle_rsz_cache.json` |
| Known keys | `factoradic_private_keys.csv` |
| Panel | `logs/SOLVED_NONCE_PANEL.{json,csv}` |
| Rows | **82** solved spends with known d |
| k verifies vs r | **82/82** |

Suggested holdout: train puzzles n<=50 (50), test n>50 (32).

k bit-length: min=249, median=256, max=256.

## Sign-invariant nonce

Bitcoin low-S can flip recovered nonce `k -> N-k`. Always use:

```text
k* = min(k, N-k)
```

## K-00 admissibility (required before rules)

| Tag | Panel |
|-----|-------|
| sources | blockstream: 68; hashkeys partial: 14 |
| low_S | 76/82 |
| See | `logs/K00_PANEL_ADMISSIBILITY.md` |

Do not train a universal P135 rule from the mixture unless it survives **leave-one-source-out**.

## Candidates

| ID | Verdict | note |
|----|---------|------|
| K-01 orbit-safe 8-bit bins on k* | **FAIL** | holdout retention 0.22 ≈ random; LOSO collapses; byte-bin dead |
| K-02 RFC6979(d,z) exact match | **ATTRIBUTION** | hashkeys 14/14; blockstream 30/68; signer ID not universal k-rule |
| K-03 hashkeys txid batch | **ATTRIBUTION_CONFIRMED** | in-batch 14/14 vs out 30/68; P135 on same tx |

**Boundary:** No universal empirical k-rule may be transferred from heterogeneous puzzle spends to P135.

**P135 (batch-scoped, not a solve):**

```text
Strongest justified: 14 solved inputs on tx 17e4e323… used RFC6979-SHA256 (or equivalent).
Supported (not proven) for P135: k_135 = RFC6979_SHA256(d_135, z_135)
Validator: [d]G = P_135  AND  ECDSA_RFC6979(d,z) = (r,s)
```

Does **not** independently narrow the private-key range (HMAC keyed by d).
Remaining uncertainty: input-level signer consistency within the tx.

Buys: nonce-model attribution, candidate rejection, batch isolation.
Does not buy: an equation independent of d.

## Promotion gate for a nonce rule R

A candidate constraint R (predicate / sieve on observables that may involve r,s,z,P,
and optionally hypothesized structure on k) promotes only if on **held-out** solved
signatures:

```text
retention of true k* = 100%
surviving candidates / N  << 1
survives leave-one-source-out
survives random uniform k* null (pass rate ≈ reduction, not 100%)
k <-> N-k control OK
```

Also require:

* preregistration before peeking (`logs/prereg/K_CONSTRAINT_PREREG_TEMPLATE.md`)
* not DL recomputation of known d
* not vacuous curve membership

## What this lab is for

Calibrate constraints that **retain true historical nonces** while shrinking the
candidate set — then ask whether the same rule narrows Puzzle 135's equation
without claiming a solve from coordinate resemblance.

## Closed (do not reopen)

Coordinate-similarity branches F-01…F-06 (factoradic, offsets, doubling, GLV argmin MI,
adjacent Hamming). K-01 byte-bin clustering. See archive ledgers under
`ARCHIVE/briefcase/factoradic_native_lead_falsified/`.
