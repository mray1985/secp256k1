# Puzzle 99 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1JWnE6p6UN7ZJBN7TtcbNDoRcjFtuDWoNL

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 99 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 99
address = 1JWnE6p6UN7ZJBN7TtcbNDoRcjFtuDWoNL
key range [2^98, 2^99) = [316912650057057350374175801344, 633825300114114700748351602687)
range_min hex = 0x4000000000000000000000000
range_max hex = 0x7ffffffffffffffffffffffff
btc_value = 9.9
hash160 = c01bf430a97cbcdaedddba87ef4ea21c456cebdb
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
Target hash160 = c01bf430a97cbcdaedddba87ef4ea21c456cebdb
```
