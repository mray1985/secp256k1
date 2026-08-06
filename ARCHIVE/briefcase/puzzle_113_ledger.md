# Puzzle 113 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1NeGn21dUDDeqFQ63xb2SpgUuXuBLA4WT4

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 113 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 113
address = 1NeGn21dUDDeqFQ63xb2SpgUuXuBLA4WT4
key range [2^112, 2^113) = [5192296858534827628530496329220096, 10384593717069655257060992658440191)
range_min hex = 0x10000000000000000000000000000
range_max hex = 0x1ffffffffffffffffffffffffffff
btc_value = 11.3
hash160 = ed673389e4b12925316f9166d56d701829e53cf8
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
Target hash160 = ed673389e4b12925316f9166d56d701829e53cf8
```
