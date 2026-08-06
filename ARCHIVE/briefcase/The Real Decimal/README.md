# The Real Decimal

Corrected fractional / packet silhouette for **everything** in the briefcase.

| Path | Contents |
|------|----------|
| `MANIFEST.json` | counts + lens rules |
| `index.md` | human index |
| `globals/constants.json` | p, N, G, β, Λ, … |
| `puzzles/puzzle_NNN.json` | per-puzzle packets + coordinates + RSZ + scalar |

```text
python build_the_real_decimal.py
python build_roof_stitch_catalog.py
python build_y_tail_carry_scan.py
python build_carry_threshold_ledger.py
python build_stitch_roof_comparison.py
python build_field_native_pair_packet.py
python build_pair_minus_wrap_scan.py
python build_residue_numerator_briefcase_scan.py
python build_residue_offset_class_scan.py
python build_p135_ledger.py
python build_p135_rsz_courtroom.py
python build_tdad_scalar_courtroom.py
python build_tdad_index_playlist_scan.py
python corrected_lens_candidate_gate.py
python corrected_lens_fractional_power_gate.py
```

| `corrected_lens_ecdlp_verdict.*` | raw corrected lens → ECDLP gates |
| `fractional_power_ecdlp_verdict.*` | fractional-power shells on corrected lens → ECDLP gates |
| `exhibit_fractional_roofs_mod_p_N.*` | mod p / mod N as p/2^256 and N/2^256 roofs |
| `exhibit_N_over_p_cross_courtroom.*` | N/p = scalar roof inside field courtroom |
| `exhibit_roof_stitch_catalog.*` | p.N / N.p roof-stitches (overflow vs under-roof) |
| `exhibit_y_tail_carry_scan.*` | y-tail carry: floor(x.y/p*N) vs floor(x/p*N) |
| `exhibit_carry_threshold_ledger.*` | exact threshold rem*10^d + N*y >= p*10^d + ledger wrap |
| `exhibit_stitch_roof_comparison.*` | decimal vs x.(y/p) vs x.(y/N) — roof gauge wins |
| `exhibit_field_native_pair_packet.*` | 0.x_y in base p; P_pair vs curve wrap m/p^2 |
| `exhibit_pair_minus_wrap_scan.*` | residue = (x*p+y-m)/p² vs β-slots, RSZ, roofs |
| `exhibit_residue_numerator_briefcase_scan.*` | num mod p/N/DELTA across all briefcase ways |
| `exhibit_residue_offset_class_scan.*` | (num−d) mod 2^k banded offsets — lane closed |
| `P135/` | P135 local courtroom ledger + RSZ courtroom |
| `P135/tdad_scalar_courtroom.*` | P135 TDAD missing — scalar recipe not filed |
| `exhibit_tdad_index_playlist_scan.*` | TDAD index playlist constraints — rhythm vs path |
