# Puzzle 106 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 18KsfuHuzQaBTNLASyj15hy4LuqPUo1FNB

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 106 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 106
address = 18KsfuHuzQaBTNLASyj15hy4LuqPUo1FNB
key range [2^105, 2^106) = [40564819207303340847894502572032, 81129638414606681695789005144063)
range_min hex = 0x200000000000000000000000000
range_max hex = 0x3ffffffffffffffffffffffffff
btc_value = 10.6
hash160 = 505aaa63a5e209dfb90cee683a8e227a8c278e47
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
Target hash160 = 505aaa63a5e209dfb90cee683a8e227a8c278e47
```
