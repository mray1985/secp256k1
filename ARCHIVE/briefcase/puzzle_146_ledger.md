# Puzzle 146 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1M7ipcdYHey2Y5RZM34MBbpugghmjaV89P

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 146 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 146
address = 1M7ipcdYHey2Y5RZM34MBbpugghmjaV89P
key range [2^145, 2^146) = [44601490397061246283071436545296723011960832, 89202980794122492566142873090593446023921663)
range_min hex = 0x2000000000000000000000000000000000000
range_max hex = 0x3ffffffffffffffffffffffffffffffffffff
btc_value = 14.6
hash160 = dca7ebfb78ce21884300f133d89244bc4b1b756f
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
Target hash160 = dca7ebfb78ce21884300f133d89244bc4b1b756f
```
