# Puzzle 156 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1FTpAbQa4h8trvhQXjXnmNhqdiGBd1oraE

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 156 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 156
address = 1FTpAbQa4h8trvhQXjXnmNhqdiGBd1oraE
key range [2^155, 2^156) = [45671926166590716193865151022383844364247891968, 91343852333181432387730302044767688728495783935)
range_min hex = 0x800000000000000000000000000000000000000
range_max hex = 0xfffffffffffffffffffffffffffffffffffffff
btc_value = 15.6
hash160 = 9ea3f29aaedf7da10b1488934c50a39e271b0b64
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
Target hash160 = 9ea3f29aaedf7da10b1488934c50a39e271b0b64
```
