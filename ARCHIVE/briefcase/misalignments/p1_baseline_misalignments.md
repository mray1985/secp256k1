# P1 baseline misalignments

Puzzle 1 is `d = 1` → `P = G`. Every verified side-process on P1 is the **curve origin**.
Each other pubkey puzzle is measured the same way; `delta_from_P1` is the misalignment.

## P1 origin

- off_by_map_p_to_n = `0`
- packet_p = `0.47556152915955157247070934588462193610…`
- floor(packet·N) = `55066263022277343669578718895168534326044960953502664657548891769041582144310`
- map_p_to_n(Gx) = `55066263022277343669578718895168534326044960953502664657548891769041582144310`
- beta_slot_ok = `True`
- shell floor_ratio − correction = `0.0000000000000000000000000000000000000002774213006018339586669968875087664867421`

## Does P1's off-by tell us every other puzzle?

- P1 off_by = `0`
- same as P1: **47** / 88
- different: **41** / 88
- off_by value counts: `{'0': 47, '1': 41}`

**No.** `off_by` is only a 0/1 floor nudge from the decimal packet, not a scalar defect.

## Invariants (true for P1 and all pubkey puzzles)

- beta_slot_ok: 88/88
- shell ratio ≈ correction: 88/88

These are **curve laws**, not per-puzzle offsets from P1.

## Solved: is Δlog2(Px) from P1 equal to log2(d)?

- mean(Δlog2(Px) − log2(d)) = `-45.989453`
- stdev = `30.776561`
- range = `[-129.9927, -0.5516]`

Large spread ⇒ P1 does **not** give a fixed additive defect that yields d.

## Sample deltas (solved)

| P | d | off_by | Δoff_by vs P1 | Δlog2(Px) | log2(d) | Δlog2(Px)−log2(d) |
|---|---|--------|---------------|-----------|---------|-------------------|
| 1 | 1 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 2 | 3 | 0 | 0 | 1.0334 | 1.5850 | -0.5516 |
| 3 | 7 | 1 | 1 | -0.3926 | 2.8074 | -3.1999 |
| 4 | 8 | 0 | 0 | -1.3729 | 3.0000 | -4.3729 |
| 5 | 21 | 1 | 1 | -1.1951 | 4.3923 | -5.5875 |
| 6 | 49 | 0 | 0 | 0.9962 | 5.6147 | -4.6185 |
| 7 | 76 | 1 | 1 | 0.3042 | 6.2479 | -5.9438 |
| 8 | 224 | 0 | 0 | -3.8007 | 7.8074 | -11.6080 |
| 9 | 467 | 0 | 0 | -0.8536 | 8.8673 | -9.7208 |
| 10 | 514 | 0 | 0 | 0.4615 | 9.0056 | -8.5441 |
| 11 | 1155 | 0 | 0 | 0.1915 | 10.1737 | -9.9822 |
| 12 | 2683 | 0 | 0 | 0.1913 | 11.3896 | -11.1984 |
| 13 | 5216 | 0 | 0 | 0.4889 | 12.3487 | -11.8598 |
| 14 | 10544 | 1 | 1 | 0.5717 | 13.3641 | -12.7924 |
| 15 | 26867 | 1 | 1 | 1.0646 | 14.7135 | -13.6489 |
| 16 | 51510 | 0 | 0 | 0.3719 | 15.6526 | -15.2806 |
| 17 | 95823 | 1 | 1 | -0.9411 | 16.5481 | -17.4892 |
| 18 | 198669 | 0 | 0 | -3.2392 | 17.6000 | -20.8392 |
| 19 | 357535 | 1 | 1 | 0.1319 | 18.4477 | -18.3158 |
| 20 | 863317 | 1 | 1 | -1.0139 | 19.7195 | -20.7334 |

## Ruling

P1 is the origin (G). Invariants (beta, shell ratio, on_curve) hold for all. Variable misalignments (packet, floor_N, log2_Px) are point-specific fingerprints, not a single off-by that maps P1 -> every puzzle's d. Use P1 as null control: anything true for P1 and all puzzles is curve law; anything that varies is coordinate identity, not a universal range defect.

Judge Popcorn: **P1 is the origin star, not a universal offset key. What matches P1 everywhere is law; what differs is identity.**
