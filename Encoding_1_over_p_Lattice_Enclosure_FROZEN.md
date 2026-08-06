# Encoding of 1/p — Lattice Enclosure (FROZEN)

**Status: FROZEN.** Encoding theory only. Not ECDLP. No further decimal/reciprocal experiments.

---

## Exact statement

Write \(10^k = Ap + r\) with \(A=\lfloor 10^k/p\rfloor\) and \(0<r<p\) (valid for all finite \(k\) since \(p\nmid 10^k\)).

Lower / upper decimal lattice points:

\[
T_k=\frac{A}{10^k},\qquad
U_k=\frac{A+1}{10^k}.
\]

Then

\[
\boxed{
T_k<\frac1p<U_k
}
\qquad\text{and}\qquad
\boxed{
T_kp<1<U_kp.
}
\]

Distances:

\[
1-T_kp=\frac{r}{10^k},\qquad
U_kp-1=\frac{p-r}{10^k}.
\]

Incrementing the last displayed digit of a truncation of \(1/p\) adds \(10^{-k}\), jumping from \(T_k\) to \(U_k\) — not completing the exact reciprocal.

## No terminating decimal equals \(1/p\)

A finite decimal has denominator \(10^k=2^k5^k\). Equality \(1/p=T\) would require \(p\mid 10^k\). Secp256k1’s \(p\) is neither \(2\) nor \(5\), so

\[
\boxed{
\text{no finite decimal of }1/p\text{, multiplied by }p\text{, equals exactly }1.
}
\]

Only the infinite expansion, or the exact rational \((1,p)\), does.

## Relation to frozen resolution note

Parent lattice note: `Resolution_Coarse_Fine_Lattice.md`.  
Next central object: packed integer \(E=xp+y\) (`Phase_VI_Exact_Rational_Encoding.md`).
