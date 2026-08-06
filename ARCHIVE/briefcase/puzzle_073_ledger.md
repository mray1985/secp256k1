# Puzzle 73 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 12VVRNPi4SJqUTsp6FmqDqY5sGosDtysn4

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 73 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 73
address = 12VVRNPi4SJqUTsp6FmqDqY5sGosDtysn4
key range [2^72, 2^73) = [4722366482869645213696, 9444732965739290427391)
range_min hex = 0x1000000000000000000
range_max hex = 0x1ffffffffffffffffff
btc_value = 7.3
hash160 = 105b7f253f0ebd7843adaebbd805c944bfb863e4
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
Target hash160 = 105b7f253f0ebd7843adaebbd805c944bfb863e4
```
