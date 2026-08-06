# Puzzle 136 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1UDHPdovvR985NrWSkdWQDEQ1xuRiTALq

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 136 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 136
address = 1UDHPdovvR985NrWSkdWQDEQ1xuRiTALq
key range [2^135, 2^136) = [43556142965880123323311949751266331066368, 87112285931760246646623899502532662132735)
range_min hex = 0x8000000000000000000000000000000000
range_max hex = 0xffffffffffffffffffffffffffffffffff
btc_value = 13.6
hash160 = 05257be4b57ee43fc09762d5d3a9ad4a6e1a0364
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
Target hash160 = 05257be4b57ee43fc09762d5d3a9ad4a6e1a0364
```
