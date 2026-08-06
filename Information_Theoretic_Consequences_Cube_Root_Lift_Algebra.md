# Information-Theoretic Consequences of Primitive Cube-Root Lift Algebra

**Phase IV — Information Flow**  
**Status:** Correlation phase closed. Carry reconstruction and forced lifts frozen.  
**Parents:** `Algebra_Primitive_Cube_Root_Lifts_ABSTRACT.md`, `Phase_III_Inverse_Algebra.md`  
**Method:** theorem → proof → numerical verification. No patterns, guesses, correlations, or heuristics.

---

## One-sentence answer

The current theorems reveal **no information about an unknown scalar beyond the known sixfold GLV symmetry**: every proven invariant that is computable from a public point \(P\) is constant on the sixfold orbit and is a deterministic function of \(P\), so it contributes **\(b'=0\)** additional search bits beyond \(b=\log_2 6\).

---

# Section 1 — Orbit invariants

## Objects

\[
\mathcal{X}=\bigl\{x,\ \beta x\bmod p,\ \beta^2 x\bmod p\bigr\},
\qquad
\mathcal{U}=\bigl\{u,\ \lambda u\bmod N,\ \lambda^2 u\bmod N\bigr\}.
\]

(Here \(u\) is a placeholder for a reduced scalar residue; for \(P=dG\) one may take \(u=d\bmod N\).)

## Classification key

| Label | Meaning |
|-------|---------|
| **constant** | Same value for every admissible nonzero orbit |
| **dependent** | A function of a simpler invariant already listed |
| **independent** | Not a function of the other listed invariants in the same ring (may still be a function of the full point/scalar) |

## Field / residue-ring invariants of \(\mathcal{X}\) (in \(\mathbb{F}_p\))

| Invariant | Formula | Class | Reason |
|-----------|---------|-------|--------|
| Trace | \(x+\beta x+\beta^2 x=0\) | **constant** | \(1+\beta+\beta^2=0\) |
| Norm / product | \(x\cdot(\beta x)\cdot(\beta^2 x)=x^3\) | **dependent** | Function of \(x\) (equivalently of \(x^3\)) |
| Elem. symmetric \(e_1\) | \(0\) | **constant** | Trace |
| Elem. symmetric \(e_2\) | \(x\cdot\beta x+(\beta x)\cdot\beta^2 x+\beta^2 x\cdot x=x^2(1+\beta+\beta^2)=0\) | **constant** | Same as trace identity |
| Elem. symmetric \(e_3\) | \(x^3\) | **dependent** | Norm |
| Minimal polynomial | \(T^3-x^3\) | **dependent** | Determined by \(x^3\) (\(e_1=e_2=0\)) |
| Discriminant of \(T^3-x^3\) | \(-27\,x^6\) (char \(\neq 2,3\)) | **dependent** | Function of \(x\) |

## Integer-lift invariants of \(\mathcal{X}\) (reduced representatives)

| Invariant | Formula | Class | Reason |
|-----------|---------|-------|--------|
| Orbit sum \(S_x\) | \(x_0+x_1+x_2=q_x\,p\) | **dependent** | Determined by \(q_x\) and \(p\) |
| Carry class \(q_x\) | \(q_x\in\{1,2\}\) | **independent** among lift data | Not visible in \(\mathbb{F}_p\); not a function of the field-trace (constant). Still a function of the reduced triple, hence of \(x\). |
| Edge carry \(c_x\) | \(\lfloor(x+x_1)/p\rfloor\in\{0,1\}\) | **dependent** | \(q_x=1+c_x\) along the reconstruction edge used in the theorem (orbit class matches) |

## Scalar side \(\mathcal{U}\) (parallel)

| Invariant | Class | Notes |
|-----------|-------|-------|
| Trace in \(\mathbb{Z}/N\mathbb{Z}\) | **constant** (\(0\)) | Same \(\Phi_3\) |
| Norm \(u^3\) | **dependent** | Function of \(u\) |
| Carry class \(q_u\in\{1,2\}\) | **independent** among lift data | Function of \(u\); parallel to \(q_x\), not identified with it |

## Sixfold constancy

**Theorem 1.1.** Every set-invariant of \(\mathcal{X}\) (including \(q_x\)) is constant on

\[
\{\,\pm P,\ \pm\psi(P),\ \pm\psi^2(P)\,\}.
\]

**Proof.** Negation preserves \(x\). \(\psi\) permutes the three reduced \(x\)-values, so the unordered set and its sum \(S_x\) are unchanged. Hence \(q_x=S_x/p\) is unchanged.

---

# Section 2 — Information content

Prior for entropy upper bounds: an invariant \(I\) taking values in a finite set \(V\) satisfies

\[
H(I)\le\log_2|V|,
\]

with equality iff \(I\) is uniform on \(V\). We use only this bound unless a value is **constant** (then \(H=0\)).

| Invariant | \(\lvert V\rvert\) | Entropy bound | Observable from public \(P=(x,y)\)? |
|-----------|--------------------|---------------|--------------------------------------|
| Field trace of \(\mathcal{X}\) | \(1\) | \(H=0\) | Yes (always \(0\)) |
| Field norm \(x^3\) | \(\le p\) | \(H\le\log_2 p\) | Yes (from \(x\)) |
| \(q_x\) | \(2\) | \(H(q_x)\le 1\) bit | Yes (from \(x\)) |
| \(c_x\) | \(2\) | \(H(c_x)\le 1\) bit | Yes (from \(x\)) |
| \(q_u\) | \(2\) | \(H(q_u)\le 1\) bit | **No** (needs scalar) |
| Full \(\mathcal{X}\) as set | \(\sim p/3\) orbits | \(H\le\log_2((p-1)/3)\) | Yes |
| Full \(\mathcal{U}\) as set | \(\sim N/3\) orbits | \(H\le\log_2((N-1)/3)\) | **No** |

**Theorem 2.1 (No free bits given \(P\)).**  
If \(I\) is any function of \(\mathcal{X}\) or of \((x,y)\), then

\[
H\bigl(I\bigm|P\bigr)=0.
\]

**Proof.** \(P\) determines \((x,y)\), which determines \(\mathcal{X}\), \(q_x\), \(c_x\), and all field symmetric functions of \(\mathcal{X}\).

**Corollary 2.2.** Mutual information \(I(q_x;d\mid P)=0\). The carry class does not reduce uncertainty about \(d\) once \(P\) is known.

**Theorem 2.3 (Independent lift bit is not a DL bit).**  
Although \(H(q_x)\le 1\), this bit is:

1. computable from public \(x\), and  
2. constant on each sixfold orbit (Theorem 1.1).

Therefore it partitions **orbits**, not points inside an orbit, and adds **no** refinement beyond the sixfold equivalence already used in GLV collision search.

---

# Section 3 — Recoverability from \(P=(x,y)\)

| Invariant | Directly from \(P\) | After one \(\psi\) (optional) | Requires scalar / ECDLP |
|-----------|---------------------|------------------------------|-------------------------|
| \(x\), \(y\), \(E(P)=xp+y\) | Yes | — | No |
| \(\mathcal{X}\), \(x^3\), field trace \(0\) | Yes | — | No |
| \(q_x\), \(c_x\), \(S_x\) | Yes | — | No |
| \(\psi(P)\), \(\psi^2(P)\) | Yes (endomorphism on coordinates) | Yes | No |
| \(\mathcal{U}(d)\), \(q_u\), \(d^3\) | No | No | **Yes** |
| Equality \(q_x=q_u\) as a predicate on unknown \(d\) | No | No | Would require \(d\) |

**Theorem 3.1.** Every invariant appearing in the carry reconstruction theorem for the instance \((p,\beta)\) is polynomial-time computable from the affine coordinates of \(P\). No invariant of the instance \((N,\lambda)\) is computable from \(P\) by the accepted theorems alone.

---

# Section 4 — Bridge limits

**Statement to decide.** Exists nontrivial invariant \(I\) with \(I(P)=I(d)\) for all \(P=dG\), or no such identity under the current algebra.

Here **nontrivial** means: not constant, and not reducible to a quantity already known to match by the GLV definition \(\psi(P)=[\lambda]P\) (e.g. we do not count “the orbit label of \(P\) equals the orbit label of \(d\) under \(\mu_3\times\{\pm1\}\)” as a new bridge — that **is** the sixfold symmetry).

**Candidate lift bridge.** \(q_x(P)=q_u(d)\) for \(P=dG\).

**Theorem 4.1 (No carry-class bridge).**  
The identity \(q_x(dG)=q_u(d)\) is **false** in general.

**Proof.** Both sides take values in \(\{1,2\}\). It suffices to exhibit one \(d\) with inequality. Verification produces many (Phase III: \(93/200\) mismatches on a fixed sample stream). Structurally: \(q_x\) depends on the reduced embedding of \(\{x,\beta x,\beta^2 x\}\subset\mathbb{Z}\) relative to \(p\), while \(q_u\) depends on \(\{d,\lambda d,\lambda^2 d\}\subset\mathbb{Z}\) relative to \(N\). The accepted theorems give parallel \(\Phi_3\)-calculus, not an equality of classes. \(\Delta=p-N\) does not appear in either carry formula (Section 5), so it supplies no forced identification.

**Theorem 4.2 (No ring-hom identification of invariants).**  
There is no unital ring homomorphism \(\mathbb{F}_p\to\mathbb{Z}/N\mathbb{Z}\) (or converse). Hence no bridge that identifies all residue-ring invariants of \(\mathcal{X}\) with those of \(\mathcal{U}\) by transport of structure.

**Theorem 4.3 (Limit of the current algebra).**  
Under the frozen theorems, the only exact \(P\leftrightarrow d\) matching that relates the two cube-root orbits is the classical CM/GLV law

\[
\psi(P)=[\lambda]P,
\]

which generates the sixfold geometric–scalar dictionary. No further exact invariant equality \(I(P)=I(d)\) is implied for lift carries, orbit-sum classes, or field symmetric polynomials beyond what that law already encodes.

---

# Section 5 — \(\Delta\) analysis

**Theorem 5.1 (\(\Delta\) does not enter carry reconstruction).**  
In the abstract carry theorem for \((M,t)\),

\[
a_1=(ta)\bmod M,\quad
c=\Big\lfloor\frac{a+a_1}{M}\Big\rfloor,\quad
q=1+c,\quad
a_2=qM-a-a_1,
\]

the only parameters are \(M\) and \(t\). For the secp instances, \((M,t)\in\{(p,\beta),(N,\lambda)\}\). The quantity \(\Delta=p-N\) does not appear.

**Proof.** Immediate from the statement: each instance is self-contained. Substituting \(p=N+\Delta\) into the \(p\)-carry equations does not produce the \(N\)-carry equations, nor a relation between \(q_x\) and \(q_u\).

**Theorem 5.2 (Role of \(\Delta\)).**  
\(\Delta\) governs only the **signature lift** ambiguity \(R_x\leftrightarrow r=R_x\bmod N\) (unique iff \(r\ge\Delta\)). That is bridge algebra between integer representatives in \([0,p)\) and residues mod \(N\), not a term inside cube-root carry reconstruction.

**Corollary 5.3.** No theorem forces \(\Delta\) into the carry equations; they remain independent of \(\Delta\) by construction.

---

# Section 6 — Complexity accounting

Let the baseline exhaustive scalar search have cardinality \(2^k\) with \(k=\log_2(N-1)\) (order of magnitude \(k=256\) for secp256k1).

| Theorem / structure | After | Bits \(b\) | Justification |
|---------------------|-------|------------|---------------|
| None (raw search) | \(2^k\) | \(0\) | — |
| Sixfold GLV orbit \(\{\pm1\}\times\{1,\lambda,\lambda^2\}\) | \(2^{k-\log_2 6}\) | \(b=\log_2 6\) | Equivalence classes of size \(6\) on nonzero points/scalars; classical |
| Carry reconstruction / \(q_x\) / field symmetric polys of \(\mathcal{X}\) | \(2^{k-\log_2 6}\) | \(b'=\mathbf{0}\) **additional** | Theorems 2.1–2.3, 4.1–4.3: invariants are functions of \(P\) and constant on the same sixfold classes |
| Forced lift \(1+t+t^2=M\) | unchanged | \(0\) | Structural identity inside each ring |
| \(\Delta\) signature lift | unchanged for ECDLP from \(P\) | \(0\) | Concerned with \(R_x\leftrightarrow r\), not with recovering \(d\) from \(P\) |

**Never claimed:** “faster ECDLP” from carry algebra alone.  
**Claimed:** original \(2^k\) → after GLV symmetry \(2^{k-\log_2 6}\); after cube-root **lift** theorems, still \(2^{k-\log_2 6}\).

---

# Section 7 — Formal statements (index)

1. **Theorem 1.1** — Sixfold constancy of \(\mathcal{X}\)-invariants including \(q_x\).  
2. **Theorem 2.1** — \(H(I\mid P)=0\) for all \(P\)-computable invariants.  
3. **Theorem 2.3** — The \(\le 1\) bit in \(q_x\) does not refine sixfold classes.  
4. **Theorem 3.1** — Recoverability split: \((p,\beta)\) yes from \(P\); \((N,\lambda)\) no.  
5. **Theorem 4.1** — \(q_x=q_u\) is not an identity.  
6. **Theorem 4.2** — No ring-hom bridge.  
7. **Theorem 4.3** — Only GLV/CM matching relates the two orbits.  
8. **Theorem 5.1–5.2** — \(\Delta\) absent from carries; present only in signature lifts.  
9. **Section 6 table** — \(b=\log_2 6\), \(b'=0\).

Verification script: `phase_iv_information_flow_verify.py`  
Log: `logs/PHASE_IV_INFORMATION_FLOW_VERIFY.txt`

---

# Final answer (success criterion)

> **Do the current theorems reveal any information about an unknown scalar beyond the known sixfold symmetry?**

**No.**

Quantitatively: additional reduction \(b'=0\). The only rigorously justified search-space factor from cube-root orbit geometry remains

\[
2^{k}\;\longrightarrow\;2^{k-\log_2 6},
\]

which is the classical sixfold GLV symmetry, not a consequence of carry bits, orbit-sum classes, or \(\Delta\) beyond what that symmetry already encodes.

This is a **limit theorem** for the present framework: further progress on discrete-log information requires a new theorem outside the frozen carry/lift algebra (or a genuine new bridge identity, which Section 4 shows the current algebra does not provide).
