# LEDGER P71-S01 — Address-scanner calibration

**Status:** **PASS** (Python reference path) — GPU agreement pending. Not a P71 solve.

> Exact path \(d\to\) compressed SEC \(\to\) SHA256 \(\to\) RIPEMD160. **No Kangaroo.**

## Target identity

| Field | Value |
|-------|-------|
| Address | `1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU` |
| hash160 | `F6F5431D25BBF7B12E8ADD9AF5E3475C44A0A5B8` |
| Band | \([2^{70},2^{71})\), \(W=2^{70}\) |
| Pubkey | **not exposed** |

## Calibration results (2026-07-10)

| Check | Result |
|-------|--------|
| Oracle (8 trials, width \(2^{12}\)) | **8/8 PASS** |
| Solved addresses (1,5,10,20,30,40,50,65,70) | **9/9 PASS** |
| Checkpoint resume | **PASS** |
| Partition coverage | **PASS** |
| Python CPU rate | ≈ **9.3×10³** keys/s |
| CPU/GPU identical | pending (no GPU scanner wired) |

Full \(2^{70}\) band **not** scanned. Pattern/shelf2 hunters (e.g. legacy `p71_hash160_hunt.py`) are **out of scope** under the admission freeze.

## Artifacts

- Harness: `p71_s01_scanner_calibration.py`
- Results: `logs/p71_s01/P71_S01_calibration_results.json`
- Prereg: `logs/prereg/P71-S-20260710-01_scanner_calibration.md`
