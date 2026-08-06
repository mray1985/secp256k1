# Ledger: K-00 admissibility + K-01 byte-bin — FALSIFIED

## K-00 Panel admissibility

82/82 `r`-verification proves **algebraic correctness**, not a shared nonce process.

| Tag | Result |
|-----|--------|
| sources | blockstream spend tx: **68**; hashkeys.space partial spend: **14** |
| low_S | 76/82 (92.7%) |
| unique pubs / txids | see `K00_PANEL_ADMISSIBILITY.md` |
| sighash / SegWit | unknown (not in cache) |

**Rule:** do not train a universal P135 nonce rule from the mixture unless it survives **leave-one-source-out**. Heterogeneous panel remains a useful null panel.

Always use sign-invariant orbit:

```text
k* = min(k, N-k)
```

## K-01 Orbit-safe byte-bin recurrence — FALSIFIED

Locked 8-bit bins on `k*` only (no width sweep, no r/s/z features).

| Metric | Value |
|--------|------:|
| \|B_train\| / 256 | 47/256 = **0.184** |
| holdout retention (n>50) | **0.219** (not 100%) |
| random uniform pass | 0.188 ≈ survivor fraction |
| k↔N-k control | OK |
| LOSO blockstream | retention **0.074** |
| LOSO hashkeys | retention **0.357** |
| **Verdict** | **FAIL** |

> Independently observed nonces do **not** repeatedly occupy a restricted set of
> sign-invariant 8-bit magnitude bands. Holdout retention matches random chance
> at the survivor fraction; source-held-out testing collapses further.

**Byte-bin clustering is dead** under this locked definition. Do not reopen with
4/12/16-bit knobs — that is the same question.

Artifacts: `K00_PANEL_ADMISSIBILITY.*`, `K-20260710-01_byte_bin_result.txt`,
`k00_k01_orbit_byte_bin.py`.
