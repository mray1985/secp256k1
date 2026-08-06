# Puzzle 96 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 15ANYzzCp5BFHcCnVFzXqyibpzgPLWaD8b

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 96 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 96
address = 15ANYzzCp5BFHcCnVFzXqyibpzgPLWaD8b
key range [2^95, 2^96) = [39614081257132168796771975168, 79228162514264337593543950335)
range_min hex = 0x800000000000000000000000
range_max hex = 0xffffffffffffffffffffffff
btc_value = 9.6
hash160 = 2da63cbd251d23c7b633cb287c09e6cf888b3fe4
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
Target hash160 = 2da63cbd251d23c7b633cb287c09e6cf888b3fe4
```
