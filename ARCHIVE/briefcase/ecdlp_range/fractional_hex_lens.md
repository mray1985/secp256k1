# fractional_hex_lens

## H is just the hex digits

```text
H does not change.
The decimal point changes the courtroom.

0x1  = 1
0x.1 = 1/16 = 0.0625
```

## Demo: .FAD

- fractional hex: `0x.FAD`
- fractional binary: `0b.111110101101`
- decimal: `0.979736328125`
- wrong lens (whole): `4013`

## 256-bit rule

```text
0x.<64 hex digits> = int(H,16) / 2^256 = v / 2^256
```

## Packets

```text
stitch first:   x.y
then normalize: x.y / p
```

Do not promote the stitch to a giant integer first.

## P135 under the right lens

- Px as `0x.H`: `0x.145d2611c823a396e…`
- frac_hex_256(Px): `0.079546336499460462554501802883040753799770017855946243657403747988734875069402535`
- decimal packet / p: `0.0795463364994604625545018028830407537997…`
- Px/p (field placement): `0.079546336499460462554501802883040753799770017855946243657403747988737825607679794`

## Ruling

Wrong binary structure (whole-int silhouette) would scramble every pattern.
Right structure: fractional bitstring after the point, then normalize.

Judge Popcorn: **same digits, different side of the dot — different courtroom.**

Rebuild: `python build_fractional_hex_lens.py`
