# Puzzle 89 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 19QciEHbGVNY4hrhfKXmcBBCrJSBZ6TaVt

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 89 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 89
address = 19QciEHbGVNY4hrhfKXmcBBCrJSBZ6TaVt
key range [2^88, 2^89) = [309485009821345068724781056, 618970019642690137449562111)
range_min hex = 0x10000000000000000000000
range_max hex = 0x1ffffffffffffffffffffff
btc_value = 8.9
hash160 = 5c3862203d1e44ab3af441503e22db97b1c5097e
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
Target hash160 = 5c3862203d1e44ab3af441503e22db97b1c5097e
```
