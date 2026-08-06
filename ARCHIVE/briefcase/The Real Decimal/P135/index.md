# P135 local courtroom ledger

Single puzzle courtroom. Every object under the correct roof.

## Status

```text
UNSOLVED · pubkey exposed · RSZ from hashkeys partial spend
Residue lane: CLOSED (witness only, not extractor)
```

## Identity

| Field | Value |
|-------|-------|
| address | `16RGFo6hjq9ym6Pj7N5H7L1NR1rVPJyw2v` |
| d-window | `[2^134, 2^135)` |
| N-mirror | `[N-2^135+1, N-2^134]` |

## Pubkey (field roof /p)

```text
Px / p  = 0.079546336499460468250077838092693127691745758056...
Py / p  = 0.599700575314508044222350235941121354699134826660...
(p−y)/p = 0.400299424685491955777649764058878645300865173339...
```

## Field-native packet (primary: p−y)

```text
P_pair     = (x*p + y) / p²  = 0.x_y in base p
m / p²     = curve wrap limb
residue/p² = (x*p + y − m) / p²

P_pair   ≈ 0.07954633649946046825007783809269312769174575805664062...
m/p²     ≈ 0.00050333896195810972403611449621507745177950710058212...
residue  ≈ 0.07904299753750235191240847143490100279450416564941406...
ratio    ≈ 158.037312
```

## Carry (admitted fact)

```text
carry_y   = 1
carry_pmy = 1
threshold = (N*x mod p) + y >= p
```

## RSZ (scalar roof /N)

```text
s*k ≡ z + r*d (mod N)

r/N = 0.782896794304763443683725654409499838948249816894...
s/N = 0.133944641451081258853861299940035678446292877197...
z/N = 0.572394351232331510814788089192006736993789672851...
k   = unknown
```

## Λ bridges

```text
Λ  = Px3/rx3 mod p  verified=True
Λ1 = Px3/rx2 mod p  verified=True
Λ/Λ1 = β² mod p      verified=True
```

## β-slots

**Px:** Px1, Px2, Px3 — see `ledger.json` → `beta_Px_slots`  
**rx:** rx1, rx2, rx3 — rx3 = rx2·β — see `beta_rx_slots`

## Residue classification (filed)

```text
field-native packet:     factual
curve wrap m:            factual
pair-minus-wrap:         factual
num mod p = (y−m) mod p: factual
residue as d:            no
shared fingerprint:      no
offset class mask:       no
```

## Ruling

```text
Residue is evidence of structure, not extraction.
RSZ courtroom filed — see rsz_courtroom.md
```

## RSZ courtroom (filed)

```text
Candidates: 68 field-native k maps
Nonce gate x([k]G)=r: 0 pass
Full gate (range + [d]G=P): 0 pass

Structural facts verified:
  r = rx2, rx3 = rx2·β, Λ bridges, R point recovered

Verdict: field-native scalars do not yield k.
Open lane: RSZ algebra (Λ/rx slot packets) — not residue numerators.
TDAD scalar: puzzle 135 line EMPTY — no T_135/N packet filed (see tdad_scalar_courtroom.md).
```

## TDAD scalar (filed globally)

```text
82/82 solved TDAD entries: T_n == d_n, [T_n]G == P
Scalar packet T_n/N = d_n/N exactly (delta/N = 0)
P135: no operator sequence in double_and_add.txt
```

Judge Popcorn: **The residue is dismissed as suspect, but retained as a witness. RSZ is in session.**
