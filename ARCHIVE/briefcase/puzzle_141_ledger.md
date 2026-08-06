# Puzzle 141 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1CD91Vm97mLQvXhrnoMChhJx4TP9MaQkJo

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 141 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 141
address = 1CD91Vm97mLQvXhrnoMChhJx4TP9MaQkJo
key range [2^140, 2^141) = [1393796574908163946345982392040522594123776, 2787593149816327892691964784081045188247551)
range_min hex = 0x100000000000000000000000000000000000
range_max hex = 0x1fffffffffffffffffffffffffffffffffff
btc_value = 14.1
hash160 = 7af50f73fd580f1713af3a6f9c5de49643ec6fc6
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
Target hash160 = 7af50f73fd580f1713af3a6f9c5de49643ec6fc6
```
