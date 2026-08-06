# Puzzle 79 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1ARk8HWJMn8js8tQmGUJeQHjSE7KRkn2t8

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 79 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 79
address = 1ARk8HWJMn8js8tQmGUJeQHjSE7KRkn2t8
key range [2^78, 2^79) = [302231454903657293676544, 604462909807314587353087)
range_min hex = 0x40000000000000000000
range_max hex = 0x7fffffffffffffffffff
btc_value = 7.9
hash160 = 67671d5490c272e3ab7ddd34030d587738df33da
solved = False
private key d = unknown (unsolved — not zero)
solve_date = —
public_key leaked = False
```

### Phase 01_no_pubkey

#### pubkey not exposed on chain  [?]
**Formula:** no spend tx with public key — brute-force address only
**Note:** Puzzles without partial spend remain hash160-only targets.
```
Cannot build Px/Py or RSZ bridge until pubkey is revealed by a spend.
Target hash160 = 67671d5490c272e3ab7ddd34030d587738df33da
```
