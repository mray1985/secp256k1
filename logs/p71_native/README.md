# P71 native backend bridge

Bridge for **P71-S03** native/GPU scanner equivalence.

Supports:

| Backend | Binary | Notes |
|---------|--------|-------|
| NVIDIA CUDA | `cuBitCrack` | Preferred GPU path |
| AMD/Intel OpenCL | `clBitCrack` | **Experimental** per BitCrack docs |
| CPU (WSL) | `keyhunt` | `-m address -l compress` |

Locked verification (independent of the scanner):

```text
d → [d]G → compressed SEC → SHA256 → RIPEMD160
```

Compare 20-byte HASH160. Reconstruct Base58 **only after** a verified hit.
Reject out-of-range or HASH160-mismatch reports.

## Install tools

- BitCrack: https://github.com/brichard19/BitCrack  
- KeyHunt: https://github.com/albertobsd/keyhunt  

Place binaries somewhere stable (e.g. `C:\tools\BitCrack\bin\`, `./keyhunt/keyhunt` under WSL).

## NVIDIA / OpenCL examples

```powershell
# OpenCL (Intel HD 530 on this host) — EXPERIMENTAL upstream
python p71_s03_native_gpu_equivalence.py `
  --backend native `
  --native-backend bitcrack `
  --native-binary C:\tools\BitCrack\bin\clBitCrack.exe `
  --calib-puzzle 1

python p71_native_backend.py `
  --backend bitcrack `
  --binary C:\tools\BitCrack\bin\clBitCrack.exe `
  --target 1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU `
  --start 400000000000000000 `
  --end 7fffffffffffffffff `
  --seconds 180 `
  --output logs\p71_s03\ocl_sustained\benchmark_180s.json
```

CUDA `cuBitCrack` requires an NVIDIA GPU (not present here).

## WSL CPU example

```bash
python3 p71_native_backend.py \
  --backend keyhunt \
  --binary ./keyhunt/keyhunt \
  --target 1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU \
  --start 400000000000000000 \
  --end 7fffffffffffffffff \
  --threads 4 \
  --seconds 600 \
  --output logs/p71_native/keyhunt_benchmark.json
```

## P71-S03 calibration (required first)

Use a **small solved range** and `--expect-private`:

```powershell
# Example: puzzle 1  (d=1) — tiny window; allow outside P71 band
# This host: clBitCrack (OpenCL / Intel HD 530). Use cuBitCrack only with NVIDIA.
python p71_native_backend.py `
  --backend bitcrack `
  --binary C:\tools\BitCrack\bin\clBitCrack.exe `
  --target 1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH `
  --start 1 `
  --end 20 `
  --expect-private 1 `
  --allow-outside-p71-band `
  --found-file logs\p71_native\calib_found.txt `
  --output logs\p71_native\s03_calib_puzzle1.json
```

Or via the S03 harness:

```powershell
python p71_s03_native_gpu_equivalence.py `
  --backend native `
  --native-backend bitcrack `
  --native-binary C:\tools\BitCrack\bin\clBitCrack.exe `
  --calib-puzzle 1
```

**Pass condition:** native reports the expected private key **and** the bridge independently verifies compressed HASH160.

## Inclusive Puzzle 71 band

```text
2^70 ≤ d ≤ 2^71 − 1
hex: 400000000000000000 … 7fffffffffffffffff
```

Full-band runs omit `--allow-outside-p71-band`. Calibration windows require it.

## Outputs

JSON includes: exact command, `R_peak`, `R_sustained`, rate samples, reported keys,
verified hits, rejected hits, `--expect-private` match flag.

Pool dashboard rates are **not** written as local \(R\).
