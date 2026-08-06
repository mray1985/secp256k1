# briefcase/real — real-decimal & defect exhibits

New tree. Does **not** overwrite `exhibit_coordinate_packet_shadow.*` or puzzle ledgers.

| File | Purpose |
|------|---------|
| `decimal_dlp_ledger.md` / `.json` | Real-decimal DLP embedding (pubkey puzzles) |
| `exhibit_fourth_power_defect_shell.md` / `.json` | **Primary label:** `p−N = base_defect^4 × correction` |
| `exhibit_defect_exponent.md` / `.json` | Alias of the same identity (exponent form) |
| `probe_defect_shell_ledger_map.md` / `.json` | B/B4/Δ/C vs β/Λ/RSZ — three courtrooms |
| `probe_correction_multiplier.md` / `.json` | C-scaling of Λ/GAP + packet×correction |
| `exhibit_defect_shell_packet_confirmed.md` / `.json` | **Narrow label:** ruler confirmed, not Λ/GAP operator |

Rebuild:

```text
python build_real_decimal_dlp_ledger.py
python verify_defect_exponent.py
python probe_defect_shell_ledger_map.py
python probe_correction_multiplier.py
```

Ruling: ruler for field↔scalar courtroom gap — not the key.
