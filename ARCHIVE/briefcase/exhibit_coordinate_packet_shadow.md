# EXHIBIT: coordinate_packet_shadow (P135)

**Verdict:** verified coordinate bookkeeping — **not** equivalent to `Lambda_N` / `GAP_x` / `GAP_y` — **not** direct `d`/`k` recovery.

Re-run: `python verify_coordinate_packet_shadow.py`

---

## Classification

Two different p→N maps:

```text
integer-only map:
  Px → floor(Px * N / p) = …4859   (= map_p_to_n(Px))

coordinate-packet map:
  Px.y → floor((Px.y) * N / p) = …4860
```

The off-by-one is **not an error**. The packet is not bare `Px`; it is:

```text
Px.y = Px + decimal_fraction_y
```

where the fractional digits are the **p−y** branch. That `0.y` bump is enough to cross the next integer after scaling by `N/p`.

---

## Strongest identities

```text
packet_p = (Px.y_decimal) / p

packet_p * p = Px.y_decimal          # field witness
packet_p * N = scalar-shadow packet  # scalar-order shadow
packet_p * (p - N) = field packet - scalar packet
```

Three ceilings, same packet family:

| Multiplier | Courtroom | Role |
|------------|-----------|------|
| `p` | field prime | field witness `Px.y` |
| `N` | scalar order | scalar-shadow packet |
| `2^256` | binary ceiling | binary-ceiling `x.y` (packet may differ slightly) |

---

## Not Λ-bridge gaps

```text
GAP_x = Lambda_N - Lambda mod N
GAP_y = lambda_y_N - Lambda_N mod N
```

Those are **bridge-ratio** p→N gaps.

```text
packet_p * Δ = field_packet - scalar_packet
```

is a **coordinate-packet** p→N displacement.

Same p/N defect family (`Δ = p − N`), different object. Do **not** jam into Λ machinery.

---

## Verified P135 values

```text
Px     = 9210836494447108270027136741376870869791784014198948301625976867708124077590
p−y    = 46351506704828816385393879789131775975171267756561783641521771795450741674800
Δ      = 432420386565659656852420866390673177326

map_p_to_n(Px) = floor(Px*N/p)
               = 9210836494447108270027136741376870869757386556619969566208268645556489194859

floor(packet_p * N)
               = 9210836494447108270027136741376870869757386556619969566208268645556489194860

packet_p * p  → integer part = Px
fractional digits of (packet_p * p) start with p−y
```

`packet_p` (field packet / p):

```text
0.079546336499460462554501802883040753799770017855946243657403747988737825607683797376362420847353351108638651635660059457338972369055727427831496239538405074
```

---

## Judge Popcorn

Same packet, different courtroom: **p gives the field witness; N gives the scalar-shadow witness.** The one-off is the decimal witness nudging the floor over the line.
