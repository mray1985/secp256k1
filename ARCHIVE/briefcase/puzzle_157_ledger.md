# Puzzle 157 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 14JHoRAdmJg3XR4RjMDh6Wed6ft6hzbQe9

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 157 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 157
address = 14JHoRAdmJg3XR4RjMDh6Wed6ft6hzbQe9
key range [2^156, 2^157) = [91343852333181432387730302044767688728495783936, 182687704666362864775460604089535377456991567871)
range_min hex = 0x1000000000000000000000000000000000000000
range_max hex = 0x1fffffffffffffffffffffffffffffffffffffff
btc_value = 15.7
hash160 = 242d790e5a168043c76f0539fd894b73ee67b3b3
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
Target hash160 = 242d790e5a168043c76f0539fd894b73ee67b3b3
```
