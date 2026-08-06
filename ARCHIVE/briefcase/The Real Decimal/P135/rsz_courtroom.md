# P135 RSZ courtroom

Field-native witnesses under `/p` and `/p²` meet RSZ under `/N`.

## Verdict

```text
0 nonce hits — field-native k map does not reach R point
```

## Structural RSZ facts

| fact | pass |
|------|------|
| `r_equals_rx2` | True |
| `rx3_equals_rx2_beta` | True |
| `rx1_equals_rx2_beta_sq` | True |
| `R_point_recovered` | True |
| `R_x_equals_r` | True |
| `Lambda_equals_Px3_over_rx3` | True |
| `Lambda1_equals_Px3_over_rx2` | True |
| `Lambda_over_Lambda1_eq_beta_sq` | True |
| `Px_slot_chain` | True |
| `map_p_to_n_r_offset` | 81442418975298844065958007179272673015085628003970948200642364287470231482281 |
| `r_over_N` | 0.782896794304763443683725654409499838948249816894531250000000 |
| `s_over_N` | 0.133944641451081258853861299940035678446292877197265625000000 |
| `z_over_N` | 0.572394351232331510814788089192006736993789672851562500000000 |
| `Px_over_p_matches_r_over_N_roof` | False |

## RSZ roof (/N)

```text
r/N = 0.782896794304763443683725654409499838948249816894531250000000
s/N = 0.133944641451081258853861299940035678446292877197265625000000
z/N = 0.572394351232331510814788089192006736993789672851562500000000
s*k ≡ z + r*d (mod N)
```

## Field vs RSZ comparisons (honest — mostly unequal)

| a | b | equal |
|---|---|-------|
| r mod p | Px mod p | no |
| r mod N | map_p_to_n(Px) | no |
| r − map_p_to_n(Px) = 81442418975298844065958007179272673015424168538405229749738775490250174433509 | — | — |
| residue_num mod N | z mod N | no |
| residue_num mod p | r mod p | no |
| P_pair_num mod N | r mod N | no |
| carry_y | carry on rx2/pmy | yes |

## k candidate trials

Candidates tested: **68**
Nonce gate `[k]G.x == r`: **0**
Full gate stack pass: **0**

## Sanity (puzzle 100 known k)

```json
{
  "ok": true,
  "puzzle": 100,
  "k": "12107164864847556103224566827231474081368335030183654868671403733078048742431",
  "d_known": "868221233689326498340379183142",
  "d_derived": "868221233689326498340379183142",
  "nonce_ok": true,
  "ec_ok": true,
  "in_range": true,
  "note": "pipeline check only \u2014 gate_stack RSZ step is P135-hardcoded"
}
```

## Ruling

Residue retained as witness only. RSZ is the open lane.
Field-native scalars (map_p_to_n, floor pair, residue num) do not yield k with x([k]G)=r. Next: structural RSZ algebra (Λ bridges, rx slot packets) or external k search — not residue numerators.
