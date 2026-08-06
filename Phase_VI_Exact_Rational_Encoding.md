# Phase VI — Exact Rational Encoding

**Status:** Decimal / reciprocal lines frozen.  
**Frozen parents:** `Resolution_Coarse_Fine_Lattice.md`, `Encoding_1_over_p_Lattice_Enclosure_FROZEN.md`.  
**Accepted carry / cube-root theorems:** untouched.

---

## Objective

Eliminate decimal arithmetic from the theory. Internal work uses only the packed integer

\[
\boxed{E=xp+y.}
\]

Decimals are a serialization of \(\Phi=E/p^2\), not a foundation.

---

# Section 1 — Canonical coordinate

**Definition.** For affine \(P=(x,y)\) with reduced \(x,y\in\{0,\ldots,p-1\}\):

\[
E(P)\;:=\;xp+y\in\{0,1,\ldots,p^2-1\}.
\]

**Rule.** Internally never form \(x/p+y/p^2\) except for human-readable output. All algebra uses \(E\).

---

# Section 2 — Formulas (no decimals)

**Theorem 2.1 (Identity).**

\[
E(P)=xp+y.
\]

**Theorem 2.2 (Negation).**

\[
E(-P)=x\,p+(p-y)=E(P)+p-2y,
\qquad
E(P)+E(-P)=p(2x+1).
\]

**Theorem 2.3 (GLV \(\psi\)).**  
On secp256k1, \(\psi(x,y)=(\beta x\bmod p,\ y)\). Write \(\beta x = q_1 p + x_1\) with \(x_1=\beta x\bmod p\) and \(q_1=\lfloor\beta x/p\rfloor\). Then

\[
E(\psi(P))=x_1\,p+y=(\beta x-q_1 p)\,p+y=\beta\,xp-q_1 p^2+y.
\]

In particular

\[
E(\psi(P))\neq \beta\,E(P)
\]

in general (\(\beta E(P)=\beta xp+\beta y\)).

**Theorem 2.4 (GLV \(\psi^2\)).**  
With \(x_2=\beta^2 x\bmod p\) and \(q_2=\lfloor\beta^2 x/p\rfloor\),

\[
E(\psi^2(P))=x_2\,p+y=\beta^2 xp-q_2 p^2+y.
\]

**Corollary 2.5.** The fine residue \(E\bmod p\) is invariant under \(\psi\) and \(\psi^2\) (equals \(y\)). Negation replaces it by \(p-y\) (unless \(y=0\)).

---

# Section 3 — Orbit algebra of \(E\)

Let \(x_0=x\), \(x_1=\beta x\bmod p\), \(x_2=\beta^2 x\bmod p\), and

\[
E_j=x_j\,p+y\qquad(j=0,1,2).
\]

**Theorem 3.1 (Orbit sum).**  
By the carry reconstruction theorem, \(x_0+x_1+x_2=q_x\,p\) with \(q_x\in\{1,2\}\). Therefore

\[
E_0+E_1+E_2=p(x_0+x_1+x_2)+3y=q_x\,p^2+3y.
\]

**Theorem 3.2 (Orbit differences).**

\[
E_i-E_j=(x_i-x_j)\,p.
\]

Differences kill the fine residue and recover pure coarse gaps.

**Theorem 3.3 (Fine extraction).**

\[
E_j\bmod p=y\qquad\text{for all }j\in\{0,1,2\}.
\]

**Theorem 3.4 (Coarse extraction).**

\[
\bigl\lfloor E_j/p\bigr\rfloor=x_j.
\]

Hence the unordered coarse orbit \(\mathcal{X}\) and the carry class \(q_x\) are recoverable from \(\{E_0,E_1,E_2\}\) without decimals.

**Theorem 3.5 (No new DL bits).**  
The maps \(E\mapsto\{E_0,E_1,E_2\}\) and \(E\mapsto q_x\) factor through public \(P\) and the sixfold geometric orbit. By Phase V obstruction, they contribute \(b'=0\) beyond GLV.

**Symmetric polynomials in the \(E_j\).**  
Elementary symmetric functions of \((E_0,E_1,E_2)\) are polynomials in \(\{x_j\}\) and \(y\) with coefficients in \(\mathbb{Z}[p]\). The first power sum is Theorem 3.1. No identification with a scalar-side packed object is claimed.

---

# Section 4 — Packing / unique recovery

**Theorem 4.1 (Bijection).**  
The map

\[
\{0,\ldots,p-1\}^2\;\longrightarrow\;\{0,\ldots,p^2-1\},
\qquad
(x,y)\longmapsto xp+y
\]

is a bijection. Inverse:

\[
x=\bigl\lfloor E/p\bigr\rfloor,\qquad y=E\bmod p.
\]

**Proof.** For \(0\le E<p^2\), Euclidean division by \(p\) yields unique \(x,y\) with \(0\le y<p\) and \(E=xp+y\), hence \(0\le x<p\).

**Corollary 4.2.** \(E\) is necessary and sufficient to reconstruct the affine pair \((x,y)\). Packing loses no affine information.

---

# Section 5 — Bridge: reduction modulo \(N\)

**Theorem 5.1 (Congruence).**  
Since \(p=N+\Delta\),

\[
E=xp+y\equiv x\Delta+y\pmod{N}.
\]

**Theorem 5.2 (No ring-hom transport).**  
There is still no unital ring homomorphism \(\mathbb{F}_p\to\mathbb{Z}/N\mathbb{Z}\). Reducing \(E\) mod \(N\) does not identify the \(p\)-carry algebra with the \(N\)-carry algebra.

**Theorem 5.3.** The residue \(E\bmod N\) is publicly computable from \(P\) (via \(x,y\)). It is a function of \(P\), hence Phase IV applies: \(H(E\bmod N\mid P)=0\), and no additional ECDLP bits beyond GLV follow from knowing it.

---

# Section 6 — Recoverability vs \(r\), \(R_x\), \(x\), \(y\)

Exact identities (no statistics):

| Quantity | Relation to \(E\) |
|----------|-------------------|
| \(x\) | \(\lfloor E/p\rfloor\) |
| \(y\) | \(E\bmod p\) |
| \(E\bmod N\) | \(x\Delta+y\bmod N\) |
| Signature \(r=R_x\bmod N\) | Concerned with a **nonce** point’s \(x\), not with pubkey \(E\) |
| \(R_x\) lift vs \(r\) when \(r<\Delta\) | Signature-lift algebra (Phase II); independent of pubkey \(E\) |

**Theorem 6.1.** For a public key \(P\), \(E(P)\bmod N\) does not equal a signature \(r\) by any identity of the frozen algebra. They are different geometric objects unless a separate theorem identifies them (none accepted).

---

# Section 7 — Hierarchy (general theorem)

**Theorem 7.1.** Decimal precision theorems are **corollaries** of the packed integer and its lattices, not foundations.

```text
Curve point P = (x, y)
        ↓
Packed integer E = xp + y
        ↓
Rational coordinate Φ = E / p²
        ↓
Decimal encoding (floor / display)
        ↓
Displayed digits
```

Lattice resolutions \(1/p\) and \(1/p^2\) live at the rational/packed layer. Depths \(k=78\) and \(k=155\) are base-10 encodings of those resolutions (`Resolution_Coarse_Fine_Lattice.md`).

---

# Section 8 — Complexity (engineering only)

Operating on \(E\) (as an integer \(<p^2\), about \(512\) bits):

| Task | Effect vs \((x,y)\) pair | ECDLP claim |
|------|--------------------------|-------------|
| Storage | One integer instead of two field elements (same bit budget \(\sim 2\log_2 p\)) | None |
| Equality / comparison | Single integer compare | None |
| Hashing / canonicalization | Hash one integer; unique for affine \(P\) | None |
| Orbit generation | Compute \(E_j=x_j p+y\) after \(\psi\) on coordinates, or rebuild from \((x_j,y)\) | None; still GLV cost |

**No claim** that \(E\) reduces discrete-log search complexity. Phase IV–V: \(b'=0\) beyond \(\log_2 6\).

---

## Artifacts

| File | Role |
|------|------|
| `Phase_VI_Exact_Rational_Encoding.md` | This document |
| `phase_vi_exact_rational_encoding_verify.py` | Theorem / proof / verification |
| `logs/PHASE_VI_EXACT_RATIONAL_ENCODING_VERIFY.txt` | Log |

---

## Freeze boundary

- No more decimal precision experiments.
- No more \(1/p\) last-digit / enclosure probes (see `Encoding_1_over_p_Lattice_Enclosure_FROZEN.md`).
- Further work, if any, studies algebra of \(E\) under the hierarchy above — without claiming ECDLP reduction unless a new theorem proves \(b'>0\).
