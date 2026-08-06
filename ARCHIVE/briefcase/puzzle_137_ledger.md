# Puzzle 137 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 15nf31J46iLuK1ZkTnqHo7WgN5cARFK3RA

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 137 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 137
address = 15nf31J46iLuK1ZkTnqHo7WgN5cARFK3RA
key range [2^136, 2^137) = [87112285931760246646623899502532662132736, 174224571863520493293247799005065324265471)
range_min hex = 0x10000000000000000000000000000000000
range_max hex = 0x1ffffffffffffffffffffffffffffffffff
btc_value = 13.7
hash160 = 3482f8986e13c018692053a784481c63a3554c9c
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
Target hash160 = 3482f8986e13c018692053a784481c63a3554c9c
```
