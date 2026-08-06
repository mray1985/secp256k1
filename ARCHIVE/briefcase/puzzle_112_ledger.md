# Puzzle 112 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 18A7NA9FTsnJxWgkoFfPAFbQzuQxpRtCos

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 112 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 112
address = 18A7NA9FTsnJxWgkoFfPAFbQzuQxpRtCos
key range [2^111, 2^112) = [2596148429267413814265248164610048, 5192296858534827628530496329220095)
range_min hex = 0x8000000000000000000000000000
range_max hex = 0xffffffffffffffffffffffffffff
btc_value = 11.2
hash160 = 4e81efec43c5195aeca0e3877664330418b8e48e
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
Target hash160 = 4e81efec43c5195aeca0e3877664330418b8e48e
```
