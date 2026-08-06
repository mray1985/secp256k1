# Puzzle 126 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1AWCLZAjKbV1P7AHvaPNCKiB7ZWVDMxFiz

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 126 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 126
address = 1AWCLZAjKbV1P7AHvaPNCKiB7ZWVDMxFiz
key range [2^125, 2^126) = [42535295865117307932921825928971026432, 85070591730234615865843651857942052863)
range_min hex = 0x20000000000000000000000000000000
range_max hex = 0x3fffffffffffffffffffffffffffffff
btc_value = 12.6
hash160 = 683ea8a1ef06eada90556017d44323b5c04e00f1
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
Target hash160 = 683ea8a1ef06eada90556017d44323b5c04e00f1
```
