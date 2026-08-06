# Puzzle 132 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1KrU4dHE5WrW8rhWDsTRjR21r8t3dsrS3R

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 132 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 132
address = 1KrU4dHE5WrW8rhWDsTRjR21r8t3dsrS3R
key range [2^131, 2^132) = [2722258935367507707706996859454145691648, 5444517870735015415413993718908291383295)
range_min hex = 0x800000000000000000000000000000000
range_max hex = 0xfffffffffffffffffffffffffffffffff
btc_value = 13.2
hash160 = cecd3ca4319651bd3afd1e23ab66e111ed38d16d
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
Target hash160 = cecd3ca4319651bd3afd1e23ab66e111ed38d16d
```
