# Puzzle 129 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1Hz3uv3nNZzBVMXLGadCucgjiCs5W9vaGz

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 129 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 129
address = 1Hz3uv3nNZzBVMXLGadCucgjiCs5W9vaGz
key range [2^128, 2^129) = [340282366920938463463374607431768211456, 680564733841876926926749214863536422911)
range_min hex = 0x100000000000000000000000000000000
range_max hex = 0x1ffffffffffffffffffffffffffffffff
btc_value = 12.9
hash160 = ba4c2748360a6b66263e11d1dc8658463ca5ff18
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
Target hash160 = ba4c2748360a6b66263e11d1dc8658463ca5ff18
```
