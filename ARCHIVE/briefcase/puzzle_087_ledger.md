# Puzzle 87 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1PxH3K1Shdjb7gSEoTX7UPDZ6SH4qGPrvq

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 87 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 87
address = 1PxH3K1Shdjb7gSEoTX7UPDZ6SH4qGPrvq
key range [2^86, 2^87) = [77371252455336267181195264, 154742504910672534362390527)
range_min hex = 0x4000000000000000000000
range_max hex = 0x7fffffffffffffffffffff
btc_value = 8.7
hash160 = fbc708d671c03e26661b9c08f77598a529858b5e
solved = False
private key d = unknown (unsolved — not zero)
solve_date = —
public_key leaked = False
```

### Phase 01_no_pubkey

#### pubkey not exposed on chain  [?]
**Formula:** no spend tx with public key — brute-force address only
**Note:** Puzzles without partial spend remain hash160-only targets.
```
Cannot build Px/Py or RSZ bridge until pubkey is revealed by a spend.
Target hash160 = fbc708d671c03e26661b9c08f77598a529858b5e
```
