# Puzzle 74 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1FWGcVDK3JGzCC3WtkYetULPszMaK2Jksv

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 74 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 74
address = 1FWGcVDK3JGzCC3WtkYetULPszMaK2Jksv
key range [2^73, 2^74) = [9444732965739290427392, 18889465931478580854783)
range_min hex = 0x2000000000000000000
range_max hex = 0x3ffffffffffffffffff
btc_value = 7.4
hash160 = 9f1adb20baeacc38b3f49f3df6906a0e48f2df3d
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
Target hash160 = 9f1adb20baeacc38b3f49f3df6906a0e48f2df3d
```
