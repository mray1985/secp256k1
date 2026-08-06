# S-20260710-02 — Native Kangaroo equivalence and throughput (PRE-REGISTERED)

**Status:** LOCKED before evaluation. Separate from S-01 — not a faster continuation of the same result.

| Field | Value |
|-------|-------|
| Candidate ID | S-20260710-02 |
| Short name | native_kangaroo_equivalence_throughput |
| Date registered | 2026-07-10 |
| Date first evaluated | *(pending)* |
| Prerequisite | **S-01 PASS** (Python reference correct + checkpoint-reproducible) |

---

## Boundary

S-01 validated the **method** (interval-DLP on band-floor \(Q\)), not P135 feasibility.
S-02 asks whether the **native** JeanLucPons Kangaroo reproduces the same scalars and
yields a **trustworthy throughput distribution** for projection.

## Exact target (same as S-01 / P135)

```text
L = 2^{n-1}
Q = P_n - [L]G
Q = [u]G,   0 ≤ u < L
d_n = L + u
```

Native infile: `start=0`, `end=L-1` (inclusive), pubkey = compressed \(Q\).
Recovered native scalar = \(u\); verify \([u]G=Q\) and \([L+u]G=P_n\).

## Locked requirements (before evaluation)

* Same solved ladder: **35, 40, 45, 50**; **55** only after earlier stages pass.
* **≥ 10 independent seeds** per practical puzzle size (document actual native RNG /
  run identity — JeanLuc `rseed` is not harness-controlled unless patched).
* Native recovered \(u\) must equal Python reference \(u\) and known \(d_n - L\).
* Every hit: \([u]G=Q\), \([L+u]G=P_n\); no false collision survives verification.
* Record: wall time, device, kangaroo count, DP setting (`-d`), total reported operations, seed/run id.
* **Separate operation metrics:** JeanLuc `Count` (counter sum) vs Python harness `ops`
  — treat as identical only after demonstrated equivalence on shared trials.
* **Checkpoint restoration:** fresh run and resumed run must recover the same scalar (independent test).
* **No GLV / negation speedup claim** from executable features alone — measure by controlled
  on/off builds or documented modes.

## Per-run statistic

\[
C_i = \frac{\text{operations}_i}{\sqrt{2^{n-1}}}
\]

Report per \(n\): **median**, range, and preferably **90th percentile** of \(C_i\).
Median beats one lucky/unlucky walk.

## Throughput projection (if native passes)

\[
T_{135} \approx \frac{C \cdot 2^{67}}{\text{measured effective group operations per second}}
\]

Use \(C\) from the **calibrated native distribution** (median / p90 range), **not** the best run.
Present as a range; do not pretend the constant is guaranteed.

## Promotion gate

S-02 passes only when:

1. all recovered keys exact (native = Python = known \(d_n-L\));
2. no false collision survives full verification;
3. checkpoint restoration passes;
4. measured scaling proportional to \(\sqrt{L}\);
5. native throughput reproducible across runs;
6. P135 resource estimate stated from measured throughput as a range.

## Ledger lines

> **S-01: PASS** — reference interval-DLP implementation is correct and checkpoint-reproducible.
> No P135 feasibility promotion.

> **S-02:** Can the native engine reproduce the same scalars and provide a trustworthy
> throughput distribution?

## Result (2026-07-10)

**PASS** on CPU (WSL patched JeanLucPons). Not P135-ready.

| n | seeds | median \(C\) | p90 \(C\) | range \(C\) | native=known | checkpoint |
|--:|------:|-------------:|----------:|------------:|:------------:|:----------:|
| 35 | 10 | 1.65 | 4.27 | 1.17–5.43 | ✓ | — |
| 40 | 10 | 1.56 | 3.42 | 0.24–3.71 | ✓ | — |
| 45 | 10 | 2.78 | 4.77 | 0.91–5.74 | ✓ | — |
| 50 | 10 | 1.66 | 2.61 | 0.55–2.95 | ✓ | interrupt PASS |

Throughput ≈ \(1.70\times 10^{7}\) ops/s (n≥45).  
\(T_{135}\) range ≈ \(4.6\times 10^{5}\)–\(1.3\times 10^{6}\) CPU-years at that rate.

Notes: no GLV/negation claim; native Count ≠ Python ops.
