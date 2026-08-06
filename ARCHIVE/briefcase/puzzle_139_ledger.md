# Puzzle 139 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1Fz63c775VV9fNyj25d9Xfw3YHE6sKCxbt

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 139 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 139
address = 1Fz63c775VV9fNyj25d9Xfw3YHE6sKCxbt
key range [2^138, 2^139) = [348449143727040986586495598010130648530944, 696898287454081973172991196020261297061887)
range_min hex = 0x40000000000000000000000000000000000
range_max hex = 0x7ffffffffffffffffffffffffffffffffff
btc_value = 13.9
hash160 = a45dae9cd5d3fde21e5aa9a95367d107267b3b8a
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
Target hash160 = a45dae9cd5d3fde21e5aa9a95367d107267b3b8a
```
