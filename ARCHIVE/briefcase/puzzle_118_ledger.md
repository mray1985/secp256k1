# Puzzle 118 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1PJZPzvGX19a7twf5HyD2VvNiPdHLzm9F6

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 118 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 118
address = 1PJZPzvGX19a7twf5HyD2VvNiPdHLzm9F6
key range [2^117, 2^118) = [166153499473114484112975882535043072, 332306998946228968225951765070086143)
range_min hex = 0x200000000000000000000000000000
range_max hex = 0x3fffffffffffffffffffffffffffff
btc_value = 11.8
hash160 = f4a4e1c11a5bbbd2fc139d221825407c66e0b8b4
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
Target hash160 = f4a4e1c11a5bbbd2fc139d221825407c66e0b8b4
```
