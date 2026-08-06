# P71 search — unique S then 2^29 remainder dial

## Two-stage filter (not 2^42 × EC)

```text
Stage A: masks → unique subset sums S
Stage B: per unique S → at most 2^29 remainder steps
Stage C: EC/hash160 only on T = S + r survivors
```

## Stage A — dedupe masks to unique S

```text
2^42 masks  →  MITM (21+21)  →  unique achievable S values

Keep S iff:
  S can reach P71 band with remainder < 2^29
  ⟺  S ∈ [2^70 − (2^29 − 1),  2^71 − 1]
  ⟺  S ∈ [LO − M + 1,  HI]
```

Many masks collapse to the same S. **Do not EC-check per mask.**

## Stage B — remainder dial per unique S

For each unique S kept:

```text
r_min = max(0, LO − S)
r_max = min(2^29 − 1, HI − S)

if r_min ≤ r_max:
    for r in [r_min .. r_max]:     # at most 2^29 steps
        T = S + r
        gate hash160([T]G)
```

| S location | Remainder steps |
|------------|----------------:|
| S already in `[LO, HI]` | `min(2^29−1, HI−S) + 1` ≤ **2^29** |
| S below LO (but ≥ LO−M+1) | lift band — still ≤ **2^29** |
| S above HI | drop |

**Per unique S: at most 2^29 remainder filters, not 2^42.**

## Total EC work

```text
EC checks ≤  (# unique S in reach window)  ×  2^29   [worst case per S]

NOT:
  2^42 × 2^29 = 2^71
  2^42 raw masks
```

## MITM stats (pool 1..42, Python)

| Metric | Value |
|--------|------:|
| Partial sums (21+21) | ~1.46M + ~2.10M |
| Reach-window mask-pairs | ~1.09×10^12 |
| Bare in-band mask-pairs | ~1.09×10^12 |

Mask-pairs ≫ unique S. Stage A dedupe is the critical compression step before the remainder dial.

## Pipeline

```text
1. MITM build all achievable S (or stream-merge into sorted unique set)
2. Dedupe → unique S
3. Filter S ∈ [LO − M + 1, HI]
4. For each unique S: r ∈ [max(0,LO−S), min(M−1,HI−S)]
5. EC/hash160 on T = S + r only
```

## Ruling

```text
2^42 masks collapse to unique S first.
Each unique S gets at most a 2^29 remainder dial.
EC only on T = S + r in [2^70, 2^71).

Judge Popcorn: dedupe the sums, dial the remainder, knock only on survivors.
```
