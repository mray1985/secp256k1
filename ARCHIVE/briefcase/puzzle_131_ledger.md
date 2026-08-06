# Puzzle 131 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 16zRPnT8znwq42q7XeMkZUhb1bKqgRogyy

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 131 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 131
address = 16zRPnT8znwq42q7XeMkZUhb1bKqgRogyy
key range [2^130, 2^131) = [1361129467683753853853498429727072845824, 2722258935367507707706996859454145691647)
range_min hex = 0x400000000000000000000000000000000
range_max hex = 0x7ffffffffffffffffffffffffffffffff
btc_value = 13.1
hash160 = 41b4b36a6c036568972380177eca2916cacd71de
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
Target hash160 = 41b4b36a6c036568972380177eca2916cacd71de
```
