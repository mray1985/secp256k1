# Puzzle 76 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1DJh2eHFYQfACPmrvpyWc8MSTYKh7w9eRF

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 76 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 76
address = 1DJh2eHFYQfACPmrvpyWc8MSTYKh7w9eRF
key range [2^75, 2^76) = [37778931862957161709568, 75557863725914323419135)
range_min hex = 0x8000000000000000000
range_max hex = 0xfffffffffffffffffff
btc_value = 7.6
hash160 = 86f9fea5cdecf033161dd2f8f8560768ae0a6d14
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
Target hash160 = 86f9fea5cdecf033161dd2f8f8560768ae0a6d14
```
