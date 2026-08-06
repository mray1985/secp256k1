# Puzzle 103 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1AcAmB6jmtU6AiEcXkmiNE9TNVPsj9DULf

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 103 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 103
address = 1AcAmB6jmtU6AiEcXkmiNE9TNVPsj9DULf
key range [2^102, 2^103) = [5070602400912917605986812821504, 10141204801825835211973625643007)
range_min hex = 0x40000000000000000000000000
range_max hex = 0x7fffffffffffffffffffffffff
btc_value = 10.3
hash160 = 695fd6dcf33f47166b25de968b2932b351b0afc4
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
Target hash160 = 695fd6dcf33f47166b25de968b2932b351b0afc4
```
