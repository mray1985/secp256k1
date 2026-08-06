# EXHIBIT: three lenses (map correction)

## Keeper

```text
H does not change.
The decimal point changes the courtroom.
```

## Lens stack

```text
Hex digits:
  H

Whole-number lens:
  int(H,16)

Fractional-hex lens:
  0x.H = int(H,16) / 16^len(H)

256-bit fixed lens:
  int(H,16) / 2^256

Coordinate packet lens:
  x.y / p
```

## Warning

```text
Do not promote stitched x.y into a giant integer first.
Stitch as decimal placement, then divide by p.
```

## P135 primary public witness

```text
Correct:
  Px.(p−y) / p
  or
  Px.y / p

Wrong:
  Px / p alone as the packet
  Py / p alone as the packet
  int(Px || Py) / something
```

Primary branch in this briefcase: **`Px.(p−y) / p`**.

## Fixed-width objects

For `r, s, z, Gx, Gy, p, N, p−N`, and other ≤256-bit values:

```text
value / 2^256
```

## Three legitimate lenses (do not bleed)

```text
1. fixed binary placement:
   v / 2^256

2. courtroom placement:
   field  → v / p
   scalar → v / N

3. stitched coordinate placement:
   x.y / p
```

## Protocol

Before any pattern testifies, ask:

```text
Which lens produced it?
```

| Lens | Formula | Courtroom |
|------|---------|-----------|
| fixed binary | `v / 2^256` | 256-bit roof |
| field | `v / p` | Fp |
| scalar | `v / N` | FN |
| packet | `x.y / p` | stitched coordinate |

Wrong silhouette (whole-int first) is **filed, named, and patched**.

Judge Popcorn: **same digits, different side of the dot — different courtroom. Ask the lens before the witness speaks.**

## Patch applied

Silhouette fixed in `packet_silhouette_patch.*` / `packets/`.
Every pubkey puzzle has stitched `x.y` (~156 digits), `x.y/2^256`, and `x.y/p`.
