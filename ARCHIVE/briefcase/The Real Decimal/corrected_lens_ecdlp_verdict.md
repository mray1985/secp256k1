# Corrected-lens ECDLP verdict

Sworn witnesses from **The Real Decimal** (stitched `Px.(p−y)`, `/p`, `/2^256`).

## Gates

```text
d-path:  range → [d]G==P → k=(z+r*d)*s^-1 → x([k]G)==r → s*k==z+r*d
mirror:  q in N-mirror → d=N-q → [d]G==P → [q]G==-P → RSZ
```

## Summary

- puzzles run: **11**
- d candidates tested: **220**
- q (mirror) candidates tested: **77**
- novel EC hits: **0**
- sanity (true d passes on solved): **True**

**CORRECTED LENS RUN THROUGH ECDLP GATES: NO NOVEL HITS**

## Per puzzle

| P | status | d tested | q tested | ec hits (d) | ec hits (mirror) | sanity |
|---|--------|----------|----------|-------------|------------------|--------|
| 135 | UNSOLVED_PUBKEY | 24 | 9 | 0 | 0 | — |
| 140 | UNSOLVED_PUBKEY | 21 | 7 | 0 | 0 | — |
| 145 | UNSOLVED_PUBKEY | 24 | 9 | 0 | 0 | — |
| 150 | UNSOLVED_PUBKEY | 21 | 7 | 0 | 0 | — |
| 155 | UNSOLVED_PUBKEY | 21 | 7 | 0 | 0 | — |
| 160 | UNSOLVED_PUBKEY | 21 | 7 | 0 | 0 | — |
| 1 | SOLVED | 1 | 1 | 1 | 1 | True |
| 65 | SOLVED | 21 | 7 | 0 | 0 | True |
| 75 | SOLVED | 21 | 7 | 0 | 0 | True |
| 100 | SOLVED | 21 | 7 | 0 | 0 | True |
| 130 | SOLVED | 24 | 9 | 0 | 0 | True |

## Ruling

Old lens: already judged, no hits.
Corrected lens: now judged through ECDLP candidate-close gates.
Result: **no novel hits**.

Judge Popcorn: **corrected witnesses sworn in and cross-examined. No conviction.**
