# Puzzle 154 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1NgVmsCCJaKLzGyKLFJfVequnFW9ZvnMLN

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 154 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 154
address = 1NgVmsCCJaKLzGyKLFJfVequnFW9ZvnMLN
key range [2^153, 2^154) = [11417981541647679048466287755595961091061972992, 22835963083295358096932575511191922182123945983)
range_min hex = 0x200000000000000000000000000000000000000
range_max hex = 0x3ffffffffffffffffffffffffffffffffffffff
btc_value = 15.4
hash160 = edd2e206825fa8949d1304cd82c08d64b222f2eb
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
Target hash160 = edd2e206825fa8949d1304cd82c08d64b222f2eb
```
