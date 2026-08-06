# EXHIBIT: residue offset-class scan (solved only)

Global full-mod lane closed. Local offset test:

```text
(num - d) mod 2^k
(num - (N-d)) mod 2^k
(num - r) mod 2^k
```

k ∈ {8, 16, 32, 64} · bucketed by bit-length, carry, branch, β-slot.

## Scope

```text
solved puzzles with pubkey: 82
ways per puzzle:            8 (4 heads × 2 branches)
```

## k=32 global (primary: pubkey Px + p−y)

| Ref | Unique offsets | Max share | Entropy (bits) |
|-----|----------------|-----------|--------------|
| d | 82 | 1 | 6.3576 |
| N−d | 82 | 1 | — |
| r | 82 | 1 | — |

```text
transferable candidates (max_share ≥ 25% of bucket): 0
```

At k=32 every primary offset is unique (max_share=1). Any k=8 repeats are birthday noise (~6 bits entropy).

## Carry / head / branch buckets (top max_share)

```text
  carry_head_branch (0, 'pubkey_Px', 'y') k=8 ref=N_minus_d: unique=40 max_share=4 ent=5.2192
  carry_head_branch (0, 'beta_Px3', 'y') k=8 ref=N_minus_d: unique=40 max_share=4 ent=5.2192
  head_branch ('pubkey_Px', 'y') k=8 ref=N_minus_d: unique=71 max_share=4 ent=6.0649
  head_branch ('pubkey_Px', 'p_minus_y') k=8 ref=N_minus_d: unique=66 max_share=4 ent=5.9245
  head_branch ('beta_Px1', 'y') k=8 ref=N_minus_d: unique=71 max_share=4 ent=6.0649
  head_branch ('beta_Px3', 'y') k=8 ref=N_minus_d: unique=71 max_share=4 ent=6.0649
  head_branch ('beta_Px3', 'p_minus_y') k=8 ref=N_minus_d: unique=66 max_share=4 ent=5.9245
  beta_head ('pubkey_Px',) k=8 ref=N_minus_d: unique=120 max_share=4 ent=6.7736
  beta_head ('pubkey_Px',) k=8 ref=r: unique=122 max_share=4 ent=6.798
  beta_head ('beta_Px1',) k=8 ref=d: unique=121 max_share=4 ent=6.769
```

## Classification (filed)

```text
field-native packet:           factual
curve wrap m:                  factual
pair-minus-wrap residue:       factual
residue as private-key:        no
residue as shared fingerprint: no
num mod p = (y - m) mod p:     factual (x*p ≡ 0 mod p)
```

## Clean ruling

```text
Missing-term residue is point-specific structure.
Not d. Not a shared scalar mask. Still a valid witness layer.
Local offsets: no transferable mask (k=32 all unique; k=8 high entropy)
```

Judge Popcorn: **The residue testified everywhere and lied nowhere — it just didn't identify the culprit.**
