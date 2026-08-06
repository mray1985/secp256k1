# briefcase/misalignments

| File | Purpose |
|------|---------|
| `range_error_bitmask.*` | range-only rulers (entropy ≈ 6.3) |
| `packet_range_error_bitmask.*` | direct frac·width (also ~6.3) |
| `signal_scalar_residual_scan.*` | residual / rank / neighbor |
| `hinge_power_signal_scan.*` | `(v/p)^((n-1+hinge)/256)` warp |
| `p1_baseline_misalignments.*` | P1 origin |
| `exhibit_projection_rejected_filter_valid.md` | **verdict: filter not predictor** |
| `exhibit_elo_shell_not_door.md` | e_lo wins shell, not door |
| `three_slice_hinge_power.*` | 3-slice + n-confound control |
| `elo_local_band_scan.*` | local-band / high-bit e_lo telescope |

```text
python build_three_slice_hinge_power.py
python build_elo_local_band_scan.py
python candidate_gate_stack.py --d <int>
python candidate_gate_stack.py --k <int>
```

`e_lo` = preferred lens. Not a scalar predictor. Gate stack for candidates only.
