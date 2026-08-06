# Puzzle 78 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 15qF6X51huDjqTmF9BJgxXdt1xcj46Jmhb

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 78 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 78
address = 15qF6X51huDjqTmF9BJgxXdt1xcj46Jmhb
key range [2^77, 2^78) = [151115727451828646838272, 302231454903657293676543)
range_min hex = 0x20000000000000000000
range_max hex = 0x3fffffffffffffffffff
btc_value = 7.8
hash160 = 35003c3ef8759c92092f8488fca59a042859018c
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
Target hash160 = 35003c3ef8759c92092f8488fca59a042859018c
```
