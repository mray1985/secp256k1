# Double Add (briefcase)

Formal **AD reconstruction grammar** for puzzle scalar paths.

## Files

| File | Role |
|------|------|
| `Double Add Rules.txt` | Grammar: A/D alternation, n−3 anchor, band gate, HASH160 proof |
| `ad_operation_paths.{md,json}` | Parsed paths + validation (from script) |

## Canonical DA transcript (corrected)

**Use this**, not the raw prose lines for P1–P4:

`F:\New folder\secp256k1\DOUBLE_AND_ADD+BREAKDOWN.txt`

Raw `double_and_add.txt` on F: still has early wording errors:

- **P4** described as `7+1` — wrong narrative; value 8 is correct via **D(1)A(1)D(1)A(1)D(1)**
- **P3** prose `2(3)+1` is shorthand; AD form is **D(2)A(1)**

From **P4 forward** the global AD stream never breaks (rules §8).

## Script

```bash
python analyze_ad_operation_path.py
```

Validates alternation, cross-puzzle continuity, band, and crosses recovered **k** (ECDSA nonce) with path partials on solved spends.

## Notation

- `A(m)` = add `d(m)`
- `D(m)` = double `d(m)` → contributes `2·d(m)`
- **k** = ECDSA nonce only — never puzzle scalar `d`

## Work ceiling (do not pass P70 transcript / P71 gap)

| Puzzle | Status |
|--------|--------|
| P1–P70 | Solved transcript in `double_and_add.txt` / breakdown |
| **P71–P74** | **Unsolved** — empty lines; **never use `d(71)`…`d(74)`** as path terms |
| **P73** | **Highest reconstruction target** — anchor `d(70)` via n−3 rule |
| P75+ | Later solves (non-contiguous); P75 skips gap |

P135 remains empty — AD rules are generation grammar only, not closed transcript.
