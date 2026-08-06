# Puzzle 111 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1824ZJQ7nKJ9QFTRBqn7z7dHV5EGpzUpH3

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 111 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 111
address = 1824ZJQ7nKJ9QFTRBqn7z7dHV5EGpzUpH3
key range [2^110, 2^111) = [1298074214633706907132624082305024, 2596148429267413814265248164610047)
range_min hex = 0x4000000000000000000000000000
range_max hex = 0x7fffffffffffffffffffffffffff
btc_value = 11.1
hash160 = 4cfc43fe12a330c8164251e38c0c0c3c84cf86f6
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
Target hash160 = 4cfc43fe12a330c8164251e38c0c0c3c84cf86f6
```
