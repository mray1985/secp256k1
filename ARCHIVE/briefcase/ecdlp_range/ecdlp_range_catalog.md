# ECDLP range catalog — all puzzles

Primary branch: **p−y**. N-side shadows included. Solved puzzles fully close `[d]G = P`.

## Two windows (floor/height switch)

```text
d-window:     [2^(n-1), 2^n)
N-mirror:     [N-2^n+1, N-2^(n-1)]   labels: N-2^n .. N-2^(n-1)

d floor  2^(n-1)  ↔  N-mirror height  N-2^(n-1)
d height 2^n      ↔  N-mirror floor   N-2^n

N-d for solved d must sit in N-mirror.
map_p_to_n / floor(packet·N) classified in N-mirror (may or may not land).
```

## Summary

- pubkey puzzles: **88**/160
- solved: **82**
- ECDLP closed (`[d]G`): **82**/82
- beta ok: **88**/88
- shell ok (p−y): **88**/88
- d in d-window: **82**/82
- N−d in N-mirror: **82**/82
- map_p_to_n(Px) in N-mirror: **0**/88
- floor(packet·N) p−y in N-mirror: **0**/88

## Per-puzzle

| P | status | d in d-win | N−d in N-mir | [d]G | beta | shell | off_by | mapN in mir | floorN in mir |
|---|--------|------------|--------------|------|------|-------|--------|-------------|---------------|
| 1 | SOLVED | True | True | True | True | True | 0 | False | False |
| 2 | SOLVED | True | True | True | True | True | 0 | False | False |
| 3 | SOLVED | True | True | True | True | True | 1 | False | False |
| 4 | SOLVED | True | True | True | True | True | 0 | False | False |
| 5 | SOLVED | True | True | True | True | True | 1 | False | False |
| 6 | SOLVED | True | True | True | True | True | 0 | False | False |
| 7 | SOLVED | True | True | True | True | True | 1 | False | False |
| 8 | SOLVED | True | True | True | True | True | 0 | False | False |
| 9 | SOLVED | True | True | True | True | True | 0 | False | False |
| 10 | SOLVED | True | True | True | True | True | 0 | False | False |
| 11 | SOLVED | True | True | True | True | True | 0 | False | False |
| 12 | SOLVED | True | True | True | True | True | 0 | False | False |
| 13 | SOLVED | True | True | True | True | True | 0 | False | False |
| 14 | SOLVED | True | True | True | True | True | 1 | False | False |
| 15 | SOLVED | True | True | True | True | True | 1 | False | False |
| 16 | SOLVED | True | True | True | True | True | 0 | False | False |
| 17 | SOLVED | True | True | True | True | True | 1 | False | False |
| 18 | SOLVED | True | True | True | True | True | 0 | False | False |
| 19 | SOLVED | True | True | True | True | True | 1 | False | False |
| 20 | SOLVED | True | True | True | True | True | 1 | False | False |
| 21 | SOLVED | True | True | True | True | True | 1 | False | False |
| 22 | SOLVED | True | True | True | True | True | 0 | False | False |
| 23 | SOLVED | True | True | True | True | True | 0 | False | False |
| 24 | SOLVED | True | True | True | True | True | 1 | False | False |
| 25 | SOLVED | True | True | True | True | True | 1 | False | False |
| 26 | SOLVED | True | True | True | True | True | 0 | False | False |
| 27 | SOLVED | True | True | True | True | True | 0 | False | False |
| 28 | SOLVED | True | True | True | True | True | 0 | False | False |
| 29 | SOLVED | True | True | True | True | True | 1 | False | False |
| 30 | SOLVED | True | True | True | True | True | 0 | False | False |
| 31 | SOLVED | True | True | True | True | True | 0 | False | False |
| 32 | SOLVED | True | True | True | True | True | 1 | False | False |
| 33 | SOLVED | True | True | True | True | True | 0 | False | False |
| 34 | SOLVED | True | True | True | True | True | 0 | False | False |
| 35 | SOLVED | True | True | True | True | True | 1 | False | False |
| 36 | SOLVED | True | True | True | True | True | 1 | False | False |
| 37 | SOLVED | True | True | True | True | True | 0 | False | False |
| 38 | SOLVED | True | True | True | True | True | 1 | False | False |
| 39 | SOLVED | True | True | True | True | True | 0 | False | False |
| 40 | SOLVED | True | True | True | True | True | 1 | False | False |
| 41 | SOLVED | True | True | True | True | True | 1 | False | False |
| 42 | SOLVED | True | True | True | True | True | 0 | False | False |
| 43 | SOLVED | True | True | True | True | True | 1 | False | False |
| 44 | SOLVED | True | True | True | True | True | 1 | False | False |
| 45 | SOLVED | True | True | True | True | True | 1 | False | False |
| 46 | SOLVED | True | True | True | True | True | 1 | False | False |
| 47 | SOLVED | True | True | True | True | True | 0 | False | False |
| 48 | SOLVED | True | True | True | True | True | 1 | False | False |
| 49 | SOLVED | True | True | True | True | True | 1 | False | False |
| 50 | SOLVED | True | True | True | True | True | 0 | False | False |
| 51 | SOLVED | True | True | True | True | True | 1 | False | False |
| 52 | SOLVED | True | True | True | True | True | 1 | False | False |
| 53 | SOLVED | True | True | True | True | True | 1 | False | False |
| 54 | SOLVED | True | True | True | True | True | 0 | False | False |
| 55 | SOLVED | True | True | True | True | True | 0 | False | False |
| 56 | SOLVED | True | True | True | True | True | 0 | False | False |
| 57 | SOLVED | True | True | True | True | True | 1 | False | False |
| 58 | SOLVED | True | True | True | True | True | 1 | False | False |
| 59 | SOLVED | True | True | True | True | True | 0 | False | False |
| 60 | SOLVED | True | True | True | True | True | 0 | False | False |
| 61 | SOLVED | True | True | True | True | True | 1 | False | False |
| 62 | SOLVED | True | True | True | True | True | 1 | False | False |
| 63 | SOLVED | True | True | True | True | True | 1 | False | False |
| 64 | SOLVED | True | True | True | True | True | 1 | False | False |
| 65 | SOLVED | True | True | True | True | True | 0 | False | False |
| 66 | SOLVED | True | True | True | True | True | 1 | False | False |
| 67 | SOLVED | True | True | True | True | True | 1 | False | False |
| 68 | SOLVED | True | True | True | True | True | 1 | False | False |
| 69 | SOLVED | True | True | True | True | True | 0 | False | False |
| 70 | SOLVED | True | True | True | True | True | 0 | False | False |
| 71 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 72 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 73 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 74 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 75 | SOLVED | True | True | True | True | True | 0 | False | False |
| 76 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 77 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 78 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 79 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 80 | SOLVED | True | True | True | True | True | 0 | False | False |
| 81 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 82 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 83 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 84 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 85 | SOLVED | True | True | True | True | True | 1 | False | False |
| 86 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 87 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 88 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 89 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 90 | SOLVED | True | True | True | True | True | 0 | False | False |
| 91 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 92 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 93 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 94 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 95 | SOLVED | True | True | True | True | True | 0 | False | False |
| 96 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 97 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 98 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 99 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 100 | SOLVED | True | True | True | True | True | 0 | False | False |
| 101 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 102 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 103 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 104 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 105 | SOLVED | True | True | True | True | True | 0 | False | False |
| 106 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 107 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 108 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 109 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 110 | SOLVED | True | True | True | True | True | 0 | False | False |
| 111 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 112 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 113 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 114 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 115 | SOLVED | True | True | True | True | True | 0 | False | False |
| 116 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 117 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 118 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 119 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 120 | SOLVED | True | True | True | True | True | 0 | False | False |
| 121 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 122 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 123 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 124 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 125 | SOLVED | True | True | True | True | True | 1 | False | False |
| 126 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 127 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 128 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 129 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 130 | SOLVED | True | True | True | True | True | 1 | False | False |
| 131 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 132 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 133 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 134 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 135 | UNSOLVED_PUBKEY | None | None | False | True | True | 1 | False | False |
| 136 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 137 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 138 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 139 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 140 | UNSOLVED_PUBKEY | None | None | False | True | True | 0 | False | False |
| 141 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 142 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 143 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 144 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 145 | UNSOLVED_PUBKEY | None | None | False | True | True | 1 | False | False |
| 146 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 147 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 148 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 149 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 150 | UNSOLVED_PUBKEY | None | None | False | True | True | 0 | False | False |
| 151 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 152 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 153 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 154 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 155 | UNSOLVED_PUBKEY | None | None | False | True | True | 0 | False | False |
| 156 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 157 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 158 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 159 | NO_PUBKEY | — | — | — | — | — | — | — | — |
| 160 | UNSOLVED_PUBKEY | None | None | False | True | True | 0 | False | False |

## Stack applied per pubkey puzzle

```text
1. ECDLP statement in d-window [2^(n-1), 2^n)
2. N-mirror window [N-2^n+1, N-2^(n-1)]
3. Px, Py, p−y, on-curve
4. branch y + branch p−y packets
5. map_p_to_n / floor(packet·N) / off_by — classified in N-mirror
6. defect shell
7. beta slots
8. e_lo / e_hinge / e_hi warps
9. if solved: d in d-window, N−d in N-mirror, [d]G verify
```

Rebuild: `python build_ecdlp_range_catalog.py`

Judge Popcorn: **d docks in the low bit slip; N−d docks in the mirrored high slip. Floor and height trade places across the order.**
