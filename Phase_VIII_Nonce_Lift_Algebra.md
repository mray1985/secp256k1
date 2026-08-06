# Phase VIII — Nonce Lift Algebra

**Status:** Phases III–VII frozen. Do not reopen \(q_x/q_u\), carry, packed pubkey \(E\), decimals/lattices, or GLV-only identity hunts.

**Primary question.** Can the lift ambiguity \(R_x\in\{r,r+N\}\) (when \(r<\Delta\)) combine with ECDSA to remove \(k\) or \(d\) candidates beyond GLV?

**ECDSA convention (standard).** Signatures satisfy

\[
sk\equiv z+rd\pmod N
\]

i.e. \(s\equiv k^{-1}(z+rd)\pmod N\). (Not \(sk+rd\equiv z\).)

---

# Section 1 — Lift regimes for the nonce point

Let \(R=kG=(R_x,R_y)\) with reduced \(R_x,R_y\in\{0,\ldots,p-1\}\), and \(r=R_x\bmod N\).

**Theorem 1.1 (Signature lift; Phase II).**  
With \(p=N+\Delta\) and \(0\le R_x<p\):

| Regime | Conclusion |
|--------|------------|
| \(r\ge\Delta\) | \(R_x=r\) necessarily (unique) |
| \(r<\Delta\) | \(R_x\in\{r,\,r+N\}\cap[0,p)\) — both integers lie in range |

**Theorem 1.2.** The published signature integer is always the residue \(r\in\mathbb{Z}/N\mathbb{Z}\). The affine field coordinate is the lift \(R_x\in\mathbb{F}_p\cong\{0,\ldots,p-1\}\). These coincide as integers iff \(R_x<N\).

**Theorem 1.3 (Curve attachment).**  
Each viable lift \(X\in\{r,r+N\}\cap[0,p)\) may or may not admit \(Y\) with \(Y^2\equiv X^3+7\pmod p\). Lift admissibility as an affine secp256k1 \(x\)-coordinate is a curve condition, independent of the scalar equation in §3.

---

# Section 2 — Packed nonce \(E_R\)

**Definition.**

\[
E_R=R_x\,p+R_y.
\]

**Theorem 2.1 (Phase VII, lift-independent).**

\[
E_R\equiv r\Delta+R_y\pmod N
\]

for **both** admissible lifts \(R_x\in\{r,r+N\}\).

**Theorem 2.2.** Given public \(r\) and \(e_R=E_R\bmod N\),

\[
R_y\equiv e_R-r\Delta\pmod N,
\]

with the same \(\Delta\)-lift dichotomy on \(R_y\in[0,p)\) as in Phase VII Thm E.2. Knowing \(e_R\) (with \(r\)) is equivalent to knowing \(R_y\) up to at most one bit of lift ambiguity — not a new expression for \(k\).

---

# Section 3 — ECDSA and lifts

**Theorem 3.1 (Lift invariance of the scalar equation).**  
The ECDSA relation

\[
sk\equiv z+rd\pmod N
\]

is an identity in \(\mathbb{Z}/N\mathbb{Z}\). It depends on the residue \(r\), not on which lift \(R_x\in\{r,r+N\}\) is the affine \(x\)-coordinate of \(R\).

**Corollary 3.2.** The two geometric lifts (when \(r<\Delta\)) induce **the same** affine linear constraint on the pair \((k,d)\). They do **not** produce two different congruence classes for \(k\) or \(d\) inside the signature equation.

**Theorem 3.3 (Candidate map from \(k\)).**  
If \(r\) is invertible mod \(N\), then for each \(k\in(\mathbb{Z}/N\mathbb{Z})^\times\),

\[
d\equiv r^{-1}(sk-z)\pmod N
\]

is uniquely determined by \((k,r,s,z)\), independent of the \(R_x\) lift.

**Theorem 3.4 (Geometric filter vs algebraic filter).**  
The condition \((kG)_x\bmod N=r\) means

\[
(kG)_x\in\{r\}\quad\text{or}\quad(kG)_x\in\{r,r+N\}
\]

according as \(r\ge\Delta\) or \(r<\Delta\) (restricted to values that appear as affine \(x\)-coordinates). This filters **points** \(R=kG\). It does not alter Theorem 3.1’s linear relation. Given a full public \(R\), the lift is known and \(k\) remains an ECDLP instance.

---

# Section 4 — Recoverable-quantity classification

| Quantity | Publicly computable from \((r,s,z,Q)\)? | Signature-local? | Needs nonce \(k\) / point \(R\)? | Needs private \(d\)? |
|----------|----------------------------------------|------------------|----------------------------------|----------------------|
| \(r,s,z\) | Yes | Yes | No | No |
| Lift regime (\(r?\Delta\)) | Yes (compare \(r\) to \(\Delta\)) | Yes | No | No |
| Unique \(R_x\) when \(r\ge\Delta\) | As integer candidate \(r\) | Yes | Curve check that \(r\) is an \(x\)-coord | No |
| Which of \(\{r,r+N\}\) when \(r<\Delta\) | **No** (binary ambiguity) | — | Yes (true \(R\)) or ECDLP-scale search | No |
| \(E_R\bmod N\) | Only if \(R\) or \(R_y\) known | — | Yes | No |
| \(k\) | No | — | Yes (definition) | Via eq. with \(d\) |
| \(d\) | No | — | Via eq. with \(k\) | Yes |
| \(e_R\equiv r\Delta+R_y\) | Equivalent to \(R_y\) (mod lift) | — | Needs \(R_y\) or \(E_R\) | No |

---

# Section 5 — Entropy accounting

**Theorem 5.1 (Lift bit).**  
When \(r\ge\Delta\), lift entropy is \(0\) (unique \(R_x=r\)).  
When \(r<\Delta\), there are at most **two** integer candidates for \(R_x\). Absolute upper bound on information in knowing the correct lift:

\[
b_{\mathrm{lift}}\le 1\text{ bit}.
\]

This bit is about the **affine representative of \(x(R)\)**, not a theorem removing half of all \(k\in\mathbb{Z}/N\mathbb{Z}\) from the ECDSA line \(sk\equiv z+rd\).

**Theorem 5.2 (No automatic \(k\)-halving).**  
Let \(\mathcal{K}_r=\{k:(kG)_x\bmod N=r\}\). Passing from “unknown lift” to “known lift \(R_x=X_0\)” replaces \(\mathcal{K}_r\) by \(\{k:(kG)_x=X_0\}\), a subset. The index / density ratio depends on how often both lifts occur as group \(x\)-coordinates and on \(y\)-signs. There is **no** identity of the frozen algebra proving

\[
|\mathcal{K}_r|=2\cdot|\{k:(kG)_x=X_0\}|
\]

uniformly for all signatures. Hence one **cannot** claim a rigorous \(2^{k}\to 2^{k-1}\) on nonce space from lift alone without a separate density theorem (not available here; not estimated).

**Theorem 5.3 (Signature-equation obstruction).**  
Every constraint deduced solely from \(sk\equiv z+rd\pmod N\) (with public \(r,s,z\)) is invariant under \(R_x\mapsto R_x\pm N\) whenever both are considered as preimages of \(r\). Therefore lift choice does not remove \((k,d)\) candidates from that linear equation beyond what \(r\) already encodes.

---

# Section 6 — Obstruction / success criterion

**Success criterion.** A theorem removing valid \(k\) or \(d\) candidates **beyond GLV**.

**Theorem 6.1 (Phase VIII obstruction).**  
Within the nonce-lift + ECDSA fragment studied here:

1. Lift ambiguity is at most a binary choice on \(R_x\) when \(r<\Delta\) (\(b_{\mathrm{lift}}\le 1\)), concerning affine encoding.
2. The ECDSA scalar equation is lift-invariant (Thm 3.1–3.3).
3. \(E_R\bmod N\) adds no independent \(k\)-constraint beyond \(R_y\) (Thm 2.1–2.2).
4. No proven reduction of the form \(2^{k}\to 2^{k-b}\) on \(k\) or \(d\) with \(b>0\) beyond classical GLV, arising from lift algebra alone.

**Verdict: B** for this branch — obstruction. Close nonce-lift-as-ECDSA-splitter.

GLV sixfold on the nonce point remains the only rigorous orbit reduction already counted elsewhere:

\[
2^{k}\;\longrightarrow\;2^{k-\log_2 6}
\]

in the orbit-search model — not improved by Phase VIII.

---

# Final table

| Candidate | Public? | Changes ECDSA \((k,d)\) line? | Refines \(k\) beyond GLV? | Bits claimed | Status |
|-----------|---------|-------------------------------|---------------------------|--------------|--------|
| Lift regime \(r?\Delta\) | Yes | No | No | \(0\) on scalars | Proven |
| Unique \(R_x=r\) (\(r\ge\Delta\)) | Candidate | No | No | \(0\) | Proven |
| Branch \(\{r,r+N\}\) (\(r<\Delta\)) | No | No (same \(r\)) | At most geometric filter; no uniform \(b=1\) on \(k\) | \(\le 1\) on lift only | Proven bound; not DL cut |
| \(E_R\bmod N\) | From \(R\) | No | No | \(0\) | Proven |
| \(d=r^{-1}(sk-z)\) | Needs \(k\) | Definition | Equivalent to knowing \(k\) | — | Standard ECDSA |
| Lift + ECDSA alone removes \(k/d\) beyond GLV | — | — | **No** | \(b'=0\) | **Obstruction 6.1** |

---

## Artifacts

| File | Role |
|------|------|
| `Phase_VIII_Nonce_Lift_Algebra.md` | This document |
| `phase_viii_nonce_lift_verify.py` | Theorem / proof / verification |
| `logs/PHASE_VIII_NONCE_LIFT_VERIFY.txt` | Log |

---

## Freeze

Close the packed-\(E\) family (VII) and the nonce-lift-as-scalar-splitter branch (VIII). Further work needs a source of constraints **outside** public-point / lift-only / \(r\)-only linear ECDSA algebra — or must accept that the framework stops at GLV \(b=\log_2 6\), \(b'=0\).
