# Puzzle 123 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1CdufMQL892A69KXgv6UNBD17ywWqYpKut

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 123 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 123
address = 1CdufMQL892A69KXgv6UNBD17ywWqYpKut
key range [2^122, 2^123) = [5316911983139663491615228241121378304, 10633823966279326983230456482242756607)
range_min hex = 0x4000000000000000000000000000000
range_max hex = 0x7ffffffffffffffffffffffffffffff
btc_value = 12.3
hash160 = 7fa4515066ba6905f894b2078f9af7b1379169cf
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
Target hash160 = 7fa4515066ba6905f894b2078f9af7b1379169cf
```
