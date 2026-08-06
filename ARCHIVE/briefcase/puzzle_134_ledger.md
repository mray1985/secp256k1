# Puzzle 134 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 13A3JrvXmvg5w9XGvyyR4JEJqiLz8ZySY3

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 134 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 134
address = 13A3JrvXmvg5w9XGvyyR4JEJqiLz8ZySY3
key range [2^133, 2^134) = [10889035741470030830827987437816582766592, 21778071482940061661655974875633165533183)
range_min hex = 0x2000000000000000000000000000000000
range_max hex = 0x3fffffffffffffffffffffffffffffffff
btc_value = 13.4
hash160 = 17a5ebfaf62e73f149e33ba674836801f13a80b9
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
Target hash160 = 17a5ebfaf62e73f149e33ba674836801f13a80b9
```
