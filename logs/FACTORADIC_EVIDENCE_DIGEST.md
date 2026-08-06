# Factoradic evidence digest

Status ledger for factoradic probes on known Bitcoin puzzle keys (puzzles 1–70 unless noted).

---

## CLAIM: Factoradic native-lead pub/private pairing

**Status: FALSIFIED** as a pub/private pairing invariant.

### Compact claim line

> Native \(m=n\) factoradic lead fractions give \(r=0.61\), but random and shuffled nulls produce similar correlations (\(p\approx 0.14\)–\(0.24\)); therefore the effect is explained by common bit-width/factoradic drift rather than paired public/private structure.

### Operational definition (still valid as a comparison rule)

\[
Px_{\mathrm{lead}}(n)=\left\lfloor\frac{Px}{2^{L-n}}\right\rfloor,\qquad L=\mathrm{bitlength}(Px)
\]

i.e. native-normalize \(Px\), then retain exactly \(n\) leading bits — not fixed-width lead bits, and not the low \(n\) bits.

### Observed (real pairing)

| metric | value |
|--------|------:|
| \(r\) | \(+0.610\) |
| close (\(\|\Delta\mathrm{frac}\|<0.1\)) | \(0.614\) |
| MAE | \(0.135\) |
| permutation \(p\) (paired shuffle of fractions) | \(0.0025\) |
| holdout train \(1\)–\(50\) / test \(51\)–\(70\) | \(r=0.561\) / \(0.726\) |

Offset \(c=0\) (\(n\ge 8\)): \(r=0.634\). Secondary \(c=4\): \(r=0.390\) (weaker; intervening offsets oscillate — not a ridge).

def256 (\(L=256\)) at \(m=n\): \(r\approx 0.186\) — fails; native width is required for the *apparent* effect.

### Decisive nulls (falsification)

| null | mean \(r\) | \(p(\|r\|\ge 0.61)\) |
|------|----------:|--------------------:|
| A: random 256-bit → native \(m=n\) | \(+0.527\) | \(0.24\) |
| B: random exact \(n\)-bit ints | \(+0.519\) | \(0.21\) |
| C: shuffle real \(Px\) across puzzles | \(+0.484\) | \(0.14\) |
| D: A residualized (linear \(n\) removed) | \(+0.494\) vs residual real \(0.584\) | \(0.23\) |
| E: random \(n\)-bit \(d'\) vs \([d']G.x\) | \(+0.528\) | \(0.24\) |

Close-rate under A: null mean \(0.631\) **beats** real \(0.614\).

### What remains true

- The **sawtooth / factoradic ladder** in private-key representation is real.
- Native \(m=n\) is a well-defined **same-scale** factoradic comparison.
- Apparent tracking comes from **shared progression with \(n\)**, not from \(d\mapsto [d]G_x\).

### What is closed

- Native-lead factoradic alignment as an EC coupling / pairing invariant.
- Fixed-width and proportional lead windows as stronger alternatives (no stable ridge under either width definition).
- **Further tuning of lead width / offsets / thresholds** — stop; that mines the same artifact.

### Policy going forward (filter, not solver)

Three products of the failed idea:

| Product | Role |
|---------|------|
| Frozen false positive | Archive so native-\(n\) lead is not rediscovered |
| False-positive benchmark | \(0.610-0.485=0.125\) with \(p\approx 0.15\) — ordinary coincidence shape, not a magical cutoff |
| Promotion gate | Real relation must break when \(d\) is attached to the wrong public point |

**Laboratory rule:**

```text
"Looks similar"  ≠  "depends on the correct pairing."
Ask:  P_i = [d_i]G  versus  P_π(i) ≠ [d_i]G
Need: score_real strong, score_shuffled ordinary, Δ unusually large.
```

**Pre-register** each \(F\) before peeking (`logs/prereg/F_PREREG_TEMPLATE.md`):
formula, domains \(p\)/\(N\), score, expected direction, parameters, holdout, nulls.

**Exclude trivial classes:** \(F=\mathbf{1}\{P=[d]G\}\) (DL recompute) and formulas implied by \(y^2=x^3+7\pmod p\) (curve membership alone).

**Promotion gate** (all required):

```text
advantage > 0.12
p_shuffle < 0.01
beats random n-bit
beats random EC pairs
holds out-of-sample
direction consistent across puzzle ranges
```

Worthwhile middle ground: compact \(F(d,Px,Py)\) not guaranteed by curve membership, destroyed by permutation.

Harness: `pairing_advantage_filter.py` · gate: `logs/PAIRING_PROMOTION_GATE.md` · prereg: `logs/prereg/`

### Candidates evaluated under the gate

| ID | Name | Verdict | Δ | p_shuffle | note |
|----|------|---------|--:|----------:|------|
| F-20260709-01 | band_floor_translation | **FAIL** | −0.069 | 0.57 | After removing \(2^{n-1}\), \(\phi(u)\) vs \(\phi((Q_x+Q_y)\bmod p)\) shows no pairing fingerprint |
| F-20260709-02 | mersenne_carry_ladder | **FAIL** | \(M=0.31\) | \(p_{\mathrm{global}}=0.53\) | **Mersenne offset rescue — FALSIFIED.** Searching \(A_j=2^j-1\) across 257 rungs does not rescue locked \(\phi(u)\leftrightarrow\phi((Q_x+Q_y)\bmod p)\); global \(p=0.53\), train/holdout direction reverses, hinge \(j=n{-}1{\to}n\) null |
| F-20260709-03 | band_floor_tangent_slope | **FAIL** | −0.145 | 0.23 | Replaced feature with \(T(Q)=3Q_x^2(2Q_y)^{-1}\); no pairing fingerprint; train/test advantage sign flip |
| F-20260709-04 | band_floor_doubled_x | **FAIL** | −0.025 | 0.80 | Sibling \(X_2(Q)=T^2-2Q_x\); null under pairing gate |
| F-20260709-05 | glv_orbit_mutual_information | **FAIL** | 0.000 | 1.00 | Locked argmin GLV labels: \(a\equiv 0\) for all puzzle-scale \(d\) (degenerate); \(I(a;b)=0\) identically |
| F-20260709-06 | adjacent_hamming_coupling | **FAIL** | +0.047 | 0.73 | Neighbor Hamming rates (compressed SEC); no local private→public similarity; train/test sign flip |

**Strategic pivot:** stop asking coordinates to resemble \(d\); start testing constraints on \(k\) inside ECDSA (\(sk\equiv z+rd\pmod N\)). Panel: `logs/SOLVED_NONCE_PANEL.*` (82 verified). Lab: `logs/K_CONSTRAINT_LAB.md`.

| ID | Name | Verdict | note |
|----|------|---------|------|
| K-00 | panel_admissibility | diagnostic | 68 blockstream + 14 hashkeys; use \(k^\star\); LOSO required |
| K-01 | orbit_safe_byte_bin | **FAIL** | holdout retention 0.22 ≈ random; byte-bin clustering dead |
| K-02 | rfc6979_deterministic_id | **ATTRIBUTION** | hashkeys partial spend **14/14** RFC6979; blockstream 30/68 mixed; not a universal P135 sieve |
| K-03 | hashkeys_batch_attribution | **ATTRIBUTION_CONFIRMED** | 14/14 on tx `17e4e323…`; P135 co-located (supported, not proven); validator only — does not narrow keyspace |

### Creator-side generator (left nonce lab)

| ID | Name | Verdict | note |
|----|------|---------|------|
| G-01 | creator_payload_lcg_64 | **FAIL** | \(a\Delta_1\equiv\Delta_2\pmod{2^{64}}\) has no solution: \(\gcd(\Delta_1,2^{64})=2\nmid\) odd \(\Delta_2\) |
| G-02 | sha256_chained_puzzle_keys | **FAIL** | 0/11 edges exact; first miss 75→80; parameter-free SHA-256 chain CLOSED |
| G-03 | payload_serial_dcor_gate | **FAIL** | A p=0.84, B p=0.65; both below null p99; invent-another-formula cycle CLOSED |

Cheap documented failure — as designed.

**Closed branch:** “wrong offset, same feature.” Two experiments agree:

\[
\boxed{\text{factoradic phase of }Q_x+Q_y\text{ does not encode the attached scalar}}
\]

Stop changing offsets for the coordinate-sum feature. Next candidates must replace the **feature**, not the translation amount.

### Artifacts

- Archive: `ARCHIVE/briefcase/factoradic_native_lead_falsified/`
- `logs/prereg/F-20260709-01*`
- `logs/F-20260709-01_band_floor_result.txt`
- `f_20260709_01_band_floor.py`
- `logs/FACTORADIC_LEAD_SWEEP_BOTH_DEFS.txt`
- `logs/FACTORADIC_NATIVE_LEAD_NULL.txt`
- `logs/PAIRING_ADVANTAGE_FILTER_CONTROL.txt`
- `pairing_advantage_filter.py`

---

## Related open / standing

| item | status |
|------|--------|
| Factoradic ladder / sawtooth on \(d\) (1–70) | standing representation fact / null model |
| Native \(m=n\) lead as control feature | keep; expect FAIL on pairing-advantage filter |
| F-20260709-01 band-floor translation | **FAIL** — no compact fingerprint after floor removal |
| F-20260709-02 Mersenne carry ladder | **FAIL** — \(p_{\mathrm{global}}=0.53\); offset search does not rescue locked feature |
| F-20260709-03 band-floor + \(T(Q)\) | **FAIL** — group-law tangent feature also null under pairing gate |
| F-20260709-04 band-floor + \(X_2(Q)\) | **FAIL** — doubled-\(x\) sibling also null |
| F-20260709-05 GLV orbit \(I(a;b)\) | **FAIL** — scalar argmin degenerate (\(a\equiv 0\)) on puzzle keys; MI vacuous |
| F-20260709-06 adjacent Hamming | **FAIL** — local private binary change does not couple to local public SEC change |
| **Pivot** | ECDSA nonce \(k\) constraints — see `K_CONSTRAINT_LAB.md` |
| **S-01** range-DLP kangaroo calibration | **PASS** — oracle + ladder 35/40/45; Python ref correct; no P135 promotion — `LEDGER_S01_range_dlp_calibration.md` |
| **S-02** native Kangaroo equivalence | **PASS** (CPU) — 40/40 exact; checkpoint PASS; \(T_{135}\sim 10^{5}\)–\(10^{6}\) CPU-yr — `LEDGER_S02_native_kangaroo_equivalence.md` |
| **S-03** feasibility / bit-cut gate | **LOCKED** — lead must remove ~40–57 verified bits; else not operationally relevant — `LEDGER_S03_feasibility_boundary.md` |
| **S-04** lead-to-bitcut audit | **EVALUATED** — 17 leads, **0** verified bits; decisive Q unanswered by any surviving claim — `LEDGER_S04_lead_to_bitcut_audit.md` |
| **S-05** new-lead admission gate | **LOCKED / FROZEN** — no run without \((F,S,\|S\|,\mathrm{justification})\) — `LEDGER_S05_new_lead_admission_gate.md` |
| **P71-S01** address-scanner calibration | **PASS** (Python ref) — oracle/solved/checkpoint — `LEDGER_P71_S01_scanner_calibration.md` |
| **P71-S02** scanner feasibility boundary | **UPDATED** — measured CPU \(R=1.33\times10^{7}\)/s; 1-year mean cut ≈20.4 bits; launch **NO** — `LEDGER_P71_S02_feasibility_boundary.md` |
| **P71-S03** native/GPU scanner equivalence | **PASS** — KeyHunt CPU \(R_{\mathrm{sust}}\approx1.33\times10^{7}\); OpenCL iGPU (HD 530) \(R_{\mathrm{sust}}\approx4.59\times10^{6}\) (slower); CUDA N/A — `LEDGER_P71_S03_native_gpu_equivalence.md` |
| **Log-ratio cross-puzzle** \(d\log a/\log b\) | **NULL** — \(F\approx d\) tautology; \(F/d\) fails pairing gate (\(p\sim0.4\)–\(0.97\)); **0 bits** — `LEDGER_LOG_RATIO_FALSIFICATION.md` |

### Project freeze (2026-07-10)

\[
d_{135}\in[2^{134},2^{135}),\quad W=2^{134},\quad b_{\mathrm{removed}}=0.
\]

> The tested factoradic, creator-sequence, curve-derived, transaction-derived, barcode, tax-math, echo, rotation, and residue hypotheses do not presently exclude any private-key candidate within the known Puzzle 135 interval.

\[
\boxed{\text{No new run without a preregistered explicit set and a measurable bit cut.}}
\]

### Puzzle 71 operational track

\[
2^{70}\le d_{71}\le 2^{71}-1,\quad W=2^{70},\quad
\text{addr}=\texttt{1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU}.
\]

No pubkey ⇒ linear hash160 scan (avg \(2^{69}\) tests), **not** kangaroo.  
Legacy shelf2 hunters are frozen unless they supply explicit \(S\).

**Stack:** P71-S01 PASS · P71-S02 UPDATED (CPU \(R=1.33\times10^{7}\)/s) · P71-S03 PASS (CPU + OpenCL iGPU measured; CUDA N/A) · Launch **NO**.

\[
T_{\mathrm{mean}}\approx 1.41\times 10^{6}\ \text{years},\quad
b_{\mathrm{cut}}(1\text{ year mean})\approx 20.4\text{ bits},\quad
b_{\mathrm{removed}}=0.
\]

\[
\boxed{\text{Scanner ready; search not economically ready.}}
\]

\[
\boxed{\text{No P71 experiment unless it defines an explicit }S\subseteq[2^{70},2^{71})\text{ or a new GPU/OpenCL calibration.}}
\]
| Full-field \(Px\) factoradic vs \(d\) | no link (\(\mathrm{corr}\approx 0\)) |
| Puzzle 71 / 135 ECDLP | open; orthogonal to this claim |
