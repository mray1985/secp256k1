# Puzzle 109 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1GvgAXVCbA8FBjXfWiAms4ytFeJcKsoyhL

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 109 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 109
address = 1GvgAXVCbA8FBjXfWiAms4ytFeJcKsoyhL
key range [2^108, 2^109) = [324518553658426726783156020576256, 649037107316853453566312041152511)
range_min hex = 0x1000000000000000000000000000
range_max hex = 0x1fffffffffffffffffffffffffff
btc_value = 10.9
hash160 = aeb0a0197442d4ade8ef41442d557b0e22b85ac0
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
Target hash160 = aeb0a0197442d4ade8ef41442d557b0e22b85ac0
```
