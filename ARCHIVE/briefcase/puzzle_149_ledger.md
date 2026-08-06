# Puzzle 149 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1CXvTzR6qv8wJ7eprzUKeWxyGcHwDYP1i2

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 149 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 149
address = 1CXvTzR6qv8wJ7eprzUKeWxyGcHwDYP1i2
key range [2^148, 2^149) = [356811923176489970264571492362373784095686656, 713623846352979940529142984724747568191373311)
range_min hex = 0x10000000000000000000000000000000000000
range_max hex = 0x1fffffffffffffffffffffffffffffffffffff
btc_value = 14.9
hash160 = 7e827e3b90da24c2a15f7b67e3bbece39955a5d0
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
Target hash160 = 7e827e3b90da24c2a15f7b67e3bbece39955a5d0
```
