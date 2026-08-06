# Ledger: Translated-point / doubling branch — CLOSED

> Entire **translated-point / doubling-feature branch is CLOSED** (F-01…F-04).
> No further \(T^{-1}\), \(Y_2\), \(x(4Q)\), \(x(8Q)\), or offset knobs on that machinery.

Also:

> **Mersenne offset rescue — FALSIFIED** (see `LEDGER_MERSENNE_OFFSET_RESCUE.md`).

---

# Ledger: GLV orbit MI — FALSIFIED (degenerate on puzzle keys)

> **GLV order-3 orbit mutual information — FALSIFIED as a pairing probe on puzzles 1–70.**
> Locked labels \(a=\arg\min_j(\lambda^j d\bmod N)\), \(b=\arg\min_j(\beta^j P_x\bmod p)\),
> score \(I(a;b)\). For all puzzle-scale \(d\), \(a\equiv 0\) (multiplying by \(\lambda,\lambda^2\)
> yields larger residues than \(d\)), so \(I\equiv 0\) and \(\Delta\equiv 0\), \(p=1\).

The coordinate label \(b\) does vary (\(\approx 27/20/23\)), but with constant \(a\) there is
no categorical alignment to detect. Any non-degenerate GLV labeling (e.g. relative
orbit index, mid-representative) requires a **new prereg**, not a post-hoc fix.

If the next move leaves single-pair coordinate features, test **neighboring puzzle pairs**.

Artifacts: `F-20260709-05_*`, `f_20260709_05_glv_orbit_mi.py`.
