# Puzzle 143 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 13N66gCzWWHEZBxhVxG18P8wyjEWF9Yoi1

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 143 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 143
address = 13N66gCzWWHEZBxhVxG18P8wyjEWF9Yoi1
key range [2^142, 2^143) = [5575186299632655785383929568162090376495104, 11150372599265311570767859136324180752990207)
range_min hex = 0x400000000000000000000000000000000000
range_max hex = 0x7fffffffffffffffffffffffffffffffffff
btc_value = 14.3
hash160 = 19ed3e03d19ddcedd5fa86543be820b3a7951650
solved = False
private key d = unknown (unsolved — not zero)
solve_date = —
public_key leaked = False
```

### Phase 01_no_pubkey

#### pubkey not exposed on chain  [?]
**Formula:** no spend tx with public key — brute-force address only
**Note:** Puzzles without partial spend remain hash160-only targets.
```
Cannot build Px/Py or RSZ bridge until pubkey is revealed by a spend.
Target hash160 = 19ed3e03d19ddcedd5fa86543be820b3a7951650
```
