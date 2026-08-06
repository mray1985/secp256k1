# Puzzle 72 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1JTK7s9YVYywfm5XUH7RNhHJH1LshCaRFR

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 72 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 72
address = 1JTK7s9YVYywfm5XUH7RNhHJH1LshCaRFR
key range [2^71, 2^72) = [2361183241434822606848, 4722366482869645213695)
range_min hex = 0x800000000000000000
range_max hex = 0xffffffffffffffffff
btc_value = 7.2
hash160 = bf7413e8df4e7a34ce9dc13e2f2648783ec54adb
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
Target hash160 = bf7413e8df4e7a34ce9dc13e2f2648783ec54adb
```
