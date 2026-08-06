# EXHIBIT: projection rejected — filter valid

**Location:** `ARCHIVE/briefcase/misalignments/`

## Right question, clean negative

```text
Not:  does public signal directly become scalar?
But:  does public signal order / cluster scalar behavior?

Answer: mostly no.
Best:  x_ratio / packet_frac ≈ −0.274 Spearman (faint anti-correlation)
Hinge-power warp: ≈ −0.280 (still WEAK)
```

Public coordinates are a **point identity fingerprint**, not a **scalar navigation chart**.

## REJECTED

```text
scalar position from range anchors
scalar position from packet fraction
scalar position from defect fraction
scalar position from signal rank
transferable binary error mask from these rulers
public coordinate signal → scalar range position → transferable P135 prediction
```

Wilderness burned: direct projection and rank-as-compass.

## VALID

```text
public coordinate signal
  → fingerprint / classification / exclusion filter
  → candidate checking
```

## P135_public_fingerprint_hint

```text
neighbors (plain): 4, 30, 18, 20, 58
neighbors (hinge-power): 64, 58, 53, 115, 110
mean scalar_position ≈ 0.54
cluster: middle-ish
confidence: weak
not actionable without RSZ / candidate gate
```

## Gate stack (next lane)

Not “where is d?” — but “given candidate d or k, do side-ledgers agree?”

```text
candidate d
  ↓ range check
  ↓ [d]G x/y check
  ↓ β slot consistency
  ↓ packet fingerprint match
  ↓ p/N shadow match
  ↓ RSZ if signature candidate exists
```

```text
candidate k
  ↓ d = (s*k − z) * r⁻¹ mod N
  ↓ range check
  ↓ [d]G == P135
```

Run: `python candidate_gate_stack.py --d <int>` or `--k <int>`

## Ruling

```text
Instrument:     valid
Projection:     rejected
Rank model:     weak / not navigable
Neighbor hint:  middle-ish, weak
Next move:      packet/β/defect as candidate filters, not scalar predictors
Door:           still [d]G and RSZ
```

Judge Popcorn: **stars confirm where we already think we are; they are not a road sign to d.**
