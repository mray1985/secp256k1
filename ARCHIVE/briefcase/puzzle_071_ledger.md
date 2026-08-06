# Puzzle 71 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 71 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 71
address = 1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU
key range [2^70, 2^71) = [1180591620717411303424, 2361183241434822606847)
range_min hex = 0x400000000000000000
range_max hex = 0x7fffffffffffffffff
btc_value = 7.1
hash160 = f6f5431d25bbf7b12e8add9af5e3475c44a0a5b8
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
Target hash160 = f6f5431d25bbf7b12e8add9af5e3475c44a0a5b8
```
