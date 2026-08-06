# Puzzle 128 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1MZ2L1gFrCtkkn6DnTT2e4PFUTHw9gNwaj

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 128 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 128
address = 1MZ2L1gFrCtkkn6DnTT2e4PFUTHw9gNwaj
key range [2^127, 2^128) = [170141183460469231731687303715884105728, 340282366920938463463374607431768211455)
range_min hex = 0x80000000000000000000000000000000
range_max hex = 0xffffffffffffffffffffffffffffffff
btc_value = 12.8
hash160 = e170ef514689d7230da362a0c121a07723550512
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
Target hash160 = e170ef514689d7230da362a0c121a07723550512
```
