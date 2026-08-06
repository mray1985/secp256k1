# Puzzle 121 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1GDSuiThEV64c166LUFC9uDcVdGjqkxKyh

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 121 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 121
address = 1GDSuiThEV64c166LUFC9uDcVdGjqkxKyh
key range [2^120, 2^121) = [1329227995784915872903807060280344576, 2658455991569831745807614120560689151)
range_min hex = 0x1000000000000000000000000000000
range_max hex = 0x1ffffffffffffffffffffffffffffff
btc_value = 12.1
hash160 = a6e4818537e42f7b3f021daa810367dad4dda16f
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
Target hash160 = a6e4818537e42f7b3f021daa810367dad4dda16f
```
