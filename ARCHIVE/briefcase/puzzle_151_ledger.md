# Puzzle 151 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 13Q84TNNvgcL3HJiqQPvyBb9m4hxjS3jkV

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 151 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 151
address = 13Q84TNNvgcL3HJiqQPvyBb9m4hxjS3jkV
key range [2^150, 2^151) = [1427247692705959881058285969449495136382746624, 2854495385411919762116571938898990272765493247)
range_min hex = 0x40000000000000000000000000000000000000
range_max hex = 0x7fffffffffffffffffffffffffffffffffffff
btc_value = 15.1
hash160 = 1a4fb632f0de0c53a0a31d57f840a19e56c645ee
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
Target hash160 = 1a4fb632f0de0c53a0a31d57f840a19e56c645ee
```
