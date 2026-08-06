# ChatSieve TRUE71 — decipherment of `chatsieve_true71_results.txt`

Source: `01_Code/harvesting/ChatSieve_TRUE71.py` → output `chatsieve_true71_results.txt`

## What the script actually does (not infinite-precision sieve)

The script does **not** search keys. It:

1. Computes **band geometry** for puzzle height `h`:
   ```text
   lower = 2^(h-1)
   upper = 2^h - 1
   D     = 2^(h-1)          (band width)
   D/8   = 2^(h-4)
   mid   = lower + D/2 = 3·2^(h-2)
   ```

2. Defines **three lane scalars** (pure integer band markers):
   ```text
   A = mid − D/8
   B = mid
   C = mid + D/8
   ```

3. Takes public point `P = (Px, Py)` and computes **real-space echoes**:
   ```text
   x_echo   = exp(ln(Px) · h/256)   ≈ Px^(h/256)
   y_echo   = exp(ln(Py) · h/256)
   c_echo   = exp(ln(Px³+7) · h/256)
   ```
   (Implemented as `Decimal` log/exp — high precision, but **not mod p / mod N**.)

4. Scores each lane by distance/ratio to echoes and (for solved puzzles) to known `d`.

5. For P135 candidates: applies **Omega filter** `((r·d − z) mod N) mod 9 ∈ {1,4,7}` then **EC verify** `[d]G == P135`.

**Proof rule (correct):** only `scalar_mult(d) == target pubkey` counts.

---

## Structural checks that always pass

For every puzzle height in the file:

```text
x([8]P) = x([(N−8)]P)     True
y([8]P) + y([(N−8)]P) = p  True
```

This is standard secp256k1 involution (N−8 = −8 mod N). It validates the EC implementation, not the private key.

---

## P135 lane table (from file lines 581–629)

| Lane | scalar d | in [2^134,2^135)? | lane / y_echo | log2 drift y |
|------|----------|:-----------------:|--------------:|-------------:|
| **A** mid−D/8 | 29944848289042584784776965453995602608128 | ✓ | 1.114 | +0.156 |
| **B** mid | 32667107224410092492483962313449748299776 | ✓ | 1.215 | +0.282 |
| **C** mid+D/8 | 35389366159777600200190959172903893991424 | ✓ | 1.317 | +0.397 |

These are exactly your tested Lane A/B/C values. **All fail `[d]G = P135`.**

### P135 echoes (filed)

```text
Px  = 9210836494447108270027136741376870869791784014198948301625976867708124077590
Py  = 0x667a05e9a1bdd6f70142b66558bd12ce2c0f9cbc7001b20c8a6a109c80dc5330  (even y lift)

x^(135/256)              = 11463001237408327447691220331129418464562
y^(135/256)              = 26876308129676390477323096284295564392846
(x³+7)^(135/256)         = 35883159410670495955909009950774262134599
```

The curve echo `35883159410670495955909009950774262134599` matches your `figured_it_out.txt` residue — consistent across the framework.

### Omega filter on lanes (script rule)

```text
((r·d − z) mod N) mod 9:

  Lane A → 8   (rejected)
  Lane B → 6   (rejected)
  Lane C → 4   (passes Ω+ phase {1,4,7})
```

Only **Lane C** survives the mod-9 orientation filter — but still **fails EC**. Orientation filter ≠ key.

---

## Calibration on solved puzzles (what lane / echo ratios mean)

For **known** keys, the script prints `lane / priv`. Closest-to-1 ratio picks which lane sits nearest the true scalar — **but the winning lane letter varies by puzzle**:

| Puzzle | nearest lane | best ratio | lane/priv |
|--------|--------------|------------|-----------|
| P70 | C | C | 0.9885 |
| P90 | A | A | 0.9805 |
| P100 | A | A | 1.0038 |
| P130 | C | C | 1.0019 |

**Ruling:** D/8 lanes are **band compass points**, not a universal `d` formula. They approximate solved keys at ~0.84–1.19× depending on height and lane letter.

Echo ratios (`lane / x_echo`, `lane / y_echo`) are **post-hoc real-space comparisons**. For P135, lanes are ~2.6–3.1× `x_echo` and ~1.1–1.3× `y_echo` — they do **not** collapse to 1.0 (no altitude lock from this file alone).

---

## Height 70 block (lines 1–58)

Uses **solved d_70** pubkey, not P71 address. Purpose: calibrate lane drift on a known key at the 70-bit band shape.

Best fit: **Lane C** at `lane/priv = 0.988` (offset −1.12×10^19 from d_70).

This is the same band geometry reused when you later talk about P71's `[2^70, 2^71)` range — but **height 70 ≠ puzzle 71**.

---

## Cross-exam vs Reversal Land claims

| Claim | File evidence | Verdict |
|-------|---------------|---------|
| D/8 descent strips bit depth | Lanes are `mid ± D/8` on **d** band | **Geometry only** — not proven descent on pubkey |
| Echo projection tracks scalar path | Echoes are `Px^(h/256)` in **ℝ**, compared to lane integers | **Diagnostic**, not deterministic |
| Field closure / barcode | Not computed in this file | **Not tested here** |
| Ω mod 9 predicts bridge | Lane C passes for P135; A/B fail | **Partial filter** — C still wrong key |
| Ratio isolates F_n altitude | P135 ratios ≠ 1; solved puzzles vary | **Not isolated** in this output |

---

## Honest state after reading the file

```text
ChatSieve TRUE71 output is a CALIBRATION LOG, not a sieve result.

It confirms:
  ✓ EC math (N−8 reflection)
  ✓ P135 lane scalars A/B/C are in-range band markers
  ✓ Curve echo matches prior figured_it_out residue
  ✓ Lane C alone passes Ω+ mod-9 for those three candidates

It does NOT provide:
  ✗ d_135
  ✗ Any hash160/EC hit
  ✗ Proof that lane/echo ratios uniquely determine d

Next gate for P135: [d]G = P135 with catalog Py branch,
  not lane midpoint ± D/8 alone.
```

## Relation to scaled TDAD lane

Separate track: `T = Σ 2^29·d_i + r` with `2^42` masks (P71) or `~2^134` (P135). ChatSieve lanes are **band midpoints**, not TDAD playlist sums. Both need **`[d]G` EC gate**.
