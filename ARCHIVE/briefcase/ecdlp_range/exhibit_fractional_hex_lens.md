# EXHIBIT: fractional hex lens (right side of the dot)

## Correction

We were at risk of reading the **wrong binary silhouette**.

```text
Wrong lens:
  H as whole number
  hex string → giant integer → "decimal number"

Right lens:
  0x.H as fractional bit placement
  hex string → fractional binary → decimal fraction → normalize
```

`H` is only shorthand for **the hex digits**. `H` does not change from 1.
**The decimal point changes the courtroom.**

```text
0x1   = 1 × 16^0     = 1
0x.1  = 1 × 16^-1    = 1/16 = 0.0625
```

Same digit, different side of the dot.

## Hex fraction → binary → decimal

One hex digit = four binary bits.

```text
.FAD_hex
F = 1111
A = 1010
D = 1101

0x.FAD = 0b.111110101101
       = int(0xFAD) / 16^3
       = 4013 / 4096
       = 0.979736328125
```

## Full 256-bit object

```text
64 hex digits
= 256 binary bits

0x.<64 hex digits>
= 0b.<256 bits>
= int(H, 16) / 2^256
```

So for any value `v` already in `0 .. 2^256-1`:

```text
frac_hex_256(v) = v / 2^256
```

That is the binary fractional placement of `v` under the 256-bit roof.

## Coordinate packets (still stitch, then normalize)

```text
stitch first:   x.y
then normalize: x.y / p
```

Do **not** promote the stitched form to a giant integer and call that the geometry.

## Clean phrase

```text
H does not change.
The decimal point changes the courtroom.

Before the point, hex is a whole number.
After the point, the same hex becomes a binary/decimal placement in (0,1).
```

## Relation to roofs

```text
e_roof_binary = 1           abstract 2^256 roof
e_roof_N      = log2(N)/256 true order roof (< 1)

frac_hex_256(v) = v / 2^256   placement under binary roof
```

Rebuild: `python build_fractional_hex_lens.py`
