# Genesis RSZ coupled invariants

Rows: **184** | with d: **82** | with pubkey: **184**
ECDSA resid zero: **82/82** | x([k]G)==r: **82/82**

## vs marginal baseline

| test | r(n, feature) |
|------|---------------|
| marginal r/N | +0.071 |
| best coupled | +0.324 (kd_mod_over_N, solved_k) |

## Lane A — ECDSA system (solved, k recovered)

| feature | r(n) | perm p |
|---------|------|--------|
| k_over_N | -0.147 | 0.177 |
| k_inv_over_N | -0.061 | 0.573 |
| k_minus_d_signed | -0.029 | 0.807 |
| kinv_minus_inv5_signed | -0.176 | 0.114 |
| kd_mod_over_N | +0.324 | 0.000 |
| d_minus_T_over_N | +0.000 | 1.000 |
| k_minus_T_signed | -0.029 | 0.807 |

**kd_mod artifact:** r(n, log2 d) = **+1.000** — k*d/N inherits index through d-scale, not k-structure.

_Note: `d_minus_T` is tautological (transcript stores final d). Meaningful TDAD tests need operation-path intermediates, not final scalar._

## Lane B — Roof stitch (r vs map_p_to_n(Px))

| band | feature | r(n) | perm p |
|------|---------|------|--------|
| all | roof_stitch_norm | +0.102 | 0.158 |
| all | roof_stitch_signed | -0.083 | 0.267 |
| all | r_minus_px_map_over_N | -0.009 | 0.910 |
| all | rem_minus_r_mod_p_over_p | -0.024 | 0.724 |
| all | defect_px_minus_p_times_map_over_N | +0.000 | 1.000 |
| 161-256 | roof_stitch_norm | +0.027 | 0.802 |
| 161-256 | roof_stitch_signed | +0.004 | 0.969 |
| 161-256 | r_minus_px_map_over_N | +0.011 | 0.905 |
| 161-256 | rem_minus_r_mod_p_over_p | +0.029 | 0.785 |
| 161-256 | defect_px_minus_p_times_map_over_N | +0.000 | 1.000 |
| solved | roof_stitch_norm | -0.016 | 0.893 |
| solved | roof_stitch_signed | +0.097 | 0.406 |
| solved | r_minus_px_map_over_N | +0.050 | 0.643 |
| solved | rem_minus_r_mod_p_over_p | -0.007 | 0.950 |
| solved | defect_px_minus_p_times_map_over_N | +0.000 | 1.000 |

## Lane C — TDAD subset

| feature | r(n) | perm p |
|---------|------|--------|
| d_minus_T_over_N | +0.000 | 1.000 |
| k_minus_T_signed | -0.029 | 0.807 |
| kinv_minus_inv5_signed | -0.176 | 0.114 |

## P135 vs 161-256 cloud (z-score on coupled features)

| feature | z |
|---------|---|
| r_minus_px_map_over_N | +1.63 |
| roof_stitch_signed | -0.85 |
| roof_stitch_norm | +0.64 |
| rem_minus_r_mod_p_over_p | -0.44 |
| defect_px_minus_p_times_map_over_N | +0.00 |

## Scope

Coupled panel tests **multi-variable** structure. Null perm p > 0.05 means no index encoding in that invariant.
Does **not** close TDAD recipe search or full f(r,s,z,k,d,p,N) algebra.

JSON: `puzzle_genesis_rsz_coupled.json`
