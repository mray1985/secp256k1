# Puzzle 82 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 13zYrYhhJxp6Ui1VV7pqa5WDhNWM45ARAC

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 82 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 82
address = 13zYrYhhJxp6Ui1VV7pqa5WDhNWM45ARAC
key range [2^81, 2^82) = [2417851639229258349412352, 4835703278458516698824703)
range_min hex = 0x200000000000000000000
range_max hex = 0x3ffffffffffffffffffff
btc_value = 8.2
hash160 = 20d28d4e87543947c7e4913bcdceaa16e2f8f061
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
Target hash160 = 20d28d4e87543947c7e4913bcdceaa16e2f8f061
```
