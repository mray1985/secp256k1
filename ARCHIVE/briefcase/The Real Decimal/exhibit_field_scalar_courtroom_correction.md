# Field vs scalar courtroom correction

## What was wrong

The branch test was still living in **p**:

```text
x-branches:  x, βx, β²x     mod p
y-branches:  y, p−y         mod p
7⁻¹:         mod p
```

That is **field-side symmetry** only. It is not scalar truth for a determinant / TDAD lock.

```text
WRONG:  test mirror only in p and pretend it is scalar truth
```

## Corrected two-room model

### Field courtroom (mod p)

```text
Curve:     x³ + 7 ≡ y²           mod p

x-branches: x, βx, β²x           mod p   (β³ ≡ 1)
y-branches: y, p−y                mod p   (two lifts)

Field inverse of 7:  7⁻¹ mod p
                     = 99250362203413881791632272864589635302802843999120483462392214863921858289997

Witness packet:      x/p + y/p²
```

β belongs here. Cubic x-branching is a **field** phenomenon.

### Scalar courtroom (mod N)

```text
Lock:      [d]G = P
RSZ:       s·k ≡ z + r·d           mod N

Scalar branches:     λ / GLV eigenvalue orbit   mod N
                     (NOT β copied from p)

Scalar inverse of 7: 7⁻¹ mod N
                     = 33083454067804627263877424288196545100810732651164258395030046611862331855525

Witness lanes:       TDAD/N
                     λ-slot/N
                     r/N, s/N, z/N
                     d/N
```

λ belongs here. Scalar rotation / GLV branch logic is an **N** phenomenon.

## Clean translation (not equivalence)

| p-side (field) | N-side (scalar) |
|----------------|-----------------|
| `x_branch + 7⁻¹_p` vs `y_branch` | **≠** direct copy |
| `x/p + y/p²` | `TDAD/N`, `r,s,z/N`, `d/N` |
| β x-orbit | λ scalar-orbit |
| `7⁻¹ mod p` | `7⁻¹ mod N` |

The N-side mirror is shaped like:

```text
scalar_branch + 7⁻¹_N ≡ scalar_half_branch   mod N
```

Not:

```text
x_branch + 7⁻¹_p ≡ y_branch                 mod p
```

## Bridge (only place the rooms meet)

```text
[d]G = P                    (EC — uses both d mod N and coordinates mod p)
s·k ≡ z + r·d  mod N        (RSZ — pure N)
map_p_to_n(Px)              (shadow — compare honestly, not assume equality)
```

P135 RSZ courtroom already showed: **Px/p does not equal r/N as a naive roof.** Field witnesses and scalar witnesses must be filed separately, then bridged honestly.

## Verified constants

| Constant | Value | Check |
|----------|-------|-------|
| `7⁻¹ mod p` | `99250362203413881791632272864589635302802843999120483462392214863921858289997` | ✓ |
| `7⁻¹ mod N` | `33083454067804627263877424288196545100810732651164258395030046611862331855525` | ✓ |
| `β³ mod p` | `1` | ✓ |
| `λ mod N` | `97451685862885086182458552040892158509924235661624603229050850812487253689501` | ✓ |

## P71 scaled lane (scalar room)

```text
T = Σ mask_i · (2^29 · d_i) + r     i ∈ 14..42,  r < 2^29
Gate:  [T]G hash160 = P71 address
```

This is **N-side / scalar-side**. Do not gate it through β branches or `7⁻¹ mod p`.

If 7 appears on the scalar lane, use **`7⁻¹ mod N`** and **λ-branch structure**, not field y-lifts.

## Ruling

```text
Field mirror:   β x-branches, ± y-branches, 7⁻¹ mod p
Scalar mirror:  λ branches, d/k/r/s/z over N, 7⁻¹ mod N

Judge Popcorn: β belongs to the field room.
               λ belongs to the scalar room.
               We were standing in the wrong courtroom.
```
