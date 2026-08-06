# Puzzle 159 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 14u4nA5sugaswb6SZgn5av2vuChdMnD9E5

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 159 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 159
address = 14u4nA5sugaswb6SZgn5av2vuChdMnD9E5
key range [2^158, 2^159) = [365375409332725729550921208179070754913983135744, 730750818665451459101842416358141509827966271487)
range_min hex = 0x4000000000000000000000000000000000000000
range_max hex = 0x7fffffffffffffffffffffffffffffffffffffff
btc_value = 15.9
hash160 = 2ac1295b4e54b3f15bb0a99f84018d2082495645
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
Target hash160 = 2ac1295b4e54b3f15bb0a99f84018d2082495645
```
