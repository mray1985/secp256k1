# Puzzle 94 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1K6xGMUbs6ZTXBnhw1pippqwK6wjBWtNpL

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 94 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 94
address = 1K6xGMUbs6ZTXBnhw1pippqwK6wjBWtNpL
key range [2^93, 2^94) = [9903520314283042199192993792, 19807040628566084398385987583)
range_min hex = 0x200000000000000000000000
range_max hex = 0x3fffffffffffffffffffffff
btc_value = 9.4
hash160 = c6927a00970d0165327d0a6db7950f05720c295c
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
Target hash160 = c6927a00970d0165327d0a6db7950f05720c295c
```
