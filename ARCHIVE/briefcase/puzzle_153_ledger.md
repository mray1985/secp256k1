# Puzzle 153 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 18192XpzzdDi2K11QVHR7td2HcPS6Qs5vg

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 153 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 153
address = 18192XpzzdDi2K11QVHR7td2HcPS6Qs5vg
key range [2^152, 2^153) = [5708990770823839524233143877797980545530986496, 11417981541647679048466287755595961091061972991)
range_min hex = 0x100000000000000000000000000000000000000
range_max hex = 0x1ffffffffffffffffffffffffffffffffffffff
btc_value = 15.3
hash160 = 4ccf94a1b0efd63cddeee0ef5eee5ebe720cfcbf
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
Target hash160 = 4ccf94a1b0efd63cddeee0ef5eee5ebe720cfcbf
```
