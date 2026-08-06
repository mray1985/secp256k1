# LEDGER P71-S03 — Native/GPU scanner equivalence

**Status:** **PASS** (KeyHunt CPU) + **OpenCL iGPU EVALUATED** (clBitCrack / Intel HD 530). CUDA still absent.

> **Scanner ready on CPU and OpenCL iGPU; search not economically ready. CUDA not available on this host.**

## Devices

| Backend | Binary | Device | Status |
|---------|--------|--------|--------|
| KeyHunt CPU | `./keyhunt` (WSL) | host CPU | **PASS** — \(R_{\mathrm{sust}}\approx1.33\times10^{7}\)/s |
| OpenCL BitCrack | `C:\tools\BitCrack\bin\clBitCrack.exe` v0.31 | Intel HD Graphics 530 | **PASS** Puzzle-1; sustained measured |
| CUDA BitCrack | `cuBitCrack.exe` | — | **N/A** (no NVIDIA) |

Upstream: clBitCrack is **EXPERIMENTAL**; Intel mul bug workaround is in ≥0.29 (we use 0.31). Correctness gated by independent HASH160 verify.

## Puzzle-1 calibration (clBitCrack) — PASS

\[
d=1,\qquad S=[1,32]
\]

All gate fields **true** after filtering BitCrack keyspace-banner false parses.

## OpenCL sustained (180 s, production band)

| Metric | Value |
|--------|------:|
| \(R_{\mathrm{peak}}\) | \(4.73\times10^{6}\) keys/s |
| \(R_{\mathrm{sustained}}\) | \(4.59\times10^{6}\) keys/s |
| keys reported | ≈ \(6.30\times10^{8}\) |
| rejected / unverified hits | 0 |

**Note:** iGPU OpenCL is **slower** than measured KeyHunt CPU on this host. Feasibility / launch math continues to use the **CPU sustained** rate unless a faster discrete GPU appears.

### Full-band @ OpenCL \(R=4.59\times10^{6}\)/s (illustrative only)

| Quantity | Value |
|----------|------:|
| \(T_{\mathrm{mean}}\) | ≈ \(4.07\times10^{6}\) years |
| 1-year mean \(b_{\mathrm{cut}}\) | ≈ 21.95 bits |

## Stack

| ID | Status |
|----|--------|
| P71-S01 | PASS |
| P71-S02 | UPDATED — use CPU \(R=1.33\times10^{7}\) for feasibility |
| P71-S03 | **PASS** CPU + **OpenCL iGPU measured** |
| CUDA lane | NOT AVAILABLE |
| Launch | **NO** |

\[
\boxed{\text{Scanner ready; search not economically ready.}}
\]

## Artifacts

- `C:\tools\BitCrack\bin\clBitCrack.exe` + `*.cl`
- `logs/p71_s03/native_calib/s03_calib_n1.json`
- `logs/p71_s03/ocl_sustained/benchmark_180s.json`
- CPU promotion: `logs/p71_s03/promotion/`
