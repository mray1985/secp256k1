# Puzzle 108 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1HB1iKUqeffnVsvQsbpC6dNi1XKbyNuqao

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 108 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 108
address = 1HB1iKUqeffnVsvQsbpC6dNi1XKbyNuqao
key range [2^107, 2^108) = [162259276829213363391578010288128, 324518553658426726783156020576255)
range_min hex = 0x800000000000000000000000000
range_max hex = 0xfffffffffffffffffffffffffff
btc_value = 10.8
hash160 = b166c44f12c7fc565f37ff6288ee64e0f0ec9a0b
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
Target hash160 = b166c44f12c7fc565f37ff6288ee64e0f0ec9a0b
```
