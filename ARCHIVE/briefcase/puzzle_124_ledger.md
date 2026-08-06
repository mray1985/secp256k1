# Puzzle 124 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1BkkGsX9ZM6iwL3zbqs7HWBV7SvosR6m8N

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 124 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 124
address = 1BkkGsX9ZM6iwL3zbqs7HWBV7SvosR6m8N
key range [2^123, 2^124) = [10633823966279326983230456482242756608, 21267647932558653966460912964485513215)
range_min hex = 0x8000000000000000000000000000000
range_max hex = 0xfffffffffffffffffffffffffffffff
btc_value = 12.4
hash160 = 75f74467ce7214f1767406d5ed12012aa523c48e
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
Target hash160 = 75f74467ce7214f1767406d5ed12012aa523c48e
```
