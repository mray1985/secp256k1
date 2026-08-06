# P71 2^29 combination scan (MITM)

Pool: indices **14..42** (29 slots) → **2^29 = 536870912** subsets
Remainder bucket: **< 2^29 = 536870912**

- Half-sum build: 0.18s
- Bare sums in `[2^70,2^71)`: sampled **200** (capped)
- Subset sums where `T71_filed - sum < 2^29`: **0**
- Hash160 checked: **200**
- Hash160 hits: **0**

