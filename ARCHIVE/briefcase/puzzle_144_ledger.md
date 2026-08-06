# Puzzle 144 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1NevxKDYuDcCh1ZMMi6ftmWwGrZKC6j7Ux

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 144 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 144
address = 1NevxKDYuDcCh1ZMMi6ftmWwGrZKC6j7Ux
key range [2^143, 2^144) = [11150372599265311570767859136324180752990208, 22300745198530623141535718272648361505980415)
range_min hex = 0x800000000000000000000000000000000000
range_max hex = 0xffffffffffffffffffffffffffffffffffff
btc_value = 14.4
hash160 = ed87120066e244ff5331d5f8625873d7a3acc39c
solved = False
private key d = 0 (unsolved)
solve_date = —
public_key leaked = False
```

### Phase 01_no_pubkey

#### pubkey not exposed on chain  [?]
**Formula:** no spend tx with public key — brute-force address only
**Note:** Puzzles without partial spend remain hash160-only targets.
```
Cannot build Px/Py or RSZ bridge until pubkey is revealed by a spend.
Target hash160 = ed87120066e244ff5331d5f8625873d7a3acc39c
```
