# Puzzle 114 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 174SNxfqpdMGYy5YQcfLbSTK3MRNZEePoy

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 114 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 114
address = 174SNxfqpdMGYy5YQcfLbSTK3MRNZEePoy
key range [2^113, 2^114) = [10384593717069655257060992658440192, 20769187434139310514121985316880383)
range_min hex = 0x20000000000000000000000000000
range_max hex = 0x3ffffffffffffffffffffffffffff
btc_value = 11.4
hash160 = 42773005f9594cd16b10985d428418acb7f352ec
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
Target hash160 = 42773005f9594cd16b10985d428418acb7f352ec
```
