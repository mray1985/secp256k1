# Puzzle 84 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1CMq3SvFcVEcpLMuuH8PUcNiqsK1oicG2D

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 84 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 84
address = 1CMq3SvFcVEcpLMuuH8PUcNiqsK1oicG2D
key range [2^83, 2^84) = [9671406556917033397649408, 19342813113834066795298815)
range_min hex = 0x800000000000000000000
range_max hex = 0xfffffffffffffffffffff
btc_value = 8.4
hash160 = 7c99ce73e19f9fbfcce4825ae88261e2b0b0b040
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
Target hash160 = 7c99ce73e19f9fbfcce4825ae88261e2b0b0b040
```
