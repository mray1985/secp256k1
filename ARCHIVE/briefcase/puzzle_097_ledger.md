# Puzzle 97 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 18ywPwj39nGjqBrQJSzZVq2izR12MDpDr8

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 97 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 97
address = 18ywPwj39nGjqBrQJSzZVq2izR12MDpDr8
key range [2^96, 2^97) = [79228162514264337593543950336, 158456325028528675187087900671)
range_min hex = 0x1000000000000000000000000
range_max hex = 0x1ffffffffffffffffffffffff
btc_value = 9.7
hash160 = 578d94dc6f40fff35f91f6fba9b71c46b361dff2
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
Target hash160 = 578d94dc6f40fff35f91f6fba9b71c46b361dff2
```
