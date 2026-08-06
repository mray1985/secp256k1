# Notebook photos → code map

Maps `ECDLP/IMG_*.jpeg` bridge notebook to `ecdlp_full_pipeline.py`, `genesis_calibration.py`, and batch probe scripts.

**Legend**

| Symbol | Meaning |
|--------|---------|
| ✅ | Implemented and run automatically |
| ⚠️ | Implemented but **corrected** vs notebook (notebook formula kept as diagnostic) |
| 🔧 | Probe / batch layer only (not closure test) |
| ❌ | Not automated — manual or missing |
| 🚫 | Code explicitly **rejects** notebook step as win condition |

---

## Photo index

| File | Notebook section |
|------|------------------|
| IMG_9999 | 1. p-Side — small bridge Λ |
| IMG_0001 | 2. N-Side — Λ_N, GAP, defect d |
| IMG_0002 | 3. Carry b3_x, b3_yN |
| IMG_0003 | 4. Closing bridge — cubic check, adjust d, k ≡ Λ_N |
| IMG_0004 | Summary + final answer |
| IMG_9988–9998 | Detailed N-side closure appendix |

---

## IMG_9999 — p-Side (small bridge)

| Notebook | Code | Status |
|----------|------|--------|
| Three x-roots per point (G, P, r) | `DEFAULT_GX`, `DEFAULT_PX`, `DEFAULT_RX`; cube-root slots via `all_cube_roots_mod_p` | ✅ |
| Normalizers \(n_i^3 \equiv 1 \pmod p\) | Phase 1: `N1_HINT/N2_HINT/N3_HINT`, `latin_row`, slot collapse | ✅ |
| \(\Lambda = Px_i \cdot rx_i^{-1} \pmod p\) (same all slots) | Phase 5: `Lambdas`, `Lambda = Px[i]*rx[i]^-1 mod p` | ✅ |
| \(\Lambda = CP1 \cdot CR1^{-1}\) | Phase 4–5: `CP1`, `CR1` collapse | ✅ |
| \(y^2 = x^3 + 7\) | `y_roots`, `y_even`, Phase 7 | ✅ |
| Cubic aggregate \(IP = \prod Px_i\) | Phase 6: `IP`, `IR`, `IP == Lambda^3 * IR mod p` | ✅ |

**genesis_calibration:** `bridge_state()` uses `lambda_p = Px[row]*rx[row]^-1 mod N` (N-map of p-bridge row).

---

## IMG_0001 — N-Side (big bridge)

| Notebook | Code | Status |
|----------|------|--------|
| \(Qx \equiv \Lambda_N \cdot qx \pmod N\) | Phase 10: `Lambda_N`, per-row `Lambda_Ns[i]` | ✅ |
| Scale \(Q = P\cdot\delta\), \(q = r\cdot\delta\) | Phase 9: `Qx`, `qx`, `delta = p - N` | ✅ |
| \(\Lambda_N = \Lambda + \text{GAP}\) | Phase 10: `GAP = (Lambda_N - Lambda) % N` | ✅ |
| \(\Lambda_N(d) = \Lambda + \text{GAP} + d\) | Phase 14: `defect(d) = (delta + d) % N`; mirror band corners | ⚠️ Uses **δ+d** framing, not literal notebook additive on Λ_N |
| Puzzle band \([2^{n-1}, 2^n)\) | `puzzle_band(n)`, `PuzzleConfig.lo/hi/top` | ✅ |

**Batch:** `compare_family_mirror_batch.py` — `GAP = Lambda_N_row - Lambda_p mod N`, shelf2, offset bits.

---

## IMG_0002 — Carries

| Notebook | Code | Status |
|----------|------|--------|
| \(b3_x = (\Lambda_N \cdot qx_3 - Qx_3) / N\) integer | Phase 11: `carry(Lambda_N * qx[i] - Qx[i], N)`; `family_bridge.row_carries` | ✅ |
| \(y^3 \equiv R \pmod N\) → three y roots | `all_cube_roots_mod(N, …)`, IMG_9993 path in `verify_residue_solutions` | ✅ |
| \(b3_{yN} = (\Lambda_{yN} \cdot qy - Qy) / N\) integer | Phase 11: `carry(lam_y_N * qy3 - Qy3, N)` | ✅ |
| Carries must be whole numbers | `carry()`, `carry_quotient()`; regression checks | ✅ |

**Note:** Pipeline uses **active row** index `cfg.row` (P115 row 3, P135 row 2), not always slot 3.

---

## IMG_0003 — Closing the bridge

| Notebook step | Code | Status |
|---------------|------|--------|
| **1. Cubic check** \(\Lambda_{yN}^2 \equiv \Lambda_N^3 \pmod N\) | Phase 12 logs `naive_n_cubic_mix`; `emit_family_bridge` marks **WRONG LAYER** | 🚫 Diagnostic only |
| **2. Adjust d** until carries integer | Phase 14 defect lanes + Phase 17 `verify_d_candidates`; **no automated d search loop** | ⚠️ Partial |
| **3. Extract** \(k \equiv \Lambda_N \pmod N\) | `compute_scalar_frame`; compares candidates — **does not assert k=Λ_N** | 🚫 |

**Code’s actual closure laws (replace notebook step 1):**

- **LAW-P:** `lambda_y^2 == (Px^3+7)/(rx^3+7) mod p` — `verify_core_lambda_laws`
- **LAW-N:** `lambda_yN^2 == Y_comp/Y_r_comp mod N` — `verify_n_y_compression`
- **Family-X:** `L1*L2*L3 == Cq == IQ/Iq` — `verify_family_bridge`

---

## IMG_0004 — Summary facts

| Notebook fact | Code | Status |
|---------------|------|--------|
| p-side = starting shape | Phases 1–8 | ✅ |
| N-side = stretch to full curve | Phases 9–10, heaven carry | ✅ |
| Carries = integer glue | Phase 11, `p_side_compress_carry`, `slot_compress_carry` | ✅ |
| Defect d aligns x/y | Phase 14 `defect(d)`; mirror band; shelf `d ≈ shelf2 + offset mod LO` | ⚠️ |
| Final: find d making carries integer + cubic match | Phase 17 `d*G == P` only acceptance | ⚠️ EC verify, not carry-only |

---

## IMG_9988 — x-carry detail

| Notebook | Code |
|----------|------|
| \(b3_x = (\Lambda_N \cdot qx_3 - Qx_3)/N\) | `carry_quotient` in `compute_order_in_the_court` (decimal display); Phase 11 integer `carry` |
| Non-integer ⇒ congruence false | `carry()` returns `ok=False` with remainder |

---

## IMG_9989 — Defect d sensitivity

| Notebook | Code | Status |
|----------|------|--------|
| \(\Lambda_N(d) = \Lambda_N(0) + d\) | Phase 14 shrinkage interval; not full Λ_N(d) sweep | ⚠️ |
| \(b3_x(d) = b3_x(0) + d\cdot qx_3/N\) | Phase 14: `b_x(LO) ~ b_x(0) + LO*qx//N` | ⚠️ LO corner only |
| Flat until \(d\cdot qx_3\) crosses multiple of N | ❌ No step-scan automator |

---

## IMG_9990 — Cubic N-bridge

| Notebook | Code | Status |
|----------|------|--------|
| \(IQ = \prod Qx_i\), \(Iq = \prod qx_i\) | `verify_n_side_balance` (`iq`, `i_r`); Phase 13 | ✅ |
| \(IQ \equiv \Lambda_N^3 \cdot Iq \pmod N\) | Phase 13 — logged as **expected FAIL** (single-row) | ⚠️ |
| \(IQ \equiv \Lambda_{N,\text{family}} \cdot Iq\) | `family_prod_eq_cq` in `verify_family_bridge` | ✅ |
| \(B_{\text{cubic}} = (\Lambda_N^3 Iq - IQ) // N\) | Phase 13 `carry(B_num, N)` | ✅ (diagnostic) |

---

## IMG_9991 — Height-aware Λ_cubic

| Notebook | Code | Status |
|----------|------|--------|
| \(\Lambda_{\text{cubic}} = \sqrt[3]{IQ \cdot Iq^{-1}} \pmod N\) | `all_cube_roots_mod(N, family_prod)` → `lambda_n_family_cbrt` | ✅ |
| Verify \(\Lambda_{\text{cubic}} \equiv \Lambda_N\) | Compared to **family product**, not single row | ⚠️ |

---

## IMG_9992 — N-side vector summary

| Notebook | Code | Status |
|----------|------|--------|
| \(\vec{Qx} = \Lambda_N \vec{qx} - N\vec{b}\) | Per-row `carry` in `verify_family_bridge`; `compute_order_in_the_court` carry display | ✅ |
| GAP nonlinear if \(b3_x\) drifts with d | Batch: H−10 offset law **1/26** (P115 only) | 🔧 Empirical |

---

## IMG_9993 — Three y roots mod N

| Notebook | Code | Status |
|----------|------|--------|
| \(y_1 = R^{(2N+1)/9} \pmod N\) | `cube_root_mod_prime`, `all_cube_roots_mod` with \(\beta_N\) | ✅ |
| \(y_2 = y_1 \beta_N\), \(y_3 = y_1 \beta_N^2\) | `DELTA_CUBE_ROOTS_N` / primitive cube root of unity | ✅ |

---

## IMG_9994 — y-side bridge

| Notebook | Code | Status |
|----------|------|--------|
| \(\Lambda_{yN} = Qy \cdot qy^{-1} \pmod N\) | Phase 11 `lam_y_N`; `verify_n_y_compression.lambda_y_n` | ✅ |
| One branch aligns with x-bridge | `branch_grid` in `verify_n_y_compression`; parity branches | ✅ |

---

## IMG_9995 — y-carry

| Notebook | Code | Status |
|----------|------|--------|
| \(b3_{yN} = (\Lambda_{yN}\cdot qy - Qy)/N\) | Phase 11; `compute_order_in_the_court.by_display` | ✅ |

---

## IMG_9996 — Grand alignment

| Notebook | Code | Status |
|----------|------|--------|
| \(\Lambda_N^3 \equiv \Lambda_{yN}^2 \pmod N\) | Phase 12 **WRONG LAYER** flag | 🚫 |
| Correct curve lock | LAW-P + LAW-N + weighted corrected forms Phase 12 | ✅ |

---

## IMG_9997 — d on y-side

| Notebook | Code | Status |
|----------|------|--------|
| \(\Delta b3_{yN} \approx qy/N\) per unit d | ❌ Not implemented as sensitivity sweep | ❌ |
| Closed when \(b3_{yN}\) integer + x/y match | Phase 11 carry ok + LAW-N | ⚠️ |

---

## IMG_9998 — Extract k

| Notebook | Code | Status |
|----------|------|--------|
| \(k \equiv \Lambda_N \pmod N\) | Compared in `compare_bridge_to_scalar_frame` — **not assumed** | 🚫 |
| Solve = find d with integer carries + cubic | Phase 17: **`d*G == P`** in band | ✅ (stricter) |
| \(k\) sometimes \(\Lambda_N^2\) | Not implemented as extraction rule | ❌ |

---

## genesis_calibration.py role

| Function | Maps to |
|----------|---------|
| `bridge_state(cfg)` | Orchestrates OITC + shelf + GAP + alignment frame |
| `compute_order_in_the_court` | Shelf2/3/y, carry decimals, cube residues |
| `build_bridge_offset_terms` | Offset vocabulary vs genesis coinbase bytes |
| `match_report` | Calibration hits (P115 offset 105 bits) |
| `genesis_coinbase_features` | External byte feed — **not in notebook photos** |

---

## Probe layer (not in photos, your session work)

| Script | Purpose |
|--------|---------|
| `k_xy_mod134_distance.py` | `bridge_k_pair` → `k_x = floor(NΛ/p)`, `k_y` tilt; `puzzle_k_transforms` |
| `k_xy_distance_table.py` | r1/r2 vs priv `d`; stable gap pattern |
| `k_xy_distance_percentiles.py` | Percentile distances across solved puzzles |
| `compare_family_mirror_batch.py` | GAP, shelf2, mirror defect batch |
| `ARCHIVE/PUZZLE_MOD_CONVENTION.md` | r1/r2 band transforms |

---

## What’s implemented vs still manual

### Fully automated (run pipeline)

- p-side Λ, cubic aggregates, y-side LAW-P  
- N-side scale, IQ/Iq, family bridge L1·L2·L3  
- Heaven carry rebirth (LAW-N)  
- Integer carry checks b_x, b_yN  
- GAP, defect(δ+d) corners, shelf/OITC matrix  
- d candidate battery + **`d*G == P`** verification  

### Partially automated

- **d search:** candidates generated, not iterated until carries+cubic close  
- **Λ_N(d) sensitivity:** corner/shrinkage math only  
- **Notebook cubic check:** logged as wrong-layer diagnostic  

### Manual / not in code

- Stepwise **d wiggle** until b3_x and b3_yN simultaneously integer (notebook closure loop)  
- **k := Λ_N** as final readout (code uses scalar frame m = d·k⁻¹ instead)  
- IMG_9989/9997 **Δb per unit d** sensitivity tables  

### Recommended win condition (code vs notebook)

| Source | Win condition |
|--------|----------------|
| **Notebook photos** | Integer carries + \(\Lambda_{yN}^2 \equiv \Lambda_N^3\) + \(k \equiv \Lambda_N\) |
| **ecdlp_full_pipeline.py** | LAW-P + LAW-N + family bridge + **`d·G = P`** and `d ∈ [2^{n-1}, 2^n)` |
| **Your k-distance work** | Stable **n − dist_bits** pattern on r1/r2 probes (not dist=0) |

---

## Run commands

```powershell
python C:\Users\mitch\Desktop\secp256k1\ECDLP\ecdlp_full_pipeline.py --defaults
python C:\Users\mitch\Desktop\secp256k1\genesis_calibration.py
python C:\Users\mitch\Desktop\secp256k1\compare_family_mirror_batch.py
python C:\Users\mitch\Desktop\secp256k1\k_xy_distance_table.py
```
