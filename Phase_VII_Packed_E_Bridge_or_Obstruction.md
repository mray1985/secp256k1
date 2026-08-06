# Phase VII — Packed-\(E\) Bridge or Obstruction

**Status:** All prior phases frozen. Do not reopen carry, \(q_x\leftrightarrow q_u\), orientation, decimals, lattice-digit work, Phase IV–VI conclusions.

**Primary question.** Does any publicly computable residue / decomposition of

\[
E(P)=xp+y
\]

modulo \(N\) refine the known sixfold scalar orbit?

**Known identity (Phase VI):**

\[
E\equiv x\Delta+y\pmod N,\qquad \Delta=p-N.
\]

---

# Section A — Full \(E\bmod N\) algebra

Write \(e(P)=E(P)\bmod N\in\{0,\ldots,N-1\}\) and \(E=q_E N+e\).

**Theorem A.1 (Base).**

\[
e(P)\equiv x\Delta+y\pmod N.
\]

**Theorem A.2 (Negation).**  
\(E(-P)=E(P)+p-2y\), so

\[
e(-P)\equiv e(P)+\Delta-2y\pmod N.
\]

Equivalently \(e(-P)\equiv x\Delta+(p-y)\equiv x\Delta+\Delta-y\pmod N\).

**Theorem A.3 (GLV \(\psi\)).**  
With \(x_1=\beta x\bmod p\),

\[
e(\psi(P))\equiv x_1\Delta+y\pmod N.
\]

**Theorem A.4 (GLV \(\psi^2\)).**  
With \(x_2=\beta^2 x\bmod p\),

\[
e(\psi^2(P))\equiv x_2\Delta+y\pmod N.
\]

**Notation.** \(e_0=e(P)\), \(e_1=e(\psi(P))\), \(e_2=e(\psi^2(P))\), \(e_{-}=e(-P)\).

All formulas follow from \(p\equiv\Delta\pmod N\) and the Phase VI expressions for \(E(\cdot)\). No numerical fitting.

---

# Section B — Orbit sum modulo \(N\)

**Theorem B.1.** From \(E_0+E_1+E_2=q_x p^2+3y\) and \(p^2\equiv\Delta^2\pmod N\),

\[
\boxed{
E_0+E_1+E_2\equiv q_x\Delta^2+3y\pmod N.
}
\]

**Theorem B.2 (Classification of the sum residue).**  
Let \(S_e=(E_0+E_1+E_2)\bmod N\).

1. **Publicly computable:** yes (from \(P\): compute \(q_x,y\), or sum the three packed \(E_j\)).
2. **Orbit-only:** yes for the **unordered** GLV \(x\)-orbit with fixed \(y\): \(q_x\) and \(y\) are constant on \(\{P,\psi(P),\psi^2(P)\}\), so \(S_e\) is too. On the full sixfold, \(y\mapsto p-y\) under negation replaces \(3y\) by \(3(p-y)\equiv 3\Delta-3y\pmod N\), so the **full sixfold** does not fix a single \(S_e\); the \(\mu_3\)-half does.
3. **Sign-sensitive:** yes — \(S_e\) flips with the \(y\)-branch as above.
4. **\(\lambda\)-position-sensitive:** no within a fixed \(\mu_3\) half (same \(q_x,y\)).
5. **Scalar-refining / bits:** no beyond GLV. \(S_e\) is a function of public \((q_x,y)\) already determined by \(P\). Phase IV: \(H(S_e\mid P)=0\). Additional \(b'=0\).

---

# Section C — Negation pair

**Theorem C.1.**

\[
e(-P)\equiv e(P)+\Delta-2y\pmod N.
\]

**Theorem C.2.** The pair \(\{e(P),e(-P)\}\) is determined by \((e(P),y,\Delta)\) or equivalently by \((x,y)\). It encodes the same information as the known \(y\)-branch together with \(e(P)\). It does **not** refine the sixfold quotient: \(P\) and \(-P\) already lie in the same \(\sim_{\mathrm{GLV}}\) class. Bits gained beyond GLV: \(b'=0\).

---

# Section D — GLV differences modulo \(N\)

**Theorem D.1.** From \(E_i-E_j=(x_i-x_j)p\),

\[
E_i-E_j\equiv(x_i-x_j)\Delta\pmod N.
\]

Write

\[
d_{01}\equiv(x_1-x_0)\Delta,\quad
d_{12}\equiv(x_2-x_1)\Delta,\quad
d_{20}\equiv(x_0-x_2)\Delta\pmod N.
\]

**Theorem D.2.** Each \(d_{ij}\) is a public function of the ordered pair \((x_i,x_j)\). The unordered set \(\{d_{01},d_{12},d_{20}\}\) is a function of the unordered coarse orbit \(\mathcal{X}\) and \(\Delta\). By Phase V, any symmetric function of \(\mathcal{X}\) is orbit-only on the sixfold geometry → \(b'=0\).

Ordered \((d_{01},d_{12},d_{20})\) is \(\lambda\)-position-sensitive (depends on labeling \(x_0=\!x(P)\)), but that labeling is already fixed once \(P\) is known. No hidden scalar filter.

---

# Section E — Signature / nonce connection

Nonce point \(R=(R_x,R_y)\) with reduced \(R_x,R_y\in\{0,\ldots,p-1\}\), signature \(r=R_x\bmod N\).

**Theorem E.1 (Lift-independent congruence).**  
Let \(E_R=R_x p+R_y\). Then for **both** lifts \(R_x\in\{r,\,r+N\}\cap[0,p)\) (when both exist),

\[
E_R\equiv r\Delta+R_y\pmod N.
\]

**Proof.** If \(R_x=r\), immediate. If \(R_x=r+N\), then
\((r+N)\Delta+R_y=r\Delta+N\Delta+R_y\equiv r\Delta+R_y\pmod N\).

**Theorem E.2.** Given public \(r\) and \(e_R=E_R\bmod N\),

\[
R_y\equiv e_R-r\Delta\pmod N.
\]

With \(R_y\in[0,p)=[0,N+\Delta)\), the residue \(\rho=(e_R-r\Delta)\bmod N\) determines \(R_y\) uniquely if \(\rho\ge\Delta\), and leaves the ambiguous pair \(\{\rho,\rho+N\}\) if \(\rho<\Delta\) — the same \(\Delta\)-lift dichotomy as for \(R_x\).

**Theorem E.3.** In the usual setting where the verifier reconstructs or already uses curve points, \(E_R\bmod N\) does **not** supply an independent constraint on the nonce scalar \(k\) beyond knowledge of \(R\) (up to that lift ambiguity on \(y\)). It is not a new \(k\)-orbit invariant from the frozen algebra. Conditional bits on \(k\): none proved from \(e_R\) alone.

Pubkey \(E(P)\bmod N\) and nonce \(E_R\bmod N\) remain separate objects.

---

# Section F — Obstruction theorem

**Theorem F.1 (Packed-\(E\) modulo-\(N\) obstruction).**  
Let \(\mathcal{F}\) be any quantity computed from

\[
\bigl\{e(P),\,e(\psi(P)),\,e(\psi^2(P)),\,e(-P),\,e(-\psi(P)),\,e(-\psi^2(P))\bigr\}
\]

by symmetric operations over \(\mathbb{Z}/N\mathbb{Z}\), optionally using public constants \(\Delta,\beta,p,N\), and optionally using \(q_x\) or other Phase VI packed-orbit identities. Then:

1. \(\mathcal{F}\) is a deterministic function of the sixfold geometric orbit of \(P\) (hence of public \(P\)).
2. \(H(\mathcal{F}\mid P)=0\).
3. \(\mathcal{F}\) does not refine \(\sim_{\mathrm{GLV}}\) beyond the classical sixfold accounting.
4. Therefore the packed-\(E\) modulo-\(N\) family yields

\[
\boxed{b'=0.}
\]

**Proof.** Each \(e(\pm\psi^j(P))\) equals \((\pm\!\!:y\text{-branch})\) and \((\beta^j x\bmod p)\,\Delta\pm\cdots\) as in §A — all determined by the sixfold orbit. Symmetric combinations are constant on that orbit. Phase IV–V then give \(b'=0\). Non-symmetric labeling (e.g. raw \(e(P)\)) still satisfies \(H(e(P)\mid P)=0\) and does not shrink the search for the unique \(d\) with \(P=dG\).

**Theorem F.2 (No counterexample in this family).**  
No quantity in §A–D is both (i) independent of the public orbit data and (ii) scalar-refining with positive proven \(b'\). Success criterion **B**.

---

# Final table

| Candidate | Public? | Orbit-only? | Sign-sens.? | \(\lambda\)-pos.? | Scalar-refining? | Bits \(b'\) | Status |
|-----------|---------|-------------|-------------|-------------------|------------------|------------|--------|
| \(e=E\bmod N\) | Yes | No (label of \(P\)) | Yes | Yes | No (fn of \(P\)) | \(0\) | Proven |
| \(e(-P)\) | Yes | No | Yes | Yes | No | \(0\) | Proven |
| \(e(\psi),e(\psi^2)\) | Yes | No | with \(y\) | Yes | No | \(0\) | Proven |
| \(S_e\equiv q_x\Delta^2+3y\) | Yes | on \(\mu_3\) half | Yes | No | No | \(0\) | Proven |
| \(\{d_{ij}\}\) set | Yes | Yes (via \(\mathcal{X}\)) | No | No | No | \(0\) | Proven |
| ordered \((d_{ij})\) | Yes | No | No | Yes | No | \(0\) | Proven |
| \(\{e(\pm\psi^j P)\}\) symmetric | Yes | Yes | absorbed | absorbed | No | \(0\) | **Obstruction F.1** |
| \(E_R\bmod N\) (nonce) | if \(R\) known | — | — | — | \(\equiv r\Delta+R_y\); not new \(k\) bit | \(0\) on \(k\) | Proven E |
| Full packed-\(E\) mod \(N\) family | Yes | when symmetrized | — | — | No | \(\boxed{0}\) | **B** |

---

## Complexity reminder

\[
2^k\;\longrightarrow\;2^{k-\log_2 6}
\]

only (classical GLV). Packed-\(E\bmod N\) adds \(b'=0\).

---

## Artifacts

| File | Role |
|------|------|
| `Phase_VII_Packed_E_Bridge_or_Obstruction.md` | This document |
| `phase_vii_packed_e_verify.py` | Theorem / proof / verification |
| `logs/PHASE_VII_PACKED_E_VERIFY.txt` | Log |

---

## Verdict

**B.** The entire packed-\(E\) modulo-\(N\) family still gives \(b'=0\). The identity \(E_0+E_1+E_2\equiv q_x\Delta^2+3y\pmod N\) is exact and useful structurally, but every term is public from the point orbit.
