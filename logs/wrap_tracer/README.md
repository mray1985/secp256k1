# Dual-domain wrap tracer

**Status:** instrument only — **0 verified key bits**.

\[
\boxed{\text{coordinates reduce modulo }p,\qquad \text{scalars reduce modulo }N}
\]

## What it records

| Domain | Object | Quotient kept |
|--------|--------|---------------|
| field \(p\) | affine add/double intermediates | signed \(q_p\) |
| scalar \(N\) | \(a\pm b\) when provenance known | signed \(q_N\) |

Event for one affine step:

\[
(q_{\Delta x},\, q_{\Delta y},\, q_\lambda,\, q_x,\, q_y)
\]

## What it does *not* do

* Does not infer \(N\)-wrap from coordinates alone (that is DLP).
* Does not treat \(x\ge N\) as an \(N\)-scalar wrap (shelf \([N,p)\) only).
* Does not claim intrinsic labels on points — quotients are **formula-path** dependent (affine path implemented here).

## Run

```powershell
python dual_domain_wrap_tracer.py --self-check --demo
```

Module API: `add_points_with_trace`, `subtract_points_with_trace`,
`add_with_optional_scalars`, `scalar_add_with_trace`, `scalar_subtract_with_trace`.

Artifact: `logs/wrap_tracer/dual_domain_self_check.json`
