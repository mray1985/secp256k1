# Puzzle 158 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 19z6waranEf8CcP8FqNgdwUe1QRxvUNKBG

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 158 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 158
address = 19z6waranEf8CcP8FqNgdwUe1QRxvUNKBG
key range [2^157, 2^158) = [182687704666362864775460604089535377456991567872, 365375409332725729550921208179070754913983135743)
range_min hex = 0x2000000000000000000000000000000000000000
range_max hex = 0x3fffffffffffffffffffffffffffffffffffffff
btc_value = 15.8
hash160 = 628dacebb0faa7f81670e174ca4c8a95a7e37029
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
Target hash160 = 628dacebb0faa7f81670e174ca4c8a95a7e37029
```
