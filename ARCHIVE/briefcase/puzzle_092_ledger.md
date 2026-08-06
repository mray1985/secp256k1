# Puzzle 92 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 1AE8NzzgKE7Yhz7BWtAcAAxiFMbPo82NB5

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 92 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 92
address = 1AE8NzzgKE7Yhz7BWtAcAAxiFMbPo82NB5
key range [2^91, 2^92) = [2475880078570760549798248448, 4951760157141521099596496895)
range_min hex = 0x80000000000000000000000
range_max hex = 0xfffffffffffffffffffffff
btc_value = 9.2
hash160 = 6534b31208fe6e100d29f9c9c75aac8bf06fbb38
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
Target hash160 = 6534b31208fe6e100d29f9c9c75aac8bf06fbb38
```
