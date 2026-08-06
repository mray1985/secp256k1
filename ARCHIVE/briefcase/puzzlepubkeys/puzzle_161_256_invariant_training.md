# Puzzle 161-256 pubkey invariant training

Question: can public-key-only features predict puzzle index n?

Training set: 96 revealed pubkeys from genesis spend.

## Top correlations with n

| feature | r | p_perm |
|---------|---|--------|
| py_popcount | -0.2053 | 0.0510 |
| py_mod_p_frac | 0.1543 | 0.1210 |
| p_minus_py_frac | -0.1543 | 0.1210 |
| echo_py_256 | 0.1543 | 0.1210 |
| hash160_left5 | -0.1519 | 0.1260 |
| log10_py | 0.1510 | 0.1520 |
| px_xor_py_pop | -0.1465 | 0.1670 |
| px_py_ratio_log | -0.0934 | 0.3640 |
| px_mod9 | -0.0923 | 0.3430 |
| inv_px_frac | 0.0882 | 0.3680 |
| echo_h_256 | 0.0826 | 0.4390 |
| log10_hash160 | 0.0636 | 0.5480 |
| py_mod256 | -0.0586 | 0.5330 |
| carry_pmy_mod9 | -0.0522 | 0.6190 |
| py_mod9 | -0.0482 | 0.6380 |

**R² (top-5 features → n):** 0.0436  (null median 0.0124)

## Ruling (narrow)

**Ruling A:** No *pubkey-only* invariant recovers puzzle index on 161–256.

This does **not** falsify scalar-side (`d`, `k`, `r,s,z`, TDAD), field↔scalar bridge (`p−N`, `N/p`), sweep tx structure, or “last is first” as a **scalar** checksum trail.

See: `../putting_the_puzzle_together/cursor_chatgpt_correlation.md`
