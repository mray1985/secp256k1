# Puzzle 142 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 15MnK2jXPqTMURX4xC3h4mAZxyCcaWWEDD

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 142 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 142
address = 15MnK2jXPqTMURX4xC3h4mAZxyCcaWWEDD
key range [2^141, 2^142) = [2787593149816327892691964784081045188247552, 5575186299632655785383929568162090376495103)
range_min hex = 0x200000000000000000000000000000000000
range_max hex = 0x3fffffffffffffffffffffffffffffffffff
btc_value = 14.2
hash160 = 2fcea55e6d027a2ba7c7ebe95eedf47766730fe2
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
Target hash160 = 2fcea55e6d027a2ba7c7ebe95eedf47766730fe2
```
