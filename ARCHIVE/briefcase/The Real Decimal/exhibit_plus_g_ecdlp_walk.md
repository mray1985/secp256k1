# P + kG → ECDLP walk — ruling (P135 / P160)

Script: `probe_plus_g_ecdlp_walk.py`  
Sweep: **k = 0 … 2048** per puzzle, full phase-17 candidate pool (~270–290 scalars/shift).

## Method (sound if pipeline solves)

```text
P_k     = P + k·G
Pipeline on P_k  →  find d_k with [d_k]G = P_k
Backtrack        →  d = (d_k − k) mod N
Certify          →  [d]G = P  and  d ∈ [2^(n−1), 2^n)
```

Algebra is correct: if `P = d·G` then `P_k = (d+k)·G`.

## Calibration — P5 (solved, tiny band)

| k | pipeline hit d_k | backtrack d_k − k | true d=21 |
|---|------------------|-------------------|-----------|
| 0 | 21 | 21 | ✓ |
| 1 | 22 | 21 | ✓ |
| 2 | 23 | 21 | ✓ |
| … | … | … | ✓ |

Walk **works** when bridge candidates actually contain the shifted scalar (small puzzles only).

## P135 — UNSOLVED

```text
Pubkey: 02145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16
Band:   [2^134, 2^135)
Shifts tested: 2049 (k = 0..2048)
Pipeline EC hits on P_k: 0
Backtrack candidates: none
```

## P160 — UNSOLVED

```text
Shifts tested: 2049 (k = 0..2048)
Pipeline EC hits on P_k: 0
```

## Why it fails at P135+

The ECDLP pipeline does **not** solve high puzzles — it emits ~270 bridge residues (Lambda, shelf2+offset, matrix tracks). On P115 (solved) with **no** `known_d` injection: **0 EC hits**. Hits on solved puzzles in `pipeline_scorecard.txt` require injecting ground-truth `d` into the candidate list.

Walking `P + kG` only re-anchors the pubkey; it does not enlarge the candidate set into the true scalar class at bit-height 134+.

## Ruling

```text
P + kG → ECDLP backtrack:  CLOSED for P135/P160 at k ≤ 2048
Reason: pipeline never certifies [d_k]G = P_k on shifted points
Next:   scaled TDAD / hash160 gate / BSGS on constrained mask space
```

## Structured offset walk (follow-up)

Script: `probe_plus_g_structured.py`

k drawn from shelf2/gap geometry (not brute sequential):

| Source | examples |
|--------|----------|
| bridge offset terms mod LO | gap, shrink, matrix deltas |
| alignment raw − shelf2 | ~200 lattice deltas |
| offset-bit boundaries | ob ∈ {132,133,134} for P135 |
| solved transfer | P110–P130 observed offsets |
| band D/8 spacing | ChatSieve lane width |
| small k | 1..64 |

| Puzzle | k tested | EC hits on P±kG | certified d |
|--------|----------|-----------------|-------------|
| P135 | 281 | 0 | none |
| P160 | 311 | 0 | none |

Also tested P − kG and alternate backtracks `(d±k) mod N`: still 0 raw pipeline hits.

**Structured shift lane: CLOSED** — same root cause as brute walk; pipeline does not solve at bit-height 134+.
