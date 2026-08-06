# Coarse / Fine Resolution — Lattice Form

**Status: FROZEN**

This note freezes the coarse/fine channel line. It separates three layers that earlier drafts mixed together.

---

## 1. The mathematical object

\[
E=xp+y,
\qquad
\Phi=\frac{E}{p^2}.
\]

Here \(x,y\in\{0,1,\ldots,p-1\}\) are reduced affine coordinates (or \(y\) as the fine residue in the packed integer). No numeral system is involved.

---

## 2. The lattice resolutions (the theorem)

\[
\boxed{\text{coarse lattice spacing}=\dfrac1p}
\]

\[
\boxed{\text{fine / full packed lattice spacing}=\dfrac1{p^2}}
\]

### Coarse lattice

Distinct residues satisfy

\[
\left|\frac{x_1}{p}-\frac{x_2}{p}\right|
\ge
\frac1p.
\]

Therefore **any** encoding whose bin width is at most the lattice spacing preserves injectivity.

### Fine / packed lattice

Distinct packed integers \(E\) satisfy

\[
\left|\frac{E_1}{p^2}-\frac{E_2}{p^2}\right|
\ge
\frac1{p^2}.
\]

(The same spacing governs \(y/p^2\) along a fixed coarse residue.)

Again: any encoding with bin width \(\le 1/p^2\) is injective on that lattice.

These statements are **base-independent**. The same geometry applies in binary, hexadecimal, or any radix; only the encoding of a bin changes.

---

## 3. A particular encoding (corollaries)

Decimal floor truncation is one encoding, not the theorem.

Bin width at depth \(k\):

\[
10^{-k}.
\]

### Corollary — coarse decimal depth

\[
10^{-k}\le\frac1p
\iff
10^k\ge p.
\]

Secp256k1:

\[
10^{77}<p<10^{78}.
\]

Minimum decimal depth:

\[
\boxed{k=78.}
\]

So \(\operatorname{Tax}_{78}(x/p)\) is injective; \(\operatorname{Tax}_{77}\) necessarily has collisions.

### Corollary — fine / packed decimal depth

\[
10^{-k}\le\frac1{p^2}
\iff
10^k\ge p^2.
\]

Secp256k1:

\[
10^{154}<p^2<10^{155}.
\]

Minimum decimal depth:

\[
\boxed{k=155.}
\]

So floor truncation at 155 places is injective for \(y/p^2\) and for \(E/p^2\); depth 154 necessarily collides.

### Display margins only

**79** and **156** are one-digit display margins. They are not part of the injectivity theorem.

### Other radices

For radix \(b\), replace \(10^k\) by \(b^k\). The minimum depth is the least \(k\) with \(b^k\ge p\) (coarse) or \(b^k\ge p^2\) (fine). The lattice theorem is unchanged.

---

## Hierarchy (locked)

| Layer | Content |
|-------|---------|
| Object | \(E=xp+y\), \(\Phi=E/p^2\) |
| Theorem | resolutions \(1/p\) and \(1/p^2\) |
| Encoding | e.g. decimal floor at \(k=78\) / \(k=155\) |
| Non-theorem | \(79\) / \(156\) display margins |

---

## Verification

`resolution_lattice_verify.py` → `logs/RESOLUTION_LATTICE_VERIFY.txt`

Bounds \(10^{77}<p<10^{78}\) and \(10^{154}<p^2<10^{155}\) are checked by integer comparison. Explicit floor collisions exist at depths \(77\) and \(154\), not at the threshold depths.

---

## Freeze

Do not reopen decimal \(\Phi\) operators, Tax/sales-tax probes, digit-bleed correlation, or \(1/p\) last-digit enclosure probes from this line.

Reciprocal enclosure freeze: `Encoding_1_over_p_Lattice_Enclosure_FROZEN.md`.  
Next central object: packed integer \(E\) in `Phase_VI_Exact_Rational_Encoding.md`.

Downstream work should cite **resolution \(1/p\) / \(1/p^2\)** and \(E=xp+y\), not digit slogans.
