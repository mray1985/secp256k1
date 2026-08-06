# EXHIBIT: residue numerator briefcase scan

Integer lane: `num = x*p + y - m` across **all briefcase ways**.

## Mod lenses

```text
num mod p
num mod N
num mod DELTA
num mod 2^256
```

Identity: `num mod p = (y - m) mod p` — verified (0 failures).

## Ways scanned

```text
heads:    pubkey_Px, beta_Px1/2/3, rx_slot_*, Gx_slot_*
branches: y, p_minus_y
total:    1760 residue rows (88 puzzles)
```

## Primary witness (pubkey Px + p−y)

```text
unique (mod p, mod N, mod DELTA) triplets: 88 / 88
max puzzles sharing one triplet:          1
```

No transferable global fingerprint — triplets are point-specific.

## Exact full-mod hits

```text
total exact (mod p/N/DELTA/2^256) hits: 0
d exact mod hits:                       0
d low-32 primary hits:                  0
```

Exact full-mod equality is empty — expected at 256-bit scale.

## Low-bit hits (top)

```text
  rx_slot_1+p_minus_y | low_8 | P135_rx_slot_2: 4
  Gx_slot_2+p_minus_y | low_8 | Py: 3
  rx_slot_1+y | low_8 | Gx_slot_3: 3
  rx_slot_3+p_minus_y | low_8 | p_minus_y: 3
  rx_slot_1+y | low_8 | B: 3
  Gx_slot_1+y | low_8 | range_lo: 3
  rx_slot_3+y | low_8 | Gx_slot_2: 2
  rx_slot_3+p_minus_y | low_8 | P135_Px_slot_3: 2
  pubkey_Px+p_minus_y | low_8 | LAMBDA1: 2
  beta_Px3+p_minus_y | low_8 | LAMBDA1: 2
```

## Primary mod_p / mod_N exact hits

```text
mod_p: none
mod_N: none
```

## P135 primary (pubkey + p−y)

```text
num mod p     = 91798970085009692294219283771835672128096405902929...
num mod N     = (256-bit residue class)
num mod DELTA = 154617683605367131951950111006061580519...
mod_p hits    = []
```

## Clean ruling

```text
Factual structure: yes — integer mod lane works on all briefcase ways
This is d:         no — 0 exact d mod hits
Transferable mask: no — 88 unique primary triplets
```

Judge Popcorn: **The residue testified in every courtroom. No conviction.**
