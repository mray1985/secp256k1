# Puzzle 93 — Operation Ledger

Full-information format: **formula → values → live verification**.
Re-run: `python build_puzzle_ledger_briefcase.py`

## Verdict

- **status:** UNSOLVED — no pubkey
- **rsz:** TBD — no pubkey
- **address:** 17Q7tuG2JwFFU9rXVj3uZqRtioH3mx2Jad

**Operations:** 2 total, 1 verified

---

### Phase 00_identity

#### Puzzle 93 catalog row  [✓]
**Formula:** privatekeys.pw / blockchain
```
puzzle = 93
address = 17Q7tuG2JwFFU9rXVj3uZqRtioH3mx2Jad
key range [2^92, 2^93) = [4951760157141521099596496896, 9903520314283042199192993791)
range_min hex = 0x100000000000000000000000
range_max hex = 0x1fffffffffffffffffffffff
btc_value = 9.3
hash160 = 463013cd41279f2fd0c31d0a16db3972bfffac8d
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
Target hash160 = 463013cd41279f2fd0c31d0a16db3972bfffac8d
```
