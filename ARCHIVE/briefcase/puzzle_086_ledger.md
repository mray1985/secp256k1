# Puzzle 86 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1K3x5L6G57Y494fDqBfrojD28UJv4s5JcK

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 86 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 86
address = 1K3x5L6G57Y494fDqBfrojD28UJv4s5JcK
key range [2^85, 2^86) = [38685626227668133590597632, 77371252455336267181195263)
range_min hex = 0x2000000000000000000000
range_max hex = 0x3fffffffffffffffffffff
btc_value = 8.6
hash160 = c60111ed3d63b49665747b0e31eb382da5193535
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
Target hash160 = c60111ed3d63b49665747b0e31eb382da5193535
```
