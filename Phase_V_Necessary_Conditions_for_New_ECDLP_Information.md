# Phase V — Necessary Conditions for New ECDLP Information

**Status:** Phase IV frozen (\(b'=0\) beyond GLV). Do not rerun Phase IV.  
**Out of scope:** \(q_x=q_u\), orientation bridges, decimal \(\Phi\) operators, generic correlation.  
**Parents:** `Information_Theoretic_Consequences_Cube_Root_Lift_Algebra.md`, Phase III.

---

## One-sentence answer

Any invariant that factors through the unordered three-\(x\) GLV orbit is **orbit-only** and **cannot** give \(b'>0\); a theorem with \(b'>0\) must supply a **publicly computable** quantity that is **not** constant on the sixfold geometric orbit, or a **conditional** constraint outside that orbit (signature / nonce / new \(p\)–\(N\) bridge).

---

# Section 1 — Definition of a valid leak

Let \(P=dG\) with \(d\in\{1,\ldots,N-1\}\). Write \(\sim_{\mathrm{GLV}}\) for the equivalence

\[
d\;\sim_{\mathrm{GLV}}\;
\lambda d,\;
\lambda^2 d,\;
-d,\;
-\lambda d,\;
-\lambda^2 d
\pmod N
\]

(nonzero residues; classes of size \(6\) for generic \(d\)).

**Definition 1.1 (Valid leak).** A pair of maps \((I,J)\) is a **valid leak** if all of the following hold:

1. **Public computability.** \(I(P)\) is computed from public data
   \(\{x,y,r,p,N,\beta,\lambda,\Delta\}\) (and curve constants) without unknown-scalar multiplication and without solving ECDLP.
2. **Scalar dependence.** The composition \(d\mapsto I(dG)\) is not a constant function on \(\{1,\ldots,N-1\}\).
3. **Orbit refinement.** \(J\) (equivalently \(d\mapsto I(dG)\)) is **not** constant on \(\sim_{\mathrm{GLV}}\)-classes *in a way that fails to further partition the quotient*: more precisely, the level sets of \(d\mapsto I(dG)\) must be a **strict refinement** of the partition into \(\sim_{\mathrm{GLV}}\)-classes, **or** — when the search model already quotients by \(\sim_{\mathrm{GLV}}\) — the map must induce a **nontrivial partition of the set of classes**.
4. **Holdout exactness.** The identity \(I(dG)=J(d)\) is symbolic and holds for all admissible \(d\) (not a fitted correlation).
5. **Complexity gain.** If \(I\) takes \(m\) values with known multiplicities \(n_1,\ldots,n_m\) on the search domain of size \(2^k\) (or on the GLV quotient of size \(\approx 2^{k}/\mathrm{6}\)), then:
   - **worst-case** bits: \(b_{\mathrm{wc}}=\log_2\!\bigl(2^k/\max_i n_i\bigr)\) (equivalently reduction to the largest fibre);
   - **average-case** entropy: \(b_{\mathrm{avg}}=H(I)\) under the uniform prior on the domain;
   - for **balanced** \(m\)-ary \(I\): \(b_{\mathrm{avg}}=\log_2 m\).

**Clarification (public \(P\) model).** If \(P\) is fully known, then \(H(I\mid P)=0\) for every publicly computable \(I\). In that model, \(b'>0\) requires that \(I\) define a **search filter** whose fibres are smaller than the GLV fibres already used — i.e. refinement of \(\sim_{\mathrm{GLV}}\) — not merely a function of \(P\).

**Corollary 1.2.** An invariant constant on each geometric sixfold orbit of \(P\) cannot refine \(\sim_{\mathrm{GLV}}\) (Section 5). At best it labels whole classes; with public \(P\), that label is already known and yields \(b'=0\).

---

# Section 2 — Impossibility tests and classification

**Test 2.1 (Orbit-only test).**  
If there exists \(K\) such that

\[
I(P)=K\bigl(\{\,P,\psi(P),\psi^2(P),-P,-\psi(P),-\psi^2(P)\,\}\bigr)
\]

for all affine \(P\), then \(I\) is **orbit-only**: it is constant on each sixfold geometric orbit, hence \(d\mapsto I(dG)\) is constant on each \(\sim_{\mathrm{GLV}}\)-class. Such an \(I\) **does not refine** the sixfold scalar orbit.

**Theorem 2.2 (Classification of known invariants).**

| Invariant | Verdict | Reason |
|-----------|---------|--------|
| Field trace of \(\mathcal{X}\) | **orbit-only** | Constant \(0\) on all nonzero orbits |
| \(e_1,e_2\) of \(\mathcal{X}\) | **orbit-only** | Constant \(0\) |
| Norm / \(x^3\) / \(\mathrm{disc}(T^3-x^3)\) | **orbit-only** | Function of unordered \(\mathcal{X}\) |
| Symmetric polynomials of \(\mathcal{X}\) | **orbit-only** | Same |
| Orbit sum \(S_x=q_x p\) | **orbit-only** | Function of unordered reduced \(\mathcal{X}\) |
| Carry class \(q_x\) | **orbit-only** | \(q_x=S_x/p\); constant on sixfold (Phase IV Thm 1.1) |
| Edge carry \(c_x\) | **orbit-only** | \(q_x=1+c_x\); same |
| Unordered set \(\mathcal{X}\) | **orbit-only** | Definition of the geometric \(x\)-orbit |
| Canonical sixfold representative of \(P\) | **orbit-only** | By construction a section of the orbit quotient |
| \(y\)-branch (sign of \(P\)) | **orbit-only** *relative to sixfold* | Distinguishes \(P\) vs \(-P\), but both lie in the **same** sixfold class; does not refine \(\sim_{\mathrm{GLV}}\) as a scalar partition beyond size \(6\) already counted |
| \(\Delta\) lift class / \(r\leftrightarrow R_x\) ambiguity | **not a function of \(P=dG\) alone** in the pubkey model; for signatures see §4 | Concerns \(R_x\in[0,p)\) vs \(r=R_x\bmod N\); not an invariant of the pubkey point’s \(\mathcal{X}\) |
| \(q_u\), \(\mathcal{U}(d)\), scalar carry | **not publicly computable** | Requires \(d\). On the scalar side: \(q_u\) is constant on the \(\mu_3\)-orbit \(\{d,\lambda d,\lambda^2 d\}\) and satisfies \(q_u(-d)=3-q_u(d)\) (sign flip). Even as a scalar function it is **not** available from public \(P\); see §4. |
| Map \(d\mapsto d\) | **equivalent to ECDLP** | — |

**Theorem 2.3.** Every invariant in the frozen cube-root **lift** algebra on the \(p\)-side that is a symmetric function of the reduced triple \(\mathcal{X}\) is orbit-only. None is scalar-refining in the sense of Definition 1.1(3) beyond GLV.

---

# Section 3 — Required bridge theorem (precision)

**Missing theorem form.**

\[
F_p(x,y,\beta,\Delta)
\;=\;
F_N(d,\lambda)
\quad\text{for all }P=dG,
\]

where:

- \(F_p\) is publicly computable (Def. 1.1(1));
- \(F_N\) is **not** constant on \(\sim_{\mathrm{GLV}}\)-classes **or** induces a nontrivial partition of the class set with \(H(F_N)>0\) usable as a filter with public \(P\) still implying the filter equals something **not** already determined by the sixfold orbit of \(P\).

**Tension.** If \(F_p\) is a function of the sixfold orbit of \(P\), then \(F_N(d)\) equals that orbit label, which **is** constant on \(\sim_{\mathrm{GLV}}\) — so condition (3) fails. Therefore:

**Proposition 3.1 (Necessary shape).**  
Any bridge with \(b'>0\) in the public-\(P\) search model must use an \(F_p\) that is **not** a function of \(\{\pm P,\pm\psi(P),\pm\psi^2(P)\}\) alone — e.g. it must involve:

- signature data \((r,s,z)\), or
- an auxiliary public value not determined by that orbit, or
- a constraint that is **conditional** (Section 4),

or else it must refine search in a model where \(P\) is **not** fully known (excluded here).

**Allowed derivation sources only:**

- curve equation \(y^2=x^3+7\);
- endomorphism \(\psi(P)=[\lambda]P\), \(\psi(x,y)=(\beta x,y)\);
- ECDSA \(sk\equiv z+rd\pmod N\);
- \(r=R_x\bmod N\), \(p=N+\Delta\);
- \(\Phi_3(t)=t^2+t+1\);
- exact lift ambiguity for \(R_x\).

**No numerical search for \(F\).**

**Open (not claimed).** Existence of such an \(F_p\) outside orbit-only data. Phase V does **not** construct one.

---

# Section 4 — Signature-specific information (conditional)

ECDSA: \(s k \equiv z + r d\pmod N\), with \(R=kG=(R_x,R_y)\), \(r=R_x\bmod N\).

Prior on \(d\): uniform in \(\{1,\ldots,N-1\}\) (or on GLV quotient). Treat each row as **if** the listed constraint is known exactly; do not assume it exists in the wild.

| Conditional constraint | Effect on \(d\) | Bits (exact form) |
|------------------------|-----------------|-------------------|
| Full nonce \(k\) known | \(d\equiv r^{-1}(sk-z)\pmod N\) | Solves for \(d\): \(b=k_{\mathrm{prior}}\) (ECDLP-trivializing) |
| \(k\) in an interval of length \(L\) | \(d\) constrained by linear congruence with unknown in interval (hidden-number / lattice regime) | Not a fixed \(b\) from cube-root algebra; outside frozen theorems. **Open** as exact \(2^{k-b}\) without lattice hypotheses |
| \(k\) known only up to \(\sim_{\mathrm{GLV}}\) (nonce orbit class) | \(6\) candidate \(k\); each gives a candidate \(d\) | At most \(\log_2 6\) bits vs full \(k\) unknown; **does not** exceed GLV accounting already used on the nonce side |
| \(R_x\) lift branch known when \(r<\Delta\) (\(R_x\in\{r,r+N\}\)) | Selects which of two affine \(x\)-lifts; constrains \(kG\)'s \(x\) among two possibilities | At most \(1\) bit on the **nonce point’s** lift, not on \(d\) directly; couples to \(d\) only through ECDSA. **Conditional \(\le 1\) bit on lift**, not a proven \(b'>0\) on \(d\)-space from pubkey algebra alone |
| Cube-root class of \(r\bmod N\) (i.e. \(\mathcal{U}(r)\) or \(q_u(r)\)) | \(r\) is public in ECDSA, so this is public — \(H=0\) given the signature | \(b'=0\) additional (already known from \(r\)) |
| Carry class \(q_u(d)\) | Not public | On scalars: constant on \(\{d,\lambda d,\lambda^2 d\}\), flips under \(d\mapsto -d\). **If** it were public and used to split each sixfold class into two sign halves, that would be at most \(1\) bit refining \(6\to 3\) — still not available from pubkey/\(\mathcal{X}\) algebra. Status for public \(P\): **no bits** |
| Relation “pubkey orbit label \(=\) nonce orbit label” | Would constrain \((d,k)\) jointly | **Not a theorem** of the frozen algebra (Phase IV refuted \(q_x=q_u\)). Status: **impossible** as that identity; other relations **open** |

**Theorem 4.1.** Among constraints that are theorems of the frozen cube-root lift algebra alone, none yields a proven \(b'>0\) on \(d\) given a public verification key \(P\). Signature-side quantities that are public (\(r\), and functions of \(r\)) give \(H(\cdot\mid\mathrm{sig})=0\).

---

# Section 5 — Obstruction theorem (lower bound)

**Theorem 5.1 (Obstruction — unordered three-\(x\) orbit).**  
Let \(I\) be any function of the unordered set

\[
\mathcal{X}(P)=\bigl\{x,\ \beta x\bmod p,\ \beta^2 x\bmod p\bigr\}
\]

(equivalently: any symmetric function of the three reduced residues; including \(q_x\), \(c_x\), \(S_x\), field trace, norm, elementary symmetric polynomials, \(T^3-x^3\), and its discriminant). Then:

1. \(I(P)=I(Q)\) whenever \(Q\) lies in the sixfold geometric orbit of \(P\).
2. Consequently \(I(dG)=I((\lambda d)G)=I((-d)G)=\cdots\), so \(d\mapsto I(dG)\) is constant on each \(\sim_{\mathrm{GLV}}\)-class.
3. Therefore \(I\) **cannot refine** the sixfold scalar orbit: it reveals neither the GLV position (\(\{1,\lambda,\lambda^2\}\)-coset representative) nor the sign inside that class.
4. In the public-\(P\) model, \(I(P)\) is determined by \(P\), and search reduction beyond \(2^{k-\log_2 6}\) satisfies \(b'=0\).

**Proof.**  
(1) Negation preserves \(x\). The map \(\psi\) sends \(x\mapsto\beta x\bmod p\), permuting \(\mathcal{X}\). Hence every function of the unordered set \(\mathcal{X}\) is constant on \(\{\pm P,\pm\psi(P),\pm\psi^2(P)\}\).  
(2) Under \(P=dG\) and \(\psi(P)=[\lambda]P\), that geometric orbit is \(\{(\pm\lambda^j d)G:j=0,1,2\}\).  
(3) Refining \(\sim_{\mathrm{GLV}}\) would require a non-constant function on some class; contradicted by (2).  
(4) Phase IV accounting: baseline after GLV is \(2^{k-\log_2 6}\); an orbit-only label adds no further fibre refinement when \(P\) is known.

**Corollary 5.2.** Exact structure for \(q_x\), carries, and symmetric polynomials is compatible with \(b'=0\): they are nontrivial as **algebra** and trivial as **GLV-refining information**.

**Corollary 5.3 (Where new information must live).**  
Any theorem with \(b'>0\) must use data **outside** the unordered three-\(x\) orbit — e.g. ordered/signed data that breaks sixfold constancy **and** still yields a scalar filter (hard under public \(P\)), signature/nonce constraints, or a bridge \(F_p=F_N\) whose \(F_p\) is not an \(\mathcal{X}\)-symmetric function.

---

# Section 6 — Output artifacts

| File | Role |
|------|------|
| `Phase_V_Necessary_Conditions_for_New_ECDLP_Information.md` | This document |
| `phase_v_conditions_verify.py` | Theorem / proof / verification |
| `logs/PHASE_V_CONDITIONS_VERIFY.txt` | Log |

---

# Final table

| Candidate theorem | Publicly computable? | Refines sixfold orbit? | Bits gained | Proven / impossible / open |
|-------------------|----------------------|-------------------------|-------------|----------------------------|
| \(I=q_x\) / \(c_x\) / \(S_x\) | Yes | No | \(b'=0\) | **Impossible** (Thm 5.1) |
| Field trace / \(e_1,e_2\) of \(\mathcal{X}\) | Yes | No | \(0\) | **Impossible** (constant / Thm 5.1) |
| Norm \(x^3\), \(\mathrm{disc}\), sym. polys of \(\mathcal{X}\) | Yes | No | \(b'=0\) | **Impossible** (Thm 5.1) |
| Unordered \(\mathcal{X}\) / canonical sixfold rep | Yes | No | \(b'=0\) | **Impossible** (by definition / Thm 5.1) |
| \(y\)-sign alone | Yes | No (same sixfold class) | \(b'=0\) beyond \(\log_2 6\) | **Impossible** as extra beyond GLV |
| \(q_u\) / scalar \(\mathcal{U}\) | No | Sign-half only (\(\mu_3\)-constant; flips under negation) | \(0\) from public \(P\); at most \(1\) if \(q_u\) were an oracle | **Not publicly computable** |
| Identity \(q_x(P)=q_u(d)\) | Would be | — | — | **Impossible** (Phase IV; not revisited) |
| \(\Delta\) lift bit from pubkey \(P\) only | N/A | No | \(0\) | **Impossible** as pubkey \(\mathcal{X}\)-invariant |
| \(R_x\) lift branch given ECDSA \(r\) with \(r<\Delta\) | Yes (branch is a choice / oracle) | Acts on nonce \(x\)-lift | \(\le 1\) bit on lift (conditional) | **Open** as exact \(d\)-space \(2^{k-b}\) |
| Full nonce \(k\) known | Conditional | Solves \(d\) | Full prior | **Proven** conditional (ECDSA algebra), not from cube-root lifts |
| Nonce known up to GLV class | Conditional | \(\le\log_2 6\) on \(k\) | \(\le\log_2 6\) | **Proven** bound; not \(b'>0\) beyond GLV |
| Hidden-number interval on \(k\) | Conditional | Lattice-dependent | Not fixed here | **Open** (outside frozen algebra) |
| Bridge \(F_p(x,y,\beta,\Delta)=F_N(d,\lambda)\) with \(F_p\) not \(\mathcal{X}\)-symmetric | Required form | Required | Would need \(H>0\) fibre proof | **Open** (necessary form in §3; no construction) |
| Any symmetric-\(\mathcal{X}\) invariant | Yes | No | \(b'=0\) | **Impossible** (Thm 5.1) **obstruction** |

---

## Success criterion

**B achieved:** a broad class of candidates — all invariants depending only on the unordered three-\(x\) orbit — **can never** give \(b'>0\).

\[
\boxed{
\text{Any invariant depending only on the unordered three-}x\text{ orbit cannot reveal the scalar’s GLV position or sign.}
}

\]

No claim of \(b'>0\). No new identity hunt inside the closed carry algebra.
