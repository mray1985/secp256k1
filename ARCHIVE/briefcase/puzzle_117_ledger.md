# Puzzle 117 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1KNRfGWw7Q9Rmwsc6NT5zsdvEb9M2Wkj5Z

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 117 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 117
address = 1KNRfGWw7Q9Rmwsc6NT5zsdvEb9M2Wkj5Z
key range [2^116, 2^117) = [83076749736557242056487941267521536, 166153499473114484112975882535043071)
range_min hex = 0x100000000000000000000000000000
range_max hex = 0x1fffffffffffffffffffffffffffff
btc_value = 11.7
hash160 = c97f9591e28687be1c4d972e25be7c372a3221b4
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
Target hash160 = c97f9591e28687be1c4d972e25be7c372a3221b4
```
