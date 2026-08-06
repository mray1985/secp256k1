# Pairing promotion gate

## Laboratory rule (locked)

```text
"Looks similar"  ≠  "depends on the correct pairing."
```

The archive preserves the sawtooth as a known false-positive shape.
The harness asks the only useful question:

```text
P_i = [d_i]G     versus     P_π(i) ≠ [d_i]G
```

A genuine pairing-dependent candidate must show three things **simultaneously**:

```text
score_real       strong
score_shuffled   ordinary
Δ = real − shuffled   unusually large
```

The key word is **unusually**. An advantage of `0.125` is neither good nor bad by
itself; its `p ≈ 0.15` says that advantage arises routinely under broken pairings.
So `0.125` is the **known false-positive benchmark**, not a magical cutoff.

---

## What the sawtooth taught us

The factoradic pattern is real, but it also appears in random same-width numbers.
**The sawtooth itself is not the key signal.** Similarity between `d` and `Px`
is not enough. A useful relation must depend on the fact that **this exact point
equals `[d]G`**. When public points are shuffled among private keys, the score
must collapse.

---

## Pre-registration (before peeking)

Register each proposed `F` **before** examining results. Template:

`logs/prereg/F_PREREG_TEMPLATE.md`

Lock in advance:

* exact formula and reductions
* coordinate/scalar domains: `p` or `N`
* score definition
* expected direction
* allowed parameters (no post-hoc grid expansion)
* holdout split
* null families

That prevents another flexible sweep from finding whichever setting resembles a signal.

---

## Trivial classes — exclude

Do **not** promote:

1. **DL recomputation**
   ```text
   F(d,P) = 1{P = [d]G}
   ```
   (or any check that only verifies the already-known solved `d` against its point)

2. **Curve membership alone**
   ```text
   y² − x³ − 7 ≡ 0  (mod p)
   ```
   (every valid curve point satisfies this regardless of which `d` it is paired with)

**Worthwhile middle ground:** a compact transform using `(d, Px, Py)` that is
**not** guaranteed by curve membership alone and **is** destroyed by permutation —
a measurable fingerprint of the correct attachment, not another pretty rhythm.

---

## Promote only if all hold

```text
advantage > 0.12          # beat the known false-positive benchmark
p_shuffle < 0.01          # Δ is unusually large under the null
beats random n-bit
beats random EC pairs
holds out-of-sample
direction consistent across puzzle ranges
```

Harness: `pairing_advantage_filter.py`  
Pre-reg template: `logs/prereg/F_PREREG_TEMPLATE.md`  
Control log: `PAIRING_ADVANTAGE_FILTER_CONTROL.txt`  
Archive: `ARCHIVE/briefcase/factoradic_native_lead_falsified/`
