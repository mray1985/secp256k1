# Puzzle 147 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 18aNhurEAJsw6BAgtANpexk5ob1aGTwSeL

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 147 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 147
address = 18aNhurEAJsw6BAgtANpexk5ob1aGTwSeL
key range [2^146, 2^147) = [89202980794122492566142873090593446023921664, 178405961588244985132285746181186892047843327)
range_min hex = 0x4000000000000000000000000000000000000
range_max hex = 0x7ffffffffffffffffffffffffffffffffffff
btc_value = 14.7
hash160 = 5318b9d7fcc93873f768725eb68ba2c924bb07ee
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
Target hash160 = 5318b9d7fcc93873f768725eb68ba2c924bb07ee
```
