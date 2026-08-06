# Puzzle 133 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 17uDfp5r4n441xkgLFmhNoSW1KWp6xVLD

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 133 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 133
address = 17uDfp5r4n441xkgLFmhNoSW1KWp6xVLD
key range [2^132, 2^133) = [5444517870735015415413993718908291383296, 10889035741470030830827987437816582766591)
range_min hex = 0x1000000000000000000000000000000000
range_max hex = 0x1fffffffffffffffffffffffffffffffff
btc_value = 13.3
hash160 = 014e15e4ea6da460cc7835e262676baa37988e4f
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
Target hash160 = 014e15e4ea6da460cc7835e262676baa37988e4f
```
