# R1 — secp256r1 / NIST P-256 control catalog

Folder: `ARCHIVE/briefcase/R1/`

**Role:** control curve for packet / modulus-defect bookkeeping.
**Not** for β x-slot machinery (`a = -3`; no shared-y β orbit).

Rebuild: `python build_r1_catalog.py`

## Constants

```text
curve:  secp256r1 / NIST P-256
form:   y² = x³ − 3x + b mod p
a:      -3  (mod p = 115792089210356248762697446949407573530086143415290314195533631308867097853948)
b:      41058363725152142129326129780047268409114441015993725554835256314039467401291
p:      115792089210356248762697446949407573530086143415290314195533631308867097853951
n:      115792089210356248762697446949407573529996955224135760342422259061068512044369
h:      1
Gx:     48439561293906451759052585252797914202762949526041747995844080717082404635286
Gy:     36134250956749795798585127919587881956611106672985015071877198253568414405109
G on curve: True
```

## Defect ladder

```text
2^256
  ↓ field_defect = 2^256 − p = 26959946660873538059280334323183841250350249843923952699046031785985
     = 2^224 − 2^192 − 2^96 + 1
p
  ↓ order_defect = p − n = 89188191154553853111372247798585809582
n

2^256 − n = order_ceiling_defect = 26959946660873538059280334323273029441504803697035324946844617595567
         = (2^256 − p) + (p − n)
```

### Rulers (base order matters)

| Label | Formula | Value |
|-------|---------|-------|
| **field-base** | `log_(2^256 − p)(p − n)` | `0.56280442953422954234985021664533330274110926094288348522273981913222066338359785` |
| **order-ceiling-base** | `log_(2^256 − n)(p − n)` | `0.56280442953422954234985021664532131127305369020418013870970437663211414062062550` |
| **reciprocal order-ceiling** | `log_(p − n)(2^256 − n)` | `1.7768161505544447679701476022546251617606824678762225488994736175389019147508337` |
| **reciprocal field** | `log_(p − n)(2^256 − p)` | `1.7768161505544447679701476022545873037890818731234816298378523485709889164047113` |

```text
2^256 − p : how far the field prime sits below the 256-bit ceiling
p − n     : how far the scalar order sits below the field prime
2^256 − n : total ceiling gap down to the scalar order
         = (2^256 − p) + (p − n)
```

Note: `1.7768…` is **not** `log_(2^256−n)(p−n)` (that is still `≈ 0.5628`).
It is the reciprocal: `log_(p−n)(2^256−n) = 1 / log_(2^256−n)(p−n)`.

Same gaps, different ruler. Change the ruler, change the exponent.

**k1-style fourth-power shell?** `False`

`order_defect / field_defect^4` = `1.6882285539827675161673243383662568237294012831075242947994357454361952168234883E-232` (≈ 0 — not a shell echo)

## β cube roots of unity

`p ≡ 1 (mod 3)` → nontrivial β exists: **True**

β values exist, but **shared y² orbit fails** because `a ≠ 0`:

```text
(βx)³ − 3(βx) + b ≠ x³ − 3x + b   in general
```

- β=`…53261006` y²(βGx)==y²(Gx)? **False**
- β=`…44592944` y²(βGx)==y²(Gx)? **False**

**beta_orbit_shares_y_sq_with_Gx:** `False`

## Packet (generator G)

Branch `y` (primary for R1 catalog):

- packet_p = `0.41833221616640542714193266437725716213668363727732783968260272165921150433707274`
- floor(packet_p · p) = `48439561293906451759052585252797914202762949526041747995844080717082404635286` (matches Gx: `True`)
- floor(packet_p · n) = `48439561293906451759052585252797914202725639232380190484935571995336873986452`
- map_p_to_n(Gx) = `48439561293906451759052585252797914202725639232380190484935571995336873986451`
- off_by_map_p_to_n = `1`

Identity (transfers from k1):

```text
packet × p − packet × n = packet × (p − n)
```

packet × (p−n) = `37310293661557510908508721745530648834.098383547506003164342778588814443335764382`

## What transfers vs secp256k1

| Transfers | Does not transfer |
|-----------|-------------------|
| packet = Decimal(Gx.Gy)/p | β x-slot orbit with shared y² |
| packet×(p−n) displacement | fourth-power defect shell |
| map_p_to_n / floor drift | Λ / β spend-line bridges |
| ceiling defect ladder (different shape) | Bitcoin RSZ ledger objects |

## Verdict

```text
R1 = control courtroom
packet/defect bookkeeping: YES
β-slot geometry:            NO
fourth-power shell (k1):    NO
role: prove what disappears when a ≠ 0
```

Judge Popcorn: **same size cousin, different furniture. Use R1 to audit the ruler, not to move the β chairs.**
