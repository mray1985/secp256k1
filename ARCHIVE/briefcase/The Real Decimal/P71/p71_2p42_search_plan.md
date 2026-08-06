# P71 scaled search — 2^42 straight version

## Count

```text
Pool: indices 1..42 (42 terms at weight 536870912 = 2^29)
Mask: each index in or out

2^42 = 4,398,046,511,104 combinations
     ≈ 4.4 trillion
```

Not `2^29` (that was the 14..42 sub-pool only).

## Phase 1 — integer subset sums (fast)

```text
T = Σ mask_i · 536870912(i)

MITM split: 21 + 21
  left:  2^21 = 2,097,152 partial sums
  right: 2^21 = 2,097,152 partial sums
  work:  ~4.2M partial sums + bisect merge
```

| Pool | Half split | Build time (Python) | In-band mask-pairs |
|------|------------|---------------------|-------------------:|
| 14..42 (29 slots) | 14 + 15 | ~0.13 s | ~190M |
| **1..42 (42 slots)** | **21 + 21** | **~18 s** | **~1.09×10^12** |

Integer sum filtering is **fast**. Full 1..42 MITM builds in seconds-to-minutes.

## Phase 2 — remainder dial

```text
T = S + r
r ∈ [0, 2^29)
only where 2^70 ≤ S + r ≤ 2^71 − 1
```

Worst case per mask: up to 2^29 remainder steps. Do **not** multiply EC checks by 2^29 blindly — only `r` that keep `T` in band.

## Phase 3 — EC / hash160 (slow)

```text
T → [T]G → compressed → hash160 → compare P71
```

If we EC-checked all 2^42 masks raw:

| Rate | Time for 4.4T checks |
|------|----------------------|
| 100k/s | ~509 days |
| 1M/s | ~51 days |
| 10M/s | ~5.1 days |
| 100M/s | ~12.2 hours |

**Do not hash-check all 2^42.**

## Best path

```text
1. MITM build subset sums (21+21)
2. Keep pairs where sum ∈ [2^70, 2^71)   [still huge for 1..42 — dedupe unique S first]
3. Apply remainder rule r < 2^29 only on survivors
4. EC/hash160 only final T candidates
```

## Vocabulary (allowed weights)

Only `536870912(1)` … `536870912(42)` — see `scaled_contributions.md`.

Solo in-band: **only index 42** alone. All other terms need subset + remainder.

## Ruling

```text
2^42 raw combinations:     too many to EC-check directly on CPU
2^42 subset sums (MITM):   manageable integer filter
In-band survivors (1..42): still ~10^12 mask-pairs — must dedupe + remainder narrow before EC

Judge Popcorn: 4.4 trillion is too many doors to kick.
               Sort sums into hallways first; knock only on doors in the right hallway.
```

## Courtroom

Scalar-side gate only: `[T]G` hash160 = P71. Not β / 7⁻¹ mod p. See `exhibit_field_scalar_courtroom_correction.md`.
