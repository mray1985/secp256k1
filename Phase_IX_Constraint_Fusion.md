# Phase IX — Constraint Fusion

**Status:** Phases III–VIII frozen. No new single-source invariants.

**Question.** Can two individually non-informative (beyond GLV) exact results become informative **when combined** — not by correlation search, but by proving the intersection is strictly stronger than either conjunct alone?

**Public transcript.** For a standard signed key:

\[
T=(P,\,r,\,s,\,z),\qquad P=dG,
\]

with ECDSA \(sk\equiv z+rd\pmod N\). Optional non-transcript oracles (e.g. full nonce point \(R\)) are classified separately.

---

# Information vocabulary

A quantity \(X\) is **transcript-determined** if there is an algorithm with \(X=f(T)\) (using only public curve constants \(\beta,\lambda,p,N,\Delta\)).

**Lemma 0.1.** If \(X=f(T)\) and \(Y=g(T)\), then for any secret \(S\in\{d,k,(d,k)\}\),

\[
H(S\mid T,X,Y)=H(S\mid T).
\]

**Proof.** \(X,Y\) are functions of \(T\).

**Corollary 0.2.** Fusion of transcript-determined quantities never reduces entropy of \(d\) or \(k\) below the transcript baseline. In particular it cannot produce \(b'>0\) beyond what \(T\) and ECDSA already encode (plus classical GLV on orbit search).

---

# Section 1 — GLV orbit + lift regime + \(q_x\)

**Ingredients.**

| Piece | Determined by |
|-------|----------------|
| GLV class of \(P\) | \(P\) |
| \(q_x(P)\) | \(x(P)\) hence \(P\) |
| Lift regime of published \(r\) | \(r\) vs \(\Delta\) |

All three are transcript-determined when \(T\) includes \(P\) and \(r\).

**Theorem 1.1.** The conjunction

\[
\bigl(\text{GLV class of }P\bigr)
\;\wedge\;
\bigl(q_x(P)\bigr)
\;\wedge\;
\bigl(r?\Delta\text{ lift regime}\bigr)
\]

is transcript-determined. By Lemma 0.1 it adds **no** entropy reduction on \(d\) or \(k\) beyond \(T\).

**Theorem 1.2 (No cross-object miracle).**  
Lift regime concerns the **nonce residue** \(r\); GLV/\(q_x\) concern the **pubkey** \(P\). No identity of Phases III–VIII identifies them. Their conjunction is a product constraint (restrict \(P\)’s labels) × (label \(r\)’s regime), not a new equation coupling \(d\) to \(k\) beyond ECDSA.

**Classification:** logical conjunction only → **B** for this triple.

---

# Section 2 — Packed \(E\) + signature

Consider \((E(P),\,r,\,s,\,z)\) simultaneously.

**Theorem 2.1.** \(E(P)=x(P)\,p+y(P)\) is a bijection on affine coordinates (Phase VI). Hence

\[
\bigl(E(P),\,r,\,s,\,z\bigr)
\quad\text{carries exactly the same information as}\quad
\bigl(P,\,r,\,s,\,z\bigr)=T
\]

for affine \(P\). The fusion “packed \(E\) + signature” is **equal** to the transcript alone (plus serialization). Entropy of \((d,k)\) unchanged.

**Theorem 2.2.** Phase VII: \(E\bmod N\) is also transcript-determined. Including it in the fusion does not enlarge the constraint set beyond \(T\).

**Classification:** conjunction / re-encoding of \(T\) → **B**. Bits gained \(b'=0\).

---

# Section 3 — Public point + nonce point \((P,R)\)

**Case 3A — Only transcript \(T\) (usual).**  
\(R\) is not given; only \(r=R_x\bmod N\). Fusion \((P,R)\) is unavailable. Reducing to \((P,r)\) is §1–2.

**Case 3B — Oracle gives affine \(R=kG\).**  
Then \(T'=T\cup\{R\}\) (or \(T\) with \(R\) replacing the mere residue \(r\), subject to \(R_x\bmod N=r\)).

**Theorem 3.1.** Even given \((P,R,s,z)\) with \(R_x\bmod N=r\),

\[
sk\equiv z+rd\pmod N
\]

still relates two unknowns \((k,d)\). Knowing the points \(P=dG\) and \(R=kG\) does not yield \(k\) or \(d\) without solving ECDLP (or using the linear relation with one scalar known).

**Theorem 3.2.** Phase VIII: lift choice is settled once \(R\) is given. That removes \(\le 1\) bit of **lift encoding** ambiguity, already not a proven uniform halving of \(k\)-space. It is not a fusion **derived from** two Phase III–VII pubkey theorems; it is the oracle “give \(R\)”.

**Theorem 3.3.** No identity proved in III–VIII produces, from \((P,R)\) alone without ECDLP, a scalar restriction beyond:

- GLV on each point’s orbit,
- ECDSA linearity if \((r,s,z)\) present,
- lift fixed by \(R\).

**Classification:** As a **fusion of frozen public theorems** (without an \(R\)-oracle) → **B**. With an \(R\)-oracle → still no \(b'>0\) theorem on \(k,d\) beyond GLV + “one ECDLP instance for \(k\) if you solve it”.

---

# Section 4 — Constraint graph (pairwise fusion)

Nodes (frozen theorems):

1. Carry reconstruction / cube-root lifts  
2. GLV sixfold  
3. Lift theorem (\(R_x\leftrightarrow r\))  
4. Packed \(E\) (and \(E\bmod N\))  
5. ECDSA \(sk\equiv z+rd\)  
6. Phase V unordered-\(\mathcal{X}\) obstruction / Phase IV \(b'=0\) meta  

**Theorem 4.1 (Pairwise fusion table).**  
For every pair \(\{i,j\}\) among nodes that produce only transcript-determined outputs when applied to \(T\), the conjunction \(i\wedge j\) is transcript-determined (or a restatement of ECDSA + public labels). No pair implies a theorem that removes \((k,d)\) candidates beyond:

\[
2^{k}\to 2^{k-\log_2 6}
\]

(GLV orbit accounting) together with the single linear ECDSA relation already in \(T\).

| Pair | What conjunction gives | New scalar cut? |
|------|------------------------|-----------------|
| Carry + GLV | Orbit labels of \(P\) | No (\(b'=0\)) |
| Carry + Lift | \(q_x(P)\) and \(r?\Delta\) | No coupling |
| Carry + Packed \(E\) | Same as \(E\)/orbit of \(P\) | No |
| Carry + ECDSA | ECDSA + labels of \(P\) | No beyond ECDSA+\(T\) |
| GLV + Lift | Orbit of \(P\) + regime of \(r\) | No |
| GLV + Packed \(E\) | Serialization of orbit | No |
| GLV + ECDSA | Standard signed key | No beyond \(T\) |
| Lift + Packed \(E\) | \(r\)-regime + \(E(P)\) | No |
| Lift + ECDSA | Lift-invariant ECDSA (VIII) | No |
| Packed \(E\) + ECDSA | Equivalent to \(T\) (Thm 2.1) | No |
| Any + Phase V/IV meta | Obstruction statements | No positive \(b'\) |

**Theorem 4.2 (No emergent edge).**  
There is no proved identity \(F_i\wedge F_j\Rightarrow C\) where \(C\) is a scalar constraint not implied by \(F_i\), not implied by \(F_j\), and stronger than \(T\)+GLV on \((k,d)\). Pairwise fusion yields only **logical conjunction** of existing conclusions.

---

# Section 5 — What “stronger intersection” would have required

For outcome **A**, one would need a theorem schematically like

\[
I_1(T)=a,\quad I_2(T)=b
\quad\Longrightarrow\quad
d\in S
\]

or \(k\in S'\), with \(|S|\) strictly smaller than what ECDSA+\(T\)+GLV already force — and where the implication uses **both** \(I_1\) and \(I_2\) essentially.

All Phase III–VIII invariants eligible on \(T\) fail the premise “not already functions of \(T\)” or fail to constrain scalars beyond ECDSA’s one linear relation.

---

# Final table

| Fusion | Outcome | Beyond GLV \(b'\)? | Status |
|--------|---------|-------------------|--------|
| GLV + lift + \(q_x\) | Conjunction of transcript labels | \(0\) | **B** |
| \((E,r,s,z)\) | Equivalent to \(T\) | \(0\) | **B** |
| \((P,R)\) without \(R\) oracle | Not a public fusion | — | N/A → reduces to \(T\) |
| \((P,R)\) with \(R\) oracle | Lift fixed; ECDSA still 1 DoF; ECDLP for scalars | \(0\) from fusion of III–VIII | **B** for frozen graph |
| All pairwise theorem nodes on \(T\) | Conjunction only | \(0\) | **B** (Thm 4.1–4.2) |

---

## Success criterion

**B.** Every examined fusion of previously independent exact results is the logical conjunction (or re-encoding) of transcript-determined quantities with ECDSA; **no additional entropy reduction** on \(k\) or \(d\) beyond classical GLV and the single ECDSA line.

The obstruction through Phase VIII is **not** an artifact of studying sources one at a time: their **combinations**, under the public transcript, remain non-informative in the same sense.

---

## Artifacts

| File | Role |
|------|------|
| `Phase_IX_Constraint_Fusion.md` | This document |
| `phase_ix_constraint_fusion_verify.py` | Theorem / proof / verification |
| `logs/PHASE_IX_CONSTRAINT_FUSION_VERIFY.txt` | Log |

---

## Project stance after IX

Exact structure (carry, \(\Phi_3\), \(E\), lattices, lifts) stands. Information claim beyond GLV does not — singly or fused on the public transcript. Any future positive \(b'\) requires a source of constraint **not** transcript-determined by \((P,r,s,z)\) alone (or a new theorem outside this graph).
