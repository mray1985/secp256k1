# Puzzle 101 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1CKCVdbDJasYmhswB6HKZHEAnNaDpK7W4n

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 101 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 101
address = 1CKCVdbDJasYmhswB6HKZHEAnNaDpK7W4n
key range [2^100, 2^101) = [1267650600228229401496703205376, 2535301200456458802993406410751)
range_min hex = 0x10000000000000000000000000
range_max hex = 0x1fffffffffffffffffffffffff
btc_value = 10.1
hash160 = 7c1a77205c03b9909663b2034faa0b544e6bc96b
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
Target hash160 = 7c1a77205c03b9909663b2034faa0b544e6bc96b
```
