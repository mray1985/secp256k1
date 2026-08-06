# Puzzle 81 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 15qsCm78whspNQFydGJQk5rexzxTQopnHZ

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 81 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 81
address = 15qsCm78whspNQFydGJQk5rexzxTQopnHZ
key range [2^80, 2^81) = [1208925819614629174706176, 2417851639229258349412351)
range_min hex = 0x100000000000000000000
range_max hex = 0x1ffffffffffffffffffff
btc_value = 8.1
hash160 = 351e605fac813965951ba433b7c2956bf8ad95ce
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
Target hash160 = 351e605fac813965951ba433b7c2956bf8ad95ce
```
