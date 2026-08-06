# Puzzle 104 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1EQJvpsmhazYCcKX5Au6AZmZKRnzarMVZu

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 104 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 104
address = 1EQJvpsmhazYCcKX5Au6AZmZKRnzarMVZu
key range [2^103, 2^104) = [10141204801825835211973625643008, 20282409603651670423947251286015)
range_min hex = 0x80000000000000000000000000
range_max hex = 0xffffffffffffffffffffffffff
btc_value = 10.4
hash160 = 93022af9a38f3ebb0c3f15dd1c83f8fadaf64e74
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
Target hash160 = 93022af9a38f3ebb0c3f15dd1c83f8fadaf64e74
```
