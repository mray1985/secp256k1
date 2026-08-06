# Puzzle 107 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 15EJFC5ZTs9nhsdvSUeBXjLAuYq3SWaxTc

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 107 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 107
address = 15EJFC5ZTs9nhsdvSUeBXjLAuYq3SWaxTc
key range [2^106, 2^107) = [81129638414606681695789005144064, 162259276829213363391578010288127)
range_min hex = 0x400000000000000000000000000
range_max hex = 0x7ffffffffffffffffffffffffff
btc_value = 10.7
hash160 = 2e644e46b042ffa86da35c54d7275f1abe6d4911
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
Target hash160 = 2e644e46b042ffa86da35c54d7275f1abe6d4911
```
