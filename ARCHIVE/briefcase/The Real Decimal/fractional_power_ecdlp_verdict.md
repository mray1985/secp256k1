# Fractional-power shells on corrected lens — ECDLP verdict

Raw Real Decimal lens: already judged, no novel hits.
This run: **fractional-power oath** on the same corrected bases.

## Bases

```text
packet_p, packet_256, hex_stitch_512
beta slot packets Px_i.(p−y)/p and /2^256
r/N, s/N, z/N, r/2^256 when RSZ exists
```

## Exponents

- `e_hi=n/256`
- `e_lo=(n-1)/256`
- `e_hinge=(n-1+log2(3/2))/256`
- `e_roof_N=log2(N)/256`
- `e_q_low=log2(N-2^n)/256`
- `e_q_high=log2(N-2^(n-1))/256`
- `e_q=log2(N-d)/256 (solved)`
- `e_mirror_proxy=255/256`

## Gates

```text
[d]G == P
k = (z+r*d)*s^-1 mod N
x([k]G) == r
s*k == z+r*d mod N
mirror: q dock, d=N−q, [q]G == −P
```

## Summary

- coverage: **all 88 pubkey puzzles** (82 solved + 6 unsolved); 72 NO_PUBKEY skipped
- d candidates: **4204**
- q candidates: **6595**
- novel EC hits: **0**
- sanity true d (all solved): **True**

**FRACTIONAL-POWER SHELLS ON CORRECTED LENS: NO NOVEL HITS**

## Per puzzle

| P | status | d tested | q tested | ec hits d | ec hits mir | sanity |
|---|--------|----------|----------|-----------|-------------|--------|
| 1 | SOLVED | 1 | 1 | 1 | 1 | True |
| 2 | SOLVED | 2 | 2 | 1 | 1 | True |
| 3 | SOLVED | 4 | 4 | 1 | 1 | True |
| 4 | SOLVED | 8 | 8 | 1 | 1 | True |
| 5 | SOLVED | 4 | 15 | 0 | 1 | True |
| 6 | SOLVED | 13 | 26 | 1 | 1 | True |
| 7 | SOLVED | 13 | 40 | 0 | 1 | True |
| 8 | SOLVED | 29 | 51 | 0 | 1 | True |
| 9 | SOLVED | 26 | 59 | 0 | 0 | True |
| 10 | SOLVED | 42 | 68 | 0 | 0 | True |
| 11 | SOLVED | 52 | 76 | 0 | 0 | True |
| 12 | SOLVED | 51 | 76 | 0 | 0 | True |
| 13 | SOLVED | 51 | 78 | 0 | 0 | True |
| 14 | SOLVED | 54 | 79 | 0 | 0 | True |
| 15 | SOLVED | 53 | 77 | 0 | 0 | True |
| 16 | SOLVED | 58 | 80 | 0 | 0 | True |
| 17 | SOLVED | 54 | 80 | 0 | 0 | True |
| 18 | SOLVED | 53 | 81 | 0 | 0 | True |
| 19 | SOLVED | 52 | 80 | 0 | 0 | True |
| 20 | SOLVED | 50 | 80 | 0 | 0 | True |
| 21 | SOLVED | 52 | 80 | 0 | 0 | True |
| 22 | SOLVED | 52 | 81 | 0 | 0 | True |
| 23 | SOLVED | 54 | 80 | 0 | 0 | True |
| 24 | SOLVED | 50 | 80 | 0 | 0 | True |
| 25 | SOLVED | 52 | 81 | 0 | 0 | True |
| 26 | SOLVED | 52 | 81 | 0 | 0 | True |
| 27 | SOLVED | 52 | 82 | 0 | 0 | True |
| 28 | SOLVED | 56 | 81 | 0 | 0 | True |
| 29 | SOLVED | 50 | 82 | 0 | 0 | True |
| 30 | SOLVED | 52 | 80 | 0 | 0 | True |
| 31 | SOLVED | 52 | 80 | 0 | 0 | True |
| 32 | SOLVED | 54 | 83 | 0 | 0 | True |
| 33 | SOLVED | 56 | 81 | 0 | 0 | True |
| 34 | SOLVED | 48 | 80 | 0 | 0 | True |
| 35 | SOLVED | 56 | 80 | 0 | 0 | True |
| 36 | SOLVED | 56 | 80 | 0 | 0 | True |
| 37 | SOLVED | 50 | 80 | 0 | 0 | True |
| 38 | SOLVED | 56 | 80 | 0 | 0 | True |
| 39 | SOLVED | 50 | 80 | 0 | 0 | True |
| 40 | SOLVED | 58 | 80 | 0 | 0 | True |
| 41 | SOLVED | 54 | 81 | 0 | 0 | True |
| 42 | SOLVED | 54 | 80 | 0 | 0 | True |
| 43 | SOLVED | 52 | 80 | 0 | 0 | True |
| 44 | SOLVED | 52 | 80 | 0 | 0 | True |
| 45 | SOLVED | 52 | 80 | 0 | 0 | True |
| 46 | SOLVED | 54 | 80 | 0 | 0 | True |
| 47 | SOLVED | 50 | 80 | 0 | 0 | True |
| 48 | SOLVED | 58 | 81 | 0 | 0 | True |
| 49 | SOLVED | 52 | 81 | 0 | 0 | True |
| 50 | SOLVED | 52 | 84 | 0 | 0 | True |
| 51 | SOLVED | 58 | 80 | 0 | 0 | True |
| 52 | SOLVED | 50 | 80 | 0 | 0 | True |
| 53 | SOLVED | 50 | 80 | 0 | 0 | True |
| 54 | SOLVED | 48 | 80 | 0 | 0 | True |
| 55 | SOLVED | 56 | 83 | 0 | 0 | True |
| 56 | SOLVED | 48 | 80 | 0 | 0 | True |
| 57 | SOLVED | 54 | 81 | 0 | 0 | True |
| 58 | SOLVED | 52 | 80 | 0 | 0 | True |
| 59 | SOLVED | 50 | 84 | 0 | 0 | True |
| 60 | SOLVED | 52 | 80 | 0 | 0 | True |
| 61 | SOLVED | 49 | 80 | 0 | 0 | True |
| 62 | SOLVED | 52 | 80 | 0 | 0 | True |
| 63 | SOLVED | 52 | 80 | 0 | 0 | True |
| 64 | SOLVED | 50 | 80 | 0 | 0 | True |
| 65 | SOLVED | 47 | 85 | 0 | 0 | True |
| 66 | SOLVED | 48 | 80 | 0 | 0 | True |
| 67 | SOLVED | 47 | 85 | 0 | 0 | True |
| 68 | SOLVED | 50 | 84 | 0 | 0 | True |
| 69 | SOLVED | 45 | 80 | 0 | 0 | True |
| 70 | SOLVED | 52 | 80 | 0 | 0 | True |
| 75 | SOLVED | 50 | 80 | 0 | 0 | True |
| 80 | SOLVED | 54 | 80 | 0 | 0 | True |
| 85 | SOLVED | 47 | 82 | 0 | 0 | True |
| 90 | SOLVED | 47 | 80 | 0 | 0 | True |
| 95 | SOLVED | 54 | 80 | 0 | 0 | True |
| 100 | SOLVED | 51 | 80 | 0 | 0 | True |
| 105 | SOLVED | 51 | 82 | 0 | 0 | True |
| 110 | SOLVED | 41 | 81 | 0 | 0 | True |
| 115 | SOLVED | 48 | 80 | 0 | 0 | True |
| 120 | SOLVED | 43 | 80 | 0 | 0 | True |
| 125 | SOLVED | 41 | 80 | 0 | 0 | True |
| 130 | SOLVED | 63 | 85 | 0 | 0 | True |
| 135 | UNSOLVED_PUBKEY | 56 | 85 | 0 | 0 | — |
| 140 | UNSOLVED_PUBKEY | 55 | 90 | 0 | 0 | — |
| 145 | UNSOLVED_PUBKEY | 58 | 86 | 0 | 0 | — |
| 150 | UNSOLVED_PUBKEY | 58 | 89 | 0 | 0 | — |
| 155 | UNSOLVED_PUBKEY | 63 | 87 | 0 | 0 | — |
| 160 | UNSOLVED_PUBKEY | 56 | 86 | 0 | 0 | — |

## Ruling

```text
Raw corrected lens:              judged, no novel hits
Fractional-power corrected lens: judged, no novel hits
```

Judge Popcorn: **the witness testified plain and under the fractional-power oath. No conviction either time.**
