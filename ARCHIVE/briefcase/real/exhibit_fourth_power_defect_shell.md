# EXHIBIT: fourth-power defect shell

**Location:** `ARCHIVE/briefcase/real/` — does not overwrite prior exhibits.

**Verdict:** modulus-construction scale for the three ceilings. **Not** a private key. **Not** `GAP_x` / `GAP_y`.

Companion verify: `python verify_defect_exponent.py` (writes `exhibit_defect_exponent.json`).

---

## Constants

```text
base_defect:
  2^256 − p = 2^32 + 977 = 4294968273

order_defect:
  p − N = 432420386565659656852420866390673177326

shell:
  base_defect^4 = 340282676544703216937471040975449195841

correction:
  (p − N) / base_defect^4 = 1.27076814769573564427030171001724224368...

relationship:
  p − N = base_defect^4 × 1.2707681476...
        = base_defect^4.010803150948509...
```

---

## Defect scale ladder

```text
2^256
  ↓ 2^32 + 977
p
  ↓ (2^32 + 977)^4 × 1.270768...
N
```

Meaning: the p→N displacement is scaled from the prime-construction defect (fourth-power echo + correction shim).

---

## Normalization for packet shadow work

Coordinate packet identity:

```text
packet × p − packet × N = packet × (p − N)
```

Rewrite with the shell:

```text
packet × (p − N)
  = packet × base_defect^4 × correction
  = packet × (2^32 + 977)^4 × 1.2707681476...
```

That compares packet displacement to the **prime construction defect**, instead of treating `p−N` as an unrelated giant.

---

## Classification (bookkeeping family)

Same family as:

```text
2^256 − p
p − N
packet × (p − N)
map_p_to_n
Lambda_N − Lambda
lambda_y_N − Lambda_N
```

**Not** the same as:

```text
GAP_x = Lambda_N − Lambda mod N
GAP_y = lambda_y_N − Lambda_N mod N
```

Those are bridge-ratio gaps. This exhibit is a **modulus-construction scale**.

---

## Correction multiplier — tests (not a solve)

```text
correction = (p − N) / (2^32 + 977)^4

packet × correction
Λ × correction mod p
Λ1 × correction mod p
lambda_y × correction mod p
GAP_x / correction
GAP_y / correction
delta_k / correction
```

If `correction` appears elsewhere, it is part of the same accounting layer. It does not by itself yield `d` or `k`.

---

## Honest limit

Tells us about architecture of:

```text
2^256, p, N
```

Does **not** tell us:

```text
d, k, P72 pubkey, P135 private key
```

Scalar lock still requires:

```text
s*k = z + r*d mod N
[d]G = P135 public key
```

---

## Judge Popcorn

**It gives us the ruler for measuring the gap between the field courtroom and the scalar courtroom. It is not the key, but it tells us what kind of floor the key is walking on.**
