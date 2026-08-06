# Puzzle 91 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1EzVHtmbN4fs4MiNk3ppEnKKhsmXYJ4s74

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 91 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 91
address = 1EzVHtmbN4fs4MiNk3ppEnKKhsmXYJ4s74
key range [2^90, 2^91) = [1237940039285380274899124224, 2475880078570760549798248447)
range_min hex = 0x40000000000000000000000
range_max hex = 0x7ffffffffffffffffffffff
btc_value = 9.1
hash160 = 9978f61b92d16c5f1a463a0995df70da1f7a7d2a
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
Target hash160 = 9978f61b92d16c5f1a463a0995df70da1f7a7d2a
```
