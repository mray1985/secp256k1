# Puzzle 152 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1LuUHyrQr8PKSvbcY1v1PiuGuqFjWpDumN

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 152 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 152
address = 1LuUHyrQr8PKSvbcY1v1PiuGuqFjWpDumN
key range [2^151, 2^152) = [2854495385411919762116571938898990272765493248, 5708990770823839524233143877797980545530986495)
range_min hex = 0x80000000000000000000000000000000000000
range_max hex = 0xffffffffffffffffffffffffffffffffffffff
btc_value = 15.2
hash160 = da56cd815fa2f0d6a4ce6d25ed7b1a01d9f9bc6b
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
Target hash160 = da56cd815fa2f0d6a4ce6d25ed7b1a01d9f9bc6b
```
