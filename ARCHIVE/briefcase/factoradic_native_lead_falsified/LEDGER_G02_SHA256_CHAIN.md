# Ledger: G-02 SHA-256 chained puzzle keys — FAIL

## Question

$$
\boxed{
d_{n+5}
\stackrel{?}{=}
2^{n+4}
+
\left(
\operatorname{SHA256}(\operatorname{int32be}(d_n))
\bmod 2^{n+4}
\right)
}
$$

## Result

**Verdict: FAIL**

Exact matches 0/11. First miss at 75->80. One mismatch closes this exact SHA-256 chain hypothesis.

| | |
|--|--|
| edges | 0/11 exact |
| first miss | {'n': 75, 'n_next': 80, 'pred': 723767090870435936183697, 'actual': 1105520030589234487939456} |
| encoding | 32-byte BE, SHA-256 once, low n+4 bits |

No approximate scores, byte-order, high-bits, hex, or alternate-hash reopen.

## G-01 reminder (precise)

G-01 FALSIFIED: \(a\Delta_1\equiv\Delta_2\pmod{2^{64}}\) has no solution because
\(\gcd(\Delta_1,2^{64})=2\) does not divide the odd right-hand side.

Artifacts: `G-20260710-02_sha256_chain_result.*`, `g02_sha256_chain.py`.
