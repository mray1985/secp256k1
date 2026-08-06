# Puzzle 127 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1G6EFyBRU86sThN3SSt3GrHu1sA7w7nzi4

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 127 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 127
address = 1G6EFyBRU86sThN3SSt3GrHu1sA7w7nzi4
key range [2^126, 2^127) = [85070591730234615865843651857942052864, 170141183460469231731687303715884105727)
range_min hex = 0x40000000000000000000000000000000
range_max hex = 0x7fffffffffffffffffffffffffffffff
btc_value = 12.7
hash160 = a58708aa98ad35c889bb36d8049bf9e9cacfd02a
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
Target hash160 = a58708aa98ad35c889bb36d8049bf9e9cacfd02a
```
