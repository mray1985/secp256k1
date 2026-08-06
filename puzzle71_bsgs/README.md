# Puzzle 71 — hash160 BSGS (address-only target)

Target: `1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU`  
hash160: `F6F5431D25BBF7B12E8ADD9AF5E3475C44A0A5B8`  
Band: `[2^70, 2^71 − 1]` — width `W = 2^70`

## Math

`0.001 × 2^70 ≈ 1.2 × 10^18` keys — still impossible to scroll linearly.

BSGS split: `M = 2^35 = ⌈√W⌉`, write `d = LO + j·M + r` with `0 ≤ r,j < M`.

| Phase | What | Disk (E:) |
|-------|------|-----------|
| **Baby** | `(hash160, r)` for `d = LO+r`, `r ∈ [0,M)` | ~858 GB h160 / ~144 GB x-only |
| **Giant** | For each `j`, Harvester-scroll `r`, check hash160 | checkpoints only |

**Important:** True **O(2^35) EC BSGS** uses **x-coordinate** collision and needs the **pubkey point Q**. hash160 alone cannot invert to Q (P71 never spent — no pubkey on chain). Giant phase here still evaluates hash160 at each candidate; baby table enables:

- sorted lookup / bloom prefilter experiments  
- **instant switch to EC BSGS** if pubkey appears later  
- parallel **j-shards** with shared baby metadata

Harvester engine: one `d₀·G`, then `P += G` per step (not full scalar mult).

## Storage layout (default E:, not C:)

```
E:\puzzle71_bsgs\
  baby\baby_h160.bin      # 25 bytes × M (build once)
  baby\baby_x.bin         # 12 bytes × M (optional, for EC-BSGS if pubkey known)
  giant\shard_XXXX.bin    # checkpoints
  logs\
```

C: is tight — **build baby table on E:** (`paths.py`). Full 2^35 baby is ~858 GB h160 (+ ~144 GB x-coords optional).

## Scripts

| Script | Purpose |
|--------|---------|
| `build_baby_h160.py` | Build baby hash160 table on E: |
| `run_giant_shard.py` | One j-shard giant pass (Harvester + hash160) |
| `run_all_shards.bat` | Queue shards (edit `SHARD_ID`) |
| `verify_hit.py` | Confirm candidate against address |

## Cleanup candidates (manual — not auto-deleted)

| Path | Size | Notes |
|------|------|-------|
| `Documents\p95v3019b20.win64` | ~370 GB | Looks like install cache |
| `Documents\vanity` | ~40 GB | Vanity search output? |
| `%TEMP%` | cleared | Already wiped this session |
