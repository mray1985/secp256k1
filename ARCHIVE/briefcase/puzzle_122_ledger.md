# Puzzle 122 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1Me3ASYt5JCTAK2XaC32RMeH34PdprrfDx

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 122 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 122
address = 1Me3ASYt5JCTAK2XaC32RMeH34PdprrfDx
key range [2^121, 2^122) = [2658455991569831745807614120560689152, 5316911983139663491615228241121378303)
range_min hex = 0x2000000000000000000000000000000
range_max hex = 0x3ffffffffffffffffffffffffffffff
btc_value = 12.2
hash160 = e263b62ea294b9650615a13b926e75944c823990
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
Target hash160 = e263b62ea294b9650615a13b926e75944c823990
```
