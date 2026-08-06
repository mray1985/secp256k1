# Puzzle 135 — Master State (durable archive)

Last consolidated: 2026-06-17 UTC. Regenerated constants: run `python ARCHIVE/snapshot_p135.py`.

## Per-puzzle k mod convention (saved)

See **`ARCHIVE/PUZZLE_MOD_CONVENTION.md`**. **N** = puzzle number.

```
d ∈ [2^(N−1), 2^N)
r1 = (k mod 2^(N−1)) + 2^(N−1)     # always in band
r2 = k mod (2^N − 1)               # lifted into band if below LO
```

**Not** `(k mod 2^N) + 2^N` — that leaves the puzzle band.

Scripts: `k_xy_distance_table.py`, `k_xy_mod134_distance.py` → `ARCHIVE/k_xy_distance_table_5_135.csv`.

## Target

- **Puzzle 135** private scalar `d` with `d·G = P` and `d ∈ [2^134, 2^135)`.
- **Pubkey (row 3):** `Px = 9210836494447108270027136741376870869791784014198948301625976867708124077590`, `Py = 46351506704828816385393879789131775975171267756561783641521771795450741674800`.
- **Only acceptance test:** EC point match + band membership. No pubkey hit from phase/k-lane scans yet.

## Curve constants

| Symbol | Value |
|--------|-------|
| **N** | `115792089237316195423570985008687907852837564279074904382605163141518161494337` |
| **p** | `115792089237316195423570985008687907853269984665640564039457584007908834671663` |
| **δ = p−N** | `432420386565659656852420866390673177326` |
| **LO = 2^134** | `21778071482940061661655974875633165533184` |
| **HI = 2^135** | `43556142965880123323311949751266331066368` |
| **TOP** | `43556142965880123323311949751266331066367` |

## Barcode / RSZ lane (frozen)

| Symbol | Value |
|--------|-------|
| **s** | `15509729875763924304053419655647994379903175655107184284998698212653288468986` |
| **z** | `66278737796829840734606014530466656889790152192829793669891337810330530090951` |
| **r (tx, rx2)** | `90653255469745952335985143920649543885181555095025199315947044135806663628368` |
| **k_Px** (pipeline, NOT tx nonce) | `19089036453356401353257357002647987614981495902151757130742235757133693952525` |
| **k_Py** | `90508964219557991953548570402867934097841441951106365697884749206559245429888` |

Pipeline: `k_Px = s⁻¹(z + r·Px) mod N` (ecdsacrack / 717.txt) — bridges pubkey x into scalar slot, **not** `d`.

## P-side Λ framework (mod p) — verified

- **Latin rotation:** `n1,n2,n3` cube roots of N mod p; `Gx_i·n_j⁻¹` → `G_A/B/C` (same for Px, rx).
- **Row constants:** `CP1 = Px_i/Gx_i`, `CR1 = rx_i/Gx_i` (identical all i).
- **Bridge:** `Λ = CP1·CR1⁻¹` ⇒ **`Px_i ≡ Λ·rx_i (mod p)`** all three rows.
- **Cubic:** `IP·IR⁻¹ ≡ Λ³ (mod p)` where `IP = ∏Px_i`, `IR = ∏rx_i`.
- **120° phase:** `β³ ≡ 1 mod p`; after Λ acts, `ε_i = Px/(Λ·rx_i) ∈ {β², β, 1}`.
- **P135 lands rx3 row** → unity phase `ε = 1` (`Px ≡ Λ·rx3 mod p`).
- **Λ (row 3):** `97451685862885086182458552040892158509924235661624603229050850812487253689501`
- **λ_y ≠ Λ_x:** `λ_y = Py/ry mod p` (y-bridge separate from x-bridge).

## N-side (mod N) — verified structure

- **Per-row:** `Qx_i ≡ Λ_i·qx_i (mod N)` — **three distinct** `Λ_i`, not one global `Λ_N` on all rows.
- **Family bridge:** `Λ_N_family = Λ_1·Λ_2·Λ_3 ≡ Cq = IQ/Iq (mod N)` — **not** `Λ_N³`.
- **GAP:** `GAP ≡ Λ_N_row3 − Λ_p (mod N)` (heaven carry between mod p and mod N).
- **Defect mirror window:** `defect(d) = δ + d (mod N)`; band floor/ceiling defects span width `2^134 − 1`.

## Shelf / carry anchors (live — see `constants_live.json`)

| Symbol | Role |
|--------|------|
| **shelf2** | `LO + (d2 mod LO)` from order-in-the-court; P115 calibration anchor |
| **shelf3, shelf_y** | parallel cube lanes |
| **C_floor** | `floor((shelf2+shelf3+shelf_y)/3)` |
| **GAP mod LO** | stable across band boundaries in report |

**P115 pattern (solved):** `d ≈ shelf2 + offset` with offset ~105 bits (`H − 10` for H=115). P135 alignment scans: **no single offset** from shelf2+{GAP, cube lifts, matrix diffs} matched `d` yet.

## ECDSA vs bridge — do not conflate

```
Real ECDSA:  k_tx = s⁻¹(z + r·d),   d = (s·k_tx − z)·r⁻¹ mod N,   r = x(k_tx·G) mod N
Bridge:      k_Px = s⁻¹(z + r·Px)   — recovers Px into scalar slot, NOT d
EC bridge:   P = (d·k⁻¹)·R = m·R,    m = d·k⁻¹ mod N
```

**NOT true for pipeline k:** `x(k_Px·G) mod N ≠ r_tx`; `r⁻¹·Px ≢ k⁻¹`.

## Mirror pair (always test both)

`d·G = (Px, Py)` ⟺ `(N−d)·G = (Px, −Py)`. Same x, flipped y.

## Search status (math scans)

- Phase band scan ±65k: **no hit**
- k-lane band scan: **no hit**
- Acceptance: `d·G == (Px, Py)` only

## Key files (tracked by snapshot)

- `p135_carry_remainder_report.py` / `.txt` — full pipeline report
- `02_Research/notes/Complexity_Simplified_p.txt` — Λ Latin square
- `00_Projects/patent/717.txt` — k_Px source
- `ECDLP/ecdlp_full_pipeline.py` — pipeline engine
- `p135_phase_band_scan.py`, `p135_k_lane_band_scan.py`

## Open math question

**Λ fixes row/phase (rx3, ε=1) but does not give d directly.** Need: defect-window N-side reconfiguration + shelf offset law that lifts from P115 pattern to H=135, or EC gate on `d·G = P` over wider stride than scanned.
