# P71 scaled contributions (2^29 lane)

```text
mult = 536870912 = 2^29
term(i) = 536870912(i) = 2^29 · d_i

P71 band: [2^70, 2^71) = [1180591620717411303424, 2361183241434822606847]
```

All values below verified against catalog. **Every user value matches.**

## Allowed crossing vocabulary (indices 1..42)

| index | 536870912(i) | bits | solo in P71 band? |
|------:|-------------:|-----:|:-----------------:|
| 42 | 1554442376562402656256 | 71 | **yes** |
| 41 | 782893191303280984064 | 70 | no |
| 40 | 538831249400555110400 | 69 | no |
| 39 | 173798519310378860544 | 68 | no |
| 38 | 78904742888188411904 | 67 | no |
| 37 | 53822146766060912640 | 66 | no |
| 36 | 22756760726808821760 | 65 | no |
| 35 | 10798015821910114304 | 64 | no |
| 34 | 7587635338290397184 | 63 | no |
| 33 | 3831882801158815744 | 62 | no |
| 32 | 1660795570899386368 | 61 | no |
| 31 | 1128711258753728512 | 60 | no |
| 30 | 554674670280900608 | 59 | no |
| 29 | 215128949368291328 | 58 | no |
| 28 | 122210292225540096 | 57 | no |
| 27 | 60102666923016192 | 56 | no |
| 26 | 29280328581382144 | 55 | no |
| 25 | 17816334482014208 | 54 | no |
| 24 | 7746336443072512 | 53 | no |
| 23 | 3005833935847424 | 52 | no |
| 22 | 1614640878452736 | 51 | no |
| 21 | 972683391008768 | 50 | no |
| 20 | 463489785135104 | 49 | no |
| 19 | 191950141521920 | 48 | no |
| 18 | 106659607216128 | 47 | no |
| 17 | 51444581400576 | 46 | no |
| 16 | 27654220677120 | 45 | no |
| 15 | 14424110792704 | 44 | no |
| 14 | 5660766896128 | 43 | no |
| 13 | 2800318676992 | 42 | no |
| 12 | 1440424656896 | 41 | no |
| 11 | 620085903360 | 40 | no |
| 10 | 275951648768 | 39 | no |
| 9 | 250718715904 | 38 | no |
| 8 | 120259084288 | 37 | no |
| 7 | 40802189312 | 36 | no |
| 6 | 26306674688 | 35 | no |
| 5 | 11274289152 | 34 | no |
| 4 | 4294967296 | 33 | no |
| 3 | 3758096384 | 32 | no |
| 2 | 1610612736 | 31 | no |
| 1 | 536870912 | 30 | no |

## Crossing rule

```text
Only 536870912(42) alone sits inside [2^70, 2^71).

All other terms are below the floor — they cross into P71 range
only as part of a subset sum (+ remainder < 2^29):

  T = Σ selected 536870912(i)  +  r
  i ∈ {1..42}, mask_i ∈ {0,1}
  r < 2^29
  T ∈ [2^70, 2^71)
```

**First-slot max:** index 42 (only term that can anchor the band alone).

**536870912(41)** is the largest term still **below** `2^70` — cannot open P71 alone.

## Search space (corrected: full pool 1..42)

```text
Pool: indices 1..42  (42 allowed weights 536870912(i))
Mask: 2^42 = 4,398,046,511,104  (~4.4 trillion)

MITM: 21 + 21  →  ~4.2M partial sums  (integer filter: fast)
EC gate: only on survivors after band + remainder filter  (slow)

See p71_2p42_search_plan.md for full timing table.
```

Earlier **2^29** count was the **14..42 sub-pool only** (29 slots). Full vocabulary is **1..42 → 2^42**.
