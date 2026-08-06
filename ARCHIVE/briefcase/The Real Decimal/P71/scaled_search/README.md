# P71 scaled search — running

Pipeline: `search_p71_scaled_mitm.py`

```text
1. MITM cache: left 2^21-1 sums, right 2^20-1 sums (index 42 required)
2. Per left sum ls: unique S = ls + rs for rs in reach window
3. Per unique S: remainder r in [max(0,LO-S), min(2^29-1, HI-S)]
4. EC/hash160 gate: T = S + r
```

## Dry-run scale (shard 0/256, require idx42)

~480k unique S per left row × ~8192 rows/shard ≈ **~4×10^9 unique S per shard**

Each S: up to **2^29** remainder steps → shard EC work ≈ **2×10^18** ops (not feasible on one CPU).

## Strategy

Run **256 shards** (configurable). Each shard is still huge — treat as long-running / distributed.

```powershell
# one shard (foreground)
python search_p71_scaled_mitm.py --shard-id 0 --shard-count 256 --require-idx42

# all shards (background jobs)
.\run_p71_scaled_shards.ps1 -ShardCount 256 -Start 0 -End 3
```

Results: `P71/scaled_search/shard_XXXX_result.json`  
Hit: `PUZZLE71_SOLVED.txt`

Cache: `P71/scaled_search/cache/{left_sums,right_sums_idx42}.bin`
