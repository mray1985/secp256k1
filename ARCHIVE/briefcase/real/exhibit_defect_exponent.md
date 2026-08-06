# EXHIBIT: defect_exponent (secp256k1 ceilings)

**Location:** `ARCHIVE/briefcase/real/` — does not overwrite prior exhibits.

**Verdict:** verified curve-constant identity. Defect scale / exponent bridge — **not** a private-key answer.

Re-run: `python verify_defect_exponent.py`

---

## Three-ceiling crack chain

```text
2^256
  ↓ defect = 2^32 + 977 = 4294968273
p
  ↓ defect = p − N ≈ (2^32 + 977)^4.0108031509
N
```

Clean identities:

```text
2^256 − p = 2^32 + 977 = 4294968273

p − N = Δ = 432420386565659656852420866390673177326

log_{2^32+977}(p − N) = 4.01080315094850966629515352622337816305...

(2^32 + 977)^4.010803150948509... = p − N
```

Split:

```text
4                    = main fourth-power defect shell
0.0108031509485...   = correction exponent
1.2707681476957...   = correction multiplier = (2^32+977)^0.01080315...
```

So:

```text
p − N
  = (2^32 + 977)^4 × 1.2707681476957356...
  = (2^32 + 977)^4 × (2^32 + 977)^0.0108031509485...
  = (2^32 + 977)^4.0108031509485...
```

Note: base is **`2^32 + 977`**, not `2^32 − 977` (because `p = 2^256 − 2^32 − 977`).

---

## Packet machinery (P135 `packet_p`)

Same `packet_p` as coordinate_packet_shadow / real-decimal ledger:

```text
packet_p × (p − N)           = full defect displacement
packet_p × (2^32+977)^4      = fourth-power shell only
packet_p × (2^32+977)^extra  = correction shim on the packet
packet_p × (Δ − BASE^4)      = shell gap on the packet
```

These are **p↔N / binary-ceiling shadows**, not Λ / GAP_x / GAP_y and not `d`.

---

## Judge Popcorn

**`2^32 + 977` is the crack between 2²⁵⁶ and p.  
`p − N` is that crack raised to about 4.010803.  
Four full turns of the binary→field crack, plus a 1.270768× correction shim.**
