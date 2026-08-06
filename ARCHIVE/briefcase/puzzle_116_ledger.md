# Puzzle 116 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1MnJ6hdhvK37VLmqcdEwqC3iFxyWH2PHUV

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 116 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 116
address = 1MnJ6hdhvK37VLmqcdEwqC3iFxyWH2PHUV
key range [2^115, 2^116) = [41538374868278621028243970633760768, 83076749736557242056487941267521535)
range_min hex = 0x80000000000000000000000000000
range_max hex = 0xfffffffffffffffffffffffffffff
btc_value = 11.6
hash160 = e3f381c34a20da049779b44cae0417c7fb2898d0
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
Target hash160 = e3f381c34a20da049779b44cae0417c7fb2898d0
```
